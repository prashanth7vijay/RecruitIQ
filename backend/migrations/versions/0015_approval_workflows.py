from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0015_approval_workflows"
down_revision = "0014_user_invitation_flow"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "approval_chains",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(20), nullable=False),  # "job" | "offer"
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "entity_type", name="uq_approval_chains_company_entity"),
    )

    op.create_table(
        "approval_chain_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("approval_chain_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("approval_chains.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("step_order", sa.Integer, nullable=False),
    )

    op.drop_column("job_approval_steps", "approver_role")
    op.add_column(
        "job_approval_steps",
        sa.Column("approver_role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id"), nullable=True),
    )

    op.drop_column("offer_approval_steps", "approver_role")
    op.add_column(
        "offer_approval_steps",
        sa.Column("approver_role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id"), nullable=True),
    )


def downgrade():
    op.drop_column("offer_approval_steps", "approver_role_id")
    op.add_column("offer_approval_steps", sa.Column("approver_role", sa.String(50), nullable=True))

    op.drop_column("job_approval_steps", "approver_role_id")
    op.add_column("job_approval_steps", sa.Column("approver_role", sa.String(50), nullable=True))

    op.drop_table("approval_chain_steps")
    op.drop_table("approval_chains")
