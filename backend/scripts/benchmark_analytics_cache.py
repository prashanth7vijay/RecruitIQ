"""
Analytics-dashboard cache benchmark.

Measures AnalyticsService.executive_summary() latency, with and
without the Redis cache, against whatever company_id you point it at
(defaults to the Phase 2 'bench-100k' dataset — run
scripts/generate_synthetic_data.py first if it doesn't exist yet).

Usage:
    python scripts/benchmark_analytics_cache.py
    python scripts/benchmark_analytics_cache.py --slug bench-noise --requests 100
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import cache as flask_cache, db
from app.services.analytics_service import AnalyticsService, _executive_summary_cache_key
from app.services.ai.ranking_metrics import percentile


def _time_calls(service, tenant_id, n):
    durations = []
    for _ in range(n):
        t0 = time.monotonic()
        service.executive_summary(tenant_id)
        durations.append((time.monotonic() - t0) * 1000)  # ms
    return durations


def main():
    parser = argparse.ArgumentParser(description="Benchmark the analytics executive-summary cache")
    parser.add_argument("--slug", default="bench-100k")
    parser.add_argument("--requests", type=int, default=50, help="Calls per phase")
    args = parser.parse_args()

    flask_app = create_app("development")
    with flask_app.app_context():
        from app.models.company import Company

        company = db.session.query(Company).filter_by(slug=args.slug).first()
        if company is None:
            print(f"No company with slug '{args.slug}' — run scripts/generate_synthetic_data.py first.")
            return
        tenant_id = company.id

        print("=" * 60)
        print("Analytics Dashboard Cache Benchmark")
        print("=" * 60)
        print(f"Company: {args.slug} ({tenant_id})")
        print(f"Requests per phase: {args.requests}\n")

        # --- without cache ---
        service_no_cache = AnalyticsService(db.session, cache=None)
        no_cache_durations = _time_calls(service_no_cache, tenant_id, args.requests)

        # --- with cache: first call is a genuine miss, rest are hits ---
        flask_cache.delete(_executive_summary_cache_key(tenant_id))
        service_cached = AnalyticsService(db.session, cache=flask_cache)

        t0 = time.monotonic()
        _, miss_meta = service_cached.executive_summary(tenant_id)
        miss_duration_ms = (time.monotonic() - t0) * 1000
        assert miss_meta["cache_hit"] is False

        hit_durations = []
        for _ in range(args.requests - 1):
            t0 = time.monotonic()
            _, meta = service_cached.executive_summary(tenant_id)
            hit_durations.append((time.monotonic() - t0) * 1000)
            assert meta["cache_hit"] is True

        print("Without cache (every call recomputes):")
        print(f"  p50: {round(percentile(no_cache_durations, 50), 2)} ms")
        print(f"  p95: {round(percentile(no_cache_durations, 95), 2)} ms")
        print(f"  p99: {round(percentile(no_cache_durations, 99), 2)} ms")

        print(f"\nWith cache (1 miss + {args.requests - 1} hits):")
        print(f"  first call (miss):  {round(miss_duration_ms, 2)} ms")
        print(f"  hit p50: {round(percentile(hit_durations, 50), 2)} ms")
        print(f"  hit p95: {round(percentile(hit_durations, 95), 2)} ms")
        print(f"  hit p99: {round(percentile(hit_durations, 99), 2)} ms")

        no_cache_p50 = percentile(no_cache_durations, 50)
        hit_p50 = percentile(hit_durations, 50)
        improvement = round(100 * (1 - hit_p50 / no_cache_p50), 1) if no_cache_p50 > 0 else 0.0
        print(f"\np50 latency improvement (cache hit vs. no cache): {improvement}%")
        print(f"Database calls avoided per hit: 5 (hiring_velocity, pipeline_health, "
              f"offer_acceptance_rate, time_to_hire, department_hiring)")


if __name__ == "__main__":
    main()
