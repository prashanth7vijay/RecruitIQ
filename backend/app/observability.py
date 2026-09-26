"""
Application-level metrics (Section 18 of the V2 brief), scoped
deliberately: this wires up the metric names that brief actually lists
and that prior phases' own work already produces real numbers for
(ranking pipeline, dashboard cache). It does NOT add
`sla_breaches_total` or similar — there is no SLA engine anywhere in
this codebase (Section 12 of the original brief was never built), and
a metric with no real data source behind it is exactly the kind of
resume-keyword addition Rule 2 warns against. If an SLA engine gets
built later, its metrics belong here too.

Uses `prometheus_client` directly — a small, standalone library, not
an actual Prometheus/Grafana deployment. `/metrics` exposes counters
in Prometheus's plain-text exposition format; whether anything ever
scrapes it (a real Prometheus server) is a deployment decision outside
this codebase's scope. Rule 10/12: this is the minimum that makes the
Section 18 metric names real and queryable, not an infrastructure
buildout.

MULTIPROCESS MODE, and why it's not optional here: Phase 5 put this
app behind 4 real gunicorn worker processes. prometheus_client's
default registry is per-process — each worker would report only the
requests it happened to handle, and scraping `/metrics` on one worker
would never show what the other 3 did. This uses prometheus_client's
documented multiprocess mode (`PROMETHEUS_MULTIPROC_DIR`) instead,
which aggregates across all worker processes via shared files on disk.
Requires `PROMETHEUS_MULTIPROC_DIR` set before the app boots (see
gunicorn.conf.py) and a `child_exit` gunicorn hook to clean up a
worker's files when it's recycled — both wired in gunicorn.conf.py.
Without both pieces, /metrics silently reverts to single-process
numbers with no error raised, which is worse than not having metrics
at all (confidently wrong beats visibly missing). Verified in
docs/observability.md by actually running multiple workers and
confirming /metrics reflects all of them, not just whichever one
served the scrape.
"""

import os
import time

from flask import Response, g, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest, multiprocess
from prometheus_client import CollectorRegistry

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds", "HTTP request duration in seconds", ["method", "endpoint"]
)

CANDIDATE_RANKING_DURATION_SECONDS = Histogram(
    "candidate_ranking_duration_seconds", "Duration of one candidate-ranking pipeline run"
)
CANDIDATE_RANKING_CANDIDATES_TOTAL = Counter(
    "candidate_ranking_candidates_total", "Candidates considered across all ranking runs"
)
CANDIDATE_RANKING_AI_REQUESTS_TOTAL = Counter(
    "candidate_ranking_ai_requests_total", "Real AI explanation calls made (cache misses)"
)
CANDIDATE_RANKING_CACHE_HITS_TOTAL = Counter(
    "candidate_ranking_cache_hits_total", "Explanation cache hits during ranking"
)
CANDIDATE_RANKING_CACHE_MISSES_TOTAL = Counter(
    "candidate_ranking_cache_misses_total", "Explanation cache misses during ranking"
)

DASHBOARD_CACHE_HITS_TOTAL = Counter(
    "dashboard_cache_hits_total", "executive_summary() served from cache"
)
DASHBOARD_CACHE_MISSES_TOTAL = Counter(
    "dashboard_cache_misses_total", "executive_summary() recomputed"
)

APPLICATION_STAGE_TRANSITIONS_TOTAL = Counter(
    "application_stage_transitions_total", "Applications moved to a new pipeline stage"
)


def record_ranking_metrics(metrics) -> None:
    """metrics: a RankingRunMetrics (app/services/ai/ranking_metrics.py).
    Called from the ranking routes/task after each run — both the sync
    and async paths produce the same RankingRunMetrics shape, so one
    function covers both."""
    CANDIDATE_RANKING_DURATION_SECONDS.observe(metrics.duration_seconds)
    CANDIDATE_RANKING_CANDIDATES_TOTAL.inc(metrics.candidates_considered)
    CANDIDATE_RANKING_AI_REQUESTS_TOTAL.inc(metrics.ai_calls_made)
    CANDIDATE_RANKING_CACHE_HITS_TOTAL.inc(metrics.ai_calls_cached)
    CANDIDATE_RANKING_CACHE_MISSES_TOTAL.inc(metrics.ai_calls_made)


def record_dashboard_cache(cache_hit: bool) -> None:
    if cache_hit:
        DASHBOARD_CACHE_HITS_TOTAL.inc()
    else:
        DASHBOARD_CACHE_MISSES_TOTAL.inc()


def register_metrics(app):
    """Wires the HTTP request counter/histogram via before/after_request,
    and adds the /metrics endpoint. Call once from create_app()."""

    @app.before_request
    def _start_timer():
        g._metrics_start_time = time.monotonic()

    @app.after_request
    def _record_request(response):
        # request.endpoint is None for a 404 on an unmatched route —
        # fall back to the raw path so those requests still count
        # instead of silently vanishing from the totals.
        endpoint = request.endpoint or request.path
        duration = time.monotonic() - g.get("_metrics_start_time", time.monotonic())

        HTTP_REQUESTS_TOTAL.labels(
            method=request.method, endpoint=endpoint, status=response.status_code
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(method=request.method, endpoint=endpoint).observe(duration)

        return response

    @app.route("/metrics")
    def metrics():
        if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)
        else:
            # Single-process fallback (dev server, tests) — real
            # numbers, just not aggregated across workers because
            # there's only one process to aggregate.
            from prometheus_client import REGISTRY as registry

        return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)
