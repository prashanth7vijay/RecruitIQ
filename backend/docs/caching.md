# Analytics Dashboard Caching (Phase 3)

## 1. Problem

`AnalyticsService.executive_summary()` runs five separate live
aggregate queries (hiring velocity, pipeline health, offer acceptance
rate, time-to-hire, department hiring) on every single call — this is
by design (see the module's own docstring: "no materialized views, no
nightly rollups... genuinely correct today"), but it's also, by a wide
margin, the single most expensive read in the whole API, and the one
an executive dashboard is most likely to poll or reload repeatedly.

`Flask-Caching` was registered in the app factory from the start of
this project but had `CACHE_TYPE` unset (a no-op backend) until Phase
1 wired it to Redis for the ranking pipeline's explanation cache. This
phase is the first thing to actually use it for analytics.

## 2. Design decision

- Only `executive_summary()` is cached — not the five sub-methods
  individually. They're each callable directly (drill-down pages use
  them), and caching them all separately would multiply the number of
  cache keys and invalidation paths for a benefit `executive_summary`
  already captures in one place, since it calls all five anyway.
- Cache key: `analytics:executive_summary:{tenant_id}` — one entry per
  tenant, matching the endpoint's own scope.
- TTL: 60 seconds, as a safety net — see Section 4.
- Active invalidation on `application.stage_changed` and
  `offer.accepted` (Celery task, `app/workers/analytics_tasks.py`,
  subscribed via the existing `EventBus`) — these are the two events
  that change data this specific summary reads. `interview.scheduled`
  and `resume.uploaded` don't feed anything in `executive_summary` and
  aren't subscribed to.
- `executive_summary()` is the only method on `AnalyticsService` whose
  return type changed — it now returns `(summary_dict, meta_dict)`
  instead of a bare dict, where `meta_dict = {"cache_hit": bool}`. Every
  other method (`hiring_velocity`, `pipeline_health`, etc.) is
  untouched, and their routes are untouched — only
  `GET /api/v1/analytics/executive-summary`'s route was updated to
  unpack the tuple and surface `cache_hit` in its own response `meta`.

## 3. Alternatives considered

- **Cache each sub-method separately.** More cache keys and
  invalidation surface for no real benefit, since `executive_summary`
  is the actual hot path — see Section 2.
- **TTL-only, no active invalidation.** Simpler, but means a
  recruiter moving a candidate through the pipeline wouldn't see it
  reflected on the dashboard for up to 60 seconds — a bad enough UX
  gap on the two events that clearly matter (stage changes, offers)
  that active invalidation was worth the small added code.
- **Invalidate on every write to any table this summary touches**
  (jobs, applications, offers, departments). Rejected: would mean
  hooking into far more write paths for marginal benefit — most of
  those tables change far less often than applications/offers do, and
  the 60s TTL already bounds the staleness for the events not
  actively covered (see Section 4).

## 4. Trade-offs, stated plainly

- **Job status changes (published/closed) aren't actively
  invalidated** — no event currently exists for that in `EventBus`.
  `hiring_velocity` and `department_hiring` both read job status, so
  publishing or closing a job won't show up on the dashboard until the
  60s TTL expires. This is a real, known gap, not an oversight — adding
  a `job.status_changed` event was judged out of scope for this pass
  (see Section 5 for the reasoning already documented in Phase 2 about
  not touching more than what's actually being measured).
- The cache is a plain value cache, not versioned — if two concurrent
  requests both miss at once, both recompute and both write the same
  key. Harmless here (idempotent, same tenant, same query), just worth
  naming: this is not a stampede-protected cache.

## 5. Implementation

`app/services/analytics_service.py` (`executive_summary`,
`_executive_summary_cache_key`), `app/workers/analytics_tasks.py`
(`invalidate_analytics_cache_task`), `app/services/event_bus.py`
(subscription wiring), `app/api/v1/analytics/routes.py`
(`executive_summary` route only).

## 6. Benchmark methodology

`scripts/benchmark_analytics_cache.py` — points `AnalyticsService` at
a real seeded company (Phase 2's `bench-100k`/`bench-noise` datasets)
and calls `executive_summary()` repeatedly: once with `cache=None`
(every call recomputes, the pre-Phase-3 behavior) and once with the
real Redis cache (one genuine miss, then N-1 real hits).

```bash
python scripts/benchmark_analytics_cache.py --slug bench-100k --requests 50
python scripts/benchmark_analytics_cache.py --slug bench-noise --requests 50
```

## 7. Results (measured, real Postgres + Redis)

| Dataset | Without cache (p50 / p95 / p99) | Cache miss (first call) | Cache hit (p50 / p95 / p99) |
|---|---:|---:|---:|
| `bench-100k` (100K candidates, 100K applications) | 260.1 / 307.0 / 856.5 ms | 268.2 ms | **0.03 / 0.06 / 0.15 ms** |
| `bench-noise` (300K candidates, 300K applications) | 722.7 / 751.4 / 787.8 ms | 698.1 ms | **0.03 / 0.05 / 0.08 ms** |

Reproduced 2026-09-22 against a real Postgres 16 + Redis 7 instance.

A cache hit costs a Redis round trip, not five SQL aggregate queries —
which is exactly why the hit numbers barely move between a 100K and a
300K dataset (0.03ms both times) while the uncached numbers scale with
data volume (260ms → 723ms). **A cache hit avoids all 5 of the
underlying aggregate queries** (`hiring_velocity`, `pipeline_health`,
`offer_acceptance_rate`, `time_to_hire`, `department_hiring`) — the
dashboard's single most expensive read becomes, on every request but
the first in any 60-second window, effectively free.

## 8. Future improvements

- A `job.status_changed` event, to close the gap in Section 4 — would
  need adding a publish call to the job status-update path, which
  doesn't currently exist for any event.
- Stampede protection (e.g. a short-lived lock around the recompute)
  if this dashboard ever sees high concurrent traffic on a cold cache —
  not a real problem at this project's current scale.
