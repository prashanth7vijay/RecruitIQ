from app.models.referral import Referral
from app.repositories.base_repository import TenantScopedRepository


class ReferralRepository(TenantScopedRepository):
    model = Referral

    def get_by_application(self, tenant_id, application_id):
        return self._base_query(tenant_id).filter(Referral.application_id == application_id).first()

    def list_for_referrer(self, tenant_id, referrer_user_id):
        return (
            self._base_query(tenant_id)
            .filter(Referral.referred_by_user_id == referrer_user_id)
            .order_by(Referral.created_at.desc())
            .all()
        )

    def get_pending_invite(self, tenant_id, job_id, candidate_id):
        return (
            self._base_query(tenant_id)
            .filter(
                Referral.job_id == job_id,
                Referral.candidate_id == candidate_id,
                Referral.application_id.is_(None),
            )
            .first()
        )

    def get_by_job_and_candidate(self, tenant_id, job_id, candidate_id):
        return (
            self._base_query(tenant_id)
            .filter(Referral.job_id == job_id, Referral.candidate_id == candidate_id)
            .first()
        )