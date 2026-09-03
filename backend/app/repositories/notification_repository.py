from app.models.notification import Notification
from app.repositories.base_repository import TenantScopedRepository


class NotificationRepository(TenantScopedRepository):
    model = Notification

    def list_for_user(self, tenant_id, user_id, unread_only=False):
        query = self._base_query(tenant_id).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.read_at.is_(None))
        return query.order_by(Notification.created_at.desc())

    def list_for_candidate(self, candidate_id, unread_only=False):
        query = self.session.query(Notification).filter(Notification.candidate_id == candidate_id)
        if unread_only:
            query = query.filter(Notification.read_at.is_(None))
        return query.order_by(Notification.created_at.desc())

    def get_for_candidate_or_404(self, notification_id, candidate_id):
        from app.exceptions.base import NotFoundError

        notification = (
            self.session.query(Notification)
            .filter(Notification.id == notification_id, Notification.candidate_id == candidate_id)
            .first()
        )
        if notification is None:
            raise NotFoundError("Notification not found")
        return notification