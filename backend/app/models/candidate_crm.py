from sqlalchemy import Column, String, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db
from app.models.base import Base, UUIDPrimaryKeyMixin


class CandidateNote(Base, UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "candidate_notes"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    candidate_profile_id = Column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=db.func.now(), nullable=False)


class CandidateTag(Base, UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "candidate_tags"
    __table_args__ = (UniqueConstraint("candidate_profile_id", "label", name="uq_candidate_tag_label"),)

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    candidate_profile_id = Column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    label = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=db.func.now(), nullable=False)
