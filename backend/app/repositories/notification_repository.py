from app.models.notification import Notification
from app.repositories.base_repository import TenantScopedRepository


class NotificationRepository(TenantScopedRepository):
    model = Notification

    def list_for_user(self, tenant_id, user_id, unread_only=False):
        query = self._base_query(tenant_id).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.read_at.is_(None))
        return query.order_by(Notification.created_at.desc())
