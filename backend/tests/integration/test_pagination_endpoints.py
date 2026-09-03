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


def _seed_candidate_profiles(db_session, company, count):
    for i in range(count):
        candidate = Candidate(email=f"person{i}@example.com", first_name="P", last_name=str(i))
        db_session.add(candidate)
        db_session.flush()
        db_session.add(CandidateProfile(company_id=company.id, candidate_id=candidate.id, skills=[]))
    db_session.commit()


def test_candidates_list_is_paginated(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "candidate.view_all")
    _seed_candidate_profiles(db_session, test_company, 25)

    page1 = auth_client.get("/api/v1/candidates?per_page=10")
    body = page1.get_json()
    assert len(body["data"]) == 10
    assert body["meta"]["pagination"]["total_items"] == 25
    assert body["meta"]["pagination"]["total_pages"] == 3
    assert body["meta"]["pagination"]["page"] == 1

    page3 = auth_client.get("/api/v1/candidates?per_page=10&page=3")
    assert len(page3.get_json()["data"]) == 5  # 25 - 2*10 = 5 remaining


def test_jobs_list_is_paginated(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "job.create")
    for i in range(15):
        auth_client.post("/api/v1/jobs", json={"title": f"Job {i}"})

    response = auth_client.get("/api/v1/jobs?per_page=5")
    body = response.get_json()
    assert len(body["data"]) == 5
    assert body["meta"]["pagination"]["total_items"] == 15
    assert body["meta"]["pagination"]["total_pages"] == 3


def test_per_page_over_max_is_capped(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "candidate.view_all")
    response = auth_client.get("/api/v1/candidates?per_page=5000")
    assert response.get_json()["meta"]["pagination"]["per_page"] == 100