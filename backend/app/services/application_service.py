from datetime import datetime, timezone

from app.exceptions.base import BusinessRuleViolationError, ConflictError
from app.models.application import Application, ApplicationStageHistory
from app.validators.state_transitions import assert_valid_job_transition


class ApplicationService:
    def __init__(self, application_repo, history_repo, job_repo, candidate_service, stage_repo, event_bus=None, audit_service=None):
        self.application_repo = application_repo
        self.history_repo = history_repo
        self.job_repo = job_repo
        self.candidate_service = candidate_service
        self.stage_repo = stage_repo
        self.event_bus = event_bus
        self.audit_service = audit_service

    def apply(self, tenant_id, job_id, email, first_name, last_name, phone=None, source="career_portal"):
        job = self.job_repo.get_or_404(job_id, tenant_id)
        if job.status != "published":
            raise BusinessRuleViolationError("This job is not currently accepting applications")
        if job.pipeline_template_id is None:
            raise BusinessRuleViolationError("This job has no pipeline configured yet")

        stages = list(self.stage_repo.list_for_template(job.pipeline_template_id))
        if not stages:
            raise BusinessRuleViolationError("This job's pipeline has no stages configured")
        first_stage = stages[0]

        candidate, profile = self.candidate_service.get_or_create_profile(
            tenant_id, email, first_name, last_name, phone, source=source
        )

        existing = self.application_repo.get_by_job_and_candidate(tenant_id, job_id, candidate.id)
        if existing is not None:
            raise ConflictError("You have already applied to this job")

        application = Application(
            company_id=tenant_id,
            job_id=job_id,
            candidate_id=candidate.id,
            candidate_profile_id=profile.id,
            current_stage_id=first_stage.id,
        )
        self.application_repo.add(application)
        self.application_repo.commit()

        self.history_repo.add(
            ApplicationStageHistory(
                application_id=application.id, from_stage_id=None, to_stage_id=first_stage.id, moved_by=None
            )
        )
        self.history_repo.commit()
        return application

    def list_for_job(self, tenant_id, job_id):
        return self.application_repo.list(tenant_id, job_id=job_id).all()

    def get(self, tenant_id, application_id):
        return self.application_repo.get_or_404(application_id, tenant_id)

    def get_timeline(self, tenant_id, application_id):
        application = self.application_repo.get_or_404(application_id, tenant_id)
        return self.history_repo.list_for_application(application.id).all()

    def move_stage(self, tenant_id, application_id, target_stage_id, moved_by, note=None):
        application = self.application_repo.get_or_404(application_id, tenant_id)
        if application.status != "active":
            raise BusinessRuleViolationError(
                f"Cannot move a {application.status} application"
            )

        from_stage_id = application.current_stage_id
        application.current_stage_id = target_stage_id
        self.application_repo.commit()

        self.history_repo.add(
            ApplicationStageHistory(
                application_id=application.id,
                from_stage_id=from_stage_id,
                to_stage_id=target_stage_id,
                moved_by=moved_by,
                note=note,
            )
        )
        self.history_repo.commit()

        if self.event_bus is not None:
            self.event_bus.publish(
                "application.stage_changed",
                {"application_id": str(application.id), "to_stage_id": str(target_stage_id)},
            )

        return application

    def reject(self, tenant_id, application_id, reason=None, acted_by=None):
        application = self.application_repo.get_or_404(application_id, tenant_id)
        if application.status != "active":
            raise BusinessRuleViolationError(f"Cannot reject a {application.status} application")

        application.status = "rejected"
        application.rejected_at = datetime.now(timezone.utc)
        application.rejection_reason = reason
        self.application_repo.commit()

        if self.audit_service is not None:
            self.audit_service.log(
                company_id=tenant_id, entity_type="Application", entity_id=application.id,
                action="rejected", actor_id=acted_by, new_value={"reason": reason},
            )
        return application
