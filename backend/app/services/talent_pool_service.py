from app.exceptions.base import BusinessRuleViolationError
from app.models.talent_pool import TalentPool


class TalentPoolService:
    def __init__(self, pool_repo, membership_repo, profile_repo):
        self.pool_repo = pool_repo
        self.membership_repo = membership_repo
        self.profile_repo = profile_repo

    def create(self, tenant_id, name, description=None):
        pool = TalentPool(company_id=tenant_id, name=name, description=description)
        self.pool_repo.add(pool)
        self.pool_repo.commit()
        return pool

    def list(self, tenant_id):
        return self.pool_repo.list(tenant_id).all()

    def get(self, tenant_id, pool_id):
        return self.pool_repo.get_or_404(pool_id, tenant_id)

    def add_candidate(self, tenant_id, pool_id, candidate_profile_id):
        self.pool_repo.get_or_404(pool_id, tenant_id)  # confirms pool belongs to this tenant
        self.profile_repo.get_or_404(candidate_profile_id, tenant_id)  # confirms profile does too

        if self.membership_repo.exists(pool_id, candidate_profile_id):
            raise BusinessRuleViolationError("Candidate is already in this talent pool")

        self.membership_repo.add(pool_id, candidate_profile_id)
        self.membership_repo.commit()

    def remove_candidate(self, tenant_id, pool_id, candidate_profile_id):
        self.pool_repo.get_or_404(pool_id, tenant_id)
        self.membership_repo.remove(pool_id, candidate_profile_id)
        self.membership_repo.commit()

    def list_members(self, tenant_id, pool_id):
        self.pool_repo.get_or_404(pool_id, tenant_id)
        memberships = self.membership_repo.list_for_pool(pool_id)
        return [
            self.profile_repo.get(m.candidate_profile_id, tenant_id)
            for m in memberships
        ]
