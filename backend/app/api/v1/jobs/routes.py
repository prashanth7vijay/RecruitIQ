from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api.v1.jobs.schemas import (
    CreateJobSchema,
    UpdateJobSchema,
    ApprovalActionSchema,
    ApprovalStepSchema,
    JobSchema,
)
from app.exceptions.base import UnauthenticatedError
from app.extensions import db
from app.repositories.approval_chain_repository import ApprovalChainRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.job_repository import JobRepository, JobApprovalStepRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.services.approval_chain_service import ApprovalChainService
from app.services.audit_service import AuditService
from app.services.job_service import JobService
from app.utils.permissions import require_permission

jobs_bp = Blueprint("jobs", __name__, url_prefix="/api/v1/jobs")


def _build_service() -> JobService:
    return JobService(
        job_repo=JobRepository(db.session),
        approval_repo=JobApprovalStepRepository(db.session),
        user_repo=UserRepository(db.session),
        approval_chain_service=ApprovalChainService(
            chain_repo=ApprovalChainRepository(db.session), role_repo=RoleRepository(db.session)
        ),
        audit_service=AuditService(AuditLogRepository(db.session)),
    )


def _tenant_id():
    if g.get("tenant_id") is None:
        raise UnauthenticatedError("Authentication required")
    return g.tenant_id


@jobs_bp.route("", methods=["GET"])
@jwt_required()
def list_jobs():
    from app.utils.pagination import paginate_query
    from app.models.job import Job

    status = request.args.get("status")
    query = JobRepository(db.session).list(_tenant_id())
    if status:
        query = query.filter(Job.status == status)
    # Deterministic order is required for OFFSET/LIMIT pagination to be
    # correct at all — without it Postgres is free to return rows in a
    # different order on every call, which means page 2 can silently
    # repeat or skip rows relative to page 1. Found while profiling
    # this query for Phase 2 (see docs/database-optimization.md).
    query = query.order_by(Job.created_at.desc())
    jobs, pagination_meta = paginate_query(query)
    return jsonify({"success": True, "data": JobSchema(many=True).dump(jobs), "meta": pagination_meta})


@jobs_bp.route("", methods=["POST"])
@jwt_required()
@require_permission("job.create")
def create_job():
    dto = CreateJobSchema().load(request.get_json() or {})
    title = dto.pop("title")
    service = _build_service()
    job = service.create_draft(
        tenant_id=_tenant_id(), created_by=get_jwt_identity(), title=title, **dto
    )
    return jsonify({"success": True, "data": JobSchema().dump(job), "meta": {}}), 201


@jobs_bp.route("/<uuid:job_id>", methods=["GET"])
@jwt_required()
def get_job(job_id):
    service = _build_service()
    job = service.get(_tenant_id(), job_id)
    return jsonify({"success": True, "data": JobSchema().dump(job), "meta": {}})


@jobs_bp.route("/<uuid:job_id>", methods=["PATCH"])
@jwt_required()
@require_permission("job.create")
def update_job(job_id):
    dto = UpdateJobSchema().load(request.get_json() or {})
    service = _build_service()
    job = service.update_fields(_tenant_id(), job_id, **dto)
    return jsonify({"success": True, "data": JobSchema().dump(job), "meta": {}})


@jobs_bp.route("/<uuid:job_id>/approval-steps", methods=["GET"])
@jwt_required()
def list_approval_steps(job_id):
    service = _build_service()
    steps = service.list_approval_steps(_tenant_id(), job_id)
    return jsonify({"success": True, "data": ApprovalStepSchema(many=True).dump(steps), "meta": {}})


@jobs_bp.route("/<uuid:job_id>/submit", methods=["POST"])
@jwt_required()
@require_permission("job.create")
def submit_for_approval(job_id):
    service = _build_service()
    job = service.submit_for_approval(_tenant_id(), job_id, acted_by=get_jwt_identity())
    return jsonify({"success": True, "data": JobSchema().dump(job), "meta": {}})


@jobs_bp.route("/<uuid:job_id>/approval-steps/<uuid:step_id>/approve", methods=["POST"])
@jwt_required()
@require_permission("job.approve")
def approve_step(job_id, step_id):
    dto = ApprovalActionSchema().load(request.get_json() or {})
    service = _build_service()
    job = service.approve_step(
        _tenant_id(), job_id, step_id, acted_by=get_jwt_identity(), comment=dto.get("comment")
    )
    return jsonify({"success": True, "data": JobSchema().dump(job), "meta": {}})


@jobs_bp.route("/<uuid:job_id>/approval-steps/<uuid:step_id>/reject", methods=["POST"])
@jwt_required()
@require_permission("job.approve")
def reject_step(job_id, step_id):
    dto = ApprovalActionSchema().load(request.get_json() or {})
    service = _build_service()
    job = service.reject_step(
        _tenant_id(), job_id, step_id, acted_by=get_jwt_identity(), comment=dto.get("comment")
    )
    return jsonify({"success": True, "data": JobSchema().dump(job), "meta": {}})


@jobs_bp.route("/<uuid:job_id>/close", methods=["POST"])
@jwt_required()
@require_permission("job.close")
def close_job(job_id):
    service = _build_service()
    job = service.close(_tenant_id(), job_id, acted_by=get_jwt_identity())
    return jsonify({"success": True, "data": JobSchema().dump(job), "meta": {}})


@jobs_bp.route("/<uuid:job_id>/archive", methods=["POST"])
@jwt_required()
@require_permission("job.close")
def archive_job(job_id):
    service = _build_service()
    job = service.archive(_tenant_id(), job_id, acted_by=get_jwt_identity())
    return jsonify({"success": True, "data": JobSchema().dump(job), "meta": {}})
