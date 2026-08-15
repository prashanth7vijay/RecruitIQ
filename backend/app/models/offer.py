from sqlalchemy import Column, String, Numeric, Text, Date, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.extensions import db
from app.models.base import Base, UUIDPrimaryKeyMixin


class Offer(Base, UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "offers"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    salary_offered = Column(Numeric(12, 2), nullable=False)
    joining_date = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, default="draft")
    # draft / pending_approval / sent / accepted / rejected / expired / withdrawn
    offer_letter_storage_key = Column(String(500), nullable=True)
    expiry_date = Column(Date, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=db.func.now(), nullable=False)


class OfferApprovalStep(Base, UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "offer_approval_steps"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    offer_id = Column(UUID(as_uuid=True), ForeignKey("offers.id", ondelete="CASCADE"), nullable=False)
    approver_role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    acted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    comment = Column(Text, nullable=True)
    step_order = Column(Integer, nullable=False)
    acted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=db.func.now(), nullable=False)

    approver_role = relationship("Role")
