# Search Optimization (Phase 4)

## 1. Problem

`SearchService`'s own docstring states, correctly, that plain `ILIKE`
search is adequate below a "500K+ candidates" threshold, and that
Postgres full-text search is where the added complexity starts earning
its keep above that. Phase 2 measured this at 100K candidates and
found it fine (4.6ms common case, 139ms worst case) — consistent with
the stated threshold.

**That threshold is implicitly per-tenant. It isn't, in practice.**
`candidates` is a deliberately global table — identity is shared
across every tenant a person has ever applied to (see `Candidate`'s
own docstring) — so a single tenant's search box pays the `ILIKE` cost
of scanning *every other tenant's* candidates too. Phase 2's 100K
measurement only had one tenant's data in the database. With Phase
2's second tenant (`bench-noise`, 300K candidates) actually present,
the real global candidate count is 402,120, and the worst-case query
(a no-match search — common in real usage, and the one shape that
can't early-exit on `LIMIT`) measured at **530ms**, not 139ms.

## 2. What didn't work on the first try

The obvious fix — add `pg_trgm` GIN indexes so Postgres can use an
index for a leading-wildcard `ILIKE '%text%'` pattern, which a plain
btree can't — didn't, by itself, change anything. Two more things had
to be found and fixed, in order, before it did:

**First: query shape.** The natural ORM query —
`candidate_profiles JOIN candidates ON ... WHERE company_id = X AND
(ILIKE OR ILIKE OR ILIKE)` — doesn't let Postgres use the trigram
indexes at all, even with `enable_seqscan` forced off. The planner
consistently drove the join from a full scan of `candidates`
regardless. Restructuring as a semi-join —
`candidate_profiles WHERE company_id = X AND candidate_id IN (SELECT
id FROM candidates WHERE ...)` — is a behaviorally identical query
(same matched rows, same order, same limit) that the planner does
index correctly. Verified with `EXPLAIN ANALYZE` before changing any
application code — raw SQL first, to isolate whether this was a
Postgres planner behavior or an SQLAlchemy artifact (it was the
former).

**Second, after the first fix looked like it worked in raw SQL but
didn't in the app: `email` is `CITEXT`, not `TEXT`.** The trigram
index's operator class is defined over `text`; comparing
`Candidate.email.ilike(pattern)` directly compiles to a `citext`
comparison, a different expression the index doesn't match. Postgres
doesn't partially apply a `BitmapOr` — **one non-indexable branch in
the `OR` made the planner abandon indexing the other two branches as
well** (first_name/last_name, which are indexed correctly on their
own) and fall back to a full sequential scan for the whole predicate.
This wasn't visible in the raw-SQL testing above because that testing
explicitly cast `email::text` by hand; the ORM's generated SQL,
compiled from `Candidate.email.ilike(pattern)` with no cast, didn't.
Running the *actual* SQLAlchemy-generated SQL text through `EXPLAIN
ANALYZE` (not a hand-written equivalent) is what surfaced this — a
reminder that "the raw SQL version is fast" doesn't guarantee the ORM
emits the same SQL.

Fixed with an explicit cast:
`cast(Candidate.email, Text).ilike(pattern)` (`app/services/
search_service.py`).

## 3. Design decision

`_search_candidates` now builds the candidate-id match as its own
`select(...)` used in a `.in_()` filter, instead of a `.join(...)`.
Behavior is unchanged — same candidates match, same order, same
limit — only the query plan differs. `_search_jobs` is untouched
(`jobs` is company-scoped already, not global, and small at any
realistic scale — no evidence it needs the same treatment).

Migration `0019_candidates_trgm_idx.py` adds `pg_trgm` GIN indexes on
`candidates.first_name`, `candidates.last_name`, and
`candidates.email::text` (the cast is part of the index definition
too — index and query need to agree on the exact expression).

## 4. Results (measured, real Postgres, 402,120 global candidates)

Through the actual application code path (`SearchService.
_search_candidates`, not raw SQL):

| Query shape | Before (original ILIKE + JOIN, no trgm index) | After (semi-join + trgm index + email cast) |
|---|---:|---:|
| No match (worst case) | 530 ms | **~1.3 ms** |
| Rare/specific match | not separately measured pre-fix | **~2.1 ms** |
| Common match (~8% of table — see caveat below) | 266 ms† | **~2.6 ms** |

† Measured against the restructured-but-not-yet-email-cast version;
the fully-original JOIN version wasn't separately re-measured for this
row since the no-match case already demonstrates the mechanism.

**Caveat on the "common match" row, stated honestly:** the synthetic
generator's `FIRST_NAMES` pool (`scripts/generate_synthetic_data.py`)
only has 12 values, so a first-name substring like "jordan" matches
roughly 8% of all 402K candidates — a real production name
distribution wouldn't concentrate this way. This makes the "common
match" case here more of a stress test of the indexed approach at high
match-count than a realistic everyday query; it's included because the
indexed version still handily beats the original, not because the
match rate itself is representative.

## 5. Decision: keep ILIKE, don't move to tsvector/Elasticsearch — yet

Per Rule 10 (prefer existing infra before adding new), `pg_trgm` is
part of Postgres itself, not a new infrastructure dependency, and it
preserves the exact current search semantics (unrestricted substring
match) with no query-language change. With it in place, `ILIKE` at
400K+ global candidates now performs comparably to what tsvector/
Elasticsearch would offer for this query shape — there's no current
evidence a heavier full-text engine would outperform it materially at
this project's actual scale. The 500K+ threshold in `SearchService`'s
docstring remains the stated point to revisit, now correctly
understood as a global count, not per-tenant.

## 6. Reproducing this

```bash
# requires Phase 2's two datasets already generated
python -c "
from app import create_app
from app.extensions import db
from app.services.search_service import SearchService
from app.models.company import Company
import time

app = create_app('development')
with app.app_context():
    company = db.session.query(Company).filter_by(slug='bench-100k').first()
    service = SearchService(db.session)
    for label, q in [('no-match', 'zzznotfound'), ('rare', '49176-31d794'), ('common', 'jordan')]:
        t0 = time.monotonic()
        results = service._search_candidates(company.id, q, 10)
        print(label, round((time.monotonic() - t0) * 1000, 2), 'ms,', len(results), 'results')
"
```
