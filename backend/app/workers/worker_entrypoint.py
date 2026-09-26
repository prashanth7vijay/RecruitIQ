"""
Entrypoint for the standalone Celery worker process (see infra/docker-compose.yml's
`worker` service: `celery -A app.workers.worker_entrypoint.celery_app worker ...`).

Why this file exists rather than pointing the worker CLI directly at
app/workers/celery_app.py: that module only defines a bare, unconfigured
Celery() instance — broker_url, result_backend, and task_always_eager
are all applied by init_celery(app), which is normally called inside
create_app() for the web process. A standalone worker process never
calls create_app(), so without this entrypoint it would start consuming
with default (broker-less) config and silently fail to connect to Redis.
"""

import os

from app import create_app
from app.workers.celery_app import celery_app, init_celery

flask_app = create_app(os.environ.get("FLASK_ENV", "development"))
init_celery(flask_app)

# Import task modules so Celery's worker registers them — tasks are
# otherwise only imported lazily (inside EventBus._subscribers or
# service methods), which is fine for the web process but the worker
# process needs them registered at startup to consume their queues.
import app.workers.resume_tasks  # noqa: F401,E402
import app.workers.email_tasks  # noqa: F401,E402
import app.workers.notification_tasks  # noqa: F401,E402
import app.workers.ranking_tasks  # noqa: F401,E402
import app.workers.analytics_tasks  # noqa: F401,E402
