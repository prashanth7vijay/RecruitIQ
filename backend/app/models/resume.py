from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.extensions import db
from app.models.base import Base, UUIDPrimaryKeyMixin


class Resume(Base, UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "resumes"

    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    storage_key = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    parse_status = Column(String(20), nullable=False, default="pending")  # pending/processing/done/failed
    parsed_data = Column(JSONB, nullable=True)
    completeness_score = Column(Numeric(5, 2), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=db.func.now(), nullable=False)
