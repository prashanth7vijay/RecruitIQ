from app.models.candidate import Candidate, CandidateProfile
from app.models.pipeline import PipelineTemplate, PipelineStage
from app.models.job import Job
from app.models.application import Application
from app.models.interview import Interview
from app.models.offer import Offer
from app.services.auth_service import _hash_password


def _signup(client, email="candidate@test.com", password="a-strong-password-1"):
    return client.post(
        "/api/v1/candidate-auth/signup",
        json={"email": email, "password": password, "first_name": "Jane", "last_name": "Doe"},
    )


def test_candidate_signup_and_login(client, db_session):
    signup_resp = _signup(client)
    assert signup_resp.status_code == 201
    assert "access_token" in signup_resp.get_json()["data"]

    login_resp = client.post(
        "/api/v1/candidate-auth/login",
        json={"email": "candidate@test.com", "password": "a-strong-password-1"},
    )
    assert login_resp.status_code == 200


def test_cannot_signup_twice_with_same_email(client, db_session):
    _signup(client)
    dup_resp = _signup(client)
    assert dup_resp.status_code == 400


def test_signup_claims_existing_guest_application_identity(client, db_session, test_company):
    guest = Candidate(email="guest@test.com", first_name="Guest", last_name="Applicant")
    db_session.add(guest)
    db_session.commit()
    guest_id = guest.id

    signup_resp = client.post(
        "/api/v1/candidate-auth/signup",
        json={
            "email": "guest@test.com", "password": "a-strong-password-1",
            "first_name": "Guest", "last_name": "Applicant",
        },
    )
    assert signup_resp.status_code == 201

    claimed = db_session.query(Candidate).filter_by(email="guest@test.com").first()
    assert claimed.id == guest_id
    assert claimed.password_hash is not None
    assert db_session.query(Candidate).filter_by(email="guest@test.com").count() == 1


def test_wrong_password_rejected(client, db_session):
    _signup(client)
    response = client.post(
        "/api/v1/candidate-auth/login", json={"email": "candidate@test.com", "password": "wrong-password"}
    )
    assert response.status_code == 401


def test_staff_token_cannot_access_candidate_portal(auth_client):
    response = auth_client.get("/api/v1/candidate-portal/me")
    assert response.status_code == 401


def test_candidate_token_cannot_access_staff_routes(client, db_session):
    signup_resp = _signup(client)
    token = signup_resp.get_json()["data"]["access_token"]
    response = client.get("/api/v1/candidates", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code in (401, 403)


def test_candidate_sees_only_their_own_applications(client, db_session, test_company, test_user):
    signup_resp = _signup(client, email="owner@test.com")
    token = signup_resp.get_json()["data"]["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    template = PipelineTemplate(company_id=test_company.id, name="Standard")
    db_session.add(template)
    db_session.commit()
    stage = PipelineStage(pipeline_template_id=template.id, name="Screen", stage_order=0, stage_type="screening")
    db_session.add(stage)
    db_session.commit()
    job = Job(company_id=test_company.id, title="Engineer", pipeline_template_id=template.id, created_by=test_user.id)
    db_session.add(job)
    db_session.commit()

    owner_candidate = db_session.query(Candidate).filter_by(email="owner@test.com").first()
    owner_profile = CandidateProfile(company_id=test_company.id, candidate_id=owner_candidate.id, skills=[])
    db_session.add(owner_profile)
    db_session.commit()
    owner_application = Application(
        company_id=test_company.id, job_id=job.id, candidate_id=owner_candidate.id,
        candidate_profile_id=owner_profile.id, current_stage_id=stage.id, status="active",
    )
    db_session.add(owner_application)

    other_candidate = Candidate(email="other@test.com", first_name="Other", last_name="Person")
    db_session.add(other_candidate)
    db_session.commit()
    other_profile = CandidateProfile(company_id=test_company.id, candidate_id=other_candidate.id, skills=[])
    db_session.add(other_profile)
    db_session.commit()
    other_application = Application(
        company_id=test_company.id, job_id=job.id, candidate_id=other_candidate.id,
        candidate_profile_id=other_profile.id, current_stage_id=stage.id, status="active",
    )
    db_session.add(other_application)
    db_session.commit()

    list_resp = client.get("/api/v1/candidate-portal/applications", headers=auth)
    assert list_resp.status_code == 200
    ids = [row["id"] for row in list_resp.get_json()["data"]]
    assert str(owner_application.id) in ids
    assert str(other_application.id) not in ids

    forbidden_resp = client.get(
        f"/api/v1/candidate-portal/applications/{other_application.id}", headers=auth
    )
    assert forbidden_resp.status_code == 404


def test_candidate_sees_interviews_for_own_application(client, db_session, test_company, test_user):
    signup_resp = _signup(client, email="interviewee@test.com")
    token = signup_resp.get_json()["data"]["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    template = PipelineTemplate(company_id=test_company.id, name="Standard")
    db_session.add(template)
    db_session.commit()
    stage = PipelineStage(pipeline_template_id=template.id, name="Onsite", stage_order=0, stage_type="interview")
    db_session.add(stage)
    db_session.commit()
    job = Job(company_id=test_company.id, title="Engineer", pipeline_template_id=template.id, created_by=test_user.id)
    db_session.add(job)
    db_session.commit()

    candidate = db_session.query(Candidate).filter_by(email="interviewee@test.com").first()
    profile = CandidateProfile(company_id=test_company.id, candidate_id=candidate.id, skills=[])
    db_session.add(profile)
    db_session.commit()
    application = Application(
        company_id=test_company.id, job_id=job.id, candidate_id=candidate.id,
        candidate_profile_id=profile.id, current_stage_id=stage.id, status="active",
    )
    db_session.add(application)
    db_session.commit()
    interview = Interview(
        company_id=test_company.id, application_id=application.id, pipeline_stage_id=stage.id,
        round_name="Technical Round", created_by=test_user.id,
    )
    db_session.add(interview)
    db_session.commit()

    response = client.get(f"/api/v1/candidate-portal/applications/{application.id}/interviews", headers=auth)
    assert response.status_code == 200
    assert response.get_json()["data"][0]["round_name"] == "Technical Round"


def test_candidate_can_accept_own_offer(client, db_session, test_company, test_user):
    signup_resp = _signup(client, email="offeree@test.com")
    token = signup_resp.get_json()["data"]["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    template = PipelineTemplate(company_id=test_company.id, name="Standard")
    db_session.add(template)
    db_session.commit()
    stage = PipelineStage(pipeline_template_id=template.id, name="Offer", stage_order=0, stage_type="offer")
    db_session.add(stage)
    db_session.commit()
    job = Job(company_id=test_company.id, title="Engineer", pipeline_template_id=template.id, created_by=test_user.id)
    db_session.add(job)
    db_session.commit()

    candidate = db_session.query(Candidate).filter_by(email="offeree@test.com").first()
    profile = CandidateProfile(company_id=test_company.id, candidate_id=candidate.id, skills=[])
    db_session.add(profile)
    db_session.commit()
    application = Application(
        company_id=test_company.id, job_id=job.id, candidate_id=candidate.id,
        candidate_profile_id=profile.id, current_stage_id=stage.id, status="active",
    )
    db_session.add(application)
    db_session.commit()
    offer = Offer(
        company_id=test_company.id, application_id=application.id, salary_offered="100000.00",
        status="sent", created_by=test_user.id,
    )
    db_session.add(offer)
    db_session.commit()

    response = client.post(f"/api/v1/candidate-portal/offers/{offer.id}/accept", headers=auth)
    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "accepted"


def test_candidate_cannot_accept_someone_elses_offer(client, db_session, test_company, test_user):
    signup_resp = _signup(client, email="attacker@test.com")
    token = signup_resp.get_json()["data"]["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    template = PipelineTemplate(company_id=test_company.id, name="Standard")
    db_session.add(template)
    db_session.commit()
    stage = PipelineStage(pipeline_template_id=template.id, name="Offer", stage_order=0, stage_type="offer")
    db_session.add(stage)
    db_session.commit()
    job = Job(company_id=test_company.id, title="Engineer", pipeline_template_id=template.id, created_by=test_user.id)
    db_session.add(job)
    db_session.commit()

    victim = Candidate(email="victim@test.com", first_name="Victim", last_name="Person")
    db_session.add(victim)
    db_session.commit()
    victim_profile = CandidateProfile(company_id=test_company.id, candidate_id=victim.id, skills=[])
    db_session.add(victim_profile)
    db_session.commit()
    victim_application = Application(
        company_id=test_company.id, job_id=job.id, candidate_id=victim.id,
        candidate_profile_id=victim_profile.id, current_stage_id=stage.id, status="active",
    )
    db_session.add(victim_application)
    db_session.commit()
    victim_offer = Offer(
        company_id=test_company.id, application_id=victim_application.id, salary_offered="150000.00",
        status="sent", created_by=test_user.id,
    )
    db_session.add(victim_offer)
    db_session.commit()

    response = client.post(f"/api/v1/candidate-portal/offers/{victim_offer.id}/accept", headers=auth)
    assert response.status_code == 404
    assert db_session.query(Offer).filter_by(id=victim_offer.id).first().status == "sent"
