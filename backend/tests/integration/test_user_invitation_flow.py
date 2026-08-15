from app.models.role import Permission, Role
from app.models.user import User


def _grant(db_session, role, code):
    perm = db_session.query(Permission).filter_by(code=code).first()
    if perm is None:
        perm = Permission(code=code)
        db_session.add(perm)
        db_session.flush()
    if perm not in role.permissions:
        role.permissions.append(perm)
    db_session.commit()


def _recruiter_role_id(db_session):
    return db_session.query(Role).filter_by(company_id=None, name="recruiter").first().id


def test_non_admin_cannot_create_user(auth_client, db_session):
    response = auth_client.post(
        "/api/v1/admin/users",
        json={
            "email": "newhire@acme-test.com",
            "first_name": "New",
            "last_name": "Hire",
            "role_id": str(_recruiter_role_id(db_session)),
        },
    )
    assert response.status_code == 403


def test_admin_creates_user_and_gets_one_time_temp_password(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "admin.manage_users")

    response = auth_client.post(
        "/api/v1/admin/users",
        json={
            "email": "newhire@acme-test.com",
            "first_name": "New",
            "last_name": "Hire",
            "role_id": str(_recruiter_role_id(db_session)),
        },
    )
    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["status"] == "active"  # active immediately — not "pending"
    assert data["must_change_password"] is True
    assert len(data["temp_password"]) >= 20  # high-entropy, not a placeholder string

    # The temp password never appears again on a subsequent read.
    list_resp = auth_client.get("/api/v1/admin/users")
    created = next(u for u in list_resp.get_json()["data"] if u["email"] == "newhire@acme-test.com")
    assert "temp_password" not in created


def test_cannot_create_duplicate_user_email(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "admin.manage_users")

    payload = {
        "email": "dup@acme-test.com",
        "first_name": "A",
        "last_name": "B",
        "role_id": str(_recruiter_role_id(db_session)),
    }
    auth_client.post("/api/v1/admin/users", json=payload)
    dup_resp = auth_client.post("/api/v1/admin/users", json=payload)
    assert dup_resp.status_code == 400


def test_cannot_create_user_with_role_from_another_tenant(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "admin.manage_users")

    from app.models.company import Company

    other_company = Company(name="Other Co", slug="other-co-invite-test")
    db_session.add(other_company)
    db_session.commit()
    foreign_role = Role(company_id=other_company.id, name="Foreign Role", is_system_role=False)
    db_session.add(foreign_role)
    db_session.commit()

    response = auth_client.post(
        "/api/v1/admin/users",
        json={
            "email": "newhire@acme-test.com",
            "first_name": "New",
            "last_name": "Hire",
            "role_id": str(foreign_role.id),
        },
    )
    assert response.status_code == 404


def test_temp_password_logs_in_but_blocks_everything_until_changed(client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "admin.manage_users")

    login_admin = client.post(
        "/api/v1/auth/login",
        json={
            "company_slug": test_company.slug,
            "email": test_user.email,
            "password": "correct-horse-battery-staple",
        },
    )
    admin_token = login_admin.get_json()["data"]["access_token"]
    admin_auth = {"Authorization": f"Bearer {admin_token}"}

    create_resp = client.post(
        "/api/v1/admin/users",
        headers=admin_auth,
        json={
            "email": "newhire@acme-test.com",
            "first_name": "New",
            "last_name": "Hire",
            "role_id": str(_recruiter_role_id(db_session)),
        },
    )
    temp_password = create_resp.get_json()["data"]["temp_password"]

    # New user logs in successfully with the temp password...
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"company_slug": test_company.slug, "email": "newhire@acme-test.com", "password": temp_password},
    )
    assert login_resp.status_code == 200
    body = login_resp.get_json()["data"]
    assert body["must_change_password"] is True
    new_user_token = body["access_token"]
    new_user_auth = {"Authorization": f"Bearer {new_user_token}"}

    # ...but is blocked from every other endpoint — server-side, not
    # just a frontend redirect the client could ignore.
    blocked_resp = client.get("/api/v1/candidates", headers=new_user_auth)
    assert blocked_resp.status_code == 403
    assert blocked_resp.get_json()["error"]["code"] == "password_change_required"

    # change-password itself remains reachable despite the block.
    change_resp = client.post(
        "/api/v1/auth/change-password",
        headers=new_user_auth,
        json={"current_password": temp_password, "new_password": "a-brand-new-strong-password"},
    )
    assert change_resp.status_code == 200
    fresh_token = change_resp.get_json()["data"]["access_token"]

    # Now unblocked with the fresh token.
    unblocked_resp = client.get("/api/v1/candidates", headers={"Authorization": f"Bearer {fresh_token}"})
    assert unblocked_resp.status_code in (200, 403)  # 403 only if candidate.view_all isn't granted — not a password_change_required block
    assert unblocked_resp.get_json().get("error", {}).get("code") != "password_change_required"

    # Logging in again afterward no longer reports must_change_password.
    relogin_resp = client.post(
        "/api/v1/auth/login",
        json={
            "company_slug": test_company.slug,
            "email": "newhire@acme-test.com",
            "password": "a-brand-new-strong-password",
        },
    )
    assert relogin_resp.get_json()["data"]["must_change_password"] is False


def test_change_password_rejects_wrong_current_password(client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "admin.manage_users")
    login_admin = client.post(
        "/api/v1/auth/login",
        json={"company_slug": test_company.slug, "email": test_user.email, "password": "correct-horse-battery-staple"},
    )
    admin_auth = {"Authorization": f"Bearer {login_admin.get_json()['data']['access_token']}"}

    create_resp = client.post(
        "/api/v1/admin/users",
        headers=admin_auth,
        json={
            "email": "newhire2@acme-test.com",
            "first_name": "New",
            "last_name": "Hire",
            "role_id": str(_recruiter_role_id(db_session)),
        },
    )
    temp_password = create_resp.get_json()["data"]["temp_password"]

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"company_slug": test_company.slug, "email": "newhire2@acme-test.com", "password": temp_password},
    )
    new_user_auth = {"Authorization": f"Bearer {login_resp.get_json()['data']['access_token']}"}

    wrong_resp = client.post(
        "/api/v1/auth/change-password",
        headers=new_user_auth,
        json={"current_password": "totally-wrong-password", "new_password": "a-brand-new-strong-password"},
    )
    assert wrong_resp.status_code == 401


def test_change_password_rejects_reusing_current_password(client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "admin.manage_users")
    login_admin = client.post(
        "/api/v1/auth/login",
        json={"company_slug": test_company.slug, "email": test_user.email, "password": "correct-horse-battery-staple"},
    )
    admin_auth = {"Authorization": f"Bearer {login_admin.get_json()['data']['access_token']}"}

    create_resp = client.post(
        "/api/v1/admin/users",
        headers=admin_auth,
        json={
            "email": "newhire3@acme-test.com",
            "first_name": "New",
            "last_name": "Hire",
            "role_id": str(_recruiter_role_id(db_session)),
        },
    )
    temp_password = create_resp.get_json()["data"]["temp_password"]

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"company_slug": test_company.slug, "email": "newhire3@acme-test.com", "password": temp_password},
    )
    new_user_auth = {"Authorization": f"Bearer {login_resp.get_json()['data']['access_token']}"}

    same_resp = client.post(
        "/api/v1/auth/change-password",
        headers=new_user_auth,
        json={"current_password": temp_password, "new_password": temp_password},
    )
    assert same_resp.status_code == 400


def test_expired_temp_password_blocks_login(client, db_session, test_user, test_company):
    from datetime import datetime, timedelta, timezone
    from app.services.auth_service import _hash_password

    expired_user = User(
        company_id=test_company.id,
        email="stale-invite@acme-test.com",
        password_hash=_hash_password("some-temp-password-value"),
        first_name="Stale",
        last_name="Invite",
        role_id=test_user.role_id,
        status="active",
        must_change_password=True,
        temp_password_expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add(expired_user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "company_slug": test_company.slug,
            "email": "stale-invite@acme-test.com",
            "password": "some-temp-password-value",
        },
    )
    assert response.status_code == 422
    assert "expired" in response.get_json()["error"]["message"].lower()


def test_register_endpoint_no_longer_exists(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "company_slug": "anything",
            "email": "x@x.com",
            "password": "whatever-password",
            "first_name": "X",
            "last_name": "Y",
        },
    )
    assert response.status_code == 404
