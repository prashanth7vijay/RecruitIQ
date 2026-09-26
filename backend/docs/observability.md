# Observability (Phase 6)

## Scope, stated upfront

Implements the Section 18 metric names this codebase already produces
real numbers for: HTTP requests, the Phase 1 ranking pipeline, the
Phase 3 dashboard cache, and stage transitions. **Does not** add
`sla_breaches_total` or any SLA metric — there is no SLA engine in
this codebase (Section 12 was never built in these five phases), and a
metric with no real data source is exactly the resume-keyword
addition Rule 2 warns against. No Prometheus server or Grafana
dashboard is deployed here either — `prometheus_client` is a small
library that makes `/metrics` real and scrapeable; standing up actual
Prometheus/Grafana is a deployment decision outside this codebase.

## What's implemented

- `/health` — was `return {"status": "ok"}, 200` unconditionally,
  checking nothing. Now actually checks Postgres (`SELECT 1`) and
  Redis (via the cache client), returns 503 with per-dependency status
  on failure.
- `/metrics` — Prometheus text format: `http_requests_total`,
  `http_request_duration_seconds` (via before/after_request),
  `candidate_ranking_duration_seconds` /
  `candidate_ranking_candidates_total` /
  `candidate_ranking_ai_requests_total` /
  `candidate_ranking_cache_hits_total` /
  `candidate_ranking_cache_misses_total` (wired into both the sync and
  async ranking routes — same `RankingRunMetrics` from Phase 1),
  `dashboard_cache_hits_total` / `dashboard_cache_misses_total` (wired
  into Phase 3's `executive_summary` route), and
  `application_stage_transitions_total`.

## The multiprocess subtlety (and why it isn't optional)

Phase 5 put this app behind 4 real gunicorn worker processes.
`prometheus_client`'s default registry is per-process — each worker
would only report the requests it happened to serve, and scraping
`/metrics` on whichever worker answers that particular request would
never show what the other 3 did. Silently wrong, not visibly broken —
worse than no metrics at all.

Fixed with `prometheus_client`'s documented multiprocess mode
(`gunicorn.conf.py`: sets `PROMETHEUS_MULTIPROC_DIR` before the app
imports, cleans it on boot, and calls `multiprocess.mark_process_dead`
in a `child_exit` hook when a worker recycles).

**Verified, not assumed:** ran the real 4-worker gunicorn command, sent
21 requests to `/health` (necessarily spread across all 4 workers by
gunicorn's own connection handling), then queried `/metrics` — it
reported exactly 21, not roughly a quarter of that. If multiprocess
mode weren't wired correctly, this number would have been wrong in a
way that gave no error, only a quietly misleading dashboard later.

## Reproducing this

```bash
gunicorn -c gunicorn.conf.py wsgi:app &
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/metrics | grep http_requests_total
```

## Follow-ups, not implemented this phase

- An SLA engine (Section 12) — if built, its metrics belong in
  `app/observability.py` alongside these.
- Actual Prometheus server + Grafana dashboards — `/metrics` is ready
  to be scraped; nothing here stands up either.
