from flask import Blueprint, request, jsonify, current_app

from app.api.v1.companies.schemas import PublicCompanySchema
from app.api.v1.public.schemas import PublicJobSchema, ApplySchema, ApplicationConfirmationSchema
from app.exceptions.base import NotFoundError
from app.extensions import db, limiter
from app.repositories.application_repository import ApplicationRepository, ApplicationStageHistoryRepository
from app.repositories.candidate_repository import (
    CandidateRepository,
    CandidateProfileRepository,
    ResumeRepository,
)
from app.repositories.company_repository import CompanyRepository
from app.repositories.job_repository import JobRepository, PipelineStageRepository
from app.services.application_service import ApplicationService
from app.services.candidate_service import CandidateService
from app.services.company_service import CompanyService
from app.services.event_bus import EventBus
from app.services.file_upload_service import FileUploadService
from app.services.job_service import JobService
from app.storage.factory import build_storage

public_bp = Blueprint("public", __name__, url_prefix="/api/v1/public")


def _resolve_tenant_id(company_slug):
    company_repo = CompanyRepository(db.session)
    company = company_repo.get_by_slug(company_slug)
    if company is None:
        raise NotFoundError("Organization not found")
    return company.id


def _build_job_service():
    return JobService(
        job_repo=JobRepository(db.session),
        approval_repo=None,  # not needed for public read-only job listing
        user_repo=None,
        approval_chain_service=None,
    )


def _build_candidate_service():
    return CandidateService(
        candidate_repo=CandidateRepository(db.session),
        profile_repo=CandidateProfileRepository(db.session),
        resume_repo=ResumeRepository(db.session),
        event_bus=EventBus(),
    )


def _build_application_service():
    return ApplicationService(
        application_repo=ApplicationRepository(db.session),
        history_repo=ApplicationStageHistoryRepository(db.session),
        job_repo=JobRepository(db.session),
        candidate_service=_build_candidate_service(),
        stage_repo=PipelineStageRepository(db.session),
        event_bus=EventBus(),
    )


@public_bp.route("/<string:company_slug>/company", methods=["GET"])
@limiter.limit("30 per minute")
def get_public_company(company_slug):
    company_repo = CompanyRepository(db.session)
    company = company_repo.get_by_slug(company_slug)
    if company is None:
        raise NotFoundError("Organization not found")

    storage = build_storage(current_app.config)
    service = CompanyService(company_repo=company_repo)
    branding = service.get_branding(company.id, storage)

    payload = {"name": company.name, "slug": company.slug, "branding": branding}
    return jsonify({"success": True, "data": PublicCompanySchema().dump(payload), "meta": {}})


@public_bp.route("/<string:company_slug>/jobs", methods=["GET"])
@limiter.limit("30 per minute")
def list_published_jobs(company_slug):
    tenant_id = _resolve_tenant_id(company_slug)
    service = _build_job_service()
    jobs = service.list(tenant_id, status="published")
    return jsonify({"success": True, "data": PublicJobSchema(many=True).dump(jobs), "meta": {}})


@public_bp.route("/<string:company_slug>/jobs/<uuid:job_id>", methods=["GET"])
@limiter.limit("30 per minute")
def get_published_job(company_slug, job_id):
    tenant_id = _resolve_tenant_id(company_slug)
    service = _build_job_service()
    job = service.get(tenant_id, job_id)
    if job.status != "published":
        raise NotFoundError("Job not found")  # draft/closed jobs are invisible publicly, not "403"
    return jsonify({"success": True, "data": PublicJobSchema().dump(job), "meta": {}})


@public_bp.route("/<string:company_slug>/jobs/<uuid:job_id>/apply", methods=["POST"])
@limiter.limit("10 per minute")  # tighter than reads — the write endpoint on the exposed surface
def apply_to_job(company_slug, job_id):
    tenant_id = _resolve_tenant_id(company_slug)

    # multipart/form-data: candidate fields arrive as form fields, resume as a file
    dto = ApplySchema().load(request.form.to_dict())

    service = _build_application_service()
    application = service.apply(
        tenant_id=tenant_id,
        job_id=job_id,
        email=dto["email"],
        first_name=dto["first_name"],
        last_name=dto["last_name"],
        phone=dto.get("phone"),
    )

    if "resume" in request.files and request.files["resume"].filename:
        storage = build_storage(current_app.config)
        upload_service = FileUploadService(storage, max_size_mb=current_app.config["MAX_UPLOAD_SIZE_MB"])
        storage_key, original_filename = upload_service.upload_resume(
            request.files["resume"], tenant_id=tenant_id, candidate_id=application.candidate_id
        )
        _build_candidate_service().attach_resume(
            tenant_id, application.candidate_profile_id, storage_key, original_filename
        )

    return jsonify(
        {"success": True, "data": ApplicationConfirmationSchema().dump(application), "meta": {}}
    ), 201
