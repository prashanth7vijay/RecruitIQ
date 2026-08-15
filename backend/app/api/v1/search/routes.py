from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required

from app.api.v1.search.schemas import SearchCandidateResultSchema, SearchJobResultSchema
from app.exceptions.base import UnauthenticatedError, ValidationError
from app.extensions import db, limiter
from app.services.search_service import SearchService

search_bp = Blueprint("search", __name__, url_prefix="/api/v1/search")


def _tenant_id():
    if g.get("tenant_id") is None:
        raise UnauthenticatedError("Authentication required")
    return g.tenant_id


@search_bp.route("", methods=["GET"])
@jwt_required()
@limiter.limit("30 per minute")
def search():
    query = request.args.get("q", "").strip()
    if not query:
        raise ValidationError("Query parameter 'q' is required", details=[{"field": "q", "message": "Required"}])

    service = SearchService(db.session)
    results = service.search(_tenant_id(), query)
    return jsonify({
        "success": True,
        "data": {
            "candidates": SearchCandidateResultSchema(many=True).dump(results["candidates"]),
            "jobs": SearchJobResultSchema(many=True).dump(results["jobs"]),
        },
        "meta": {},
    })
