from app.exceptions.base import ConflictError
from app.models.pipeline import PipelineTemplate, PipelineStage


class PipelineTemplateService:
    def __init__(self, template_repo, stage_repo):
        self.template_repo = template_repo
        self.stage_repo = stage_repo

    def create_with_stages(self, tenant_id, name, stages, is_default=False):
        if is_default:
            self.template_repo.clear_other_defaults(tenant_id)

        template = PipelineTemplate(company_id=tenant_id, name=name, is_default=is_default)
        self.template_repo.add(template)
        self.template_repo.commit()  # flush to get template.id before adding stages

        for stage_data in stages:
            self.stage_repo.add(PipelineStage(pipeline_template_id=template.id, **stage_data))
        self.stage_repo.commit()
        return template

    def list_templates(self, tenant_id):
        return self.template_repo.list(tenant_id).all()

    def get(self, tenant_id, template_id):
        return self.template_repo.get_or_404(template_id, tenant_id)

    def update(self, tenant_id, template_id, name=None, is_default=None, stages=None):
        template = self.template_repo.get_or_404(template_id, tenant_id)

        if name is not None:
            template.name = name

        if is_default is not None:
            if is_default:
                self.template_repo.clear_other_defaults(tenant_id, exclude_id=template.id)
            template.is_default = is_default

        if stages is not None:
            # Replace wholesale rather than diff/patch individual stages —
            # a pipeline's stage list is small (typically 3-7 stages) and
            # edited as a unit in the builder UI, so there's no meaningful
            # "just reorder stage 3" case that a full replace loses.
            self.stage_repo.delete_all_for_template(template.id)
            for stage_data in stages:
                self.stage_repo.add(PipelineStage(pipeline_template_id=template.id, **stage_data))

        self.template_repo.commit()
        return template

    def delete(self, tenant_id, template_id):
        template = self.template_repo.get_or_404(template_id, tenant_id)

        jobs_using = self.template_repo.count_jobs_using(tenant_id, template_id)
        if jobs_using > 0:
            raise ConflictError(
                f"Cannot delete '{template.name}' — {jobs_using} job(s) currently use this pipeline. "
                "Reassign them to a different pipeline first."
            )

        self.template_repo.delete(template)
        self.template_repo.commit()
