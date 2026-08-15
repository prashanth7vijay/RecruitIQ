from app.models.candidate import Candidate, CandidateProfile
from app.models.job import Job

class SearchService:
    def __init__(self, session):
        self.session = session

    def search(self, tenant_id, query, limit=10):
        return {
            "candidates": self._search_candidates(tenant_id, query, limit),
            "jobs": self._search_jobs(tenant_id, query, limit),
        }

    def _search_candidates(self, tenant_id, query, limit):
        pattern = f"%{query}%"
        return (
            self.session.query(CandidateProfile)
            .join(Candidate, Candidate.id == CandidateProfile.candidate_id)
            .filter(CandidateProfile.company_id == tenant_id)
            .filter(
                (Candidate.first_name.ilike(pattern))
                | (Candidate.last_name.ilike(pattern))
                | (Candidate.email.ilike(pattern))
            )
            .limit(limit)
            .all()
        )

    def _search_jobs(self, tenant_id, query, limit):
        pattern = f"%{query}%"
        return (
            self.session.query(Job)
            .filter(Job.company_id == tenant_id)
            .filter(Job.title.ilike(pattern))
            .limit(limit)
            .all()
        )
