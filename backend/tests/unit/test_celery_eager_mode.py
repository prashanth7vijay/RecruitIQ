from app import create_app
from app.workers.celery_app import celery_app


def test_task_always_eager_is_active_in_testing_config():
    create_app("testing")  # triggers init_celery() without touching the DB
    assert celery_app.conf.task_always_eager is True


def test_delay_executes_synchronously_in_eager_mode():
    create_app("testing")
    calls = []

    @celery_app.task
    def _record(value):
        calls.append(value)
        return value * 2

    result = _record.delay(21)

    # In eager mode, .delay() has already run the task by the time it
    # returns — calls is populated immediately, no worker needed.
    assert calls == [21]
    assert result.get() == 42
