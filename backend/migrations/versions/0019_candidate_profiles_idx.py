"""candidate_profiles_company_created_index

Phase 2 (DB profiling) finding, backed by EXPLAIN ANALYZE against a
100K-candidate synthetic dataset (scripts/generate_synthetic_data.py):
GET /api/v1/candidates paginates with ORDER BY created_at DESC (added
this same phase — see the jobs/candidates route fix in
docs/database-optimization.md for why an explicit order is required
at all), but `idx_candidate_profiles_company` only covers company_id,
so every page requires a full sort of every one of that tenant's
candidate_profiles rows before LIMIT/OFFSET can even apply. Confirmed
via EXPLAIN ANALYZE: a shallow page already pays for an in-memory
top-N sort (~31ms at 100K rows), and a deep page (OFFSET 80000) spills
to an on-disk external merge sort (~71ms) because Postgres has to
materialize and sort the full result set to find the requested offset.

(company_id, created_at DESC) lets the DESC-ordered pagination walk
the index directly — see docs/database-optimization.md for the
before/after numbers.

Revision ID: 0019_candidate_profiles_idx
Revises: 0017_fix_timestamp_defaults
Create Date: 2026-09-22
"""

from alembic import op

revision = "0019_candidate_profiles_idx"
down_revision = "0018_fix_timestamp_defaults"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "idx_candidate_profiles_company_created",
        "candidate_profiles",
        ["company_id", "created_at"],
        postgresql_ops={"created_at": "DESC"},
    )


def downgrade():
    op.drop_index("idx_candidate_profiles_company_created", table_name="candidate_profiles")

