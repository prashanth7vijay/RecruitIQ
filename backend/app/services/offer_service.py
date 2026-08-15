from datetime import datetime, timezone

from app.exceptions.base import BusinessRuleViolationError
from app.models.offer import Offer, OfferApprovalStep
from app.validators.state_transitions import assert_valid_offer_transition


class OfferService:
    def __init__(self, offer_repo, approval_repo, user_repo, approval_chain_service, event_bus=None, audit_service=None):
        self.offer_repo = offer_repo
        self.approval_repo = approval_repo
        self.user_repo = user_repo
        self.approval_chain_service = approval_chain_service
        self.event_bus = event_bus
        self.audit_service = audit_service

    def create_draft(self, tenant_id, application_id, created_by, salary_offered, joining_date=None, expiry_date=None):
        offer = Offer(
            company_id=tenant_id,
            application_id=application_id,
            created_by=created_by,
            salary_offered=salary_offered,
            joining_date=joining_date,
            expiry_date=expiry_date,
            status="draft",
        )
        self.offer_repo.add(offer)
        self.offer_repo.commit()
        return offer

    def get(self, tenant_id, offer_id):
        return self.offer_repo.get_or_404(offer_id, tenant_id)

    def list_for_application(self, tenant_id, application_id):
        return self.offer_repo.list_for_application(tenant_id, application_id)

    def list_approval_steps(self, tenant_id, offer_id):
        self.offer_repo.get_or_404(offer_id, tenant_id)
        return self.approval_repo.list_for_offer(tenant_id, offer_id).all()

    def submit_for_approval(self, tenant_id, offer_id):
        offer = self.offer_repo.get_or_404(offer_id, tenant_id)
        assert_valid_offer_transition(offer.status, "pending_approval")

        chain = self.approval_chain_service.get_chain(tenant_id, "offer")
        if chain is None or not chain.steps:
            raise BusinessRuleViolationError(
                "No approval chain is configured for offers yet. "
                "An admin needs to set one up before offers can be submitted for approval."
            )

        offer.status = "pending_approval"
        for chain_step in chain.steps:
            self.approval_repo.add(
                OfferApprovalStep(
                    company_id=tenant_id,
                    offer_id=offer.id,
                    approver_role_id=chain_step.role_id,
                    step_order=chain_step.step_order,
                )
            )
        self.approval_repo.commit()
        return offer

    def approve_step(self, tenant_id, offer_id, step_id, acted_by, comment=None):
        offer = self.offer_repo.get_or_404(offer_id, tenant_id)
        step = self.approval_repo.get_or_404(step_id, tenant_id)
        if step.offer_id != offer.id:
            raise BusinessRuleViolationError("Approval step does not belong to this offer")

        acting_user = self.user_repo.get_or_404(acted_by, tenant_id)
        self.approval_chain_service.assert_can_act_on_step(step, acting_user)

        step.status = "approved"
        step.acted_by = acted_by
        step.comment = comment
        step.acted_at = datetime.now(timezone.utc)
        self.approval_repo.commit()

        if self._all_steps_approved(tenant_id, offer.id):
            self._send(offer)
        return offer

    def reject_step(self, tenant_id, offer_id, step_id, acted_by, comment=None):
        offer = self.offer_repo.get_or_404(offer_id, tenant_id)
        step = self.approval_repo.get_or_404(step_id, tenant_id)
        if step.offer_id != offer.id:
            raise BusinessRuleViolationError("Approval step does not belong to this offer")

        acting_user = self.user_repo.get_or_404(acted_by, tenant_id)
        self.approval_chain_service.assert_can_act_on_step(step, acting_user)

        step.status = "rejected"
        step.acted_by = acted_by
        step.comment = comment
        step.acted_at = datetime.now(timezone.utc)
        self.approval_repo.commit()

        assert_valid_offer_transition(offer.status, "draft")
        offer.status = "draft"
        self.offer_repo.commit()
        return offer

    def accept(self, tenant_id, offer_id, acted_by=None):
        offer = self.offer_repo.get_or_404(offer_id, tenant_id)
        assert_valid_offer_transition(offer.status, "accepted")
        offer.status = "accepted"
        offer.responded_at = datetime.now(timezone.utc)
        self.offer_repo.commit()

        if self.event_bus is not None:
            self.event_bus.publish(
                "offer.accepted", {"offer_id": str(offer.id), "application_id": str(offer.application_id)}
            )
        self._audit(tenant_id, offer.id, "accepted", acted_by)
        return offer

    def decline(self, tenant_id, offer_id, acted_by=None):
        offer = self.offer_repo.get_or_404(offer_id, tenant_id)
        assert_valid_offer_transition(offer.status, "rejected")
        offer.status = "rejected"
        offer.responded_at = datetime.now(timezone.utc)
        self.offer_repo.commit()
        self._audit(tenant_id, offer.id, "declined", acted_by)
        return offer

    def withdraw(self, tenant_id, offer_id):
        offer = self.offer_repo.get_or_404(offer_id, tenant_id)
        assert_valid_offer_transition(offer.status, "withdrawn")
        offer.status = "withdrawn"
        self.offer_repo.commit()
        return offer

    def _audit(self, tenant_id, offer_id, action, acted_by):
        if self.audit_service is not None:
            self.audit_service.log(
                company_id=tenant_id, entity_type="Offer", entity_id=offer_id,
                action=action, actor_id=acted_by,
            )

    # --- internal -----------------------------------------------------

    def _all_steps_approved(self, tenant_id, offer_id):
        steps = self.approval_repo.list_for_offer(tenant_id, offer_id).all()
        return bool(steps) and all(s.status == "approved" for s in steps)

    def _send(self, offer: Offer):
        assert_valid_offer_transition(offer.status, "sent")
        offer.status = "sent"
        offer.sent_at = datetime.now(timezone.utc)
        self.offer_repo.commit()
