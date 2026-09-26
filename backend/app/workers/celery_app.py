"""
Celery app, configured with the queue-separation topology from Phase
15.1: critical (transactional email) never waits behind cpu_intensive
(resume parsing), which never competes with default (automation
dispatch) or batch (reports/analytics).

celery.conf.update(app.config) in the app factory pulls
CELERY_BROKER_URL / CELERY_RESULT_BACKEND from Flask config, so a
single source of truth (Config classes) drives both Flask and Celery.
"""

from celery import Celery

celery_app = Celery("recruitiq")

celery_app.conf.task_routes = {
    "app.workers.email_tasks.*": {"queue": "critical"},
    "app.workers.resume_tasks.*": {"queue": "cpu_intensive"},
    "app.workers.notification_tasks.*": {"queue": "default"},
    "app.workers.analytics_tasks.*": {"queue": "default"},
    # Bulk/report-shaped work (scoring a whole applicant pool) — routed
    # to 'batch' so it never competes with critical email or resume
    # parsing for worker capacity, matching the Phase 15.1 topology.
    "app.workers.ranking_tasks.*": {"queue": "batch"},
}


def init_celery(app):
    eager = app.config.get("CELERY_TASK_ALWAYS_EAGER", False)
    celery_app.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        task_always_eager=eager,
        # Needed for any job-status-polling pattern (see ranking_tasks.py
        # + GET /ai/ranking-jobs/<id>) to work under eager mode: Celery
        # doesn't persist a result to the backend for an eagerly-run task
        # unless this is set, even though the AsyncResult it hands back
        # already has the return value in memory. Only relevant when
        # eager is already on (tests), so this changes nothing in a real
        # broker-backed deployment.
        task_store_eager_result=eager,
    )

    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app
