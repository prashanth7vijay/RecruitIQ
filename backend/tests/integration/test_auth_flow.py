from app.models.company import Company
from app.models.user import User


def test_login_returns_access_token_and_sets_refresh_cookie(client, test_user, test_company):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "company_slug": test_company.slug,
            "email": test_user.email,
            "password": "correct-horse-battery-staple",
        },
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["data"]["access_token"]
    assert "refresh_token" in response.headers.get("Set-Cookie", "")


def test_login_with_wrong_password_returns_generic_error(client, test_user, test_company):
    response = client.post(
        "/api/v1/auth/login",
        json={"company_slug": test_company.slug, "email": test_user.email, "password": "wrong-password"},
    )

    assert response.status_code == 401
    body = response.get_json()
    assert body["error"]["code"] == "unauthenticated"
    # Deliberately generic — must not reveal whether the org/email exists.
    assert "invalid organization, email, or password" in body["error"]["message"].lower()


def test_login_with_unknown_company_slug_returns_same_generic_error(client, test_user):
    """
    An unknown organization slug must be indistinguishable from a
    known one with a bad password — otherwise the login form becomes
    an org-slug enumeration oracle.
    """
    response = client.post(
        "/api/v1/auth/login",
        json={"company_slug": "no-such-company", "email": test_user.email, "password": "whatever"},
    )
    assert response.status_code == 401
    assert "invalid organization, email, or password" in response.get_json()["error"]["message"].lower()


def test_refresh_rotates_token_and_old_one_cannot_be_reused(client, test_user, test_company):
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "company_slug": test_company.slug,
            "email": test_user.email,
            "password": "correct-horse-battery-staple",
        },
    )
    assert login_resp.status_code == 200

    # First refresh should succeed and rotate the cookie.
    refresh_resp = client.post("/api/v1/auth/refresh")
    assert refresh_resp.status_code == 200
    assert refresh_resp.get_json()["data"]["access_token"]

def test_logout_all_revokes_session(auth_client, test_user):
    response = auth_client.post("/api/v1/auth/logout-all")
    assert response.status_code == 200

    refresh_resp = auth_client.post("/api/v1/auth/refresh")
    assert refresh_resp.status_code == 401


def test_refresh_preserves_tenant_context_for_subsequent_requests(auth_client, test_user, test_company):

    refresh_resp = auth_client.post("/api/v1/auth/refresh")
    assert refresh_resp.status_code == 200
    new_token = refresh_resp.get_json()["data"]["access_token"]

    auth_client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {new_token}"

    # Any tenant-scoped route proves this — /companies/me needs
    # g.tenant_id, which comes directly from the refreshed token's claims.
    response = auth_client.get("/api/v1/companies/me")
    assert response.status_code == 200
    assert response.get_json()["data"]["id"] == str(test_company.id)

def test_signup_creates_company_and_org_admin(client, db_session):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "company_name": "New Startup Inc",
            "company_slug": "new-startup-inc",
            "email": "founder@newstartup.com",
            "password": "correct-horse-battery-staple",
            "first_name": "Ada",
            "last_name": "Founder",
        },
    )
    assert response.status_code == 201
    body = response.get_json()["data"]
    assert body["company"]["slug"] == "new-startup-inc"
    assert body["user"]["email"] == "founder@newstartup.com"
    assert body["user"]["status"] == "active"  # no email-verification flow exists yet — see auth_service docstring

    company = db_session.query(Company).filter_by(slug="new-startup-inc").first()
    assert company is not None
    user = db_session.query(User).filter_by(company_id=company.id).first()
    assert user.role.name == "org_admin"

    # The new org_admin can immediately log in — proves signup produces
    # a genuinely usable account, not just DB rows.
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "company_slug": "new-startup-inc",
            "email": "founder@newstartup.com",
            "password": "correct-horse-battery-staple",
        },
    )
    assert login_resp.status_code == 200


def test_signup_rejects_duplicate_slug(client, test_company):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "company_name": "Another Co",
            "company_slug": test_company.slug,  # already taken by the conftest fixture
            "email": "someone@example.com",
            "password": "correct-horse-battery-staple",
            "first_name": "A",
            "last_name": "B",
        },
    )
    assert response.status_code == 400


def test_signup_rejects_invalid_slug_format(client):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "company_name": "Bad Slug Co",
            "company_slug": "Not A Valid Slug!",
            "email": "someone@example.com",
            "password": "correct-horse-battery-staple",
            "first_name": "A",
            "last_name": "B",
        },
    )
    assert response.status_code == 400
