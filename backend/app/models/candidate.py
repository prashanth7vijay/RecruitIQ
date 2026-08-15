from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, CITEXT, JSONB
from sqlalchemy.orm import relationship

from app.extensions import db
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Candidate(Base, UUIDPrimaryKeyMixin, db.Model):

    __tablename__ = "candidates"

    email = Column(CITEXT, nullable=False, unique=True)
    password_hash = Column(String(255), nullable=True)  # nullable: can apply as guest
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=True)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=db.func.now(), nullable=False)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class CandidateProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "candidate_profiles"
    __table_args__ = (
        UniqueConstraint("company_id", "candidate_id", name="uq_candidate_profile_company_candidate"),
    )

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True)
    skills = Column(JSONB, nullable=False, default=list)
    experience_years = Column(Numeric(4, 1), nullable=True)
    expected_salary = Column(Numeric(12, 2), nullable=True)
    notice_period_days = Column(Integer, nullable=True)
    current_location = Column(String(255), nullable=True)
    preferred_location = Column(String(255), nullable=True)
    source = Column(String(50), nullable=True)  # career_portal/referral/sourced
    completeness_score = Column(Numeric(5, 2), nullable=True)

    candidate = relationship("Candidate")
