from sqlalchemy import Column, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Department(Base, UUIDPrimaryKeyMixin, db.Model):

    __tablename__ = "departments"
    __table_args__ = (UniqueConstraint("company_id", "name", name="uq_departments_company_name"),)

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(150), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)


class Team(Base, UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "teams"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(150), nullable=False)
    created_at = Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)


class Location(Base, UUIDPrimaryKeyMixin, db.Model):

    __tablename__ = "locations"
    __table_args__ = (UniqueConstraint("company_id", "name", name="uq_locations_company_name"),)

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(150), nullable=False)
    city = Column(String(150), nullable=True)
    country = Column(String(150), nullable=True)
    is_remote = Column(Boolean, nullable=False, default=False)
    created_at = Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
