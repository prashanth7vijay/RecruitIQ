from app.models.ai_request import AIRequest


class JDImprovementService:
    def __init__(self, ai_client, ai_request_repo, job_repo):
        self.ai_client = ai_client
        self.ai_request_repo = ai_request_repo
        self.job_repo = job_repo

    def get_suggestion(self, tenant_id, job_id):
        job = self.job_repo.get_or_404(job_id, tenant_id)
        prompt = (
            "Improve the following job description for clarity, inclusivity, "
            "and candidate appeal. Keep it factually equivalent — do not invent "
            "requirements or benefits not implied by the original.\n\n"
            f"Title: {job.title}\n\nDescription:\n{job.description or '(no description yet)'}"
        )
        result = self.ai_client.complete(prompt)

        ai_request = AIRequest(
            company_id=tenant_id,
            feature="jd_improvement",
            entity_type="job",
            entity_id=job_id,
            input_tokens=result.get("input_tokens"),
            output_tokens=result.get("output_tokens"),
            status="suggested",
        )
        self.ai_request_repo.add(ai_request)
        self.ai_request_repo.commit()

        return {"suggestion": result["text"], "ai_request_id": ai_request.id}

    def apply_suggestion(self, tenant_id, job_id, ai_request_id, new_description):
        job = self.job_repo.get_or_404(job_id, tenant_id)
        ai_request = self.ai_request_repo.get_or_404(ai_request_id, tenant_id)

        job.description = new_description
        ai_request.status = "accepted"
        self.ai_request_repo.commit()
        return job
