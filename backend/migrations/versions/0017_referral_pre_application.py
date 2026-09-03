from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0017_referral_pre_application"
down_revision = "0016_employee_portal"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("referrals", sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("referrals", sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=True))

    op.execute(
        """
        UPDATE referrals
        SET job_id = applications.job_id,
            candidate_id = applications.candidate_id
        FROM applications
        WHERE applications.id = referrals.application_id
        """
    )

    op.alter_column("referrals", "job_id", nullable=False)
    op.alter_column("referrals", "candidate_id", nullable=False)
    op.alter_column("referrals", "application_id", nullable=True)

    op.create_foreign_key(
        "fk_referrals_job_id", "referrals", "jobs", ["job_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_referrals_candidate_id", "referrals", "candidates", ["candidate_id"], ["id"], ondelete="CASCADE"
    )

    op.drop_constraint("referrals_application_id_fkey", "referrals", type_="foreignkey")
    op.create_foreign_key(
        "fk_referrals_application_id", "referrals", "applications", ["application_id"], ["id"]
    )


def downgrade():
    op.drop_constraint("fk_referrals_application_id", "referrals", type_="foreignkey")
    op.create_foreign_key(
        "referrals_application_id_fkey", "referrals", "applications", ["application_id"], ["id"], ondelete="CASCADE"
    )
    op.alter_column("referrals", "application_id", nullable=False)
    op.drop_constraint("fk_referrals_candidate_id", "referrals", type_="foreignkey")
    op.drop_constraint("fk_referrals_job_id", "referrals", type_="foreignkey")
    op.drop_column("referrals", "candidate_id")
    op.drop_column("referrals", "job_id")