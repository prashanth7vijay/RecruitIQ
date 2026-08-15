from app.models.ai_request import AIRequest
from app.repositories.base_repository import TenantScopedRepository


class AIRequestRepository(TenantScopedRepository):
    model = AIRequest
