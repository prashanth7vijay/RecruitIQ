"""
Shared pagination helper. Was documented in Phase 11.4 (page/per_page
query params, meta.pagination response shape) but never actually
implemented on any endpoint — every list endpoint just returned
everything. Fine at the data volumes this project has had so far;
a real gap once any list grows past a page or two. This is the one,
single implementation every list endpoint should use, so pagination
behavior (and its 100-item cap, to stop someone requesting
per_page=100000) is consistent everywhere rather than reinvented
per-route.
"""

from flask import request

DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


def paginate_query(query):
    """
    Applies LIMIT/OFFSET to a SQLAlchemy query based on the current
    request's page/per_page params, and returns (items, pagination_meta).
    """
    page = max(1, request.args.get("page", 1, type=int))
    per_page = request.args.get("per_page", DEFAULT_PER_PAGE, type=int)
    per_page = max(1, min(per_page, MAX_PER_PAGE))

    total_items = query.count()
    total_pages = max(1, (total_items + per_page - 1) // per_page)

    items = query.offset((page - 1) * per_page).limit(per_page).all()

    meta = {
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_items": total_items,
            "total_pages": total_pages,
        }
    }
    return items, meta
