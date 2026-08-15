import io
import mimetypes

from flask import Blueprint, request, current_app, send_file, abort

from app.extensions import limiter
from app.storage.factory import build_storage

files_bp = Blueprint("files", __name__, url_prefix="/api/v1/files")


@files_bp.route("/<path:key>", methods=["GET"])
@limiter.limit("60 per minute")
def serve_file(key):
    expires = request.args.get("expires")
    signature = request.args.get("signature")
    if not expires or not signature:
        abort(403)

    storage = build_storage(current_app.config)
    if not hasattr(storage, "verify_signature"):
        # Non-local backends (S3, etc.) never route through here in the
        # first place — see module docstring — so reaching this branch
        # means the config is misconfigured, not a client error.
        abort(404)

    try:
        expires_int = int(expires)
    except ValueError:
        abort(403)

    if not storage.verify_signature(key, expires_int, signature):
        abort(403)
    if not storage.exists(key):
        abort(404)

    data = storage.read_bytes(key)
    content_type = mimetypes.guess_type(key)[0] or "application/octet-stream"
    filename = key.rsplit("/", 1)[-1]

    return send_file(
        io.BytesIO(data),
        mimetype=content_type,
        as_attachment=False,
        download_name=filename,
    )
