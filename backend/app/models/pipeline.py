from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.extensions import db
from app.models.base import Base, UUIDPrimaryKeyMixin


class PipelineTemplate(Base, UUIDPrimaryKeyMixin, db.Model):
    __tablename__ = "pipeline_templates"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(150), nullable=False)
    is_default = Column(Boolean, nullable=False, default=False)

    stages = relationship("PipelineStage", order_by="PipelineStage.stage_order", cascade="all, delete-orphan")


class PipelineStage(Base, UUIDPrimaryKeyMixin, db.Model):

    __tablename__ = "pipeline_stages"
    __table_args__ = (
        UniqueConstraint("pipeline_template_id", "stage_order", name="uq_pipeline_stage_order"),
    )

    pipeline_template_id = Column(
        UUID(as_uuid=True), ForeignKey("pipeline_templates.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(100), nullable=False)
    stage_order = Column(Integer, nullable=False)
    stage_type = Column(String(30), nullable=False)  # screening/interview/assessment/offer/terminal
    sla_hours = Column(Integer, nullable=True)
