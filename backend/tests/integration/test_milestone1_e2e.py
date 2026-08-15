
from app.models.role import Permission
from app.models.job import JobApprovalStep


def _grant(db_session, role, code):
    perm = db_session.query(Permission).filter_by(code=code).first()
    if perm is None:
        perm = Permission(code=code)
        db_session.add(perm)
        db_session.flush()
    if perm not in role.permissions:
        role.permissions.append(perm)
    db_session.commit()


def test_full_milestone1_loop(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "job.create")
    _grant(db_session, test_user.role, "pipeline.manage")  # pipeline creation is now admin-gated (Pipeline Builder module)
    _grant(db_session, test_user.role, "job.approve")
    _grant(db_session, test_user.role, "application.manage")
    _grant(db_session, test_user.role, "candidate.view_all")
    _grant(db_session, test_user.role, "approval.manage_chains")

    # 1. Create a pipeline template with two stages.
    pipeline_resp = auth_client.post(
        "/api/v1/pipeline-templates",
        json={
            "name": "Standard Pipeline",
            "stages": [
                {"name": "Screening", "stage_order": 0, "stage_type": "screening"},
                {"name": "Interview", "stage_order": 1, "stage_type": "interview"},
            ],
        },
    )
    assert pipeline_resp.status_code == 201
    pipeline = pipeline_resp.get_json()["data"]
    screening_stage_id = pipeline["stages"][0]["id"]
    interview_stage_id = pipeline["stages"][1]["id"]

    # 2. Create and publish a job against that pipeline.
    create_resp = auth_client.post(
        "/api/v1/jobs", json={"title": "Backend Engineer", "pipeline_template_id": pipeline["id"]}
    )
    job_id = create_resp.get_json()["data"]["id"]

    auth_client.put("/api/v1/approval-chains/job", json={"role_ids": [str(test_user.role_id)]})
    submit_resp = auth_client.post(f"/api/v1/jobs/{job_id}/submit")
    assert submit_resp.status_code == 200

    step = db_session.query(JobApprovalStep).filter_by(job_id=job_id).first()
    approve_resp = auth_client.post(f"/api/v1/jobs/{job_id}/approval-steps/{step.id}/approve", json={})
    assert approve_resp.get_json()["data"]["status"] == "published"

    # 3. Candidate applies via the PUBLIC portal — no auth at all.
    apply_resp = auth_client.post(
        f"/api/v1/public/{test_company.slug}/jobs/{job_id}/apply",
        data={"email": "jane@example.com", "first_name": "Jane", "last_name": "Doe"},
        headers={"Authorization": ""},  # explicitly drop auth to prove this is public
    )
    assert apply_resp.status_code == 201
    application_id = apply_resp.get_json()["data"]["id"]

    # 4. Duplicate application should be rejected.
    dup_resp = auth_client.post(
        f"/api/v1/public/{test_company.slug}/jobs/{job_id}/apply",
        data={"email": "jane@example.com", "first_name": "Jane", "last_name": "Doe"},
        headers={"Authorization": ""},
    )
    assert dup_resp.status_code == 409

    # 5. Recruiter (authenticated) moves the candidate to Interview.
    move_resp = auth_client.patch(
        f"/api/v1/applications/{application_id}/stage",
        json={"target_stage_id": interview_stage_id, "note": "Strong screening call"},
    )
    assert move_resp.status_code == 200
    assert move_resp.get_json()["data"]["current_stage_id"] == interview_stage_id

    # 6. Timeline should show both stage entries in order.
    timeline_resp = auth_client.get(f"/api/v1/applications/{application_id}/timeline")
    entries = timeline_resp.get_json()["data"]
    assert len(entries) == 2
    assert entries[0]["to_stage_id"] == screening_stage_id
    assert entries[0]["from_stage_id"] is None
    assert entries[1]["to_stage_id"] == interview_stage_id
    assert entries[1]["from_stage_id"] == screening_stage_id


def test_cannot_apply_to_unpublished_job(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "job.create")
    _grant(db_session, test_user.role, "pipeline.manage")  # pipeline creation is now admin-gated (Pipeline Builder module)

    create_resp = auth_client.post("/api/v1/jobs", json={"title": "Draft Job"})
    job_id = create_resp.get_json()["data"]["id"]

    apply_resp = auth_client.post(
        f"/api/v1/public/{test_company.slug}/jobs/{job_id}/apply",
        data={"email": "someone@example.com", "first_name": "A", "last_name": "B"},
        headers={"Authorization": ""},
    )
    assert apply_resp.status_code == 422
    assert apply_resp.get_json()["error"]["code"] == "business_rule_violation"


def test_public_job_listing_never_shows_draft_jobs(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "job.create")
    _grant(db_session, test_user.role, "pipeline.manage")  # pipeline creation is now admin-gated (Pipeline Builder module)
    auth_client.post("/api/v1/jobs", json={"title": "Still Draft"})

    response = auth_client.get(f"/api/v1/public/{test_company.slug}/jobs", headers={"Authorization": ""})
    assert response.status_code == 200
    assert response.get_json()["data"] == []
