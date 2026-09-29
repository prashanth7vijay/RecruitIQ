from app.observability import (
    CANDIDATE_RANKING_CANDIDATES_TOTAL,
    DASHBOARD_CACHE_HITS_TOTAL,
    record_dashboard_cache,
    record_ranking_metrics,
)
from app.services.ai.ranking_metrics import RankingRunMetrics


def test_health_reports_ok_when_dependencies_up(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["cache"] == "ok"


def test_metrics_endpoint_exposes_prometheus_text_format(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"http_requests_total" in response.data


def test_metrics_endpoint_reflects_http_requests(client):
    client.get("/health")
    response = client.get("/metrics")
    assert b'endpoint="health"' in response.data or b"health" in response.data


def test_record_ranking_metrics_increments_counters():
    before = CANDIDATE_RANKING_CANDIDATES_TOTAL._value.get()
    metrics = RankingRunMetrics(job_id="x", candidates_considered=7, ai_calls_made=2, ai_calls_cached=5)
    record_ranking_metrics(metrics)
    after = CANDIDATE_RANKING_CANDIDATES_TOTAL._value.get()
    assert after == before + 7


def test_record_dashboard_cache_increments_hit_counter():
    before = DASHBOARD_CACHE_HITS_TOTAL._value.get()
    record_dashboard_cache(True)
    after = DASHBOARD_CACHE_HITS_TOTAL._value.get()
    assert after == before + 1
