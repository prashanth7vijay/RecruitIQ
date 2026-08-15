from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0016_employee_portal"
down_revision = "0015_approval_workflows"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "referrals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("referred_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("application_id", name="uq_referrals_application_id"),
    )


def downgrade():
    op.drop_table("referrals")
