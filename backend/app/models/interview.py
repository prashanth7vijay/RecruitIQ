from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.extensions import db
from app.models.base import Base, UUIDPrimaryKeyMixin


class Interview(Base, UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "interviews"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    pipeline_stage_id = Column(UUID(as_uuid=True), ForeignKey("pipeline_stages.id"), nullable=False)
    round_name = Column(String(100), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="scheduled")  # scheduled/completed/cancelled/rescheduled
    meeting_link = Column(String(500), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=db.func.now(), nullable=False)

    panelists = relationship("InterviewPanelist", cascade="all, delete-orphan")
    feedback_entries = relationship("InterviewFeedback", cascade="all, delete-orphan")


class InterviewPanelist(Base, db.Model):
    __tablename__ = "interview_panelists"
    __table_args__ = (PrimaryKeyConstraint("interview_id", "user_id"),)

    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_in_panel = Column(String(30), nullable=False, default="interviewer")
