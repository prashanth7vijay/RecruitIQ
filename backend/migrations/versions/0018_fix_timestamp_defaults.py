"""fix_missing_created_at_server_defaults

Bug fix, not a schema change: 24 timestamp columns across migrations
0001-0012 (companies.created_at, users.created_at, candidates.created_at,
applications.applied_at, ai_requests.created_at, and 20 others) were
declared `nullable=False` with no `server_default`, even though every
corresponding SQLAlchemy model declares `server_default=db.func.now()`
for that column.

The migration files and the models had silently drifted apart. It
went undetected because the test suite builds its schema via
Flask-SQLAlchemy's `db.create_all()` (which reads the model's
`server_default` correctly), not via these migration files — so
`flask db upgrade` was the only code path that ever exercised the
buggy DDL, and nothing in the test suite runs `flask db upgrade`.

Concretely: for any table below, inserting a row through the ORM
without explicitly setting the timestamp column raised a Postgres
NOT NULL violation on `created_at`/`applied_at`/`uploaded_at`/
`added_at` — reproduced against a real `flask db upgrade`-built
database while seeding data for the V2 ranking-pipeline benchmark
(scripts/benchmark_ranking.py). Migrations 0013, 0015, and 0016
already declare `server_default=sa.func.now()` correctly — this bug
was only ever in 0001-0012, and appears to have been fixed going
forward without being backported.

This migration only ALTERs existing columns to add the missing
default; it changes no types, no nullability, no data. New
deployments running the full migration chain from empty would now
get the fix baked into 0001-0012 directly instead of needing this
patch — this file exists for databases that already ran the buggy
versions of those migrations.

Revision ID: 0018_fix_timestamp_defaults
Revises: 0016_employee_portal
Create Date: 2026-09-22
"""

from alembic import op
import sqlalchemy as sa

revision = "0018_fix_timestamp_defaults"
down_revision = "0017_referral_pre_application"
branch_labels = None
depends_on = None

# (table, column) pairs that were missing server_default=now() in
# their original CREATE TABLE, per model cross-check.
AFFECTED_COLUMNS = [
    ("companies", "created_at"),
    ("departments", "created_at"),
    ("users", "created_at"),
    ("refresh_tokens", "created_at"),
    ("login_history", "created_at"),
    ("teams", "created_at"),
    ("jobs", "created_at"),
    ("job_approval_steps", "created_at"),
    ("candidates", "created_at"),
    ("resumes", "uploaded_at"),
    ("candidate_profiles", "created_at"),
    ("applications", "applied_at"),
    ("application_stage_history", "created_at"),
    ("notifications", "created_at"),
    ("interviews", "created_at"),
    ("interview_feedback", "created_at"),
    ("offers", "created_at"),
    ("offer_approval_steps", "created_at"),
    ("onboarding_checklists", "created_at"),
    ("ai_requests", "created_at"),
    ("talent_pools", "created_at"),
    ("talent_pool_memberships", "added_at"),
    ("candidate_notes", "created_at"),
    ("candidate_tags", "created_at"),
    ("audit_logs", "created_at"),
]


def upgrade():
    for table, column in AFFECTED_COLUMNS:
        op.alter_column(table, column, server_default=sa.func.now())


def downgrade():
    for table, column in AFFECTED_COLUMNS:
        op.alter_column(table, column, server_default=None)

