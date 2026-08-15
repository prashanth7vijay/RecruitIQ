from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0011_talent_crm"
down_revision = "0010_ai_requests"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "talent_pools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "talent_pool_memberships",
        sa.Column("talent_pool_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("talent_pools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("candidate_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("talent_pool_id", "candidate_profile_id"),
    )

    op.create_table(
        "candidate_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("candidate_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_candidate_notes_profile", "candidate_notes", ["candidate_profile_id"])

    op.create_table(
        "candidate_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("candidate_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("candidate_profile_id", "label", name="uq_candidate_tag_label"),
    )
    op.create_index("idx_candidate_tags_profile", "candidate_tags", ["candidate_profile_id"])


def downgrade():
    op.drop_table("candidate_tags")
    op.drop_table("candidate_notes")
    op.drop_table("talent_pool_memberships")
    op.drop_table("talent_pools")
