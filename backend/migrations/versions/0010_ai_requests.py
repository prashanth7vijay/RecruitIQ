from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0010_ai_requests"
down_revision = "0009_offers_onboarding"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("feature", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("input_tokens", sa.Integer, nullable=True),
        sa.Column("output_tokens", sa.Integer, nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_ai_requests_company_feature", "ai_requests", ["company_id", "feature", "created_at"])


def downgrade():
    op.drop_table("ai_requests")
