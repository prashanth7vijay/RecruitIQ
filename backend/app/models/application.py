from sqlalchemy import Column, String, Numeric, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.extensions import db
from app.models.base import Base, UUIDPrimaryKeyMixin


class Application(Base, UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("job_id", "candidate_id", name="uq_application_job_candidate"),)

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    candidate_profile_id = Column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id"), nullable=False)
    current_stage_id = Column(UUID(as_uuid=True), ForeignKey("pipeline_stages.id"), nullable=False)
    status = Column(String(20), nullable=False, default="active")  # active/rejected/withdrawn/hired
    match_score = Column(Numeric(5, 2), nullable=True)
    applied_at = Column(DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(String(255), nullable=True)

    candidate = relationship("Candidate")
    current_stage = relationship("PipelineStage")


class ApplicationStageHistory(Base, UUIDPrimaryKeyMixin, db.Model):

    __tablename__ = "application_stage_history"

    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    from_stage_id = Column(UUID(as_uuid=True), ForeignKey("pipeline_stages.id"), nullable=True)
    to_stage_id = Column(UUID(as_uuid=True), ForeignKey("pipeline_stages.id"), nullable=False)
    moved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # null = automated/candidate-initiated
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=db.func.now(), nullable=False)
