from sqlalchemy import Column, String, Numeric, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.extensions import db
from app.models.base import Base, UUIDPrimaryKeyMixin


class InterviewFeedback(Base, UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "interview_feedback"
    __table_args__ = (UniqueConstraint("interview_id", "interviewer_id", name="uq_feedback_interview_interviewer"),)

    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    interviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rubric_scores = Column(JSONB, nullable=False, default=list)  # [{criterion, score, comment}]
    overall_rating = Column(Numeric(3, 1), nullable=True)
    recommendation = Column(String(20), nullable=True)  # strong_yes/yes/no/strong_no
    notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=db.func.now(), nullable=False)
