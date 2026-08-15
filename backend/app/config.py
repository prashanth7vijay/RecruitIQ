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

    STORAGE_BACKEND = "local"
    LOCAL_STORAGE_PATH = "/data/uploads"
    EMAIL_PROVIDER = "console"

    AI_PROVIDER = os.environ.get("AI_PROVIDER", "stub")
    OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")

    MAX_UPLOAD_SIZE_MB = 15
    LOGIN_LOCKOUT_THRESHOLD = 5
    LOGIN_LOCKOUT_DURATION_MINUTES = 15
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key-do-not-use-in-prod")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-only-insecure-jwt-key")


class DevelopmentConfig(Config):
    ENV_NAME = "development"
    DEBUG = True
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
    RATELIMIT_ENABLED = False
    AI_PROVIDER = "stub"
    CELERY_TASK_ALWAYS_EAGER = True


class ProductionConfig(Config):
    ENV_NAME = "production"
    DEBUG = False
    STORAGE_BACKEND = "s3"
    EMAIL_PROVIDER = "ses"


REQUIRED_PRODUCTION_ENV_VARS = ("SECRET_KEY", "JWT_SECRET_KEY")

config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
