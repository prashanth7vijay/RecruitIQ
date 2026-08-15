from flask import request

DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


def paginate_query(query):
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
