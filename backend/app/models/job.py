from sqlalchemy import Column, String, Integer, Numeric, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.extensions import db
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Job(Base, UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "jobs"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="draft")
    employment_type = Column(String(20), nullable=True)  # remote/hybrid/onsite
    salary_min = Column(Numeric(12, 2), nullable=True)
    salary_max = Column(Numeric(12, 2), nullable=True)
    experience_min = Column(Numeric(4, 1), nullable=True)
    experience_max = Column(Numeric(4, 1), nullable=True)
    required_skills = Column(JSONB, nullable=False, default=list)
    preferred_skills = Column(JSONB, nullable=False, default=list)
    pipeline_template_id = Column(UUID(as_uuid=True), ForeignKey("pipeline_templates.id"), nullable=True)
    hiring_target_count = Column(Integer, nullable=False, default=1)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)


class JobApprovalStep(Base, UUIDPrimaryKeyMixin, db.Model):

    __tablename__ = "job_approval_steps"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    approver_role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending/approved/rejected
    acted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    comment = Column(Text, nullable=True)
    step_order = Column(Integer, nullable=False)
    acted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=db.func.now(), nullable=False)

    approver_role = relationship("Role")
