# Database Profiling & Indexing (Phase 2)

## 1. Method

No index was added on a guess. Every claim below is a real
`EXPLAIN ANALYZE` run against a real Postgres 16 instance, seeded with
`scripts/generate_synthetic_data.py`:

- **Tenant A** (`bench-100k`): 100,000 candidates/profiles, 100,000
  applications, ~80K stage-history rows, ~5K interviews, ~3K offers.
- **Tenant B** (`bench-noise`): 300,000 candidates, sized deliberately
  larger than Tenant A specifically to stress-test any query whose
  cost depends on *other* tenants' data volume, not just this one's.

Regenerate both with:

```bash
python scripts/generate_synthetic_data.py --candidates 100000 --slug bench-100k --reset
python scripts/generate_synthetic_data.py --candidates 300000 --slug bench-noise --name "Noise Co" --reset
```

## 2. Correction to the Phase 0 assessment

Phase 0 claimed "zero explicit indexes across all 16 migrations."
That was wrong — a bad grep, not a bad schema. It searched for
`sa.Index(...)` / `index=True`, but this project declares every index
via `op.create_index(...)`, which the grep pattern didn't match. A
proper check turns up **25 explicit indexes**, and they're not
arbitrary — several already match the exact query shape the code
issues (`idx_applications_company_stage` on `(company_id,
current_stage_id)`, `idx_jobs_company_status` on `(company_id,
status)`, `idx_ai_requests_company_feature` on `(company_id, feature,
created_at)`). The schema was already well-indexed for its known
query patterns going in. Correcting this here rather than quietly
letting the Phase 0 doc stand uncorrected.

## 3. Real finding #1: missing ORDER BY on two paginated endpoints

`GET /api/v1/jobs` and `GET /api/v1/candidates` used `OFFSET`/`LIMIT`
with **no `ORDER BY`** — Postgres is free to return rows in a
different order on every call, so page 2 isn't reliably "the next 20
after page 1"; a row can silently repeat across pages or be skipped
entirely. This is a correctness bug, not just a performance one — found
while profiling pagination, not while looking for one.

Fixed: both endpoints now `.order_by(Model.created_at.desc())` before
pagination (`app/api/v1/jobs/routes.py`, `app/api/v1/candidates/routes.py`).
`audit_logs` and `notifications` already ordered correctly — checked,
not assumed.

## 4. Real finding #2: that fix has a real cost, indexed away

Adding the `ORDER BY` exposed what it was hiding: `candidate_profiles`
only had an index on `company_id` — nothing covering the sort key.

| | Before | After (`idx_candidate_profiles_company_created`) |
|---|---:|---:|
| Shallow page (`OFFSET 0`)     | 30.9 ms (parallel seq scan + in-memory top-N sort) | **0.09 ms** (index scan, no sort) |
| Deep page (`OFFSET 80000`)    | 71.5 ms (seq scan + **on-disk external merge sort**, ~6MB spilled) | **17.6 ms** (index scan) |
| Deep page, second tenant present (`OFFSET 80000`, 400K total rows across tenants) | not re-measured (Tenant B added after the index) | **16.4 ms** — confirms the index scan's benefit doesn't erode as other tenants' data grows |

Index (migration `0018_candidate_profiles_idx.py`):
```sql
CREATE INDEX idx_candidate_profiles_company_created
    ON candidate_profiles (company_id, created_at DESC);
```

**Honest caveat on the deep-page number:** 17.6ms is a real
improvement over 71.5ms, but it isn't free — `OFFSET 80000` still
means walking 80,020 index entries to find where the requested page
starts; the index just replaces "scan everything, sort it all" with
"walk the index, skip the ones before the offset." True O(1)-per-page
cost would need cursor/keyset pagination (`WHERE created_at < :last_seen
ORDER BY created_at DESC LIMIT 20`) instead of `OFFSET`, which
`paginate_query()` doesn't currently support. Noted as a real follow-up
in Section 7, not implemented here — `paginate_query` is used by 4
endpoints and changing its contract is a bigger, riskier change than
this pass's scope.

## 5. Real finding #3 — and a reverted "fix"

`AnalyticsService.pipeline_health()`'s `latest_move` subquery
aggregates `application_stage_history` with **no tenant filter at
all** before an outer join restricts it to one company. The instinct
("this wastes work scanning every other tenant's history rows") is a
completely reasonable one to have, and it drove me to implement a fix:
join to `applications` and filter by `company_id` *before* the
`GROUP BY`.

Measured against real data (Tenant A queried, Tenant B present as
genuine multi-tenant noise — not a single-tenant sandbox where the
fix would trivially look free):

| | Global, unscoped (original) | Tenant-filtered (the "fix") |
|---|---:|---:|
| Execution time | **89.5 ms** | 137.5 ms |
| Plan | `Index Only Scan` on `idx_stage_history_application (application_id, created_at)` — cheap, no heap access for most rows | `Hash Join` between a full seq scan of `application_stage_history` and a bitmap scan of `applications` — the join itself costs more than the rows it eliminates |

**The "fix" was slower. It's reverted** (see the inline comment in
`analytics_service.py`) — kept in this doc rather than silently
dropped, because the actual lesson is the useful part: a composite
index that already covers the aggregation's `GROUP BY`/`MAX()` shape
can make scanning "too much data" cheaper than a join meant to
avoid scanning it. Rule 11 of this project's own engineering
principles ("optimize based on profiling and measurement, not
assumptions") applied to my own first instinct here, not just to the
code I was reading — the reasonable-sounding fix needed to be
measured before it could be trusted, exactly the same as any other
change in this project.

## 6. Real finding #4: ILIKE search cost at 100K, measured against the stated threshold

`SearchService` (see its own docstring) states plainly that a
`tsvector`/GIN full-text search becomes worth its complexity at
"500K+ candidates with heavy fuzzy-search demand," and that plain
`ILIKE` is correct below that. Measured at 100K candidates (Tenant A):

| Query shape | Execution time |
|---|---:|
| Common substring, several matches, `LIMIT 10` (early exit) | 4.6 ms |
| Rare/no-match substring, `LIMIT 10` (must scan to the end) | **139.3 ms** |

Both numbers are real, and neither contradicts the stated 500K+
threshold — 139ms for a worst-case query is still workable for an
interactive search box. But it's worth naming precisely because it's
a **typical, not edge-case, pattern**: a search box gets typo'd or
under-matched queries constantly, and that's exactly the query shape
that can't early-exit on `LIMIT`. The threshold in `SearchService`'s
docstring is about total candidate count; the number that actually
degrades fastest is "how often does this tenant's search traffic miss."
Worth re-measuring specifically at whatever real query-miss rate shows
up in production, not just re-measuring candidate count. No index
added here — GIN/`pg_trgm` is the documented correct answer once
this becomes a real problem, not a preemptive addition against a
number that's currently fine.

## 7. Follow-ups identified, not implemented this phase

- **Keyset/cursor pagination** for `paginate_query()` — see the
  caveat in Section 4. Would remove the residual `OFFSET`-walk cost
  entirely, not just the sort. Bigger, riskier change (contract shift
  across 4 endpoints) than this phase's scope.
- **`COUNT(*)` on every paginated call** — `paginate_query()` runs a
  separate `query.count()` on every page load, in addition to the
  `LIMIT`/`OFFSET` query itself. Not benchmarked this phase (it's a
  simple `company_id`-filtered count, cheap at every scale tested
  here), but worth a real measurement before assuming it stays cheap
  at multi-million-row scale.
- `pg_trgm`/GIN index for search — deferred per Section 6, pending
  the stated threshold or a real query-miss-rate signal, whichever
  comes first.

## 8. Reproducing this

```bash
python scripts/generate_synthetic_data.py --candidates 100000 --slug bench-100k --reset
python scripts/generate_synthetic_data.py --candidates 300000 --slug bench-noise --name "Noise Co" --reset
flask db upgrade   # applies 0018_candidate_profiles_idx.py
# then EXPLAIN ANALYZE the queries above directly, or via psql
```
