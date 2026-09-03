from app.models.candidate import Candidate

def test_referral_notification_appears_in_candidate_portal_after_signup(
    client, auth_client, db_session, test_user, test_company
):
    from app.models.role import Permission
    from app.models.pipeline import PipelineTemplate, PipelineStage
    from app.models.job import Job

    perm = db_session.query(Permission).filter_by(code="referral.submit").one()
    test_user.role.permissions.append(perm)
    db_session.commit()

    template = PipelineTemplate(company_id=test_company.id, name="Standard")
    db_session.add(template)
    db_session.commit()
    stage = PipelineStage(pipeline_template_id=template.id, name="Screen", stage_order=0, stage_type="screening")
    db_session.add(stage)
    db_session.commit()
    job = Job(
        company_id=test_company.id, title="Engineer", pipeline_template_id=template.id,
        status="published", created_by=test_user.id,
    )
    db_session.add(job)
    db_session.commit()

    refer_resp = auth_client.post(
        "/api/v1/employee-portal/referrals",
        json={"job_id": str(job.id), "email": "future-signup@test.com"},
    )
    assert refer_resp.status_code == 201

    signup_resp = client.post(
        "/api/v1/candidate-auth/signup",
        json={
            "email": "future-signup@test.com", "password": "a-strong-password-1",
            "first_name": "Future", "last_name": "Signup",
        },
    )
    assert signup_resp.status_code == 201
    token = signup_resp.get_json()["data"]["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    list_resp = client.get("/api/v1/candidate-portal/notifications", headers=auth)
    assert list_resp.status_code == 200
    notifications = list_resp.get_json()["data"]
    assert len(notifications) == 1
    assert notifications[0]["type"] == "referral_received"
    assert notifications[0]["payload"]["job_title"] == "Engineer"
    assert notifications[0]["read_at"] is None

    read_resp = client.patch(
        f"/api/v1/candidate-portal/notifications/{notifications[0]['id']}/read", headers=auth
    )
    assert read_resp.status_code == 200
    assert read_resp.get_json()["data"]["read_at"] is not None


def test_candidate_cannot_read_another_candidates_notification(client, db_session, test_company):
    from app.models.notification import Notification

    other = Candidate(email="other-notif@test.com", first_name="Other", last_name="Person")
    db_session.add(other)
    db_session.commit()
    other_notification = Notification(
        company_id=test_company.id, candidate_id=other.id, type="referral_received",
        channel="in_app", payload={"job_title": "Secret"},
    )
    db_session.add(other_notification)
    db_session.commit()

    signup_resp = client.post(
        "/api/v1/candidate-auth/signup",
        json={
            "email": "reader@test.com", "password": "a-strong-password-1",
            "first_name": "Reader", "last_name": "Person",
        },
    )
    token = signup_resp.get_json()["data"]["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    response = client.patch(
        f"/api/v1/candidate-portal/notifications/{other_notification.id}/read", headers=auth
    )
    assert response.status_code == 404
