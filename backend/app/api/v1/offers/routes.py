from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api.v1.offers.schemas import (
    CreateOfferSchema,
    ApprovalActionSchema,
    OfferSchema,
    OfferApprovalStepSchema,
)
from app.exceptions.base import UnauthenticatedError
from app.extensions import db
from app.repositories.approval_chain_repository import ApprovalChainRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.offer_repository import OfferRepository, OfferApprovalStepRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.services.approval_chain_service import ApprovalChainService
from app.services.audit_service import AuditService
from app.services.event_bus import EventBus
from app.services.offer_service import OfferService
from app.utils.permissions import require_permission

offers_bp = Blueprint("offers", __name__, url_prefix="/api/v1/offers")


def _build_service() -> OfferService:
    return OfferService(
        offer_repo=OfferRepository(db.session),
        approval_repo=OfferApprovalStepRepository(db.session),
        user_repo=UserRepository(db.session),
        approval_chain_service=ApprovalChainService(
            chain_repo=ApprovalChainRepository(db.session), role_repo=RoleRepository(db.session)
        ),
        event_bus=EventBus(),
        audit_service=AuditService(AuditLogRepository(db.session)),
    )


def _tenant_id():
    if g.get("tenant_id") is None:
        raise UnauthenticatedError("Authentication required")
    return g.tenant_id


@offers_bp.route("", methods=["POST"])
@jwt_required()
@require_permission("offer.create")
def create_offer():
    dto = CreateOfferSchema().load(request.get_json() or {})
    service = _build_service()
    offer = service.create_draft(tenant_id=_tenant_id(), created_by=get_jwt_identity(), **dto)
    return jsonify({"success": True, "data": OfferSchema().dump(offer), "meta": {}}), 201


@offers_bp.route("", methods=["GET"])
@jwt_required()
def list_offers():
    application_id = request.args.get("application_id")
    service = _build_service()
    offers = service.list_for_application(_tenant_id(), application_id) if application_id else []
    return jsonify({"success": True, "data": OfferSchema(many=True).dump(offers), "meta": {}})


@offers_bp.route("/<uuid:offer_id>", methods=["GET"])
@jwt_required()
def get_offer(offer_id):
    service = _build_service()
    offer = service.get(_tenant_id(), offer_id)
    return jsonify({"success": True, "data": OfferSchema().dump(offer), "meta": {}})


@offers_bp.route("/<uuid:offer_id>/approval-steps", methods=["GET"])
@jwt_required()
def list_approval_steps(offer_id):
    service = _build_service()
    steps = service.list_approval_steps(_tenant_id(), offer_id)
    return jsonify({"success": True, "data": OfferApprovalStepSchema(many=True).dump(steps), "meta": {}})


@offers_bp.route("/<uuid:offer_id>/submit", methods=["POST"])
@jwt_required()
@require_permission("offer.create")
def submit_for_approval(offer_id):
    service = _build_service()
    offer = service.submit_for_approval(_tenant_id(), offer_id)
    return jsonify({"success": True, "data": OfferSchema().dump(offer), "meta": {}})


@offers_bp.route("/<uuid:offer_id>/approval-steps/<uuid:step_id>/approve", methods=["POST"])
@jwt_required()
@require_permission("offer.approve")
def approve_step(offer_id, step_id):
    dto = ApprovalActionSchema().load(request.get_json() or {})
    service = _build_service()
    offer = service.approve_step(_tenant_id(), offer_id, step_id, acted_by=get_jwt_identity(), comment=dto.get("comment"))
    return jsonify({"success": True, "data": OfferSchema().dump(offer), "meta": {}})


@offers_bp.route("/<uuid:offer_id>/approval-steps/<uuid:step_id>/reject", methods=["POST"])
@jwt_required()
@require_permission("offer.approve")
def reject_step(offer_id, step_id):
    dto = ApprovalActionSchema().load(request.get_json() or {})
    service = _build_service()
    offer = service.reject_step(_tenant_id(), offer_id, step_id, acted_by=get_jwt_identity(), comment=dto.get("comment"))
    return jsonify({"success": True, "data": OfferSchema().dump(offer), "meta": {}})


# accept/decline/withdraw use offer.create (not offer.approve) — these
# record the CANDIDATE's decision, entered by a recruiter, since there's
# no authenticated candidate portal for offers yet (a real gap, noted in
# the README). offer.approve is only for internal approval-chain steps.
@offers_bp.route("/<uuid:offer_id>/accept", methods=["POST"])
@jwt_required()
@require_permission("offer.create")
def accept_offer(offer_id):
    service = _build_service()
    offer = service.accept(_tenant_id(), offer_id, acted_by=get_jwt_identity())
    return jsonify({"success": True, "data": OfferSchema().dump(offer), "meta": {}})


@offers_bp.route("/<uuid:offer_id>/decline", methods=["POST"])
@jwt_required()
@require_permission("offer.create")
def decline_offer(offer_id):
    service = _build_service()
    offer = service.decline(_tenant_id(), offer_id, acted_by=get_jwt_identity())
    return jsonify({"success": True, "data": OfferSchema().dump(offer), "meta": {}})


@offers_bp.route("/<uuid:offer_id>/withdraw", methods=["POST"])
@jwt_required()
@require_permission("offer.create")
def withdraw_offer(offer_id):
    service = _build_service()
    offer = service.withdraw(_tenant_id(), offer_id)
    return jsonify({"success": True, "data": OfferSchema().dump(offer), "meta": {}})
