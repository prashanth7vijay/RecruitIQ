from app.models.role import Permission
from app.models.pipeline import PipelineTemplate, PipelineStage
from app.models.job import Job
from app.models.candidate import Candidate, CandidateProfile
from app.models.application import Application


def _grant(db_session, role, code):
    perm = db_session.query(Permission).filter_by(code=code).first()
    if perm is None:
        perm = Permission(code=code)
        db_session.add(perm)
        db_session.flush()
    if perm not in role.permissions:
        role.permissions.append(perm)
    db_session.commit()


def _make_job_with_pipeline(db_session, tenant_id, test_user, required_skills):
    template = PipelineTemplate(company_id=tenant_id, name="Standard")
    db_session.add(template)
    db_session.commit()
    stage = PipelineStage(pipeline_template_id=template.id, name="Screen", stage_order=0, stage_type="screening")
    db_session.add(stage)
    db_session.commit()

    job = Job(
        company_id=tenant_id, title="Engineer", pipeline_template_id=template.id,
        required_skills=required_skills, created_by=test_user.id,
    )
    db_session.add(job)
    db_session.commit()
    return job, stage


def _make_application(db_session, tenant_id, job, stage, email, skills):
    candidate = Candidate(email=email, first_name="Test", last_name="Candidate")
    db_session.add(candidate)
    db_session.commit()
    profile = CandidateProfile(company_id=tenant_id, candidate_id=candidate.id, skills=skills)
    db_session.add(profile)
    db_session.commit()
    application = Application(
        company_id=tenant_id, job_id=job.id, candidate_id=candidate.id,
        candidate_profile_id=profile.id, current_stage_id=stage.id, status="active",
    )
    db_session.add(application)
    db_session.commit()
    return application


def test_match_score_endpoint_is_post_not_get(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "candidate.view_all")
    job, stage = _make_job_with_pipeline(db_session, test_company.id, test_user, ["python", "sql"])
    application = _make_application(db_session, test_company.id, job, stage, "a@test.com", ["python"])

    get_resp = auth_client.get(f"/api/v1/ai/applications/{application.id}/match-score")
    assert get_resp.status_code == 405  # method not allowed — this is a side-effecting operation now

    post_resp = auth_client.post(f"/api/v1/ai/applications/{application.id}/match-score")
    assert post_resp.status_code == 200
    assert post_resp.get_json()["data"]["score"] == 50.0


def test_computed_match_score_persists_and_is_visible_on_applications_list(
    auth_client, db_session, test_user, test_company
):

    _grant(db_session, test_user.role, "candidate.view_all")
    job, stage = _make_job_with_pipeline(db_session, test_company.id, test_user, ["python", "sql"])
    application = _make_application(db_session, test_company.id, job, stage, "a@test.com", ["python", "sql"])

    auth_client.post(f"/api/v1/ai/applications/{application.id}/match-score")

    list_resp = auth_client.get(f"/api/v1/applications?job_id={job.id}")
    assert list_resp.status_code == 200
    rows = list_resp.get_json()["data"]
    assert rows[0]["match_score"] == 100.0


def test_rank_candidates_scores_everyone_and_sorts_descending(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "candidate.view_all")
    job, stage = _make_job_with_pipeline(db_session, test_company.id, test_user, ["python", "sql", "docker", "aws"])

    _make_application(db_session, test_company.id, job, stage, "low@test.com", ["python"])
    _make_application(db_session, test_company.id, job, stage, "high@test.com", ["python", "sql", "docker", "aws"])
    _make_application(db_session, test_company.id, job, stage, "mid@test.com", ["python", "sql"])

    response = auth_client.post(f"/api/v1/ai/jobs/{job.id}/rank-candidates")
    assert response.status_code == 200
    rows = response.get_json()["data"]
    assert len(rows) == 3
    scores = [r["match_score"] for r in rows]
    assert scores == sorted(scores, reverse=True)
    assert rows[0]["candidate"]["email"] == "high@test.com"
    assert rows[-1]["candidate"]["email"] == "low@test.com"


def test_rank_candidates_does_not_rescore_already_scored_applications(
    auth_client, db_session, test_user, test_company
):
    _grant(db_session, test_user.role, "candidate.view_all")
    job, stage = _make_job_with_pipeline(db_session, test_company.id, test_user, ["python"])
    application = _make_application(db_session, test_company.id, job, stage, "a@test.com", ["python"])

    from app.models.ai_request import AIRequest

    auth_client.post(f"/api/v1/ai/jobs/{job.id}/rank-candidates")
    first_count = db_session.query(AIRequest).filter_by(entity_id=application.id).count()
    assert first_count == 1

    # A second ranking pass without force= should not re-score.
    auth_client.post(f"/api/v1/ai/jobs/{job.id}/rank-candidates")
    second_count = db_session.query(AIRequest).filter_by(entity_id=application.id).count()
    assert second_count == 1


def test_rank_candidates_force_rescores_everyone(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "candidate.view_all")
    job, stage = _make_job_with_pipeline(db_session, test_company.id, test_user, ["python"])
    application = _make_application(db_session, test_company.id, job, stage, "a@test.com", ["python"])

    from app.models.ai_request import AIRequest

    auth_client.post(f"/api/v1/ai/jobs/{job.id}/rank-candidates")
    auth_client.post(f"/api/v1/ai/jobs/{job.id}/rank-candidates?force=true")
    count = db_session.query(AIRequest).filter_by(entity_id=application.id).count()
    assert count == 2


def test_rank_candidates_only_scores_active_applications(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "candidate.view_all")
    job, stage = _make_job_with_pipeline(db_session, test_company.id, test_user, ["python"])
    rejected = _make_application(db_session, test_company.id, job, stage, "rej@test.com", ["python"])
    rejected.status = "rejected"
    db_session.commit()
    _make_application(db_session, test_company.id, job, stage, "active@test.com", ["python"])

    response = auth_client.post(f"/api/v1/ai/jobs/{job.id}/rank-candidates")
    emails = [r["candidate"]["email"] for r in response.get_json()["data"]]
    assert "rej@test.com" not in emails
    assert "active@test.com" in emails


def test_cannot_rank_candidates_for_another_tenants_job(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "candidate.view_all")

    from app.models.company import Company

    other_company = Company(name="Other Co", slug="other-co-ranking-test")
    db_session.add(other_company)
    db_session.commit()
    other_job, _ = _make_job_with_pipeline(db_session, other_company.id, test_user, ["python"])

    response = auth_client.post(f"/api/v1/ai/jobs/{other_job.id}/rank-candidates")
    assert response.status_code == 404


def test_non_admin_without_view_permission_cannot_rank(auth_client, db_session, test_user, test_company):
    job, _ = _make_job_with_pipeline(db_session, test_company.id, test_user, ["python"])
    response = auth_client.post(f"/api/v1/ai/jobs/{job.id}/rank-candidates")
    assert response.status_code == 403
