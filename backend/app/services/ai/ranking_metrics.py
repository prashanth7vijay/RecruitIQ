"""
Instrumentation for the candidate ranking pipeline.

RankingRunMetrics is produced once per rank_candidates_for_job() call
and returned alongside the ranked applications (see MatchScoreService).
It's what the /ai/jobs/:id/rank-candidates response's `meta` and the
benchmark script (scripts/benchmark_ranking.py) both read from — one
struct, two consumers, so the numbers a real API caller sees and the
numbers the benchmark report prints can never quietly drift apart.

percentile() is a plain, dependency-free implementation (no numpy) —
this project doesn't otherwise depend on a numeric library, and a
single sorted-list nearest-rank percentile is all p50/p95/p99 need.
"""

import math
from dataclasses import dataclass, field, asdict


@dataclass
class RankingRunMetrics:
    job_id: str
    candidates_considered: int = 0
    candidates_filtered_out: int = 0
    candidates_scored: int = 0
    ai_calls_made: int = 0
    ai_calls_cached: int = 0
    duration_seconds: float = 0.0

    @property
    def candidates_passed_filter(self) -> int:
        return self.candidates_considered - self.candidates_filtered_out

    @property
    def candidates_per_second(self) -> float:
        if self.duration_seconds <= 0:
            return 0.0
        return round(self.candidates_considered / self.duration_seconds, 2)

    @property
    def cache_hit_rate(self) -> float:
        total = self.ai_calls_made + self.ai_calls_cached
        if total == 0:
            return 0.0
        return round(self.ai_calls_cached / total, 3)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["candidates_passed_filter"] = self.candidates_passed_filter
        d["candidates_per_second"] = self.candidates_per_second
        d["cache_hit_rate"] = self.cache_hit_rate
        return d


def percentile(values: list, pct: float) -> float:
    """Nearest-rank percentile over a list of durations (seconds or ms —
    caller's choice of unit, this doesn't care). pct is 0-100.
    Returns 0.0 for an empty input rather than raising, since a
    benchmark run with zero samples of some category (e.g. zero cache
    hits) is a real, reportable state, not an error."""
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = math.ceil((pct / 100) * len(ordered))
    rank = min(max(rank, 1), len(ordered))
    return ordered[rank - 1]
