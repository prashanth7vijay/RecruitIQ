from app.models.job import Job, JobApprovalStep
from app.models.pipeline import PipelineTemplate, PipelineStage
from app.repositories.base_repository import TenantScopedRepository


class JobRepository(TenantScopedRepository):
    model = Job


class PipelineTemplateRepository(TenantScopedRepository):
    model = PipelineTemplate

    def count_jobs_using(self, tenant_id, template_id):
        if tenant_id is None:
            raise ValueError("PipelineTemplateRepository: tenant_id is required")
        return (
            self.session.query(Job)
            .filter(Job.company_id == tenant_id, Job.pipeline_template_id == template_id)
            .count()
        )

    def clear_other_defaults(self, tenant_id, exclude_id=None):
        query = self._base_query(tenant_id).filter(PipelineTemplate.is_default.is_(True))
        if exclude_id is not None:
            query = query.filter(PipelineTemplate.id != exclude_id)
        query.update({"is_default": False}, synchronize_session=False)


class JobApprovalStepRepository(TenantScopedRepository):
    model = JobApprovalStep

    def list_for_job(self, tenant_id, job_id):
        return self._base_query(tenant_id).filter(JobApprovalStep.job_id == job_id).order_by(
            JobApprovalStep.step_order
        )


class PipelineStageRepository:

    def __init__(self, session):
        self.session = session

    def list_for_template(self, pipeline_template_id):
        return (
            self.session.query(PipelineStage)
            .filter(PipelineStage.pipeline_template_id == pipeline_template_id)
            .order_by(PipelineStage.stage_order)
        )

    def delete_all_for_template(self, pipeline_template_id):
        self.session.query(PipelineStage).filter(
            PipelineStage.pipeline_template_id == pipeline_template_id
        ).delete(synchronize_session=False)

    def add(self, obj):
        self.session.add(obj)
        return obj

    def commit(self):
        self.session.commit()
