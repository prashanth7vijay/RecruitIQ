from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0013_org_structure"
down_revision = "0012_audit_logs"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("city", sa.String(150), nullable=True),
        sa.Column("country", sa.String(150), nullable=True),
        sa.Column("is_remote", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "name", name="uq_locations_company_name"),
    )

    op.add_column("users", sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_users_team_id", "users", "teams", ["team_id"], ["id"], ondelete="SET NULL"
    )

    op.add_column("users", sa.Column("manager_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_users_manager_id", "users", "users", ["manager_id"], ["id"], ondelete="SET NULL"
    )

    op.add_column("users", sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_users_location_id", "users", "locations", ["location_id"], ["id"], ondelete="SET NULL"
    )


def downgrade():
    op.drop_constraint("fk_users_location_id", "users", type_="foreignkey")
    op.drop_column("users", "location_id")
    op.drop_constraint("fk_users_manager_id", "users", type_="foreignkey")
    op.drop_column("users", "manager_id")
    op.drop_constraint("fk_users_team_id", "users", type_="foreignkey")
    op.drop_column("users", "team_id")
    op.drop_table("locations")
