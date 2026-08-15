from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.extensions import db
from app.models.base import Base, UUIDPrimaryKeyMixin


class AuditLog(Base, UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "audit_logs"

    company_id = Column(UUID(as_uuid=True), nullable=False)  # deliberately no FK — see module docstring
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # null = system/automated action
    actor_type = Column(String(20), nullable=False, default="user")  # user/system
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(50), nullable=False)
    old_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    ip_address = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=db.func.now(), nullable=False)
