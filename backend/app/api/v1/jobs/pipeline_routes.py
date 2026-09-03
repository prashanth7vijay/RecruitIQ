from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required

from app.api.v1.jobs.pipeline_schemas import (
    CreatePipelineTemplateSchema,
    UpdatePipelineTemplateSchema,
    PipelineTemplateSchema,
)
from app.exceptions.base import UnauthenticatedError
from app.extensions import db
from app.repositories.job_repository import PipelineTemplateRepository, PipelineStageRepository
from app.services.pipeline_template_service import PipelineTemplateService
from app.utils.permissions import require_permission

pipeline_templates_bp = Blueprint(
    "pipeline_templates", __name__, url_prefix="/api/v1/pipeline-templates"
)


def _build_service() -> PipelineTemplateService:
    return PipelineTemplateService(
        template_repo=PipelineTemplateRepository(db.session),
        stage_repo=PipelineStageRepository(db.session),
    )


def _tenant_id():
    if g.get("tenant_id") is None:
        raise UnauthenticatedError("Authentication required")
    return g.tenant_id


@pipeline_templates_bp.route("", methods=["GET"])
@jwt_required()
@require_permission("job.create", "pipeline.manage")
def list_templates():
    service = _build_service()
    templates = service.list_templates(_tenant_id())
    return jsonify(
        {"success": True, "data": PipelineTemplateSchema(many=True).dump(templates), "meta": {}}
    )


@pipeline_templates_bp.route("", methods=["POST"])
@jwt_required()
@require_permission("pipeline.manage")
def create_template():
    dto = CreatePipelineTemplateSchema().load(request.get_json() or {})
    service = _build_service()
    template = service.create_with_stages(
        tenant_id=_tenant_id(), name=dto["name"], stages=dto["stages"], is_default=dto["is_default"]
    )
    return jsonify(
        {"success": True, "data": PipelineTemplateSchema().dump(template), "meta": {}}
    ), 201


@pipeline_templates_bp.route("/<uuid:template_id>", methods=["GET"])
@jwt_required()
@require_permission("job.create", "pipeline.manage")
def get_template(template_id):
    service = _build_service()
    template = service.get(_tenant_id(), template_id)
    return jsonify({"success": True, "data": PipelineTemplateSchema().dump(template), "meta": {}})


@pipeline_templates_bp.route("/<uuid:template_id>", methods=["PATCH"])
@jwt_required()
@require_permission("pipeline.manage")
def update_template(template_id):
    dto = UpdatePipelineTemplateSchema().load(request.get_json() or {})
    service = _build_service()
    template = service.update(
        _tenant_id(),
        template_id,
        name=dto.get("name"),
        is_default=dto.get("is_default"),
        stages=dto.get("stages"),
    )
    return jsonify({"success": True, "data": PipelineTemplateSchema().dump(template), "meta": {}})


@pipeline_templates_bp.route("/<uuid:template_id>", methods=["DELETE"])
@jwt_required()
@require_permission("pipeline.manage")
def delete_template(template_id):
    service = _build_service()
    service.delete(_tenant_id(), template_id)
    return jsonify({"success": True, "data": None, "meta": {}})
