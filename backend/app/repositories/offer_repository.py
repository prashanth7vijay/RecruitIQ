from app.models.offer import Offer, OfferApprovalStep
from app.repositories.base_repository import TenantScopedRepository


class OfferRepository(TenantScopedRepository):
    model = Offer

    def list_for_application(self, tenant_id, application_id):
        return self._base_query(tenant_id).filter(Offer.application_id == application_id).all()


class OfferApprovalStepRepository(TenantScopedRepository):
    model = OfferApprovalStep

    def list_for_offer(self, tenant_id, offer_id):
        return self._base_query(tenant_id).filter(OfferApprovalStep.offer_id == offer_id).order_by(
            OfferApprovalStep.step_order
        )
