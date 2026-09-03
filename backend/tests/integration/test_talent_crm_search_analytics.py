from app.models.candidate import Candidate, CandidateProfile
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


def _seed_candidate_profile(db_session, company, email, first_name, last_name):
    candidate = Candidate(email=email, first_name=first_name, last_name=last_name)
    db_session.add(candidate)
    db_session.flush()
    profile = CandidateProfile(company_id=company.id, candidate_id=candidate.id, skills=[])
    db_session.add(profile)
    db_session.commit()
    return profile


def test_talent_pool_lifecycle(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "candidate.manage")
    create_pool_resp = auth_client.post("/api/v1/talent-pools", json={"name": "Frontend Devs"})
    assert create_pool_resp.status_code == 201
    pool_id = create_pool_resp.get_json()["data"]["id"]

    profile = _seed_candidate_profile(db_session, test_company, "jane@example.com", "Jane", "Doe")
    profile_id = str(profile.id)

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


def test_candidate_notes_and_tags(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "candidate.manage")
    _grant(db_session, test_user.role, "candidate.view_all")

    profile = _seed_candidate_profile(db_session, test_company, "jane2@example.com", "Jane", "Doe")
    profile_id = str(profile.id)

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


def test_can_view_resume_download_link_once_provided(auth_client, db_session, test_user, test_company):
    from app.models.resume import Resume

    _grant(db_session, test_user.role, "candidate.view_all")
    profile = _seed_candidate_profile(db_session, test_company, "resume-owner@example.com", "Res", "Owner")

    no_resume_resp = auth_client.get(f"/api/v1/candidates/{profile.id}/resume")
    assert no_resume_resp.status_code == 404

    resume = Resume(candidate_id=profile.candidate_id, storage_key="resumes/test/r.pdf", original_filename="r.pdf")
    db_session.add(resume)
    db_session.flush()
    profile.resume_id = resume.id
    db_session.commit()

    with_resume_resp = auth_client.get(f"/api/v1/candidates/{profile.id}/resume")
    assert with_resume_resp.status_code == 200
    data = with_resume_resp.get_json()["data"]
    assert data["original_filename"] == "r.pdf"
    assert "/api/v1/files/resumes/test/r.pdf" in data["url"]
    assert "signature=" in data["url"]


def test_search_finds_candidate_by_name(auth_client, db_session, test_user, test_company):
    _seed_candidate_profile(db_session, test_company, "zephyr@example.com", "Zephyr", "Quinn")

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


def test_listing_pool_members_does_not_n_plus_one(auth_client, db_session, test_user, test_company):
    from sqlalchemy import event

    _grant(db_session, test_user.role, "candidate.manage")
    pool_resp = auth_client.post("/api/v1/talent-pools", json={"name": "N+1 check"})
    pool_id = pool_resp.get_json()["data"]["id"]

    for i in range(5):
        profile = _seed_candidate_profile(
            db_session, test_company, f"nplus1-{i}@example.com", "Person", str(i)
        )
        auth_client.post(
            f"/api/v1/talent-pools/{pool_id}/members", json={"candidate_profile_id": str(profile.id)}
        )

    queries = []

    def _count(conn, cursor, statement, *args, **kwargs):
        queries.append(statement)

    event.listen(db_session.get_bind(), "before_cursor_execute", _count)
    try:
        response = auth_client.get(f"/api/v1/talent-pools/{pool_id}/members")
    finally:
        event.remove(db_session.get_bind(), "before_cursor_execute", _count)

    assert response.status_code == 200
    assert len(response.get_json()["data"]) == 5
    assert len(queries) <= 4, f"expected a small fixed query count, got {len(queries)}"