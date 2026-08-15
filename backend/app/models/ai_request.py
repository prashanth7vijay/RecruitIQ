from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db
from app.models.base import Base, UUIDPrimaryKeyMixin


class AIRequest(Base, UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "ai_requests"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    feature = Column(String(50), nullable=False)  # 'match_score', 'jd_improvement'
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False)  # suggested/accepted/rejected/failed
    created_at = Column(DateTime(timezone=True), server_default=db.func.now(), nullable=False)
