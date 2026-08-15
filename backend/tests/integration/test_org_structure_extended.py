from app.models.role import Permission
from app.models.user import User
from app.services.auth_service import _hash_password


def _grant(db_session, role, code):
    perm = db_session.query(Permission).filter_by(code=code).first()
    if perm is None:
        perm = Permission(code=code)
        db_session.add(perm)
        db_session.flush()
    if perm not in role.permissions:
        role.permissions.append(perm)
    db_session.commit()


def test_team_full_crud(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "org.manage_structure")

    create_resp = auth_client.post("/api/v1/teams", json={"name": "Platform"})
    assert create_resp.status_code == 201
    team_id = create_resp.get_json()["data"]["id"]

    get_resp = auth_client.get(f"/api/v1/teams/{team_id}")
    assert get_resp.status_code == 200
    assert get_resp.get_json()["data"]["name"] == "Platform"

    rename_resp = auth_client.patch(f"/api/v1/teams/{team_id}", json={"name": "Core Platform"})
    assert rename_resp.status_code == 200
    assert rename_resp.get_json()["data"]["name"] == "Core Platform"

    delete_resp = auth_client.delete(f"/api/v1/teams/{team_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.get_json()["data"] is None

    missing_resp = auth_client.get(f"/api/v1/teams/{team_id}")
    assert missing_resp.status_code == 404


def test_team_move_to_department_validates_tenant_ownership(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "org.manage_structure")

    from app.models.company import Company
    from app.models.department import Department

    team_resp = auth_client.post("/api/v1/teams", json={"name": "Platform"})
    team_id = team_resp.get_json()["data"]["id"]

    other_company = Company(name="Other Co", slug="other-co-team-move-test")
    db_session.add(other_company)
    db_session.commit()
    other_department = Department(company_id=other_company.id, name="Foreign Dept")
    db_session.add(other_department)
    db_session.commit()

    move_resp = auth_client.patch(
        f"/api/v1/teams/{team_id}", json={"department_id": str(other_department.id)}
    )
    assert move_resp.status_code == 404


def test_non_admin_cannot_manage_teams_or_locations(auth_client, db_session, test_user):
    create_team_resp = auth_client.post("/api/v1/teams", json={"name": "Platform"})
    assert create_team_resp.status_code == 403

    create_location_resp = auth_client.post("/api/v1/locations", json={"name": "HQ"})
    assert create_location_resp.status_code == 403


def test_location_crud(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "org.manage_structure")

    create_resp = auth_client.post(
        "/api/v1/locations", json={"name": "Bangalore Office", "city": "Bangalore", "country": "India"}
    )
    assert create_resp.status_code == 201
    location = create_resp.get_json()["data"]
    assert location["is_remote"] is False

    update_resp = auth_client.patch(
        f"/api/v1/locations/{location['id']}", json={"is_remote": True}
    )
    assert update_resp.status_code == 200
    assert update_resp.get_json()["data"]["is_remote"] is True

    list_resp = auth_client.get("/api/v1/locations")
    assert list_resp.status_code == 200
    assert any(l["id"] == location["id"] for l in list_resp.get_json()["data"])

    delete_resp = auth_client.delete(f"/api/v1/locations/{location['id']}")
    assert delete_resp.status_code == 200


def test_cannot_create_duplicate_location_name(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "org.manage_structure")

    auth_client.post("/api/v1/locations", json={"name": "HQ"})
    dup_resp = auth_client.post("/api/v1/locations", json={"name": "HQ"})
    assert dup_resp.status_code == 409


def test_user_org_placement_sets_department_team_manager_location(
    auth_client, db_session, test_user, test_company
):
    _grant(db_session, test_user.role, "org.manage_structure")

    from app.models.department import Department, Team, Location

    department = Department(company_id=test_company.id, name="Engineering")
    db_session.add(department)
    db_session.commit()
    team = Team(company_id=test_company.id, name="Platform", department_id=department.id)
    location = Location(company_id=test_company.id, name="HQ", is_remote=False)
    db_session.add_all([team, location])
    db_session.commit()

    manager = User(
        company_id=test_company.id,
        email="manager@acme-test.com",
        password_hash=_hash_password("correct-horse-battery-staple"),
        first_name="Manager",
        last_name="Person",
        role_id=test_user.role_id,
        status="active",
    )
    db_session.add(manager)
    db_session.commit()

    response = auth_client.patch(
        f"/api/v1/users/{test_user.id}/org-placement",
        json={
            "department_id": str(department.id),
            "team_id": str(team.id),
            "manager_id": str(manager.id),
            "location_id": str(location.id),
        },
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["role_id"] == str(test_user.role_id)  # unaffected — different endpoint's job


def test_user_cannot_be_own_manager(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "org.manage_structure")

    response = auth_client.patch(
        f"/api/v1/users/{test_user.id}/org-placement", json={"manager_id": str(test_user.id)}
    )
    assert response.status_code == 400


def test_org_placement_rejects_cross_tenant_manager(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "org.manage_structure")

    from app.models.company import Company

    other_company = Company(name="Other Co", slug="other-co-manager-test")
    db_session.add(other_company)
    db_session.commit()

    foreign_user = User(
        company_id=other_company.id,
        email="foreign@other-co.com",
        password_hash=_hash_password("correct-horse-battery-staple"),
        first_name="Foreign",
        last_name="User",
        role_id=test_user.role_id,
        status="active",
    )
    db_session.add(foreign_user)
    db_session.commit()

    response = auth_client.patch(
        f"/api/v1/users/{test_user.id}/org-placement", json={"manager_id": str(foreign_user.id)}
    )
    assert response.status_code == 404
