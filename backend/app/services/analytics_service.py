"""
Deliberate simplification of Phase 19's three-tier design: every
metric here is computed live, on request — no materialized views, no
nightly batch rollups. Genuinely correct today; the real tiering
becomes worth its complexity once dashboard load starts competing
with transactional write traffic, which isn't a problem at this
project's current scale. Swapping a live query for a materialized-view
read later doesn't change any caller — same shape, same service
methods, only the internals move.

Executive Dashboard module adds: hiring velocity, org-wide pipeline
health (by stage_type, not raw stage id — comparable across jobs that
use different pipeline templates), offer acceptance rate, department
breakdown, and named (not raw-UUID) recruiter performance.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from app.models.application import Application, ApplicationStageHistory
from app.models.department import Department
from app.models.job import Job
from app.models.offer import Offer
from app.models.pipeline import PipelineStage
from app.models.user import User

EXECUTIVE_SUMMARY_CACHE_TTL_SECONDS = 60


def _executive_summary_cache_key(tenant_id) -> str:
    return f"analytics:executive_summary:{tenant_id}"


class AnalyticsService:
    def __init__(self, session, cache=None):
        self.session = session
        self.cache = cache  # Flask-Caching Cache instance, or None to disable caching entirely

    def hiring_funnel(self, tenant_id, job_id):
        job = self.session.query(Job).filter_by(id=job_id, company_id=tenant_id).first()
        if job is None or job.pipeline_template_id is None:
            return []

        stages = (
            self.session.query(PipelineStage)
            .filter(PipelineStage.pipeline_template_id == job.pipeline_template_id)
            .order_by(PipelineStage.stage_order)
            .all()
        )

        counts = dict(
            self.session.query(Application.current_stage_id, func.count(Application.id))
            .filter(Application.job_id == job_id, Application.company_id == tenant_id, Application.status == "active")
            .group_by(Application.current_stage_id)
            .all()
        )

        return [
            {"stage_id": str(s.id), "stage_name": s.name, "candidate_count": counts.get(s.id, 0)}
            for s in stages
        ]

    def time_to_hire(self, tenant_id, job_id=None):
        query = (
            self.session.query(
                func.avg(
                    func.extract("epoch", Offer.responded_at - Application.applied_at) / 86400.0
                )
            )
            .join(Application, Application.id == Offer.application_id)
            .filter(Offer.company_id == tenant_id, Offer.status == "accepted")
        )
        if job_id is not None:
            query = query.filter(Application.job_id == job_id)

        avg_days = query.scalar()
        return {"avg_days_to_hire": round(avg_days, 1) if avg_days is not None else None}

    def recruiter_performance(self, tenant_id):
        """
        Named, not raw-UUID (the original version of this method dumped
        job.created_by straight to the frontend, which rendered a
        truncated UUID — not something an executive dashboard should
        show). Adds offers sent and hires alongside the existing
        application-volume count, all keyed by the same recruiter.
        """
        rows = (
            self.session.query(
                Job.created_by,
                User.first_name,
                User.last_name,
                func.count(Application.id.distinct()).label("application_count"),
                func.count(Offer.id.distinct()).label("offers_sent"),
                func.count(Offer.id.distinct()).filter(Offer.status == "accepted").label("hires"),
            )
            .join(User, User.id == Job.created_by)
            .outerjoin(Application, Application.job_id == Job.id)
            .outerjoin(
                Offer,
                (Offer.application_id == Application.id)
                & (Offer.status.in_(["sent", "accepted", "rejected", "expired"])),
            )
            .filter(Job.company_id == tenant_id)
            .group_by(Job.created_by, User.first_name, User.last_name)
            .all()
        )
        return [
            {
                "recruiter_id": str(recruiter_id),
                "recruiter_name": f"{first_name} {last_name}",
                "application_count": application_count,
                "offers_sent": offers_sent,
                "hires": hires,
            }
            for recruiter_id, first_name, last_name, application_count, offers_sent, hires in rows
        ]

    def hiring_velocity(self, tenant_id, days=30):
        """Jobs published and hires made in the trailing window — the
        two counts an exec actually wants at a glance: are we opening
        roles, and are we closing them."""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        jobs_published = (
            self.session.query(func.count(Job.id))
            .filter(
                Job.company_id == tenant_id,
                Job.status.in_(["published", "closed", "archived"]),
                Job.updated_at >= since,
            )
            .scalar()
        )
        hires = (
            self.session.query(func.count(Offer.id))
            .filter(Offer.company_id == tenant_id, Offer.status == "accepted", Offer.responded_at >= since)
            .scalar()
        )
        return {"window_days": days, "jobs_published": jobs_published or 0, "hires": hires or 0}

    def pipeline_health(self, tenant_id):
        """
        Org-wide funnel by stage_type (screening/interview/assessment/
        offer/terminal) — comparable across jobs even though each job's
        pipeline template has its own stage rows, because stage_type is
        the structural, non-customizable dimension (see PipelineStage
        docstring). Also reports average days each active application
        has sat in its CURRENT stage, as a simple staleness signal —
        derived from the most recent ApplicationStageHistory row per
        application, or applied_at if it has never moved.
        """
        counts = dict(
            self.session.query(PipelineStage.stage_type, func.count(Application.id))
            .join(Application, Application.current_stage_id == PipelineStage.id)
            .filter(Application.company_id == tenant_id, Application.status == "active")
            .group_by(PipelineStage.stage_type)
            .all()
        )

        # NOTE: an earlier version of this Phase 2 pass "fixed" this
        # subquery to filter by tenant before aggregating, on the
        # reasoning that aggregating application_stage_history globally
        # wastes work in a real multi-tenant deployment. Measured
        # against a second, independently-sized tenant (not just the
        # single-tenant sandbox), that "fix" was actually SLOWER
        # (137ms vs 89ms) — pre-filtering forces a hash join across
        # both tables, while the existing idx_stage_history_application
        # index (application_id, created_at) lets Postgres satisfy the
        # global MAX()/GROUP BY as a cheap index-only scan regardless
        # of how many tenants' rows are mixed in. Reverted. Left here,
        # not silently dropped, because "the obvious fix was measurably
        # worse, so it was reverted" is a more honest and more useful
        # record than either not mentioning it or keeping a regression
        # to avoid admitting the first instinct was wrong. Full
        # before/after numbers in docs/database-optimization.md.
        latest_move = (
            self.session.query(
                ApplicationStageHistory.application_id,
                func.max(ApplicationStageHistory.created_at).label("moved_at"),
            )
            .group_by(ApplicationStageHistory.application_id)
            .subquery()
        )
        avg_days_in_stage = (
            self.session.query(
                func.avg(
                    func.extract(
                        "epoch",
                        func.now() - func.coalesce(latest_move.c.moved_at, Application.applied_at),
                    )
                    / 86400.0
                )
            )
            .outerjoin(latest_move, latest_move.c.application_id == Application.id)
            .filter(Application.company_id == tenant_id, Application.status == "active")
            .scalar()
        )

        return {
            "by_stage_type": [{"stage_type": k, "candidate_count": v} for k, v in counts.items()],
            "avg_days_in_current_stage": round(avg_days_in_stage, 1) if avg_days_in_stage is not None else None,
        }

    def offer_acceptance_rate(self, tenant_id):
        """Rate among offers that reached a candidate decision —
        'withdrawn' (recruiter pulled it back) is deliberately excluded,
        since that was never the candidate's call to make."""
        rows = dict(
            self.session.query(Offer.status, func.count(Offer.id))
            .filter(Offer.company_id == tenant_id, Offer.status.in_(["accepted", "rejected", "expired"]))
            .group_by(Offer.status)
            .all()
        )
        accepted = rows.get("accepted", 0)
        decided = sum(rows.values())
        return {
            "accepted": accepted,
            "rejected": rows.get("rejected", 0),
            "expired": rows.get("expired", 0),
            "acceptance_rate": round(accepted / decided, 3) if decided > 0 else None,
        }

    def department_hiring(self, tenant_id):
        """Open jobs and hires per department — departments without any
        jobs are omitted rather than shown as zero rows, since an org
        with 20 departments and 2 hiring would otherwise bury the
        signal in empty rows."""
        rows = (
            self.session.query(
                Department.id,
                Department.name,
                func.count(Job.id.distinct()).label("job_count"),
                func.count(Offer.id.distinct()).filter(Offer.status == "accepted").label("hires"),
            )
            .join(Job, Job.department_id == Department.id)
            .outerjoin(Application, Application.job_id == Job.id)
            .outerjoin(Offer, Offer.application_id == Application.id)
            .filter(Department.company_id == tenant_id)
            .group_by(Department.id, Department.name)
            .all()
        )
        return [
            {"department_id": str(dept_id), "department_name": name, "job_count": job_count, "hires": hires}
            for dept_id, name, job_count, hires in rows
        ]

    def executive_summary(self, tenant_id):
        """One call for the dashboard's top-level view — everything
        below is also available individually for drill-down pages.

        Cached (Redis, if self.cache is set) for
        EXECUTIVE_SUMMARY_CACHE_TTL_SECONDS — this is the single most
        expensive analytics call (it runs all five sub-queries below on
        every hit) and the one an exec dashboard is most likely to
        poll repeatedly. Actively invalidated on 'application.
        stage_changed' and 'offer.accepted' (see
        app/workers/analytics_tasks.py) rather than left to expire on
        TTL alone — those two events cover the data this summary
        actually reads (pipeline_health, offer_acceptance_rate,
        time_to_hire, hiring_velocity's hire count). A job being
        published/closed can also change hiring_velocity/
        department_hiring, and isn't actively invalidated — no event
        currently exists for job status changes (see docs/caching.md);
        the 60s TTL is the safety net for that gap, not the primary
        mechanism.

        Returns (summary_dict, meta_dict) — meta_dict says
        {"cache_hit": bool} so the API route can report it without the
        route needing to know about cache keys itself. Every other
        method on this class is unchanged (dict-only return) since
        only this one is cached.
        """
        cache_key = _executive_summary_cache_key(tenant_id)

        if self.cache is not None:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached, {"cache_hit": True}

        summary = {
            "velocity": self.hiring_velocity(tenant_id),
            "pipeline_health": self.pipeline_health(tenant_id),
            "offer_acceptance": self.offer_acceptance_rate(tenant_id),
            "time_to_hire": self.time_to_hire(tenant_id),
            "department_hiring": self.department_hiring(tenant_id),
        }

        if self.cache is not None:
            self.cache.set(cache_key, summary, timeout=EXECUTIVE_SUMMARY_CACHE_TTL_SECONDS)

        return summary, {"cache_hit": False}
