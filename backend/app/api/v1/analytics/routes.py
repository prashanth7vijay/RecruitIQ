from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required

from app.exceptions.base import UnauthenticatedError
from app.extensions import cache, db
from app.observability import record_dashboard_cache
from app.services.analytics_service import AnalyticsService
from app.utils.permissions import require_permission

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/v1/analytics")


def _tenant_id():
    if g.get("tenant_id") is None:
        raise UnauthenticatedError("Authentication required")
    return g.tenant_id


@analytics_bp.route("/hiring-funnel", methods=["GET"])
@jwt_required()
@require_permission("analytics.view_org")
def hiring_funnel():
    job_id = request.args.get("job_id")
    service = AnalyticsService(db.session)
    funnel = service.hiring_funnel(_tenant_id(), job_id) if job_id else []
    return jsonify({"success": True, "data": funnel, "meta": {}})


@analytics_bp.route("/time-to-hire", methods=["GET"])
@jwt_required()
@require_permission("analytics.view_org")
def time_to_hire():
    job_id = request.args.get("job_id")
    service = AnalyticsService(db.session)
    result = service.time_to_hire(_tenant_id(), job_id)
    return jsonify({"success": True, "data": result, "meta": {}})


@analytics_bp.route("/recruiter-performance", methods=["GET"])
@jwt_required()
@require_permission("analytics.view_org")
def recruiter_performance():
    service = AnalyticsService(db.session)
    result = service.recruiter_performance(_tenant_id())
    return jsonify({"success": True, "data": result, "meta": {}})


@analytics_bp.route("/velocity", methods=["GET"])
@jwt_required()
@require_permission("analytics.view_org")
def hiring_velocity():
    days = request.args.get("days", default=30, type=int)
    service = AnalyticsService(db.session)
    result = service.hiring_velocity(_tenant_id(), days=days)
    return jsonify({"success": True, "data": result, "meta": {}})


@analytics_bp.route("/pipeline-health", methods=["GET"])
@jwt_required()
@require_permission("analytics.view_org")
def pipeline_health():
    service = AnalyticsService(db.session)
    result = service.pipeline_health(_tenant_id())
    return jsonify({"success": True, "data": result, "meta": {}})


@analytics_bp.route("/offer-acceptance", methods=["GET"])
@jwt_required()
@require_permission("analytics.view_org")
def offer_acceptance_rate():
    service = AnalyticsService(db.session)
    result = service.offer_acceptance_rate(_tenant_id())
    return jsonify({"success": True, "data": result, "meta": {}})


@analytics_bp.route("/department-hiring", methods=["GET"])
@jwt_required()
@require_permission("analytics.view_org")
def department_hiring():
    service = AnalyticsService(db.session)
    result = service.department_hiring(_tenant_id())
    return jsonify({"success": True, "data": result, "meta": {}})


@analytics_bp.route("/executive-summary", methods=["GET"])
@jwt_required()
@require_permission("analytics.view_org")
def executive_summary():
    service = AnalyticsService(db.session, cache=cache)
    result, meta = service.executive_summary(_tenant_id())
    record_dashboard_cache(meta["cache_hit"])
    return jsonify({"success": True, "data": result, "meta": meta})
