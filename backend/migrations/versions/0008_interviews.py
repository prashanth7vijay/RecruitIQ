from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0008_interviews"
down_revision = "0007_notifications"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "interviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pipeline_stage_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pipeline_stages.id"), nullable=False),
        sa.Column("round_name", sa.String(100), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Integer, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
        sa.Column("meeting_link", sa.String(500), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_interviews_application", "interviews", ["application_id"])
    op.create_index("idx_interviews_company_scheduled", "interviews", ["company_id", "scheduled_at"])

    op.create_table(
        "interview_panelists",
        sa.Column("interview_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_in_panel", sa.String(30), nullable=False, server_default="interviewer"),
        sa.PrimaryKeyConstraint("interview_id", "user_id"),
    )

    op.create_table(
        "interview_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("interview_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("rubric_scores", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("overall_rating", sa.Numeric(3, 1), nullable=True),
        sa.Column("recommendation", sa.String(20), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("interview_id", "interviewer_id", name="uq_feedback_interview_interviewer"),
    )
    op.create_index("idx_feedback_interviewer", "interview_feedback", ["interviewer_id", "submitted_at"])


def downgrade():
    op.drop_table("interview_feedback")
    op.drop_table("interview_panelists")
    op.drop_table("interviews")
