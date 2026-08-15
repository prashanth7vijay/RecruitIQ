import uuid
from datetime import datetime, timedelta, timezone

from app.models.role import Permission
from app.models.department import Department
from app.models.job import Job
from app.models.candidate import Candidate, CandidateProfile
from app.models.pipeline import PipelineTemplate, PipelineStage
from app.models.application import Application
from app.models.offer import Offer


def _grant(db_session, role, code):
    perm = db_session.query(Permission).filter_by(code=code).first()
    if perm is None:
        perm = Permission(code=code)
        db_session.add(perm)
        db_session.flush()
    if perm not in role.permissions:
        role.permissions.append(perm)
    db_session.commit()


def _make_pipeline(db_session, tenant_id):
    template = PipelineTemplate(company_id=tenant_id, name="Standard")
    db_session.add(template)
    db_session.commit()
    screen = PipelineStage(pipeline_template_id=template.id, name="Screen", stage_order=0, stage_type="screening")
    interview = PipelineStage(pipeline_template_id=template.id, name="Onsite", stage_order=1, stage_type="interview")
    db_session.add_all([screen, interview])
    db_session.commit()
    return template, screen, interview


def _make_candidate_application(db_session, tenant_id, job_id, stage_id, email):
    candidate = Candidate(email=email, first_name="Test", last_name="Candidate")
    db_session.add(candidate)
    db_session.commit()
    profile = CandidateProfile(company_id=tenant_id, candidate_id=candidate.id, skills=[])
    db_session.add(profile)
    db_session.commit()
    application = Application(
        company_id=tenant_id,
        job_id=job_id,
        candidate_id=candidate.id,
        candidate_profile_id=profile.id,
        current_stage_id=stage_id,
        status="active",
        applied_at=datetime.now(timezone.utc) - timedelta(days=5),
    )
    db_session.add(application)
    db_session.commit()
    return application


def test_hiring_velocity_counts_published_jobs_and_accepted_offers(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "analytics.view_org")

    template, screen, _ = _make_pipeline(db_session, test_company.id)
    job = Job(
        company_id=test_company.id, title="Engineer", pipeline_template_id=template.id,
        status="published", created_by=test_user.id,
    )
    db_session.add(job)
    db_session.commit()

    application = _make_candidate_application(db_session, test_company.id, job.id, screen.id, "vel@test.com")
    offer = Offer(
        company_id=test_company.id, application_id=application.id, salary_offered="100000.00",
        status="accepted", created_by=test_user.id, responded_at=datetime.now(timezone.utc),
    )
    db_session.add(offer)
    db_session.commit()

    response = auth_client.get("/api/v1/analytics/velocity")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["jobs_published"] == 1
    assert data["hires"] == 1


def test_pipeline_health_groups_by_stage_type_across_jobs(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "analytics.view_org")

    template, screen, interview = _make_pipeline(db_session, test_company.id)
    job = Job(company_id=test_company.id, title="Engineer", pipeline_template_id=template.id, created_by=test_user.id)
    db_session.add(job)
    db_session.commit()

    _make_candidate_application(db_session, test_company.id, job.id, screen.id, "c1@test.com")
    _make_candidate_application(db_session, test_company.id, job.id, screen.id, "c2@test.com")
    _make_candidate_application(db_session, test_company.id, job.id, interview.id, "c3@test.com")

    response = auth_client.get("/api/v1/analytics/pipeline-health")
    assert response.status_code == 200
    by_stage = {row["stage_type"]: row["candidate_count"] for row in response.get_json()["data"]["by_stage_type"]}
    assert by_stage["screening"] == 2
    assert by_stage["interview"] == 1
    # applied_at was backdated 5 days with no stage-history rows, so
    # avg_days_in_current_stage should reflect that fallback.
    assert response.get_json()["data"]["avg_days_in_current_stage"] >= 4.9


def test_offer_acceptance_rate_excludes_withdrawn(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "analytics.view_org")

    template, screen, _ = _make_pipeline(db_session, test_company.id)
    job = Job(company_id=test_company.id, title="Engineer", pipeline_template_id=template.id, created_by=test_user.id)
    db_session.add(job)
    db_session.commit()

    statuses = ["accepted", "accepted", "rejected", "expired", "withdrawn"]
    for i, status in enumerate(statuses):
        app_row = _make_candidate_application(db_session, test_company.id, job.id, screen.id, f"offer{i}@test.com")
        db_session.add(
            Offer(
                company_id=test_company.id, application_id=app_row.id, salary_offered="90000.00",
                status=status, created_by=test_user.id,
            )
        )
    db_session.commit()

    response = auth_client.get("/api/v1/analytics/offer-acceptance")
    data = response.get_json()["data"]
    assert data["accepted"] == 2
    assert data["rejected"] == 1
    assert data["expired"] == 1
    # 2 accepted out of (2+1+1)=4 decided offers — withdrawn (5th) excluded entirely.
    assert data["acceptance_rate"] == 0.5


def test_department_hiring_breakdown(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "analytics.view_org")

    department = Department(company_id=test_company.id, name="Engineering")
    db_session.add(department)
    db_session.commit()

    template, screen, _ = _make_pipeline(db_session, test_company.id)
    job = Job(
        company_id=test_company.id, title="Engineer", pipeline_template_id=template.id,
        department_id=department.id, created_by=test_user.id,
    )
    db_session.add(job)
    db_session.commit()

    application = _make_candidate_application(db_session, test_company.id, job.id, screen.id, "dept@test.com")
    db_session.add(
        Offer(
            company_id=test_company.id, application_id=application.id, salary_offered="100000.00",
            status="accepted", created_by=test_user.id,
        )
    )
    db_session.commit()

    response = auth_client.get("/api/v1/analytics/department-hiring")
    rows = response.get_json()["data"]
    assert len(rows) == 1
    assert rows[0]["department_name"] == "Engineering"
    assert rows[0]["job_count"] == 1
    assert rows[0]["hires"] == 1


def test_department_with_no_jobs_is_omitted(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "analytics.view_org")

    empty_department = Department(company_id=test_company.id, name="Marketing")
    db_session.add(empty_department)
    db_session.commit()

    response = auth_client.get("/api/v1/analytics/department-hiring")
    names = [row["department_name"] for row in response.get_json()["data"]]
    assert "Marketing" not in names


def test_recruiter_performance_shows_names_not_raw_uuids(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "analytics.view_org")

    template, screen, _ = _make_pipeline(db_session, test_company.id)
    job = Job(company_id=test_company.id, title="Engineer", pipeline_template_id=template.id, created_by=test_user.id)
    db_session.add(job)
    db_session.commit()
    _make_candidate_application(db_session, test_company.id, job.id, screen.id, "rec@test.com")

    response = auth_client.get("/api/v1/analytics/recruiter-performance")
    rows = response.get_json()["data"]
    assert len(rows) == 1
    assert rows[0]["recruiter_name"] == f"{test_user.first_name} {test_user.last_name}"
    assert rows[0]["application_count"] == 1


def test_executive_summary_combines_all_metrics(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "analytics.view_org")

    response = auth_client.get("/api/v1/analytics/executive-summary")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert set(data.keys()) == {"velocity", "pipeline_health", "offer_acceptance", "time_to_hire", "department_hiring"}


def test_non_admin_cannot_view_analytics(client, db_session, test_user, test_company):
    login = client.post(
        "/api/v1/auth/login",
        json={"company_slug": test_company.slug, "email": test_user.email, "password": "correct-horse-battery-staple"},
    )
    auth = {"Authorization": f"Bearer {login.get_json()['data']['access_token']}"}
    response = client.get("/api/v1/analytics/executive-summary", headers=auth)
    assert response.status_code == 403
