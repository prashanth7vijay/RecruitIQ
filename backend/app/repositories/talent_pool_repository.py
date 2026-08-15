from app.models.talent_pool import TalentPool, TalentPoolMembership
from app.models.candidate_crm import CandidateNote, CandidateTag
from app.repositories.base_repository import TenantScopedRepository


class TalentPoolRepository(TenantScopedRepository):
    model = TalentPool


class TalentPoolMembershipRepository:

    def __init__(self, session):
        self.session = session

    def add(self, talent_pool_id, candidate_profile_id):
        membership = TalentPoolMembership(talent_pool_id=talent_pool_id, candidate_profile_id=candidate_profile_id)
        self.session.add(membership)
        return membership

    def exists(self, talent_pool_id, candidate_profile_id):
        return (
            self.session.query(TalentPoolMembership)
            .filter_by(talent_pool_id=talent_pool_id, candidate_profile_id=candidate_profile_id)
            .first()
            is not None
        )

    def remove(self, talent_pool_id, candidate_profile_id):
        self.session.query(TalentPoolMembership).filter_by(
            talent_pool_id=talent_pool_id, candidate_profile_id=candidate_profile_id
        ).delete()

    def list_for_pool(self, talent_pool_id):
        return (
            self.session.query(TalentPoolMembership)
            .filter_by(talent_pool_id=talent_pool_id)
            .all()
        )

    def commit(self):
        self.session.commit()


class CandidateNoteRepository:
    def __init__(self, session):
        self.session = session

    def add(self, obj):
        self.session.add(obj)
        return obj

    def commit(self):
        self.session.commit()

    def list_for_profile(self, tenant_id, candidate_profile_id):
        return (
            self.session.query(CandidateNote)
            .filter_by(company_id=tenant_id, candidate_profile_id=candidate_profile_id)
            .order_by(CandidateNote.created_at.desc())
            .all()
        )


class CandidateTagRepository:
    def __init__(self, session):
        self.session = session

    def add(self, obj):
        self.session.add(obj)
        return obj

    def commit(self):
        self.session.commit()

    def list_for_profile(self, tenant_id, candidate_profile_id):
        return (
            self.session.query(CandidateTag)
            .filter_by(company_id=tenant_id, candidate_profile_id=candidate_profile_id)
            .all()
        )

    def get_by_label(self, tenant_id, candidate_profile_id, label):
        return (
            self.session.query(CandidateTag)
            .filter_by(company_id=tenant_id, candidate_profile_id=candidate_profile_id, label=label)
            .first()
        )
