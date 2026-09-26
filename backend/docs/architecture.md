# RecruitIQ V2 — Architecture Summary

```
React Frontend
      |
      v
gunicorn (4 gevent workers)  <-- was `flask run` until Sprint 17
      |
      +---- PostgreSQL (tenant-scoped via BaseRepository; 25+ indexes)
      |
      +---- Redis (Celery broker, Flask-Caching backend, rate-limit storage)
      |
      +---- Celery workers (queues: critical / cpu_intensive / default / batch)
      |         |
      |         +---- ranking_tasks (batch)      — async candidate ranking
      |         +---- analytics_tasks (default)  — dashboard cache invalidation
      |         +---- notification/email/resume tasks (pre-existing)
      |
      +---- Ollama (local AI, stub fallback for tests/CI)
      |
      +---- /metrics (Prometheus text format, multiprocess-aggregated)
```

Every component above exists for a reason traceable to a specific,
measured problem — not because it looked good on a diagram. Each is
covered in its own doc, in the order the work happened:

| Sprint | Doc | What it covers |
|---|---|---|
| 13 | [`ranking-engine.md`](ranking-engine.md) | Candidate ranking pipeline: pre-filter, caching, async path |
| 14 | [`database-optimization.md`](database-optimization.md) | Indexing, a corrected Phase 0 claim, a reverted "fix" |
| 15 | [`caching.md`](caching.md) | Analytics dashboard Redis cache |
| 16 | [`search-optimization.md`](search-optimization.md) | Two real bugs behind a search fix that didn't work on the first try |
| 17 | [`scalability.md`](scalability.md) | Load testing, and 3 real infra bugs found doing it |
| 18 | [`observability.md`](observability.md) | `/health`, `/metrics`, multiprocess metrics correctness |

`RESUME_METRICS.md` has the numbers themselves, sourced only from
these docs.

## What ties the whole V2 pass together

Every phase followed the same discipline, applied to this codebase's
own prior work and to my own changes equally:

1. **Verify before trusting a claim** — including my own. Phase 0's
   "zero indexes" and "gunicorn is already wired up" were both wrong,
   both caught in later phases by actually running the thing instead
   of reading about it, both corrected in the record rather than quietly
   fixed.
2. **Measure before shipping an optimization.** The Sprint 14 "fix"
   that turned out slower against a real second tenant is the clearest
   example — reverted, and the reversal is documented as the actual
   finding.
3. **State what wasn't done, and why**, as plainly as what was — no
   SLA metrics without an SLA engine, no Elasticsearch without evidence
   ILIKE can't keep up, no production capacity claim from a
   single-core sandbox.

Full test suite: **199/199 passing**, genuinely run against real
Postgres/Redis, not asserted from reading the code.
