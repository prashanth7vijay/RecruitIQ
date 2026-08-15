from celery import Celery

celery_app = Celery("recruitiq")

celery_app.conf.task_routes = {
    "app.workers.email_tasks.*": {"queue": "critical"},
    "app.workers.resume_tasks.*": {"queue": "cpu_intensive"},
    "app.workers.notification_tasks.*": {"queue": "default"},
}


def init_celery(app):
    celery_app.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        task_always_eager=app.config.get("CELERY_TASK_ALWAYS_EAGER", False),
    )

    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app
