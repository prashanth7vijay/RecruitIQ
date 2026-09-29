"""
Flask extension instances.

Instantiated here (unbound) and initialized against the app inside
create_app() (app/__init__.py). Keeping them here — rather than
inside the factory function — lets other modules (models, services)
import `db` etc. without a circular import back through the factory.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cache = Cache()


def _rate_limit_key():
    """Key rate limits by the authenticated user, not by IP, whenever
    a request has a valid JWT — falls back to IP for unauthenticated
    endpoints (login, register), where identity isn't established yet
    and IP-based throttling is the actual brute-force defense, not an
    accident.

    Found in Phase 5 (load testing): the default get_remote_address key
    made every request from this sandbox's single source IP share one
    counter — real users behind a shared IP (an office network, a
    corporate VPN, or just this load test) collapse into the same
    bucket and get throttled as if they were one client, even though
    they're not. Measured: 31-37% of concurrent search requests
    rejected with 429s purely from this, not real capacity. See
    docs/scalability.md.
    """
    from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
    except Exception:  # noqa: BLE001 — any JWT decode failure just falls back to IP
        identity = None

    return identity or get_remote_address()


limiter = Limiter(key_func=_rate_limit_key)
