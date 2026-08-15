from datetime import datetime, timezone
from app.exceptions.base import BusinessRuleViolationError
from app.models.job import Job, JobApprovalStep
from app.validators.state_transitions import assert_valid_job_transition


class JobService:
    def __init__(self, job_repo, approval_repo, user_repo, approval_chain_service, audit_service=None):
        self.job_repo = job_repo
        self.approval_repo = approval_repo
        self.user_repo = user_repo
        self.approval_chain_service = approval_chain_service
        self.audit_service = audit_service

    def create_draft(self, tenant_id, created_by, title, **fields):
        job = Job(
            company_id=tenant_id,
            created_by=created_by,
            title=title,
            status="draft",
            **fields,
        )
        self.job_repo.add(job)
        self.job_repo.commit()
        return job

    def get(self, tenant_id, job_id):
        return self.job_repo.get_or_404(job_id, tenant_id)

    def list(self, tenant_id, status=None):
        query = self.job_repo.list(tenant_id)
        if status:
            query = query.filter(Job.status == status)
        return query.all()

    def list_approval_steps(self, tenant_id, job_id):
        self.job_repo.get_or_404(job_id, tenant_id)  # confirms the job belongs to this tenant
        return self.approval_repo.list_for_job(tenant_id, job_id).all()

    def update_fields(self, tenant_id, job_id, **fields):
        """
        Ordinary field edits (title, description, salary range, ...) —
        deliberately does NOT accept `status` as a field. See module
        docstring / Phase 11.6 for why status changes are separate.
        """
        fields.pop("status", None)
        job = self.job_repo.get_or_404(job_id, tenant_id)
        for key, value in fields.items():
            setattr(job, key, value)
        self.job_repo.commit()
        return job

    def submit_for_approval(self, tenant_id, job_id, acted_by=None):
    
        job = self.job_repo.get_or_404(job_id, tenant_id)
        assert_valid_job_transition(job.status, "pending_approval")

        chain = self.approval_chain_service.get_chain(tenant_id, "job")
        if chain is None or not chain.steps:
            raise BusinessRuleViolationError(
                "No approval chain is configured for jobs yet. "
                "An admin needs to set one up before jobs can be submitted for approval."
            )

        old_status = job.status
        job.status = "pending_approval"
        for chain_step in chain.steps:
            self.approval_repo.add(
                JobApprovalStep(
                    company_id=tenant_id,
                    job_id=job.id,
                    approver_role_id=chain_step.role_id,
                    step_order=chain_step.step_order,
                )
            )
        self.approval_repo.commit()
        self._audit(tenant_id, job.id, "status_changed", acted_by, old_status, job.status)
        return job

    def approve_step(self, tenant_id, job_id, approval_step_id, acted_by, comment=None):
        job = self.job_repo.get_or_404(job_id, tenant_id)
        step = self.approval_repo.get_or_404(approval_step_id, tenant_id)
        if step.job_id != job.id:
            raise BusinessRuleViolationError("Approval step does not belong to this job")

        acting_user = self.user_repo.get_or_404(acted_by, tenant_id)
        self.approval_chain_service.assert_can_act_on_step(step, acting_user)

        step.status = "approved"
        step.acted_by = acted_by
        step.comment = comment
        step.acted_at = datetime.now(timezone.utc)
        self.approval_repo.commit()

        if self._all_steps_approved(tenant_id, job.id):
            self._publish(job, acted_by)
        return job

    def reject_step(self, tenant_id, job_id, approval_step_id, acted_by, comment=None):
        job = self.job_repo.get_or_404(job_id, tenant_id)
        step = self.approval_repo.get_or_404(approval_step_id, tenant_id)
        if step.job_id != job.id:
            raise BusinessRuleViolationError("Approval step does not belong to this job")

        acting_user = self.user_repo.get_or_404(acted_by, tenant_id)
        self.approval_chain_service.assert_can_act_on_step(step, acting_user)

        step.status = "rejected"
        step.acted_by = acted_by
        step.comment = comment
        step.acted_at = datetime.now(timezone.utc)
        self.approval_repo.commit()

        old_status = job.status
        assert_valid_job_transition(job.status, "draft")
        job.status = "draft"
        self.job_repo.commit()
        self._audit(tenant_id, job.id, "status_changed", acted_by, old_status, job.status)
        return job

    def close(self, tenant_id, job_id, acted_by=None):
        job = self.job_repo.get_or_404(job_id, tenant_id)
        assert_valid_job_transition(job.status, "closed")
        old_status = job.status
        job.status = "closed"
        job.closed_at = datetime.now(timezone.utc)
        self.job_repo.commit()
        self._audit(tenant_id, job.id, "status_changed", acted_by, old_status, job.status)
        return job

    def archive(self, tenant_id, job_id, acted_by=None):
        job = self.job_repo.get_or_404(job_id, tenant_id)
        assert_valid_job_transition(job.status, "archived")
        old_status = job.status
        job.status = "archived"
        self.job_repo.commit()
        self._audit(tenant_id, job.id, "status_changed", acted_by, old_status, job.status)
        return job


    def _all_steps_approved(self, tenant_id, job_id):
        steps = self.approval_repo.list_for_job(tenant_id, job_id).all()
        return bool(steps) and all(s.status == "approved" for s in steps)

    def _publish(self, job: Job, acted_by=None):
        assert_valid_job_transition(job.status, "published")
        old_status = job.status
        job.status = "published"
        job.published_at = datetime.now(timezone.utc)
        self.job_repo.commit()
        self._audit(job.company_id, job.id, "status_changed", acted_by, old_status, job.status)

    def _audit(self, tenant_id, job_id, action, acted_by, old_status, new_status):
        if self.audit_service is not None:
            self.audit_service.log(
                company_id=tenant_id, entity_type="Job", entity_id=job_id, action=action,
                actor_id=acted_by, old_value={"status": old_status}, new_value={"status": new_status},
            )
