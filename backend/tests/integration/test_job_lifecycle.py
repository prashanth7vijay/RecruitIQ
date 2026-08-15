from app.models.role import Role, Permission


def _grant_permission(db_session, role, code):
    perm = db_session.query(Permission).filter_by(code=code).first()
    if perm is None:
        perm = Permission(code=code)
        db_session.add(perm)
        db_session.flush()
    if perm not in role.permissions:
        role.permissions.append(perm)
    db_session.commit()


def test_create_job_starts_in_draft(auth_client, db_session, test_user):
    _grant_permission(db_session, test_user.role, "job.create")

    response = auth_client.post("/api/v1/jobs", json={"title": "Backend Engineer"})

    assert response.status_code == 201
    body = response.get_json()["data"]
    assert body["status"] == "draft"
    assert body["title"] == "Backend Engineer"


def test_cannot_close_a_draft_job(auth_client, db_session, test_user):
    _grant_permission(db_session, test_user.role, "job.create")
    _grant_permission(db_session, test_user.role, "job.close")

    create_resp = auth_client.post("/api/v1/jobs", json={"title": "Draft Job"})
    job_id = create_resp.get_json()["data"]["id"]

    response = auth_client.post(f"/api/v1/jobs/{job_id}/close")

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "invalid_transition"


def test_full_lifecycle_submit_approve_autopublish_close(auth_client, db_session, test_user):
    _grant_permission(db_session, test_user.role, "job.create")
    _grant_permission(db_session, test_user.role, "job.approve")
    _grant_permission(db_session, test_user.role, "job.close")
    _grant_permission(db_session, test_user.role, "approval.manage_chains")

    # Approval chains are admin-configured now, not chosen by the
    # submitter — this test's test_user plays both roles (submitter and
    # approver), so the chain just needs to name test_user's own role.
    auth_client.put(
        "/api/v1/approval-chains/job", json={"role_ids": [str(test_user.role_id)]}
    )

    create_resp = auth_client.post("/api/v1/jobs", json={"title": "Staff Engineer"})
    job_id = create_resp.get_json()["data"]["id"]

    submit_resp = auth_client.post(f"/api/v1/jobs/{job_id}/submit")
    assert submit_resp.status_code == 200
    assert submit_resp.get_json()["data"]["status"] == "pending_approval"

    job_resp = auth_client.get(f"/api/v1/jobs/{job_id}")
    # Fetch the approval step id directly via the DB, since it isn't
    # returned on the job payload itself in this API shape.
    from app.models.job import JobApprovalStep

    step = db_session.query(JobApprovalStep).filter_by(job_id=job_id).first()
    assert step is not None

    approve_resp = auth_client.post(
        f"/api/v1/jobs/{job_id}/approval-steps/{step.id}/approve", json={}
    )
    assert approve_resp.status_code == 200
    # Single approver, so the job should auto-publish once that one step is approved.
    assert approve_resp.get_json()["data"]["status"] == "published"
    assert approve_resp.get_json()["data"]["published_at"] is not None

    close_resp = auth_client.post(f"/api/v1/jobs/{job_id}/close")
    assert close_resp.status_code == 200
    assert close_resp.get_json()["data"]["status"] == "closed"

    # closed -> closed again should be rejected by the state machine
    reclose_resp = auth_client.post(f"/api/v1/jobs/{job_id}/close")
    assert reclose_resp.status_code == 409
