"""candidates_trgm_search_index

Phase 4 (search) finding, backed by EXPLAIN ANALYZE: SearchService's
own docstring documents ILIKE as correct below a stated "500K+
candidates" threshold — but that count is implicitly per-tenant. It
isn't. `candidates` is a deliberately GLOBAL table (see Candidate's
docstring / GlobalRepository — identity is shared across every tenant
a person has ever applied to), so a single tenant's search box pays
the cost of scanning every OTHER tenant's candidates too. With a
second, independently-sized tenant's data actually present (Phase 2's
`bench-noise`), the real global candidate count is 402,120, not one
tenant's 100,000 — and the worst-case query (a no-match search, which
can't early-exit on LIMIT) measured at 530ms, not the 139ms seen
against a single tenant in Phase 2. Documented in
docs/search-optimization.md, including the corrected per-tenant vs.
global distinction.

This does NOT switch the query to Postgres full-text search or
Elasticsearch — it keeps the exact same ILIKE query in
SearchService, unchanged, and adds `pg_trgm` GIN indexes so Postgres
can actually use an index for a leading-wildcard ILIKE pattern (a
plain btree can't). Preserves the current substring-match search
behavior exactly; only the query plan changes. See
docs/search-optimization.md for the measured before/after and the
reasoning for not (yet) moving to a heavier full-text/Elasticsearch
solution.

Revision ID: 0020_candidates_trgm_idx
Revises: 0018_candidate_profiles_idx
Create Date: 2026-09-22
"""

from alembic import op

revision = "0020_candidates_trgm_idx"
down_revision = "0019_candidate_profiles_idx"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX idx_candidates_first_name_trgm ON candidates USING GIN (first_name gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX idx_candidates_last_name_trgm ON candidates USING GIN (last_name gin_trgm_ops)"
    )
    # email is CITEXT, not a plain text/varchar column — cast it for
    # the trigram operator class, which is defined over text.
    op.execute(
        "CREATE INDEX idx_candidates_email_trgm ON candidates USING GIN ((email::text) gin_trgm_ops)"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_candidates_email_trgm")
    op.execute("DROP INDEX IF EXISTS idx_candidates_last_name_trgm")
    op.execute("DROP INDEX IF EXISTS idx_candidates_first_name_trgm")
    # Extension deliberately left in place on downgrade — dropping it
    # would fail loudly if anything else ever comes to depend on it,
    # and CREATE EXTENSION IF NOT EXISTS makes re-upgrading idempotent
    # either way.

