from app.models.ai_request import AIRequest

def compute_skill_overlap_score(required_skills: list, candidate_skills: list) -> float:
    if not required_skills:
        return 0.0
    required_set = {s.lower() for s in required_skills}
    candidate_set = {s.lower() for s in candidate_skills}
    overlap = required_set & candidate_set
    return round(100 * len(overlap) / len(required_set), 1)


class MatchScoreService:
    def __init__(self, ai_client, ai_request_repo, application_repo, job_repo, profile_repo):
        self.ai_client = ai_client
        self.ai_request_repo = ai_request_repo
        self.application_repo = application_repo
        self.job_repo = job_repo
        self.profile_repo = profile_repo

    def compute(self, tenant_id, application_id):
        application = self.application_repo.get_or_404(application_id, tenant_id)
        job = self.job_repo.get_or_404(application.job_id, tenant_id)
        profile = self.profile_repo.get_or_404(application.candidate_profile_id, tenant_id)

        score = compute_skill_overlap_score(job.required_skills, profile.skills)

        prompt = (
            f"A candidate has skills: {', '.join(profile.skills) or 'none listed'}. "
            f"The job requires: {', '.join(job.required_skills) or 'none listed'}. "
            f"In one sentence, explain the fit."
        )
        result = self.ai_client.complete(prompt)

        ai_request = AIRequest(
            company_id=tenant_id,
            feature="match_score",
            entity_type="application",
            entity_id=application_id,
            input_tokens=result.get("input_tokens"),
            output_tokens=result.get("output_tokens"),
            status="suggested",
        )
        self.ai_request_repo.add(ai_request)
        self.ai_request_repo.commit()

        application.match_score = score
        self.application_repo.commit()

        return {"score": score, "explanation": result["text"], "ai_request_id": ai_request.id}

    def rank_candidates_for_job(self, tenant_id, job_id, force=False):

        self.job_repo.get_or_404(job_id, tenant_id)  # 404s if the job isn't this tenant's
        applications = self.application_repo.list_active_for_job(tenant_id, job_id)

        results = []
        for application in applications:
            if force or application.match_score is None:
                self.compute(tenant_id, application.id)
            results.append(application)

        return sorted(
            results,
            key=lambda a: (-(a.match_score or 0), a.applied_at),
        )
