from app.models.role import Permission
from app.models.job import JobApprovalStep
from app.models.onboarding import OnboardingChecklist


def _grant(db_session, role, code):
    perm = db_session.query(Permission).filter_by(code=code).first()
    if perm is None:
        perm = Permission(code=code)
        db_session.add(perm)
        db_session.flush()
    if perm not in role.permissions:
        role.permissions.append(perm)
    db_session.commit()


def _create_application(auth_client, db_session, test_company, test_user):
    pipeline_resp = auth_client.post(
        "/api/v1/pipeline-templates",
        json={"name": "P", "stages": [{"name": "Offer", "stage_order": 0, "stage_type": "offer"}]},
    )
    pipeline = pipeline_resp.get_json()["data"]
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
    return apply_resp.get_json()["data"]["id"]


def test_offer_approval_chain_and_auto_send(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "job.create")
    _grant(db_session, test_user.role, "pipeline.manage")  # pipeline creation is now admin-gated (Pipeline Builder module)
    _grant(db_session, test_user.role, "job.approve")
    _grant(db_session, test_user.role, "offer.create")
    _grant(db_session, test_user.role, "offer.approve")
    _grant(db_session, test_user.role, "approval.manage_chains")

    application_id = _create_application(auth_client, db_session, test_company, test_user)

    create_resp = auth_client.post(
        "/api/v1/offers", json={"application_id": application_id, "salary_offered": "120000.00"}
    )
    assert create_resp.status_code == 201
    offer_id = create_resp.get_json()["data"]["id"]
    assert create_resp.get_json()["data"]["status"] == "draft"

    auth_client.put("/api/v1/approval-chains/offer", json={"role_ids": [str(test_user.role_id)]})
    submit_resp = auth_client.post(f"/api/v1/offers/{offer_id}/submit")
    assert submit_resp.get_json()["data"]["status"] == "pending_approval"

    from app.models.offer import OfferApprovalStep
    step = db_session.query(OfferApprovalStep).filter_by(offer_id=offer_id).first()

    approve_resp = auth_client.post(f"/api/v1/offers/{offer_id}/approval-steps/{step.id}/approve", json={})
    assert approve_resp.get_json()["data"]["status"] == "sent"  # auto-sends once fully approved


def test_offer_acceptance_triggers_onboarding_checklist(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "job.create")
    _grant(db_session, test_user.role, "pipeline.manage")  # pipeline creation is now admin-gated (Pipeline Builder module)
    _grant(db_session, test_user.role, "job.approve")
    _grant(db_session, test_user.role, "offer.create")
    _grant(db_session, test_user.role, "offer.approve")
    _grant(db_session, test_user.role, "approval.manage_chains")

    application_id = _create_application(auth_client, db_session, test_company, test_user)

    create_resp = auth_client.post(
        "/api/v1/offers", json={"application_id": application_id, "salary_offered": "120000.00"}
    )
    offer_id = create_resp.get_json()["data"]["id"]
    auth_client.put("/api/v1/approval-chains/offer", json={"role_ids": [str(test_user.role_id)]})
    auth_client.post(f"/api/v1/offers/{offer_id}/submit")

    from app.models.offer import OfferApprovalStep
    step = db_session.query(OfferApprovalStep).filter_by(offer_id=offer_id).first()
    auth_client.post(f"/api/v1/offers/{offer_id}/approval-steps/{step.id}/approve", json={})

    # This is the line that, in eager Celery mode, synchronously runs the
    # whole event chain: accept -> publish offer.accepted -> onboarding created.
    accept_resp = auth_client.post(f"/api/v1/offers/{offer_id}/accept")
    assert accept_resp.get_json()["data"]["status"] == "accepted"

    checklist = db_session.query(OnboardingChecklist).filter_by(application_id=application_id).first()
    assert checklist is not None
    assert len(checklist.tasks) == 3

    # And it's fetchable via the API.
    onboarding_resp = auth_client.get(f"/api/v1/onboarding/by-application/{application_id}")
    assert onboarding_resp.status_code == 200
    assert onboarding_resp.get_json()["data"]["status"] == "pending"


def test_cannot_send_offer_directly_without_approval(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "job.create")
    _grant(db_session, test_user.role, "pipeline.manage")  # pipeline creation is now admin-gated (Pipeline Builder module)
    _grant(db_session, test_user.role, "job.approve")
    _grant(db_session, test_user.role, "offer.create")
    _grant(db_session, test_user.role, "approval.manage_chains")

    application_id = _create_application(auth_client, db_session, test_company, test_user)
    create_resp = auth_client.post(
        "/api/v1/offers", json={"application_id": application_id, "salary_offered": "100000.00"}
    )
    offer_id = create_resp.get_json()["data"]["id"]

    # Attempting to accept a draft offer (never submitted/sent) should fail —
    # the state machine only allows accept from 'sent'. State-machine
    # violations raise InvalidTransitionError -> 409 Conflict (the offer
    # resource is in a conflicting state for this action), not 422
    # (which this app reserves for payload/business-rule validation).
    response = auth_client.post(f"/api/v1/offers/{offer_id}/accept")
    assert response.status_code == 409
