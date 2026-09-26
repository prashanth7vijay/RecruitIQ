"""
Environment-specific configuration.

ProductionConfig reads secrets via os.environ.get(...) with no
hardcoded fallback — but the actual fail-fast enforcement (crash the
process if a required secret is missing) happens in create_app() at
the point ProductionConfig is selected, not in this module at import
time. Doing it here at class-body level would make merely IMPORTING
this file crash outside of production, which broke dev/test entirely
during Sprint 1 testing — see Phase 24 build log. Keep the check in
create_app().
"""

import os
from datetime import timedelta


class Config:
    ENV_NAME = "base"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://recruitiq:recruitiq@postgres:5432/recruitiq"
    )

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_REFRESH_TOKEN_EXPIRES_REMEMBER_ME = timedelta(days=90)

    REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL

    # Flask-Caching was wired into the app factory (see extensions.py)
    # but never actually given a real backend — CACHE_TYPE defaulted to
    # Flask-Caching's own "null" backend, so every cache.get()/cache.set()
    # call silently no-op'd everywhere in the codebase. Redis is already
    # a hard dependency (Celery broker) so it's the obvious backend here
    # too, per Rule 10 (prefer existing infra before adding a new piece).
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300

    # Same problem, same fix, found in Phase 5: Flask-Limiter is
    # enabled by default (see extensions.py) with no storage URI
    # configured, which makes it silently fall back to in-memory
    # counters (Flask-Limiter's own warning: "Using the in-memory
    # storage... not recommended for production use" — visible in this
    # project's own test output). In-memory means each gunicorn worker,
    # let alone each horizontally-scaled container, enforces its own
    # independent rate limit — a client effectively gets
    # (limit x workers x replicas) requests through, not the configured
    # limit. Redis-backed makes the limit real across every process
    # sharing this REDIS_URL.
    RATELIMIT_STORAGE_URI = REDIS_URL

    # Env-overridable (not just a hardcoded per-class value like the
    # rest of this file) specifically so load testing can toggle it
    # off to measure raw backend/DB capacity separately from the
    # rate limiter's own effect — see docs/scalability.md. Defaults to
    # enabled everywhere, same as before this existed.
    RATELIMIT_ENABLED = os.environ.get("RATELIMIT_ENABLED", "true").lower() == "true"

    STORAGE_BACKEND = "local"
    LOCAL_STORAGE_PATH = "/data/uploads"
    EMAIL_PROVIDER = "console"

    # AI provider: 'ollama' (local Llama via a locally-running Ollama
    # server, free, no API key) or 'stub' (deterministic, no network
    # call at all — what actually runs in CI/this test suite, since no
    # Ollama server is available there). No paid cloud AI provider is
    # used anywhere in this project. See app/services/ai/ai_client.py.
    AI_PROVIDER = os.environ.get("AI_PROVIDER", "stub")
    OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")

    MAX_UPLOAD_SIZE_MB = 15
    LOGIN_LOCKOUT_THRESHOLD = 5
    LOGIN_LOCKOUT_DURATION_MINUTES = 15

    # Required in production; harmless placeholders elsewhere so that
    # importing/using Dev or Testing config never needs real secrets.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key-do-not-use-in-prod")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-only-insecure-jwt-key")


class DevelopmentConfig(Config):
    ENV_NAME = "development"
    DEBUG = True
    # Local dev defaults to Ollama so the AI Assist layer works out of
    # the box against `ollama serve` with no API key of any kind —
    # override via the AI_PROVIDER env var if you'd rather run stub.
    AI_PROVIDER = os.environ.get("AI_PROVIDER", "ollama")


class TestingConfig(Config):
    ENV_NAME = "testing"
    TESTING = True
    SECRET_KEY = "test-secret-key"
    JWT_SECRET_KEY = "test-jwt-secret-key"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL", "postgresql://recruitiq:recruitiq@postgres:5432/recruitiq_test"
    )
    STORAGE_BACKEND = "local"
    LOCAL_STORAGE_PATH = "/tmp/recruitiq-test-uploads"
    EMAIL_PROVIDER = "console"
    # Flask-Limiter's in-memory store persists for the whole pytest
    # session (it's not reset per test), and most integration tests log
    # in at least once via the auth_client fixture — a full run comfortably
    # exceeds login's 10/minute production limit and starts getting 429'd
    # instead of a real token. Rate limiting itself isn't what these tests
    # are for; that's exercised separately wherever a test asserts on 429s.
    RATELIMIT_ENABLED = False
    # SimpleCache (in-process dict), not RedisCache — tests shouldn't
    # depend on a Redis server being reachable, and the app fixture is
    # session-scoped (one Flask app for the whole pytest run per
    # tests/conftest.py), so a SimpleCache instance is shared the same
    # way a real backend would be across requests within one process,
    # without needing to flush anything between tests.
    CACHE_TYPE = "SimpleCache"
    # Always stub in tests — deterministic, no network call, and
    # doesn't depend on a local Ollama server being installed/running
    # wherever the test suite executes.
    AI_PROVIDER = "stub"
    # Runs Celery tasks synchronously, in-process — lets task logic be
    # genuinely executed and tested without a live Redis broker/worker.
    CELERY_TASK_ALWAYS_EAGER = True


class ProductionConfig(Config):
    ENV_NAME = "production"
    DEBUG = False
    STORAGE_BACKEND = "s3"
    EMAIL_PROVIDER = "ses"
    # AI_PROVIDER inherited from Config (env-driven, defaults to
    # 'stub'). Ollama is a local-dev tool by nature — a real production
    # deployment wanting AI features would either run its own Ollama
    # host and set AI_PROVIDER=ollama + OLLAMA_BASE_URL to reach it, or
    # a future cloud provider could be added to ai_client.py without
    # touching this file.
    # SECRET_KEY / JWT_SECRET_KEY inherited from Config's os.environ.get()
    # calls above; create_app() validates these are non-default before
    # allowing a production boot to proceed (see REQUIRED_PRODUCTION_ENV_VARS).


REQUIRED_PRODUCTION_ENV_VARS = ("SECRET_KEY", "JWT_SECRET_KEY")

config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
