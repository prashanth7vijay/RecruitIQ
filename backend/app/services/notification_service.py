from datetime import datetime, timezone

from app.models.notification import Notification


class NotificationService:
    def __init__(self, notification_repo):
        self.notification_repo = notification_repo

    def notify(self, tenant_id, notification_type, payload, user_id=None, candidate_id=None, channels=None):
        channels = channels or ["in_app"]
        created = []
        for channel in channels:
            notification = Notification(
                company_id=tenant_id,
                user_id=user_id,
                candidate_id=candidate_id,
                type=notification_type,
                channel=channel,
                payload=payload,
            )
            self.notification_repo.add(notification)
            self.notification_repo.commit()
            created.append(notification)

            if channel == "email":
                from app.workers.email_tasks import send_email_task
                send_email_task.delay(notification.id)
            elif channel == "in_app":
                from app.workers.notification_tasks import dispatch_in_app_notification_task
                dispatch_in_app_notification_task.delay(notification.id)

        return created

    def list_for_user(self, tenant_id, user_id, unread_only=False):
        return self.notification_repo.list_for_user(tenant_id, user_id, unread_only).all()

    def mark_read(self, tenant_id, notification_id):
        notification = self.notification_repo.get_or_404(notification_id, tenant_id)
        notification.read_at = datetime.now(timezone.utc)
        self.notification_repo.commit()
        return notification

    def list_for_candidate(self, candidate_id, unread_only=False):
        return self.notification_repo.list_for_candidate(candidate_id, unread_only).all()

    def mark_read_for_candidate(self, candidate_id, notification_id):
        notification = self.notification_repo.get_for_candidate_or_404(notification_id, candidate_id)
        notification.read_at = datetime.now(timezone.utc)
        self.notification_repo.commit()
        return notification