from datetime import datetime, timezone

from app.extensions import cache as flask_cache
from app.models.role import Permission
from app.models.pipeline import PipelineTemplate, PipelineStage
from app.models.job import Job
from app.models.candidate import Candidate, CandidateProfile
from app.models.application import Application
from app.models.offer import Offer
from app.services.analytics_service import _executive_summary_cache_key
from app.workers.analytics_tasks import invalidate_analytics_cache_task


def _grant(db_session, role, code):
    perm = db_session.query(Permission).filter_by(code=code).first()
    if perm is None:
        perm = Permission(code=code)
        db_session.add(perm)
        db_session.flush()
    if perm not in role.permissions:
        role.permissions.append(perm)
    db_session.commit()


def _make_pipeline_and_job(db_session, tenant_id, test_user):
    template = PipelineTemplate(company_id=tenant_id, name="Standard")
    db_session.add(template)
    db_session.commit()
    screen = PipelineStage(pipeline_template_id=template.id, name="Screen", stage_order=0, stage_type="screening")
    interview = PipelineStage(pipeline_template_id=template.id, name="Onsite", stage_order=1, stage_type="interview")
    db_session.add_all([screen, interview])
    db_session.commit()

    job = Job(company_id=tenant_id, title="Engineer", pipeline_template_id=template.id, created_by=test_user.id)
    db_session.add(job)
    db_session.commit()
    return job, screen, interview


def _make_application(db_session, tenant_id, job, stage, email):
    candidate = Candidate(email=email, first_name="Test", last_name="Candidate")
    db_session.add(candidate)
    db_session.commit()
    profile = CandidateProfile(company_id=tenant_id, candidate_id=candidate.id, skills=[])
    db_session.add(profile)
    db_session.commit()
    application = Application(
        company_id=tenant_id, job_id=job.id, candidate_id=candidate.id,
        candidate_profile_id=profile.id, current_stage_id=stage.id, status="active",
    )
    db_session.add(application)
    db_session.commit()
    return application


def test_cache_key_is_tenant_scoped():
    key_a = _executive_summary_cache_key("tenant-a")
    key_b = _executive_summary_cache_key("tenant-b")
    assert key_a != key_b
    assert "tenant-a" in key_a


def test_executive_summary_reports_cache_miss_then_hit(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "analytics.view_org")

    first = auth_client.get("/api/v1/analytics/executive-summary")
    assert first.status_code == 200
    assert first.get_json()["meta"]["cache_hit"] is False

    second = auth_client.get("/api/v1/analytics/executive-summary")
    assert second.get_json()["meta"]["cache_hit"] is True
    # Cached payload should be identical to the freshly-computed one.
    assert second.get_json()["data"] == first.get_json()["data"]


def test_executive_summary_cache_invalidated_on_stage_change(
    auth_client, db_session, test_user, test_company
):
    _grant(db_session, test_user.role, "analytics.view_org")
    _grant(db_session, test_user.role, "application.manage")
    job, screen, interview = _make_pipeline_and_job(db_session, test_company.id, test_user)
    application = _make_application(db_session, test_company.id, job, screen, "cache-invalidate@test.com")

    warm = auth_client.get("/api/v1/analytics/executive-summary")
    assert warm.get_json()["meta"]["cache_hit"] is False
    still_cached = auth_client.get("/api/v1/analytics/executive-summary")
    assert still_cached.get_json()["meta"]["cache_hit"] is True

    # CELERY_TASK_ALWAYS_EAGER=True in TestingConfig means this event's
    # subscribers (including invalidate_analytics_cache_task) run
    # synchronously, in-process, as part of this call.
    move_response = auth_client.patch(
        f"/api/v1/applications/{application.id}/stage", json={"target_stage_id": str(interview.id)}
    )
    assert move_response.status_code == 200

    after_change = auth_client.get("/api/v1/analytics/executive-summary")
    assert after_change.get_json()["meta"]["cache_hit"] is False, (
        "cache should have been invalidated by the application.stage_changed event"
    )


def test_invalidate_analytics_cache_task_clears_entry_for_offers_tenant(db_session, test_company, test_user):
    """Exercises the offer.accepted branch directly — accepting a real
    offer through the full API involves approval-chain setup unrelated
    to what this test is actually checking (that the task looks up the
    right tenant from an offer_id and clears that tenant's key)."""
    job, screen, _ = _make_pipeline_and_job(db_session, test_company.id, test_user)
    application = _make_application(db_session, test_company.id, job, screen, "offer-cache-test@test.com")

    offer = Offer(
        company_id=test_company.id,
        application_id=application.id,
        salary_offered=100000,
        status="accepted",
        created_by=test_user.id,
    )
    db_session.add(offer)
    db_session.commit()

    cache_key = _executive_summary_cache_key(test_company.id)
    flask_cache.set(cache_key, {"stale": True}, timeout=60)
    assert flask_cache.get(cache_key) is not None

    invalidate_analytics_cache_task({"offer_id": str(offer.id), "application_id": str(application.id)})

    assert flask_cache.get(cache_key) is None
