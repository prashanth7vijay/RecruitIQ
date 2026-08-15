from app.models.candidate import Candidate, CandidateProfile
from app.models.resume import Resume
from app.repositories.base_repository import TenantScopedRepository, GlobalRepository


class CandidateRepository(GlobalRepository):

    model = Candidate

    def get_by_email(self, email):
        return self.session.query(Candidate).filter(Candidate.email == email).first()


class CandidateProfileRepository(TenantScopedRepository):
    model = CandidateProfile

    def get_by_candidate(self, tenant_id, candidate_id):
        return self._base_query(tenant_id).filter(
            CandidateProfile.candidate_id == candidate_id
        ).first()


class ResumeRepository:

    model = Resume

    def __init__(self, session):
        self.session = session

    def get(self, resume_id):
        return self.session.query(Resume).filter(Resume.id == resume_id).first()

    def list_for_candidate(self, candidate_id):
        return (
            self.session.query(Resume)
            .filter(Resume.candidate_id == candidate_id)
            .order_by(Resume.version.desc())
        )

    def add(self, obj):
        self.session.add(obj)
        return obj

    def commit(self):
        self.session.commit()
