from app.models.role import Permission, Role
from app.models.user import User
from app.models.job import JobApprovalStep
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


def _create_job(auth_client, db_session, test_user):
    pipeline_resp = auth_client.post(
        "/api/v1/pipeline-templates",
        json={"name": "P", "stages": [{"name": "Screen", "stage_order": 0, "stage_type": "screening"}]},
    )
    pipeline_id = pipeline_resp.get_json()["data"]["id"]
    create_resp = auth_client.post(
        "/api/v1/jobs", json={"title": "Engineer", "pipeline_template_id": pipeline_id}
    )
    return create_resp.get_json()["data"]["id"]


def test_non_admin_cannot_configure_approval_chain(auth_client, db_session, test_user):
    role = Role(company_id=None, name="hiring_manager", is_system_role=True)
    db_session.add(role)
    db_session.commit()

    response = auth_client.put("/api/v1/approval-chains/job", json={"role_ids": [str(role.id)]})
    assert response.status_code == 403


def test_configure_and_read_approval_chain(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "approval.manage_chains")

    role_a = Role(company_id=None, name="hiring_manager", is_system_role=True)
    role_b = Role(company_id=None, name="finance", is_system_role=True)
    db_session.add_all([role_a, role_b])
    db_session.commit()

    set_resp = auth_client.put(
        "/api/v1/approval-chains/job", json={"role_ids": [str(role_a.id), str(role_b.id)]}
    )
    assert set_resp.status_code == 200
    steps = set_resp.get_json()["data"]["steps"]
    assert [s["role_name"] for s in steps] == ["hiring_manager", "finance"]

    get_resp = auth_client.get("/api/v1/approval-chains/job")
    assert get_resp.status_code == 200
    assert len(get_resp.get_json()["data"]["steps"]) == 2


def test_reconfiguring_chain_replaces_previous_steps(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "approval.manage_chains")

    role_a = Role(company_id=None, name="hiring_manager", is_system_role=True)
    role_b = Role(company_id=None, name="finance", is_system_role=True)
    db_session.add_all([role_a, role_b])
    db_session.commit()

    auth_client.put("/api/v1/approval-chains/job", json={"role_ids": [str(role_a.id)]})
    replace_resp = auth_client.put("/api/v1/approval-chains/job", json={"role_ids": [str(role_b.id)]})

    steps = replace_resp.get_json()["data"]["steps"]
    assert len(steps) == 1
    assert steps[0]["role_name"] == "finance"


def test_cannot_configure_chain_with_role_from_another_tenant(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "approval.manage_chains")

    from app.models.company import Company

    other_company = Company(name="Other Co", slug="other-co-approval-test")
    db_session.add(other_company)
    db_session.commit()
    foreign_role = Role(company_id=other_company.id, name="Foreign Role", is_system_role=False)
    db_session.add(foreign_role)
    db_session.commit()

    response = auth_client.put("/api/v1/approval-chains/job", json={"role_ids": [str(foreign_role.id)]})
    assert response.status_code == 404


def test_submit_without_configured_chain_is_rejected(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "job.create")
    _grant(db_session, test_user.role, "pipeline.manage")

    job_id = _create_job(auth_client, db_session, test_user)
    response = auth_client.post(f"/api/v1/jobs/{job_id}/submit")
    assert response.status_code == 422
    assert "approval chain" in response.get_json()["error"]["message"].lower()


def test_submit_no_longer_accepts_client_supplied_approvers(auth_client, db_session, test_user):
    """The core design fix: whatever the client sends in the body is now
    ignored entirely — the chain comes from admin configuration only."""
    _grant(db_session, test_user.role, "job.create")
    _grant(db_session, test_user.role, "pipeline.manage")
    _grant(db_session, test_user.role, "approval.manage_chains")

    other_role = Role(company_id=None, name="finance", is_system_role=True)
    db_session.add(other_role)
    db_session.commit()
    auth_client.put("/api/v1/approval-chains/job", json={"role_ids": [str(other_role.id)]})

    job_id = _create_job(auth_client, db_session, test_user)
    # Even though the request body claims a different approver, the
    # server-configured chain (finance) is what actually gets used.
    response = auth_client.post(
        f"/api/v1/jobs/{job_id}/submit", json={"approver_roles": ["some_role_the_client_made_up"]}
    )
    assert response.status_code == 200
    step = db_session.query(JobApprovalStep).filter_by(job_id=job_id).first()
    assert str(step.approver_role_id) == str(other_role.id)


def test_user_with_wrong_role_cannot_approve_step_even_with_blanket_permission(
    auth_client, db_session, test_user, test_company
):
    """This is the actual gap the module exists to close: previously,
    job.approve alone was sufficient to approve ANY step, regardless of
    which role it named."""
    _grant(db_session, test_user.role, "job.create")
    _grant(db_session, test_user.role, "pipeline.manage")
    _grant(db_session, test_user.role, "approval.manage_chains")

    required_role = Role(company_id=None, name="finance", is_system_role=True)
    db_session.add(required_role)
    db_session.commit()
    auth_client.put("/api/v1/approval-chains/job", json={"role_ids": [str(required_role.id)]})

    job_id = _create_job(auth_client, db_session, test_user)
    auth_client.post(f"/api/v1/jobs/{job_id}/submit")
    step = db_session.query(JobApprovalStep).filter_by(job_id=job_id).first()

    # test_user holds job.approve (granted below) but NOT the "finance"
    # role the step actually requires.
    _grant(db_session, test_user.role, "job.approve")
    response = auth_client.post(f"/api/v1/jobs/{job_id}/approval-steps/{step.id}/approve", json={})
    assert response.status_code == 403


def test_user_with_matching_role_can_approve_step(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "job.create")
    _grant(db_session, test_user.role, "pipeline.manage")
    _grant(db_session, test_user.role, "approval.manage_chains")

    auth_client.put("/api/v1/approval-chains/job", json={"role_ids": [str(test_user.role_id)]})
    job_id = _create_job(auth_client, db_session, test_user)
    auth_client.post(f"/api/v1/jobs/{job_id}/submit")
    step = db_session.query(JobApprovalStep).filter_by(job_id=job_id).first()

    _grant(db_session, test_user.role, "job.approve")
    response = auth_client.post(f"/api/v1/jobs/{job_id}/approval-steps/{step.id}/approve", json={})
    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "published"


def test_multi_step_chain_requires_correct_role_at_each_step(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "job.create")
    _grant(db_session, test_user.role, "pipeline.manage")
    _grant(db_session, test_user.role, "approval.manage_chains")
    _grant(db_session, test_user.role, "job.approve")

    finance_role = Role(company_id=None, name="finance", is_system_role=True)
    db_session.add(finance_role)
    db_session.commit()

    # Two-step chain: test_user's own role first, then "finance".
    auth_client.put(
        "/api/v1/approval-chains/job",
        json={"role_ids": [str(test_user.role_id), str(finance_role.id)]},
    )
    job_id = _create_job(auth_client, db_session, test_user)
    auth_client.post(f"/api/v1/jobs/{job_id}/submit")

    steps = sorted(
        db_session.query(JobApprovalStep).filter_by(job_id=job_id).all(), key=lambda s: s.step_order
    )
    first_step, second_step = steps

    # test_user can approve the first step (matches their role)...
    approve_first = auth_client.post(
        f"/api/v1/jobs/{job_id}/approval-steps/{first_step.id}/approve", json={}
    )
    assert approve_first.status_code == 200
    assert approve_first.get_json()["data"]["status"] == "pending_approval"  # not published yet

    # ...but cannot approve the second (requires "finance", which they don't hold).
    approve_second = auth_client.post(
        f"/api/v1/jobs/{job_id}/approval-steps/{second_step.id}/approve", json={}
    )
    assert approve_second.status_code == 403


def test_offer_approval_also_enforces_role_match(auth_client, db_session, test_user, test_company):
    from app.models.offer import OfferApprovalStep

    _grant(db_session, test_user.role, "job.create")
    _grant(db_session, test_user.role, "pipeline.manage")
    _grant(db_session, test_user.role, "job.approve")
    _grant(db_session, test_user.role, "offer.create")
    _grant(db_session, test_user.role, "approval.manage_chains")

    auth_client.put("/api/v1/approval-chains/job", json={"role_ids": [str(test_user.role_id)]})

    pipeline_resp = auth_client.post(
        "/api/v1/pipeline-templates",
        json={"name": "P", "stages": [{"name": "Offer", "stage_order": 0, "stage_type": "offer"}]},
    )
    pipeline_id = pipeline_resp.get_json()["data"]["id"]
    job_resp = auth_client.post("/api/v1/jobs", json={"title": "Eng", "pipeline_template_id": pipeline_id})
    job_id = job_resp.get_json()["data"]["id"]
    auth_client.post(f"/api/v1/jobs/{job_id}/submit")
    job_step = db_session.query(JobApprovalStep).filter_by(job_id=job_id).first()
    auth_client.post(f"/api/v1/jobs/{job_id}/approval-steps/{job_step.id}/approve", json={})

    apply_resp = auth_client.post(
        f"/api/v1/public/{test_company.slug}/jobs/{job_id}/apply",
        data={"email": "jane@example.com", "first_name": "Jane", "last_name": "Doe"},
        headers={"Authorization": ""},
    )
    application_id = apply_resp.get_json()["data"]["id"]

    offer_resp = auth_client.post(
        "/api/v1/offers", json={"application_id": application_id, "salary_offered": "100000.00"}
    )
    offer_id = offer_resp.get_json()["data"]["id"]

    finance_role = Role(company_id=None, name="finance", is_system_role=True)
    db_session.add(finance_role)
    db_session.commit()
    auth_client.put("/api/v1/approval-chains/offer", json={"role_ids": [str(finance_role.id)]})
    auth_client.post(f"/api/v1/offers/{offer_id}/submit")

    offer_step = db_session.query(OfferApprovalStep).filter_by(offer_id=offer_id).first()
    _grant(db_session, test_user.role, "offer.approve")
    response = auth_client.post(f"/api/v1/offers/{offer_id}/approval-steps/{offer_step.id}/approve", json={})
    assert response.status_code == 403
