from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from app.models.application import Application, ApplicationStageHistory
from app.models.department import Department
from app.models.job import Job
from app.models.offer import Offer
from app.models.pipeline import PipelineStage
from app.models.user import User


class AnalyticsService:
    def __init__(self, session):
        self.session = session

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
    
        counts = dict(
            self.session.query(PipelineStage.stage_type, func.count(Application.id))
            .join(Application, Application.current_stage_id == PipelineStage.id)
            .filter(Application.company_id == tenant_id, Application.status == "active")
            .group_by(PipelineStage.stage_type)
            .all()
        )

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
    
        return {
            "velocity": self.hiring_velocity(tenant_id),
            "pipeline_health": self.pipeline_health(tenant_id),
            "offer_acceptance": self.offer_acceptance_rate(tenant_id),
            "time_to_hire": self.time_to_hire(tenant_id),
            "department_hiring": self.department_hiring(tenant_id),
        }
