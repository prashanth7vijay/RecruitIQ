from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_jobs"
down_revision = "0002_teams"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pipeline_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "pipeline_stages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pipeline_template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pipeline_templates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("stage_order", sa.Integer, nullable=False),
        sa.Column("stage_type", sa.String(30), nullable=False),
        sa.Column("sla_hours", sa.Integer, nullable=True),
        sa.UniqueConstraint("pipeline_template_id", "stage_order", name="uq_pipeline_stage_order"),
    )

    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("employment_type", sa.String(20), nullable=True),
        sa.Column("salary_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("experience_min", sa.Numeric(4, 1), nullable=True),
        sa.Column("experience_max", sa.Numeric(4, 1), nullable=True),
        sa.Column("required_skills", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("preferred_skills", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("pipeline_template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pipeline_templates.id"), nullable=True),
        sa.Column("hiring_target_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_jobs_company_status", "jobs", ["company_id", "status"])
    op.create_index(
        "idx_jobs_published", "jobs", ["company_id", "published_at"],
        postgresql_where=sa.text("status = 'published'"),
    )

    op.create_table(
        "job_approval_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("approver_role", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("acted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("step_order", sa.Integer, nullable=False),
        sa.Column("acted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_job_approval_job", "job_approval_steps", ["job_id", "step_order"])

    # Note: no permission INSERT here (unlike migration 0002's
    # org.manage_structure) — job.create/approve/publish/close were
    # already part of SYSTEM_PERMISSIONS since Sprint 1 and are
    # populated by `flask seed-roles`, not by migrations. Migrations
    # only insert a permission row directly when introducing a
    # genuinely NEW permission code not yet in that constant list.


def downgrade():
    op.drop_table("job_approval_steps")
    op.drop_index("idx_jobs_published", table_name="jobs")
    op.drop_index("idx_jobs_company_status", table_name="jobs")
    op.drop_table("jobs")
    op.drop_table("pipeline_stages")
    op.drop_table("pipeline_templates")
