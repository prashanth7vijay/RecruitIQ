from sqlalchemy import Column, String, Boolean, Date, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.extensions import db
from app.models.base import Base, UUIDPrimaryKeyMixin


class OnboardingChecklist(Base, UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "onboarding_checklists"

    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, unique=True)
    buddy_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    manager_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    joining_date = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending/in_progress/complete
    created_at = Column(DateTime(timezone=True), server_default=db.func.now(), nullable=False)

    tasks = relationship("OnboardingTask", cascade="all, delete-orphan")


class OnboardingTask(Base, UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "onboarding_tasks"

    onboarding_checklist_id = Column(UUID(as_uuid=True), ForeignKey("onboarding_checklists.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    is_completed = Column(Boolean, nullable=False, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
