from dotenv import load_dotenv
from flask import Flask
from app.observability import register_metrics
load_dotenv()

from app.config import config_map, REQUIRED_PRODUCTION_ENV_VARS
from app.extensions import db, migrate, jwt, cache, limiter
from app.exceptions.handlers import register_error_handlers
from app.middleware.tenant_context import register_middleware
from app.observability import register_metrics


def create_app(config_name: str = "development") -> Flask:
    if config_name == "production":
        _assert_production_secrets_present()

    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    _init_extensions(app)
    _register_blueprints(app)
    register_metrics(app)
    register_error_handlers(app)
    register_middleware(app)

    return app


def _assert_production_secrets_present() -> None:
    import os

    missing = [var for var in REQUIRED_PRODUCTION_ENV_VARS if not os.environ.get(var)]
    if missing:
        raise RuntimeError(
            f"Refusing to start in production without required env vars: {', '.join(missing)}"
        )


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)

    from app.workers.celery_app import init_celery
    init_celery(app)

    # Import models only after db.init_app so they bind to this app's
    # SQLAlchemy instance â€” required for Flask-Migrate autogenerate.
    with app.app_context():
        import app.models  # noqa: F401


def _register_blueprints(app: Flask) -> None:
    from app.api.v1.auth.routes import auth_bp
    from app.api.v1.companies.routes import companies_bp
    from app.api.v1.org.routes import org_bp
    from app.api.v1.jobs.routes import jobs_bp
    from app.api.v1.jobs.pipeline_routes import pipeline_templates_bp
    from app.api.v1.candidates.routes import candidates_bp
    from app.api.v1.applications.routes import applications_bp
    from app.api.v1.public.routes import public_bp
    from app.api.v1.files.routes import files_bp
    from app.api.v1.notifications.routes import notifications_bp
    from app.api.v1.interviews.routes import interviews_bp
    from app.api.v1.offers.routes import offers_bp
    from app.api.v1.onboarding.routes import onboarding_bp
    from app.api.v1.ai.routes import ai_bp
    from app.api.v1.users.routes import users_bp
    from app.api.v1.talent_pools.routes import talent_pools_bp
    from app.api.v1.search.routes import search_bp
    from app.api.v1.analytics.routes import analytics_bp
    from app.api.v1.admin.routes import admin_bp
    from app.api.v1.roles.routes import roles_bp
    from app.api.v1.approval_chains.routes import approval_chains_bp
    from app.api.v1.candidate_auth.routes import candidate_auth_bp
    from app.api.v1.candidate_portal.routes import candidate_portal_bp
    from app.api.v1.employee_portal.routes import employee_portal_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(companies_bp)
    app.register_blueprint(org_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(pipeline_templates_bp)
    app.register_blueprint(candidates_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(interviews_bp)
    app.register_blueprint(offers_bp)
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(talent_pools_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(roles_bp)
    app.register_blueprint(approval_chains_bp)
    app.register_blueprint(candidate_auth_bp)
    app.register_blueprint(candidate_portal_bp)
    app.register_blueprint(employee_portal_bp)
    
    @app.route("/health")
    def health():
        # Was `return {"status": "ok"}, 200` unconditionally — didn't
        # actually check anything, so it couldn't detect the exact
        # failure modes Section 21 names (Redis unavailable, Postgres
        # temporarily unreachable). A health check a load balancer uses
        # to decide whether to route traffic here needs to know that.
        checks = {}

        try:
            db.session.execute(db.text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as exc:  # noqa: BLE001 — any DB failure means unhealthy, not a crash
            checks["database"] = f"error: {exc.__class__.__name__}"

        try:
            cache.get("__health_check__")
            checks["cache"] = "ok"
        except Exception as exc:  # noqa: BLE001
            checks["cache"] = f"error: {exc.__class__.__name__}"

        healthy = all(v == "ok" for v in checks.values())
        return {"status": "ok" if healthy else "degraded", "checks": checks}, (200 if healthy else 503)

    @app.cli.command("seed-roles")
    def seed_roles():
        """flask seed-roles â€” inserts/updates system-default roles & permissions."""
        from app.seeds.system_roles import run

        run()

