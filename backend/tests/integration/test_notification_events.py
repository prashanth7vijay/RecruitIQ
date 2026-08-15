from app.models.role import Permission
from app.models.job import JobApprovalStep
from app.models.notification import Notification


def _grant(db_session, role, code):
    perm = db_session.query(Permission).filter_by(code=code).first()
    if perm is None:
        perm = Permission(code=code)
        db_session.add(perm)
        db_session.flush()
    if perm not in role.permissions:
        role.permissions.append(perm)
    db_session.commit()


def test_stage_move_creates_notifications_for_recruiter_and_candidate(
    auth_client, db_session, test_user, test_company
):
    _grant(db_session, test_user.role, "job.create")
    _grant(db_session, test_user.role, "pipeline.manage")  # pipeline creation is now admin-gated (Pipeline Builder module)
    _grant(db_session, test_user.role, "job.approve")
    _grant(db_session, test_user.role, "application.manage")
    _grant(db_session, test_user.role, "approval.manage_chains")

    pipeline_resp = auth_client.post(
        "/api/v1/pipeline-templates",
        json={
            "name": "Pipeline",
            "stages": [
                {"name": "Screening", "stage_order": 0, "stage_type": "screening"},
                {"name": "Interview", "stage_order": 1, "stage_type": "interview"},
            ],
        },
    )
    pipeline = pipeline_resp.get_json()["data"]
    interview_stage_id = pipeline["stages"][1]["id"]

    create_resp = auth_client.post(
        "/api/v1/jobs", json={"title": "Engineer", "pipeline_template_id": pipeline["id"]}
    )
    job_id = create_resp.get_json()["data"]["id"]

    auth_client.put("/api/v1/approval-chains/job", json={"role_ids": [str(test_user.role_id)]})
    auth_client.post(f"/api/v1/jobs/{job_id}/submit")
    step = db_session.query(JobApprovalStep).filter_by(job_id=job_id).first()
    auth_client.post(f"/api/v1/jobs/{job_id}/approval-steps/{step.id}/approve", json={})

    apply_resp = auth_client.post(
        f"/api/v1/public/{test_company.slug}/jobs/{job_id}/apply",
        data={"email": "jane@example.com", "first_name": "Jane", "last_name": "Doe"},
        headers={"Authorization": ""},
    )
    application_id = apply_resp.get_json()["data"]["id"]

    # This is the line that, in eager mode, synchronously runs the whole
    # event chain: publish -> notify_stage_change_task -> two Notification rows.
    auth_client.patch(
        f"/api/v1/applications/{application_id}/stage",
        json={"target_stage_id": interview_stage_id},
    )

    notifications = db_session.query(Notification).filter_by(company_id=test_company.id).all()
    in_app = [n for n in notifications if n.channel == "in_app"]
    email = [n for n in notifications if n.channel == "email"]

    assert len(in_app) == 1
    assert in_app[0].user_id == test_user.id  # the job's created_by recruiter
    assert in_app[0].payload["stage_name"] == "Interview"

    assert len(email) == 1
    assert email[0].candidate_id is not None
    assert email[0].payload["first_name"] == "Jane"
