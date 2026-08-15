import os

from app import create_app
from app.workers.celery_app import celery_app, init_celery

flask_app = create_app(os.environ.get("FLASK_ENV", "development"))
init_celery(flask_app)

import app.workers.resume_tasks  # noqa: F401,E402
import app.workers.email_tasks  # noqa: F401,E402
import app.workers.notification_tasks  # noqa: F401,E402
