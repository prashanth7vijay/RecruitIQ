from app.models.role import Permission, Role
from app.models.user import User
from app.models.pipeline import PipelineTemplate, PipelineStage
from app.models.job import Job
from app.models.referral import Referral
from app.models.notification import Notification
from app.services.auth_service import _hash_password
from tests.conftest import dummy_resume


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
        json={"job_id": str(job.id), "email": "ref@test.com"},
    )
    assert response.status_code == 403


def test_submitting_a_referral_only_creates_an_invite_and_notifies_the_candidate(
    auth_client, db_session, test_user, test_company
):
    _grant(db_session, test_user.role, "referral.submit")
    job = _make_published_job(db_session, test_company.id, test_user)

    submit_resp = auth_client.post(
        "/api/v1/employee-portal/referrals",
        json={"job_id": str(job.id), "email": "candidate@test.com"},
    )
    assert submit_resp.status_code == 201

    referral = db_session.query(Referral).filter_by(id=submit_resp.get_json()["data"]["id"]).first()
    assert referral.application_id is None
    assert referral.job_id == job.id

    notification = (
        db_session.query(Notification)
        .filter_by(candidate_id=referral.candidate_id, type="referral_received")
        .first()
    )
    assert notification is not None
    assert notification.payload["job_title"] == "Engineer"

    list_resp = auth_client.get("/api/v1/employee-portal/referrals")
    assert list_resp.status_code == 200
    rows = list_resp.get_json()["data"]
    assert len(rows) == 1
    assert rows[0]["status"] == "invited"
    assert rows[0]["candidate_email"] == "candidate@test.com"
    assert rows[0]["job_title"] == "Engineer"


def test_referral_is_completed_when_the_referred_person_applies(
    client, auth_client, db_session, test_user, test_company
):
    """The end-to-end shape the referral flow is actually for: employee
    refers -> candidate applies themselves (with a resume, same as any
    applicant) -> the Referral picks up the resulting application and the
    status the employee sees starts tracking the real pipeline."""
    _grant(db_session, test_user.role, "referral.submit")
    job = _make_published_job(db_session, test_company.id, test_user)

    auth_client.post(
        "/api/v1/employee-portal/referrals",
        json={"job_id": str(job.id), "email": "candidate2@test.com"},
    )

    apply_resp = client.post(
        f"/api/v1/public/{test_company.slug}/jobs/{job.id}/apply",
        data={
            "email": "candidate2@test.com",
            "first_name": "Real",
            "last_name": "Name",
            "resume": dummy_resume(),
        },
    )
    assert apply_resp.status_code == 201
    application_id = apply_resp.get_json()["data"]["id"]

    referral = db_session.query(Referral).filter_by(company_id=test_company.id).first()
    assert str(referral.application_id) == application_id

    from app.models.application import Application

    application = db_session.query(Application).filter_by(id=application_id).first()
    application.status = "hired"
    db_session.commit()

    list_resp = auth_client.get("/api/v1/employee-portal/referrals")
    row = list_resp.get_json()["data"][0]
    assert row["status"] == "hired"
    assert row["candidate_name"] == "Real Name"  # placeholder overwritten by their own apply


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
        json={"job_id": str(draft_job.id), "email": "x@test.com"},
    )
    assert response.status_code == 422


def test_cannot_refer_same_candidate_twice_to_same_job(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "referral.submit")
    job = _make_published_job(db_session, test_company.id, test_user)

    payload = {"job_id": str(job.id), "email": "dup@test.com"}
    first = auth_client.post("/api/v1/employee-portal/referrals", json=payload)
    assert first.status_code == 201
    second = auth_client.post("/api/v1/employee-portal/referrals", json=payload)
    assert second.status_code == 409


def test_employee_sees_only_their_own_referrals_not_a_colleagues(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "referral.submit")
    job = _make_published_job(db_session, test_company.id, test_user)

    auth_client.post(
        "/api/v1/employee-portal/referrals",
        json={"job_id": str(job.id), "email": "mine@test.com"},
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

    referrals_for_colleague = ReferralService(
        session=db_session, referral_repo=ReferralRepository(db_session), job_repo=None,
    ).list_my_referrals(test_company.id, colleague.id)
    assert referrals_for_colleague == []

    own_referrals = db_session.query(Referral).filter_by(referred_by_user_id=test_user.id).all()
    assert len(own_referrals) == 1
