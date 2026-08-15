from app.models.approval_chain import ApprovalChain
from app.repositories.base_repository import TenantScopedRepository


class ApprovalChainRepository(TenantScopedRepository):
    model = ApprovalChain

    def get_for_entity_type(self, tenant_id, entity_type):
        return self._base_query(tenant_id).filter(ApprovalChain.entity_type == entity_type).first()
