from flask import Blueprint, request, jsonify, g, current_app
from flask_jwt_extended import jwt_required

from app.api.v1.companies.schemas import (
    UpdateCompanySchema,
    CompanySchema,
    UpdateBrandingSchema,
    BrandingSchema,
)
from app.exceptions.base import UnauthenticatedError, ValidationError
from app.extensions import db
from app.repositories.company_repository import CompanyRepository
from app.services.company_service import CompanyService
from app.services.file_upload_service import FileUploadService
from app.storage.factory import build_storage
from app.utils.permissions import require_permission

companies_bp = Blueprint("companies", __name__, url_prefix="/api/v1/companies")


def _build_service() -> CompanyService:
    return CompanyService(company_repo=CompanyRepository(db.session))


def _tenant_id():
    if g.get("tenant_id") is None:
        raise UnauthenticatedError("Authentication required")
    return g.tenant_id


@companies_bp.route("/me", methods=["GET"])
@jwt_required()
@require_permission("company.manage_settings")
def get_own_company():
    service = _build_service()
    company = service.get_own_company(_tenant_id())
    return jsonify({"success": True, "data": CompanySchema().dump(company), "meta": {}})


@companies_bp.route("/me", methods=["PATCH"])
@jwt_required()
@require_permission("company.manage_settings")
def update_own_company():
    dto = UpdateCompanySchema().load(request.get_json() or {})
    service = _build_service()
    company = service.update_settings(_tenant_id(), _tenant_id(), **dto)
    return jsonify({"success": True, "data": CompanySchema().dump(company), "meta": {}})



@companies_bp.route("/me/branding", methods=["GET"])
@jwt_required()
@require_permission("company.manage_settings")
def get_branding():
    storage = build_storage(current_app.config)
    service = _build_service()
    branding = service.get_branding(_tenant_id(), storage)
    return jsonify({"success": True, "data": BrandingSchema().dump(branding), "meta": {}})


@companies_bp.route("/me/branding", methods=["PATCH"])
@jwt_required()
@require_permission("company.manage_settings")
def update_branding():
    dto = UpdateBrandingSchema().load(request.get_json() or {})
    service = _build_service()
    service.update_branding(_tenant_id(), _tenant_id(), **dto)
    storage = build_storage(current_app.config)
    branding = service.get_branding(_tenant_id(), storage)
    return jsonify({"success": True, "data": BrandingSchema().dump(branding), "meta": {}})


@companies_bp.route("/me/branding/assets", methods=["POST"])
@jwt_required()
@require_permission("company.manage_settings")
def upload_branding_asset():
    asset_type = request.form.get("asset_type")
    if asset_type not in {"logo", "favicon", "cover"}:
        raise ValidationError("asset_type must be one of: logo, favicon, cover")

    file_obj = request.files.get("file")
    if file_obj is None or not file_obj.filename:
        raise ValidationError("A file is required")

    storage = build_storage(current_app.config)
    upload_service = FileUploadService(storage)
    storage_key, _ext = upload_service.upload_image(file_obj, tenant_id=_tenant_id(), asset_type=asset_type)

    service = _build_service()
    service.set_branding_asset(_tenant_id(), _tenant_id(), asset_type, storage_key)
    branding = service.get_branding(_tenant_id(), storage)
    return jsonify({"success": True, "data": BrandingSchema().dump(branding), "meta": {}}), 201
