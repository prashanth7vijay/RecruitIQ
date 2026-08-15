from app.models.role import Permission


def _grant_permission(db_session, role, code):
    perm = db_session.query(Permission).filter_by(code=code).first()
    if perm is None:
        perm = Permission(code=code)
        db_session.add(perm)
        db_session.flush()
    if perm not in role.permissions:
        role.permissions.append(perm)
    db_session.commit()


def test_get_own_company(auth_client, test_company):
    response = auth_client.get("/api/v1/companies/me")

    assert response.status_code == 200
    body = response.get_json()["data"]
    assert body["id"] == str(test_company.id)
    assert body["name"] == test_company.name


def test_update_company_requires_permission(auth_client):
    response = auth_client.patch("/api/v1/companies/me", json={"name": "New Name"})

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "permission_denied"


def test_update_company_with_permission_succeeds(auth_client, db_session, test_user):
    _grant_permission(db_session, test_user.role, "company.manage_settings")

    response = auth_client.patch("/api/v1/companies/me", json={"name": "Renamed Co"})

    assert response.status_code == 200
    assert response.get_json()["data"]["name"] == "Renamed Co"


def test_update_company_cannot_change_slug(auth_client, db_session, test_user, test_company):
    _grant_permission(db_session, test_user.role, "company.manage_settings")
    original_slug = test_company.slug

    response = auth_client.patch(
        "/api/v1/companies/me", json={"name": "Still Renamed", "slug": "hijacked-slug"}
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["slug"] == original_slug
