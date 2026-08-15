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


def test_talent_pool_lifecycle(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "candidate.manage")

    create_pool_resp = auth_client.post("/api/v1/talent-pools", json={"name": "Frontend Devs"})
    assert create_pool_resp.status_code == 201
    pool_id = create_pool_resp.get_json()["data"]["id"]

    add_candidate_resp = auth_client.post(
        "/api/v1/candidates", json={"email": "jane@example.com", "first_name": "Jane", "last_name": "Doe"}
    )
    profile_id = add_candidate_resp.get_json()["data"]["id"]

    add_member_resp = auth_client.post(
        f"/api/v1/talent-pools/{pool_id}/members", json={"candidate_profile_id": profile_id}
    )
    assert add_member_resp.status_code == 201

    # Adding the same candidate twice should be rejected, not silently duplicated.
    dup_resp = auth_client.post(
        f"/api/v1/talent-pools/{pool_id}/members", json={"candidate_profile_id": profile_id}
    )
    assert dup_resp.status_code == 422

    members_resp = auth_client.get(f"/api/v1/talent-pools/{pool_id}/members")
    assert len(members_resp.get_json()["data"]) == 1

    remove_resp = auth_client.delete(f"/api/v1/talent-pools/{pool_id}/members/{profile_id}")
    assert remove_resp.status_code == 204

    members_after_resp = auth_client.get(f"/api/v1/talent-pools/{pool_id}/members")
    assert len(members_after_resp.get_json()["data"]) == 0


def test_candidate_notes_and_tags(auth_client, db_session, test_user):
    # GET notes/tags requires candidate.view_all, separate from
    # candidate.manage which only covers create/write — same intentional
    # split as candidates list (see test_pagination_endpoints.py).
    _grant(db_session, test_user.role, "candidate.manage")
    _grant(db_session, test_user.role, "candidate.view_all")

    add_candidate_resp = auth_client.post(
        "/api/v1/candidates", json={"email": "jane2@example.com", "first_name": "Jane", "last_name": "Doe"}
    )
    profile_id = add_candidate_resp.get_json()["data"]["id"]

    note_resp = auth_client.post(f"/api/v1/candidates/{profile_id}/notes", json={"body": "Great communicator"})
    assert note_resp.status_code == 201

    notes_resp = auth_client.get(f"/api/v1/candidates/{profile_id}/notes")
    assert len(notes_resp.get_json()["data"]) == 1
    assert notes_resp.get_json()["data"][0]["body"] == "Great communicator"

    tag_resp = auth_client.post(f"/api/v1/candidates/{profile_id}/tags", json={"label": "senior"})
    assert tag_resp.status_code == 201

    # Adding the same tag twice should be idempotent, not an error.
    dup_tag_resp = auth_client.post(f"/api/v1/candidates/{profile_id}/tags", json={"label": "senior"})
    assert dup_tag_resp.status_code == 201

    tags_resp = auth_client.get(f"/api/v1/candidates/{profile_id}/tags")
    assert len(tags_resp.get_json()["data"]) == 1  # still just one — the duplicate didn't create a second row


def test_search_finds_candidate_by_name(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "candidate.manage")
    auth_client.post(
        "/api/v1/candidates", json={"email": "zephyr@example.com", "first_name": "Zephyr", "last_name": "Quinn"}
    )

    response = auth_client.get("/api/v1/search?q=Zephyr")
    assert response.status_code == 200
    assert len(response.get_json()["data"]["candidates"]) == 1


def test_search_requires_query_param(auth_client):
    response = auth_client.get("/api/v1/search")
    assert response.status_code == 400


def test_time_to_hire_returns_none_with_no_accepted_offers(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "analytics.view_org")
    response = auth_client.get("/api/v1/analytics/time-to-hire")
    assert response.status_code == 200
    assert response.get_json()["data"]["avg_days_to_hire"] is None
