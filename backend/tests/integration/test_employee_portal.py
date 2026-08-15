from app.models.role import Permission, Role
from app.models.user import User
from app.models.pipeline import PipelineTemplate, PipelineStage
from app.models.job import Job
from app.models.referral import Referral
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


def _make_published_job(db_session, tenant_id, test_user, title="Engineer"):
    template = PipelineTemplate(company_id=tenant_id, name="Standard")
    db_session.add(template)
    db_session.commit()
    stage = PipelineStage(pipeline_template_id=template.id, name="Screen", stage_order=0, stage_type="screening")
    db_session.add(stage)
    db_session.commit()
    job = Job(
        company_id=tenant_id, title=title, pipeline_template_id=template.id,
        status="published", created_by=test_user.id,
    )
    db_session.add(job)
    db_session.commit()
    return job


def test_any_authenticated_staff_can_see_open_jobs(auth_client, db_session, test_user, test_company):
    _make_published_job(db_session, test_company.id, test_user)

    response = auth_client.get("/api/v1/employee-portal/jobs")
    assert response.status_code == 200
    assert len(response.get_json()["data"]) == 1


def test_open_jobs_excludes_draft_jobs(auth_client, db_session, test_user, test_company):
    template = PipelineTemplate(company_id=test_company.id, name="Standard")
    db_session.add(template)
    db_session.commit()
    draft_job = Job(
        company_id=test_company.id, title="Secret Role", pipeline_template_id=template.id,
        status="draft", created_by=test_user.id,
    )
    db_session.add(draft_job)
    db_session.commit()

    response = auth_client.get("/api/v1/employee-portal/jobs")
    titles = [j["title"] for j in response.get_json()["data"]]
    assert "Secret Role" not in titles


def test_employee_without_permission_cannot_submit_referral(auth_client, db_session, test_user, test_company):
    job = _make_published_job(db_session, test_company.id, test_user)
    response = auth_client.post(
        "/api/v1/employee-portal/referrals",
        json={"job_id": str(job.id), "email": "ref@test.com", "first_name": "Ref", "last_name": "Erral"},
    )
    assert response.status_code == 403


def test_employee_can_submit_and_see_own_referral(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "referral.submit")
    job = _make_published_job(db_session, test_company.id, test_user)

    submit_resp = auth_client.post(
        "/api/v1/employee-portal/referrals",
        json={"job_id": str(job.id), "email": "candidate@test.com", "first_name": "Ref", "last_name": "Erral"},
    )
    assert submit_resp.status_code == 201

    list_resp = auth_client.get("/api/v1/employee-portal/referrals")
    assert list_resp.status_code == 200
    rows = list_resp.get_json()["data"]
    assert len(rows) == 1
    assert rows[0]["candidate_name"] == "Ref Erral"
    assert rows[0]["job_title"] == "Engineer"
    assert rows[0]["status"] == "active"


def test_referral_status_reflects_application_status_live(auth_client, db_session, test_user, test_company):
    """Confirms status is read from the Application, not a stale
    duplicated column — moving the application forward should change
    what the referral list reports without any referral-specific update."""
    _grant(db_session, test_user.role, "referral.submit")
    job = _make_published_job(db_session, test_company.id, test_user)

    submit_resp = auth_client.post(
        "/api/v1/employee-portal/referrals",
        json={"job_id": str(job.id), "email": "candidate2@test.com", "first_name": "Ref", "last_name": "Erral"},
    )
    application_id = submit_resp.get_json()["data"]["application_id"]

    from app.models.application import Application

    application = db_session.query(Application).filter_by(id=application_id).first()
    application.status = "hired"
    db_session.commit()

    list_resp = auth_client.get("/api/v1/employee-portal/referrals")
    assert list_resp.get_json()["data"][0]["status"] == "hired"


def test_cannot_refer_to_a_draft_job(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "referral.submit")
    template = PipelineTemplate(company_id=test_company.id, name="Standard")
    db_session.add(template)
    db_session.commit()
    draft_job = Job(
        company_id=test_company.id, title="Draft Role", pipeline_template_id=template.id,
        status="draft", created_by=test_user.id,
    )
    db_session.add(draft_job)
    db_session.commit()

    response = auth_client.post(
        "/api/v1/employee-portal/referrals",
        json={"job_id": str(draft_job.id), "email": "x@test.com", "first_name": "X", "last_name": "Y"},
    )
    assert response.status_code == 422


def test_cannot_refer_same_candidate_twice_to_same_job(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "referral.submit")
    job = _make_published_job(db_session, test_company.id, test_user)

    payload = {"job_id": str(job.id), "email": "dup@test.com", "first_name": "Dup", "last_name": "Licate"}
    first = auth_client.post("/api/v1/employee-portal/referrals", json=payload)
    assert first.status_code == 201
    second = auth_client.post("/api/v1/employee-portal/referrals", json=payload)
    assert second.status_code == 409


def test_employee_sees_only_their_own_referrals_not_a_colleagues(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "referral.submit")
    job = _make_published_job(db_session, test_company.id, test_user)

    auth_client.post(
        "/api/v1/employee-portal/referrals",
        json={"job_id": str(job.id), "email": "mine@test.com", "first_name": "Mine", "last_name": "Referral"},
    )

    colleague_role = Role(company_id=None, name="colleague_employee_test", is_system_role=True)
    db_session.add(colleague_role)
    db_session.commit()
    _grant(db_session, colleague_role, "referral.submit")
    colleague = User(
        company_id=test_company.id, email="colleague@test.com",
        password_hash=_hash_password("correct-horse-battery-staple"),
        first_name="Colleague", last_name="Person", role_id=colleague_role.id, status="active",
    )
    db_session.add(colleague)
    db_session.commit()

    from app.services.referral_service import ReferralService
    from app.repositories.referral_repository import ReferralRepository

    referral_count_for_colleague = ReferralService(
        session=db_session, referral_repo=ReferralRepository(db_session),
        application_service=None, job_repo=None,
    ).list_my_referrals(test_company.id, colleague.id)
    assert referral_count_for_colleague == []

    # Sanity: the referring user's own list still has exactly one entry.
    own_referrals = db_session.query(Referral).filter_by(referred_by_user_id=test_user.id).all()
    assert len(own_referrals) == 1
