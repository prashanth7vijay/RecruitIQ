from app.models.role import Permission
from app.models.job import JobApprovalStep
from app.models.notification import Notification
from app.models.user import User
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


def _create_published_job_with_application(auth_client, db_session, test_company, test_user):
    pipeline_resp = auth_client.post(
        "/api/v1/pipeline-templates",
        json={
            "name": "P",
            "stages": [
                {"name": "Screening", "stage_order": 0, "stage_type": "screening"},
                {"name": "Interview", "stage_order": 1, "stage_type": "interview"},
            ],
        },
    )
    pipeline = pipeline_resp.get_json()["data"]

    create_resp = auth_client.post(
        "/api/v1/jobs", json={"title": "Engineer", "pipeline_template_id": pipeline["id"]}
    )
    job_id = create_resp.get_json()["data"]["id"]
    # Approval chains are admin-configured now (Approval Workflows
    # module) — test_user plays submitter and approver, so the chain
    # just needs to name test_user's own role. Requires the caller to
    # have granted job.approve and approval.manage_chains beforehand.
    auth_client.put("/api/v1/approval-chains/job", json={"role_ids": [str(test_user.role_id)]})
    auth_client.post(f"/api/v1/jobs/{job_id}/submit")
    step = db_session.query(JobApprovalStep).filter_by(job_id=job_id).first()
    auth_client.post(f"/api/v1/jobs/{job_id}/approval-steps/{step.id}/approve", json={})

    apply_resp = auth_client.post(
        f"/api/v1/public/{test_company.slug}/jobs/{job_id}/apply",
        data={"email": "jane@example.com", "first_name": "Jane", "last_name": "Doe", "resume": dummy_resume()},
        headers={"Authorization": ""},
    )
    return apply_resp.get_json()["data"]["id"]


def test_schedule_interview_and_submit_feedback(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "job.create")
    _grant(db_session, test_user.role, "pipeline.manage")  # pipeline creation is now admin-gated (Pipeline Builder module)
    _grant(db_session, test_user.role, "job.approve")
    _grant(db_session, test_user.role, "approval.manage_chains")
    _grant(db_session, test_user.role, "interview.schedule")
    _grant(db_session, test_user.role, "interview.feedback.submit")

    application_id = _create_published_job_with_application(auth_client, db_session, test_company, test_user)

    schedule_resp = auth_client.post(
        "/api/v1/interviews",
        json={
            "application_id": application_id,
            "round_name": "Technical Round",
            "panelist_user_ids": [str(test_user.id)],
        },
    )
    assert schedule_resp.status_code == 201
    interview_id = schedule_resp.get_json()["data"]["id"]
    assert schedule_resp.get_json()["data"]["status"] == "scheduled"

    # Notification chain: scheduling should have created an in-app
    # notification for the panelist and an email for the candidate.
    notifications = db_session.query(Notification).filter_by(company_id=test_company.id).all()
    assert any(n.type == "interview_scheduled" and n.channel == "in_app" for n in notifications)
    assert any(n.type == "interview_scheduled" and n.channel == "email" for n in notifications)

    feedback_resp = auth_client.post(
        f"/api/v1/interviews/{interview_id}/feedback",
        json={
            "rubric_scores": [{"criterion": "System Design", "score": 4.5, "comment": "Strong"}],
            "overall_rating": 4.5,
            "recommendation": "strong_yes",
            "notes": "Would hire.",
        },
    )
    assert feedback_resp.status_code == 201
    assert feedback_resp.get_json()["data"]["recommendation"] == "strong_yes"

    my_interviews_resp = auth_client.get("/api/v1/interviews/mine")
    assert len(my_interviews_resp.get_json()["data"]) == 1


def test_non_panelist_cannot_submit_feedback(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "job.create")
    _grant(db_session, test_user.role, "pipeline.manage")  # pipeline creation is now admin-gated (Pipeline Builder module)
    _grant(db_session, test_user.role, "job.approve")
    _grant(db_session, test_user.role, "approval.manage_chains")
    _grant(db_session, test_user.role, "interview.schedule")
    _grant(db_session, test_user.role, "interview.feedback.submit")

    application_id = _create_published_job_with_application(auth_client, db_session, test_company, test_user)

    # Schedule with a DIFFERENT, real panelist — interview_panelists.user_id
    # has a real FK to users, so a fabricated uuid4() (the original version
    # of this test) fails at the database, not at the 403 check this test
    # is actually trying to exercise.
    other_user = User(
        company_id=test_company.id,
        email="other-panelist@acme-test.com",
        password_hash=_hash_password("correct-horse-battery-staple"),
        first_name="Other",
        last_name="Panelist",
        role_id=test_user.role_id,
        status="active",
    )
    db_session.add(other_user)
    db_session.commit()

    schedule_resp = auth_client.post(
        "/api/v1/interviews",
        json={
            "application_id": application_id,
            "round_name": "Technical Round",
            "panelist_user_ids": [str(other_user.id)],
        },
    )
    interview_id = schedule_resp.get_json()["data"]["id"]

    feedback_resp = auth_client.post(
        f"/api/v1/interviews/{interview_id}/feedback",
        json={"rubric_scores": []},
    )
    assert feedback_resp.status_code == 403


def test_cannot_reschedule_a_cancelled_interview(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "job.create")
    _grant(db_session, test_user.role, "pipeline.manage")  # pipeline creation is now admin-gated (Pipeline Builder module)
    _grant(db_session, test_user.role, "job.approve")
    _grant(db_session, test_user.role, "approval.manage_chains")
    _grant(db_session, test_user.role, "interview.schedule")

    application_id = _create_published_job_with_application(auth_client, db_session, test_company, test_user)
    schedule_resp = auth_client.post(
        "/api/v1/interviews",
        json={
            "application_id": application_id,
            "round_name": "Screen",
            "panelist_user_ids": [str(test_user.id)],
        },
    )
    interview_id = schedule_resp.get_json()["data"]["id"]

    auth_client.patch(f"/api/v1/interviews/{interview_id}/cancel")

    response = auth_client.patch(
        f"/api/v1/interviews/{interview_id}/reschedule", json={"scheduled_at": "2026-08-01T10:00:00+00:00"}
    )
    assert response.status_code == 422
