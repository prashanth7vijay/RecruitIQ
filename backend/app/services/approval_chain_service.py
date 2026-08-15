from app.exceptions.base import ValidationError, PermissionDeniedError
from app.models.approval_chain import ApprovalChain, ApprovalChainStep, ENTITY_TYPES


class ApprovalChainService:
    def __init__(self, chain_repo, role_repo):
        self.chain_repo = chain_repo
        self.role_repo = role_repo

    def get_chain(self, tenant_id, entity_type):
        self._validate_entity_type(entity_type)
        return self.chain_repo.get_for_entity_type(tenant_id, entity_type)

    def set_chain(self, tenant_id, entity_type, role_ids):
        self._validate_entity_type(entity_type)
        if not role_ids:
            raise ValidationError("An approval chain needs at least one approver role")

        # Every role must be visible to this tenant (system role, or one
        # of its own custom roles) — same check RoleService/org-placement
        # already use, so a chain can never point at another tenant's role.
        roles = [self.role_repo.get_visible_or_404(role_id, tenant_id) for role_id in role_ids]

        chain = self.chain_repo.get_for_entity_type(tenant_id, entity_type)
        if chain is None:
            chain = ApprovalChain(company_id=tenant_id, entity_type=entity_type)
            self.chain_repo.add(chain)
            self.chain_repo.commit()  # flush for chain.id before adding steps
        else:
            chain.steps = []  # cascade="all, delete-orphan" removes the old rows on commit

        for step_order, role in enumerate(roles):
            self.chain_repo.session.add(
                ApprovalChainStep(approval_chain_id=chain.id, role_id=role.id, step_order=step_order)
            )
        self.chain_repo.commit()
        return chain

    def assert_can_act_on_step(self, step, acting_user):
        
        if step.approver_role_id is None:
            # A step created before this module existed, or a chain that
            # got reconfigured after the step was already created — fail
            # closed rather than silently letting anyone approve it.
            raise PermissionDeniedError("This approval step has no configured approver role")
        if str(acting_user.role_id) != str(step.approver_role_id):
            raise PermissionDeniedError(
                "You don't hold the role required to act on this approval step"
            )

    def _validate_entity_type(self, entity_type):
        if entity_type not in ENTITY_TYPES:
            raise ValidationError(f"entity_type must be one of: {', '.join(ENTITY_TYPES)}")
