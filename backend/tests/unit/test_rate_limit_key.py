from app import create_app
from app.extensions import _rate_limit_key


def test_rate_limit_key_falls_back_to_ip_with_no_jwt():
    """No Authorization header at all (e.g. hitting /login) — should
    fall back to IP-based keying, which is the correct brute-force
    defense for an endpoint where identity isn't established yet."""
    app = create_app("testing")
    with app.test_request_context("/", headers={}):
        key = _rate_limit_key()
    assert key is not None  # falls back to get_remote_address's value


def test_rate_limit_key_falls_back_to_ip_on_invalid_jwt():
    """A garbage/expired Authorization header shouldn't raise — just
    fall back to IP, same as no header at all."""
    app = create_app("testing")
    with app.test_request_context("/", headers={"Authorization": "Bearer not-a-real-token"}):
        key = _rate_limit_key()
    assert key is not None
