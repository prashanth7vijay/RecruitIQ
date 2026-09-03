from app.models.role import Permission


def _grant(db_session, role, code):
    perm = db_session.query(Permission).filter_by(code=code).first()
    if perm is None:
        perm = Permission(code=code)
        db_session.add(perm)
        db_session.flush()
    if perm not in role.permissions:
        role.permissions.append(perm)
    db_session.commit()


def test_list_roles_includes_system_and_own_custom_roles(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "role.manage")

    create_resp = auth_client.get("/api/v1/roles")
    assert create_resp.status_code == 200
    names = {r["name"] for r in create_resp.get_json()["data"]}
    assert "org_admin" in names
    assert "recruiter" in names


def test_non_admin_cannot_create_role(auth_client, db_session, test_user):
    response = auth_client.post("/api/v1/roles", json={"name": "Sourcer", "permission_codes": []})
    assert response.status_code == 403


def test_create_update_delete_custom_role(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "role.manage")
    _grant(db_session, test_user.role, "candidate.manage")

    create_resp = auth_client.post(
        "/api/v1/roles", json={"name": "Sourcer", "permission_codes": ["candidate.manage"]}
    )
    assert create_resp.status_code == 201
    role = create_resp.get_json()["data"]
    assert role["is_system_role"] is False
    assert role["permissions"] == ["candidate.manage"]

    update_resp = auth_client.patch(f"/api/v1/roles/{role['id']}", json={"name": "Senior Sourcer"})
    assert update_resp.status_code == 200
    assert update_resp.get_json()["data"]["name"] == "Senior Sourcer"

    delete_resp = auth_client.delete(f"/api/v1/roles/{role['id']}")
    assert delete_resp.status_code == 200

    get_resp = auth_client.get(f"/api/v1/roles/{role['id']}")
    assert get_resp.status_code == 404


def test_cannot_create_duplicate_role_name(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "role.manage")

    auth_client.post("/api/v1/roles", json={"name": "Sourcer", "permission_codes": []})
    dup_resp = auth_client.post("/api/v1/roles", json={"name": "sourcer", "permission_codes": []})
    assert dup_resp.status_code == 409


def test_cannot_create_role_with_unknown_permission_code(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "role.manage")

    response = auth_client.post(
        "/api/v1/roles", json={"name": "Sourcer", "permission_codes": ["not.a.real.permission"]}
    )
    assert response.status_code == 400


def test_cannot_modify_system_role(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "role.manage")

    from app.models.role import Role

    org_admin_role = db_session.query(Role).filter_by(company_id=None, name="org_admin").first()

    # A system role (company_id IS NULL) never matches
    # get_own_custom_or_404's `company_id == tenant_id` filter, so this
    # is a 404 — same "cross-tenant access looks like non-existence"
    # posture the rest of this codebase already uses (see
    # TenantScopedRepository.get_or_404), not a 422 from a reachable
    # "you can see it but can't touch it" branch.
    response = auth_client.patch(f"/api/v1/roles/{org_admin_role.id}", json={"name": "Hacked"})
    assert response.status_code == 404

    delete_resp = auth_client.delete(f"/api/v1/roles/{org_admin_role.id}")
    assert delete_resp.status_code == 404


def test_cannot_delete_role_that_still_has_users(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "role.manage")
    _grant(db_session, test_user.role, "admin.manage_users")

    create_resp = auth_client.post("/api/v1/roles", json={"name": "Sourcer", "permission_codes": []})
    role_id = create_resp.get_json()["data"]["id"]

    assign_resp = auth_client.patch(f"/api/v1/admin/users/{test_user.id}/role", json={"role_id": role_id})
    assert assign_resp.status_code == 200
    assert assign_resp.get_json()["data"]["role_id"] == role_id

    delete_resp = auth_client.delete(f"/api/v1/roles/{role_id}")
    assert delete_resp.status_code == 409


def test_cannot_see_or_edit_another_tenants_custom_role(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "role.manage")

    from app.models.company import Company
    from app.models.role import Role

    other_company = Company(name="Other Co", slug="other-co-rbac-test")
    db_session.add(other_company)
    db_session.commit()

    other_role = Role(company_id=other_company.id, name="Other Tenant Role", is_system_role=False)
    db_session.add(other_role)
    db_session.commit()

    get_resp = auth_client.get(f"/api/v1/roles/{other_role.id}")
    assert get_resp.status_code == 404

    patch_resp = auth_client.patch(f"/api/v1/roles/{other_role.id}", json={"name": "Hijacked"})
    assert patch_resp.status_code == 404