from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_teams"
down_revision = "0001_initial_auth_foundation"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_teams_company", "teams", ["company_id"])

    # New permission for Sprint 2's org-structure management endpoints.
    op.execute(
        "INSERT INTO permissions (id, code) VALUES (gen_random_uuid(), 'org.manage_structure') "
        "ON CONFLICT (code) DO NOTHING"
    )


def downgrade():
    op.execute("DELETE FROM permissions WHERE code = 'org.manage_structure'")
    op.drop_index("idx_teams_company", table_name="teams")
    op.drop_table("teams")
