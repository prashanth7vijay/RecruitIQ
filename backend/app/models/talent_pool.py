from sqlalchemy import Column, String, ForeignKey, DateTime, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db
from app.models.base import Base, UUIDPrimaryKeyMixin


class TalentPool(Base, UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "talent_pools"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=db.func.now(), nullable=False)


class TalentPoolMembership(Base, db.Model):
    __tablename__ = "talent_pool_memberships"
    __table_args__ = (PrimaryKeyConstraint("talent_pool_id", "candidate_profile_id"),)

    talent_pool_id = Column(UUID(as_uuid=True), ForeignKey("talent_pools.id", ondelete="CASCADE"), nullable=False)
    candidate_profile_id = Column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=db.func.now(), nullable=False)
