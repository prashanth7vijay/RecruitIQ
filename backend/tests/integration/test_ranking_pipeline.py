from app.models.role import Permission
from app.models.pipeline import PipelineTemplate, PipelineStage
from app.models.job import Job
from app.models.candidate import Candidate, CandidateProfile
from app.models.application import Application
from app.models.ai_request import AIRequest


def _grant(db_session, role, code):
    perm = db_session.query(Permission).filter_by(code=code).first()
    if perm is None:
        perm = Permission(code=code)
        db_session.add(perm)
        db_session.flush()
    if perm not in role.permissions:
        role.permissions.append(perm)
    db_session.commit()


def _make_job_with_pipeline(db_session, tenant_id, test_user, required_skills, experience_min=None, experience_max=None):
    template = PipelineTemplate(company_id=tenant_id, name="Standard")
    db_session.add(template)
    db_session.commit()
    stage = PipelineStage(pipeline_template_id=template.id, name="Screen", stage_order=0, stage_type="screening")
    db_session.add(stage)
    db_session.commit()

    job = Job(
        company_id=tenant_id, title="Engineer", pipeline_template_id=template.id,
        required_skills=required_skills, created_by=test_user.id,
        experience_min=experience_min, experience_max=experience_max,
    )
    db_session.add(job)
    db_session.commit()
    return job, stage


def _make_application(db_session, tenant_id, job, stage, email, skills, experience_years=None):
    candidate = Candidate(email=email, first_name="Test", last_name="Candidate")
    db_session.add(candidate)
    db_session.commit()
    profile = CandidateProfile(
        company_id=tenant_id, candidate_id=candidate.id, skills=skills, experience_years=experience_years,
    )
    db_session.add(profile)
    db_session.commit()
    application = Application(
        company_id=tenant_id, job_id=job.id, candidate_id=candidate.id,
        candidate_profile_id=profile.id, current_stage_id=stage.id, status="active",
    )
    db_session.add(application)
    db_session.commit()
    return application


def test_rank_candidates_response_includes_ranking_metrics(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "candidate.view_all")
    job, stage = _make_job_with_pipeline(db_session, test_company.id, test_user, ["ranking-metrics-skill-a"])
    _make_application(db_session, test_company.id, job, stage, "metrics1@test.com", ["ranking-metrics-skill-a"])
    _make_application(db_session, test_company.id, job, stage, "metrics2@test.com", ["ranking-metrics-skill-a"])

    response = auth_client.post(f"/api/v1/ai/jobs/{job.id}/rank-candidates")
    assert response.status_code == 200
    meta = response.get_json()["meta"]["ranking"]
    assert meta["candidates_considered"] == 2
    assert meta["candidates_scored"] == 2
    assert meta["candidates_filtered_out"] == 0
    assert meta["duration_seconds"] >= 0


def test_candidate_with_no_required_skill_overlap_is_filtered_and_not_scored(
    auth_client, db_session, test_user, test_company
):
    _grant(db_session, test_user.role, "candidate.view_all")
    job, stage = _make_job_with_pipeline(db_session, test_company.id, test_user, ["ranking-filter-skill-python"])
    filtered_app = _make_application(
        db_session, test_company.id, job, stage, "filtered@test.com", ["ranking-filter-skill-java"]
    )
    passing_app = _make_application(
        db_session, test_company.id, job, stage, "passing@test.com", ["ranking-filter-skill-python"]
    )

    response = auth_client.post(f"/api/v1/ai/jobs/{job.id}/rank-candidates")
    assert response.status_code == 200

    meta = response.get_json()["meta"]["ranking"]
    assert meta["candidates_filtered_out"] == 1
    assert meta["candidates_scored"] == 1

    ai_requests_for_filtered = db_session.query(AIRequest).filter_by(entity_id=filtered_app.id).count()
    assert ai_requests_for_filtered == 0

    ai_requests_for_passing = db_session.query(AIRequest).filter_by(entity_id=passing_app.id).count()
    assert ai_requests_for_passing == 1

    # The filtered-out candidate is still a real applicant in the
    # response, just unscored — not silently dropped from the list.
    emails = [r["candidate"]["email"] for r in response.get_json()["data"]]
    assert "filtered@test.com" in emails
    assert "passing@test.com" in emails


def test_candidate_outside_experience_band_is_filtered_out(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "candidate.view_all")
    job, stage = _make_job_with_pipeline(
        db_session, test_company.id, test_user, ["ranking-exp-skill"], experience_min=5, experience_max=10
    )
    junior = _make_application(
        db_session, test_company.id, job, stage, "junior@test.com", ["ranking-exp-skill"], experience_years=1
    )

    response = auth_client.post(f"/api/v1/ai/jobs/{job.id}/rank-candidates")
    meta = response.get_json()["meta"]["ranking"]
    assert meta["candidates_filtered_out"] == 1

    ai_requests = db_session.query(AIRequest).filter_by(entity_id=junior.id).count()
    assert ai_requests == 0


def test_two_candidates_with_identical_skill_signature_reuse_one_ai_call(
    auth_client, db_session, test_user, test_company
):
    """The explanation cache is keyed on (tenant, required-skills,
    candidate-skills) — two applications with the exact same signature
    on the same job should only cost one real AI call between them."""
    _grant(db_session, test_user.role, "candidate.view_all")
    job, stage = _make_job_with_pipeline(db_session, test_company.id, test_user, ["ranking-cache-skill-unique-xyz"])
    _make_application(db_session, test_company.id, job, stage, "cache1@test.com", ["ranking-cache-skill-unique-xyz"])
    _make_application(db_session, test_company.id, job, stage, "cache2@test.com", ["ranking-cache-skill-unique-xyz"])

    response = auth_client.post(f"/api/v1/ai/jobs/{job.id}/rank-candidates")
    meta = response.get_json()["meta"]["ranking"]

    # Both applications get scored (2 AIRequest rows — an audit row per
    # scored application), but only one of them should have actually
    # called the AI client; the second reused the cached explanation.
    assert meta["candidates_scored"] == 2
    assert meta["ai_calls_made"] == 1
    assert meta["ai_calls_cached"] == 1
    assert meta["cache_hit_rate"] == 0.5


def test_rank_candidates_async_returns_queued_job_and_completes_eagerly(
    auth_client, db_session, test_user, test_company
):
    """CELERY_TASK_ALWAYS_EAGER=True in TestingConfig runs the task
    synchronously in-process, so by the time .delay() returns, the
    result is already available — this exercises the real task body,
    not a mock."""
    _grant(db_session, test_user.role, "candidate.view_all")
    job, stage = _make_job_with_pipeline(db_session, test_company.id, test_user, ["ranking-async-skill"])
    _make_application(db_session, test_company.id, job, stage, "async1@test.com", ["ranking-async-skill"])

    queue_resp = auth_client.post(f"/api/v1/ai/jobs/{job.id}/rank-candidates/async")
    assert queue_resp.status_code == 202
    task_id = queue_resp.get_json()["data"]["job_id"]

    status_resp = auth_client.get(f"/api/v1/ai/ranking-jobs/{task_id}")
    assert status_resp.status_code == 200
    body = status_resp.get_json()["data"]
    assert body["status"] == "COMPLETED"
    assert body["result"]["metrics"]["candidates_considered"] == 1
    assert len(body["result"]["candidates"]) == 1


def test_rank_candidates_async_404s_for_another_tenants_job(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "candidate.view_all")

    from app.models.company import Company

    other_company = Company(name="Other Co Async", slug="other-co-async-ranking-test")
    db_session.add(other_company)
    db_session.commit()
    other_job, _ = _make_job_with_pipeline(db_session, other_company.id, test_user, ["python"])

    response = auth_client.post(f"/api/v1/ai/jobs/{other_job.id}/rank-candidates/async")
    assert response.status_code == 404
