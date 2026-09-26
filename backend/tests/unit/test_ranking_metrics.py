from app.services.ai.ranking_metrics import RankingRunMetrics, percentile


def test_candidates_passed_filter_is_considered_minus_filtered():
    m = RankingRunMetrics(job_id="j1", candidates_considered=10, candidates_filtered_out=3)
    assert m.candidates_passed_filter == 7


def test_candidates_per_second_zero_when_no_duration():
    m = RankingRunMetrics(job_id="j1", candidates_considered=100, duration_seconds=0)
    assert m.candidates_per_second == 0.0


def test_candidates_per_second_computed():
    m = RankingRunMetrics(job_id="j1", candidates_considered=100, duration_seconds=10)
    assert m.candidates_per_second == 10.0


def test_cache_hit_rate_zero_when_no_ai_activity():
    m = RankingRunMetrics(job_id="j1")
    assert m.cache_hit_rate == 0.0


def test_cache_hit_rate_computed():
    m = RankingRunMetrics(job_id="j1", ai_calls_made=3, ai_calls_cached=7)
    assert m.cache_hit_rate == 0.7


def test_to_dict_includes_derived_fields():
    m = RankingRunMetrics(job_id="j1", candidates_considered=5, ai_calls_made=1, ai_calls_cached=1, duration_seconds=2)
    d = m.to_dict()
    assert d["job_id"] == "j1"
    assert "candidates_passed_filter" in d
    assert "candidates_per_second" in d
    assert "cache_hit_rate" in d


def test_percentile_empty_returns_zero():
    assert percentile([], 95) == 0.0


def test_percentile_single_value():
    assert percentile([42], 50) == 42


def test_percentile_p50_and_p99():
    values = list(range(1, 101))  # 1..100
    assert percentile(values, 50) == 50
    assert percentile(values, 99) == 99
    assert percentile(values, 100) == 100
