from app.extensions import db
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=5, default_retry_delay=30)
def send_email_task(self, notification_id):
    from app.models.notification import Notification
    from app.services.email_sender import build_email_sender
    from flask import current_app

    notification = db.session.query(Notification).filter_by(id=notification_id).first()
    if notification is None or notification.sent_at is not None:
        return  # already sent or deleted — idempotency guard

    sender = build_email_sender(current_app.config)
    sender.send(notification)

    from datetime import datetime, timezone
    notification.sent_at = datetime.now(timezone.utc)
    db.session.commit()
