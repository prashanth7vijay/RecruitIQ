from alembic import op
import sqlalchemy as sa

revision = "0014_user_invitation_flow"
down_revision = "0013_org_structure"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("must_change_password", sa.Boolean, nullable=False, server_default="false"),
    )
    op.add_column(
        "users",
        sa.Column("temp_password_expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_column("users", "temp_password_expires_at")
    op.drop_column("users", "must_change_password")
