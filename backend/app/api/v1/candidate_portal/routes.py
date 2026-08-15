from flask import Blueprint, jsonify, g

from app.api.v1.candidate_portal.schemas import (
    CandidateMeSchema,
    MyApplicationSchema,
    MyInterviewSchema,
    MyOfferSchema,
)
from app.extensions import db
from app.repositories.offer_repository import OfferRepository, OfferApprovalStepRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.approval_chain_repository import ApprovalChainRepository
from app.repositories.user_repository import UserRepository
from app.services.approval_chain_service import ApprovalChainService
from app.services.candidate_portal_service import CandidatePortalService
from app.services.offer_service import OfferService
from app.utils.candidate_auth import require_candidate_auth

candidate_portal_bp = Blueprint("candidate_portal", __name__, url_prefix="/api/v1/candidate-portal")


def _build_service() -> CandidatePortalService:
    offer_service = OfferService(
        offer_repo=OfferRepository(db.session),
        approval_repo=OfferApprovalStepRepository(db.session),
        user_repo=UserRepository(db.session),
        approval_chain_service=ApprovalChainService(
            chain_repo=ApprovalChainRepository(db.session), role_repo=RoleRepository(db.session)
        ),
    )
    return CandidatePortalService(session=db.session, offer_service=offer_service)


@candidate_portal_bp.route("/me", methods=["GET"])
@require_candidate_auth
def get_me():
    service = _build_service()
    candidate = service.get_candidate(g.candidate_id)
    return jsonify({"success": True, "data": CandidateMeSchema().dump(candidate), "meta": {}})


@candidate_portal_bp.route("/applications", methods=["GET"])
@require_candidate_auth
def list_applications():
    service = _build_service()
    rows = service.list_my_applications(g.candidate_id)
    return jsonify({"success": True, "data": MyApplicationSchema(many=True).dump(rows), "meta": {}})


@candidate_portal_bp.route("/applications/<uuid:application_id>", methods=["GET"])
@require_candidate_auth
def get_application(application_id):
    service = _build_service()
    row = service.get_my_application(g.candidate_id, application_id)
    return jsonify({"success": True, "data": MyApplicationSchema().dump(row), "meta": {}})


@candidate_portal_bp.route("/applications/<uuid:application_id>/interviews", methods=["GET"])
@require_candidate_auth
def list_interviews(application_id):
    service = _build_service()
    interviews = service.list_my_interviews(g.candidate_id, application_id)
    return jsonify({"success": True, "data": MyInterviewSchema(many=True).dump(interviews), "meta": {}})


@candidate_portal_bp.route("/offers", methods=["GET"])
@require_candidate_auth
def list_offers():
    service = _build_service()
    rows = service.list_my_offers(g.candidate_id)
    return jsonify({"success": True, "data": MyOfferSchema(many=True).dump(rows), "meta": {}})


@candidate_portal_bp.route("/offers/<uuid:offer_id>/accept", methods=["POST"])
@require_candidate_auth
def accept_offer(offer_id):
    service = _build_service()
    offer = service.accept_my_offer(g.candidate_id, offer_id)
    return jsonify({"success": True, "data": {"id": str(offer.id), "status": offer.status}, "meta": {}})


@candidate_portal_bp.route("/offers/<uuid:offer_id>/decline", methods=["POST"])
@require_candidate_auth
def decline_offer(offer_id):
    service = _build_service()
    offer = service.decline_my_offer(g.candidate_id, offer_id)
    return jsonify({"success": True, "data": {"id": str(offer.id), "status": offer.status}, "meta": {}})
