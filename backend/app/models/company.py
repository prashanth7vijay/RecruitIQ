from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB

from app.extensions import db
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Company(Base, UUIDPrimaryKeyMixin, TimestampMixin, db.Model):

    __tablename__ = "companies"

    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    plan = Column(String(50), nullable=False, default="trial")
    settings = Column(JSONB, nullable=False, default=dict)
    status = Column(String(20), nullable=False, default="active")
