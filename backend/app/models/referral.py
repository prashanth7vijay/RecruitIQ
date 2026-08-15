from sqlalchemy import Column, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db
from app.models.base import Base, UUIDPrimaryKeyMixin


class Referral(Base, UUIDPrimaryKeyMixin, db.Model):

    __tablename__ = "referrals"
    __table_args__ = (UniqueConstraint("application_id", name="uq_referrals_application_id"),)

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    referred_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=db.func.now(), nullable=False)
