from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.extensions import db
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

ENTITY_TYPES = ("job", "offer")


class ApprovalChain(Base, UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "approval_chains"
    __table_args__ = (
        UniqueConstraint("company_id", "entity_type", name="uq_approval_chains_company_entity"),
    )

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    entity_type = Column(String(20), nullable=False)

    steps = relationship(
        "ApprovalChainStep",
        order_by="ApprovalChainStep.step_order",
        cascade="all, delete-orphan",
        backref="chain",
    )


class ApprovalChainStep(Base, UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "approval_chain_steps"

    approval_chain_id = Column(
        UUID(as_uuid=True), ForeignKey("approval_chains.id", ondelete="CASCADE"), nullable=False
    )
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    step_order = Column(Integer, nullable=False)

    role = relationship("Role")
