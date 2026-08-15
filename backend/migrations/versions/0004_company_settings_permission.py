from alembic import op

revision = "0004_company_settings_permission"
down_revision = "0003_jobs"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "INSERT INTO permissions (id, code) VALUES (gen_random_uuid(), 'company.manage_settings') "
        "ON CONFLICT (code) DO NOTHING"
    )


def downgrade():
    op.execute("DELETE FROM permissions WHERE code = 'company.manage_settings'")
