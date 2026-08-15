from sqlalchemy import Column, String, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.extensions import db
from app.models.base import Base, UUIDPrimaryKeyMixin


class Notification(Base, UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint(
            "user_id IS NOT NULL OR candidate_id IS NOT NULL", name="ck_notification_has_recipient"
        ),
    )

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=True)
    type = Column(String(50), nullable=False)  # 'application_stage_changed', 'resume_uploaded', ...
    channel = Column(String(20), nullable=False)  # email/in_app
    payload = Column(JSONB, nullable=False, default=dict)
    read_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=db.func.now(), nullable=False)
