"""
Load test for RecruitIQ's API — realistic weighted endpoint mix, not
hammering one endpoint. Run against a real gunicorn server (see
docs/scalability.md for the exact command), pointed at the Phase 2
`bench-100k` dataset so every request is doing real work against
100K+ rows, not an empty table.

All simulated users share ONE JWT, fetched once via a real /auth/login
call before Locust starts (see docs/scalability.md) — logging in per
simulated user would immediately hit /auth/login's own 10-per-minute
rate limit and measure the rate limiter, not the backend. A real
client caches its token the same way; this isn't cutting a corner
load tests shouldn't take.

Usage (see docs/scalability.md for the full sequence):
    export LOAD_TEST_TOKEN=<jwt>
    export LOAD_TEST_BASE_URL=http://127.0.0.1:5000
    locust -f loadtest/locustfile.py --headless -u 50 -r 10 -t 30s \
        --host $LOAD_TEST_BASE_URL --csv=loadtest/results_50u
"""

import os
import random

from locust import HttpUser, task, between

TOKEN = os.environ.get("LOAD_TEST_TOKEN", "")
SEARCH_TERMS = ["jordan", "priya", "wei", "avery", "zzznotfound", "example.com"]


class RecruiterUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self):
        self.client.headers.update({"Authorization": f"Bearer {TOKEN}"})

    # Weighted to approximate real traffic: browsing/searching
    # candidates is the most frequent action, the dashboard is loaded
    # often but not on every click, and ranking a job's applicant pool
    # is comparatively rare and expensive.
    @task(35)
    def search_candidates(self):
        term = random.choice(SEARCH_TERMS)
        self.client.get(f"/api/v1/search?q={term}", name="/search?q=[term]")

    @task(25)
    def list_candidates(self):
        page = random.randint(1, 50)
        self.client.get(f"/api/v1/candidates?page={page}&per_page=20", name="/candidates?page=[n]")

    @task(20)
    def list_jobs(self):
        self.client.get("/api/v1/jobs", name="/jobs")

    @task(15)
    def executive_summary(self):
        self.client.get("/api/v1/analytics/executive-summary", name="/analytics/executive-summary")

    @task(5)
    def pipeline_health(self):
        self.client.get("/api/v1/analytics/pipeline-health", name="/analytics/pipeline-health")
