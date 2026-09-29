"""
EventBus — the concrete implementation of Phase 7.8's decoupling
decision. Services publish a named event with a payload dict and know
nothing about who's listening; subscribers are wired here, once, at
import time (lazy imports inside _subscribers() avoid circular
imports between workers and services).
"""


def _subscribers():
    from app.workers.resume_tasks import parse_resume_task
    from app.workers.notification_tasks import (
        notify_stage_change_task,
        notify_interview_scheduled_task,
        trigger_onboarding_task,
    )
    from app.workers.analytics_tasks import invalidate_analytics_cache_task

    return {
        "resume.uploaded": [parse_resume_task],
        "application.stage_changed": [notify_stage_change_task, invalidate_analytics_cache_task],
        "interview.scheduled": [notify_interview_scheduled_task],
        "offer.accepted": [trigger_onboarding_task, invalidate_analytics_cache_task],
    }


class EventBus:
    def publish(self, event_name: str, payload: dict) -> None:
        for task in _subscribers().get(event_name, []):
            task.delay(payload)
