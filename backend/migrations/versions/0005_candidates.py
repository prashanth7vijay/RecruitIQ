from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_candidates"
down_revision = "0004_company_settings_permission"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", postgresql.CITEXT, nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("parse_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("parsed_data", postgresql.JSONB, nullable=True),
        sa.Column("completeness_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_resumes_candidate", "resumes", ["candidate_id", "version"])

    op.create_table(
        "candidate_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resumes.id"), nullable=True),
        sa.Column("skills", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("experience_years", sa.Numeric(4, 1), nullable=True),
        sa.Column("expected_salary", sa.Numeric(12, 2), nullable=True),
        sa.Column("notice_period_days", sa.Integer, nullable=True),
        sa.Column("current_location", sa.String(255), nullable=True),
        sa.Column("preferred_location", sa.String(255), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("completeness_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("company_id", "candidate_id", name="uq_candidate_profile_company_candidate"),
    )
    op.create_index("idx_candidate_profiles_company", "candidate_profiles", ["company_id"])
    op.create_index(
        "idx_candidate_profiles_skills", "candidate_profiles", ["skills"], postgresql_using="gin"
    )

    op.execute(
        "INSERT INTO permissions (id, code) VALUES (gen_random_uuid(), 'candidate.manage') "
        "ON CONFLICT (code) DO NOTHING"
    )


def downgrade():
    op.execute("DELETE FROM permissions WHERE code = 'candidate.manage'")
    op.drop_table("candidate_profiles")
    op.drop_index("idx_resumes_candidate", table_name="resumes")
    op.drop_table("resumes")
    op.drop_table("candidates")
