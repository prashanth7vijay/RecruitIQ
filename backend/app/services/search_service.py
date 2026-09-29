"""
Deliberate simplification of Phase 18's full design: this uses plain
ILIKE queries rather than Postgres tsvector/GIN full-text search.
Genuinely correct and adequate at the data volumes a single tenant
will have for a while — the documented threshold in Phase 18.7 (500K+
candidates with heavy fuzzy-search demand) is where the real tsvector
migration becomes worth its added complexity, not before. Swapping
this out later means changing SearchService's internals only, since
callers just get {candidates: [...], jobs: [...]} either way.

V2 addition (Phase 4): that 500K+ threshold was implicitly per-tenant.
It isn't, in practice — `candidates` is a deliberately GLOBAL table
(identity shared across every tenant a person has ever applied to,
see Candidate's own docstring), so one tenant's search box pays the
ILIKE cost of every OTHER tenant's candidates too. Measured with a
second, independently-sized tenant's data actually present: a
no-match search (query text nobody matches — common in real usage,
and the shape that can't early-exit on LIMIT) cost 530ms against
402K global candidates, worse than the per-tenant number the
threshold above was written against.

pg_trgm GIN indexes (migration 0019) fix the missing-index half of
that, but two things had to be fixed to actually get Postgres to use
them:

1. The ORM's natural `JOIN candidates ... WHERE company_id = X AND
   (ILIKE OR ILIKE OR ILIKE)` shape doesn't let Postgres use them —
   measured: the planner chooses a Nested Loop driven by a full seq
   scan of `candidates`, ignoring the trigram indexes entirely.
   Restructured as a semi-join instead (`candidate_id IN (SELECT id
   FROM candidates WHERE ...)`) — a behaviorally identical query (same
   rows, same order, same limit) that the planner does index correctly.
2. `Candidate.email` is `CITEXT`, not `TEXT` — the trigram index is
   built on `email::text` (the operator class the index uses is
   defined over `text`), but a plain `Candidate.email.ilike(pattern)`
   compares as `citext`, a different expression the index doesn't
   match. Postgres doesn't partially use a BitmapOr — one
   non-indexable branch in the OR made it abandon indexing the other
   two branches as well and fall back to a full seq scan, even though
   first_name/last_name alone were indexed correctly. Fixed by
   explicitly casting: `cast(Candidate.email, Text).ilike(pattern)`.

Measured end to end, through the real ORM code path (not just raw
SQL): 3.68s -> ~1ms for the no-match case. Full numbers, plan output,
and the debugging path that found the CITEXT mismatch are in
docs/search-optimization.md.
"""

from sqlalchemy import Text, cast, select

from app.models.candidate import Candidate, CandidateProfile
from app.models.job import Job


class SearchService:
    def __init__(self, session):
        self.session = session

    def search(self, tenant_id, query, limit=10):
        return {
            "candidates": self._search_candidates(tenant_id, query, limit),
            "jobs": self._search_jobs(tenant_id, query, limit),
        }

    def _search_candidates(self, tenant_id, query, limit):
        pattern = f"%{query}%"
        # Semi-join (candidate_id IN (...)), not a JOIN, and email is
        # explicitly cast to text — both required for Postgres to
        # actually use the pg_trgm indexes here. See the module
        # docstring; either one alone isn't enough.
        matching_candidate_ids = select(Candidate.id).where(
            (Candidate.first_name.ilike(pattern))
            | (Candidate.last_name.ilike(pattern))
            | (cast(Candidate.email, Text).ilike(pattern))
        )
        return (
            self.session.query(CandidateProfile)
            .filter(CandidateProfile.company_id == tenant_id)
            .filter(CandidateProfile.candidate_id.in_(matching_candidate_ids))
            .limit(limit)
            .all()
        )

    def _search_jobs(self, tenant_id, query, limit):
        pattern = f"%{query}%"
        return (
            self.session.query(Job)
            .filter(Job.company_id == tenant_id)
            .filter(Job.title.ilike(pattern))
            .limit(limit)
            .all()
        )
