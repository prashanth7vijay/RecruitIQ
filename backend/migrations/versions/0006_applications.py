from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_applications"
down_revision = "0005_candidates"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("candidate_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidate_profiles.id"), nullable=False),
        sa.Column("current_stage_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pipeline_stages.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("match_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.String(255), nullable=True),
        sa.UniqueConstraint("job_id", "candidate_id", name="uq_application_job_candidate"),
    )
    op.create_index("idx_applications_company_stage", "applications", ["company_id", "current_stage_id"])
    op.create_index("idx_applications_job", "applications", ["job_id"])
    op.create_index("idx_applications_candidate", "applications", ["candidate_id"])

    op.create_table(
        "application_stage_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_stage_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pipeline_stages.id"), nullable=True),
        sa.Column("to_stage_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pipeline_stages.id"), nullable=False),
        sa.Column("moved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_stage_history_application", "application_stage_history", ["application_id", "created_at"])

    op.execute(
        "INSERT INTO permissions (id, code) VALUES (gen_random_uuid(), 'application.manage') "
        "ON CONFLICT (code) DO NOTHING"
    )


def downgrade():
    op.execute("DELETE FROM permissions WHERE code = 'application.manage'")
    op.drop_table("application_stage_history")
    op.drop_table("applications")
