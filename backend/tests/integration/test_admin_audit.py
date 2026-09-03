from app.models.role import Permission
from app.models.job import JobApprovalStep
from app.models.audit_log import AuditLog


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


def test_job_status_change_is_audited(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "job.create")
    _grant(db_session, test_user.role, "pipeline.manage")  # pipeline creation is now admin-gated (Pipeline Builder module)
    _grant(db_session, test_user.role, "approval.manage_chains")

    pipeline_resp = auth_client.post(
        "/api/v1/pipeline-templates",
        json={"name": "P", "stages": [{"name": "Screen", "stage_order": 0, "stage_type": "screening"}]},
    )
    pipeline_id = pipeline_resp.get_json()["data"]["id"]
    create_resp = auth_client.post(
        "/api/v1/jobs", json={"title": "Engineer", "pipeline_template_id": pipeline_id}
    )
    job_id = create_resp.get_json()["data"]["id"]

    # Approval chains are admin-configured now (see Approval Workflows
    # module) — test_user plays submitter and approver here, so the
    # chain just needs to name test_user's own role.
    auth_client.put("/api/v1/approval-chains/job", json={"role_ids": [str(test_user.role_id)]})
    auth_client.post(f"/api/v1/jobs/{job_id}/submit")

    entries = db_session.query(AuditLog).filter_by(entity_type="Job", entity_id=job_id).all()
    assert len(entries) == 1
    assert entries[0].action == "status_changed"
    assert entries[0].new_value == {"status": "pending_approval"}
    assert entries[0].actor_id == test_user.id


def test_offer_accept_is_audited(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "job.create")
    _grant(db_session, test_user.role, "pipeline.manage")  # pipeline creation is now admin-gated (Pipeline Builder module)
    _grant(db_session, test_user.role, "job.approve")
    _grant(db_session, test_user.role, "offer.create")
    _grant(db_session, test_user.role, "offer.approve")
    _grant(db_session, test_user.role, "approval.manage_chains")

    auth_client.put("/api/v1/approval-chains/job", json={"role_ids": [str(test_user.role_id)]})
    auth_client.put("/api/v1/approval-chains/offer", json={"role_ids": [str(test_user.role_id)]})

    pipeline_resp = auth_client.post(
        "/api/v1/pipeline-templates",
        json={"name": "P", "stages": [{"name": "Offer", "stage_order": 0, "stage_type": "offer"}]},
    )
    pipeline_id = pipeline_resp.get_json()["data"]["id"]
    job_resp = auth_client.post("/api/v1/jobs", json={"title": "Eng", "pipeline_template_id": pipeline_id})
    job_id = job_resp.get_json()["data"]["id"]
    auth_client.post(f"/api/v1/jobs/{job_id}/submit")
    step = db_session.query(JobApprovalStep).filter_by(job_id=job_id).first()
    auth_client.post(f"/api/v1/jobs/{job_id}/approval-steps/{step.id}/approve", json={})

    apply_resp = auth_client.post(
        f"/api/v1/public/{test_company.slug}/jobs/{job_id}/apply",
        data={"email": "jane@example.com", "first_name": "Jane", "last_name": "Doe", "resume": dummy_resume()},
        headers={"Authorization": ""},
    )
    application_id = apply_resp.get_json()["data"]["id"]

    offer_resp = auth_client.post(
        "/api/v1/offers", json={"application_id": application_id, "salary_offered": "100000.00"}
    )
    offer_id = offer_resp.get_json()["data"]["id"]
    auth_client.post(f"/api/v1/offers/{offer_id}/submit")

    from app.models.offer import OfferApprovalStep
    offer_step = db_session.query(OfferApprovalStep).filter_by(offer_id=offer_id).first()
    auth_client.post(f"/api/v1/offers/{offer_id}/approval-steps/{offer_step.id}/approve", json={})

    auth_client.post(f"/api/v1/offers/{offer_id}/accept")

    entries = db_session.query(AuditLog).filter_by(entity_type="Offer", entity_id=offer_id).all()
    assert any(e.action == "accepted" for e in entries)


def test_admin_can_list_and_update_user_status(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "admin.manage_users")

    list_resp = auth_client.get("/api/v1/admin/users")
    assert list_resp.status_code == 200
    assert len(list_resp.get_json()["data"]) >= 1

    update_resp = auth_client.patch(
        f"/api/v1/admin/users/{test_user.id}/status", json={"status": "disabled"}
    )
    assert update_resp.status_code == 200
    assert update_resp.get_json()["data"]["status"] == "disabled"

    audit_entries = db_session.query(AuditLog).filter_by(entity_type="User", entity_id=test_user.id).all()
    assert len(audit_entries) == 1
    assert audit_entries[0].action == "status_changed"


def test_admin_endpoints_require_permission(auth_client):
    response = auth_client.get("/api/v1/admin/users")
    assert response.status_code == 403


def test_system_health_reports_counts(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "admin.manage_users")
    response = auth_client.get("/api/v1/admin/system-health")
    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "ok"
    assert response.get_json()["data"]["user_count"] >= 1
