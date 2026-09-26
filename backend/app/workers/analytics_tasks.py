"""
Analytics cache invalidation.

Subscriber for 'application.stage_changed' and 'offer.accepted' — the
two events that change data executive_summary() actually reads
(pipeline_health via stage changes; offer_acceptance_rate/time_to_hire/
hiring_velocity's hire count via offer acceptance). Deletes the cached
executive_summary entry for that event's tenant so the next dashboard
load recomputes it, rather than waiting out the TTL.

Neither event payload carries company_id directly (see
notify_stage_change_task's docstring for the same pattern) — this
looks it up the same way, via the application/offer row itself.

Job status changes (published/closed) can also change
hiring_velocity/department_hiring, but no event currently exists for
that — the 60s TTL is what covers that gap, not active invalidation.
Documented, not silently missing.
"""

from app.extensions import cache, db
from app.services.analytics_service import _executive_summary_cache_key
from app.workers.celery_app import celery_app


@celery_app.task
def invalidate_analytics_cache_task(payload):
    from app.models.application import Application
    from app.models.offer import Offer

    company_id = None

    if "offer_id" in payload:
        offer = db.session.query(Offer).filter_by(id=payload["offer_id"]).first()
        if offer is not None:
            company_id = offer.company_id
    elif "application_id" in payload:
        application = db.session.query(Application).filter_by(id=payload["application_id"]).first()
        if application is not None:
            company_id = application.company_id

    if company_id is not None:
        cache.delete(_executive_summary_cache_key(company_id))
