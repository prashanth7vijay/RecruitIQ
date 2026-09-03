from app.exceptions.base import BusinessRuleViolationError, ConflictError
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.referral import Referral


class ReferralService:
    def __init__(
        self,
        session,
        referral_repo,
        job_repo,
        candidate_service=None,
        notification_service=None,
        user_repo=None,
        company=None,
    ):
        self.session = session
        self.referral_repo = referral_repo
        self.job_repo = job_repo
        self.candidate_service = candidate_service
        self.notification_service = notification_service
        self.user_repo = user_repo
        self.company = company

    def submit_referral(self, tenant_id, referrer_user_id, job_id, email):
        job = self.job_repo.get_or_404(job_id, tenant_id)
        if job.status != "published":
            raise BusinessRuleViolationError("This job is not currently accepting applications")

        candidate = self.candidate_service.find_or_create_identity(email)

        if self.referral_repo.get_by_job_and_candidate(tenant_id, job_id, candidate.id) is not None:
            raise ConflictError("This person has already been referred for this job")

        referral = self.referral_repo.model(
            company_id=tenant_id,
            job_id=job_id,
            candidate_id=candidate.id,
            application_id=None,
            referred_by_user_id=referrer_user_id,
        )
        self.referral_repo.add(referral)
        self.referral_repo.commit()

        if self.notification_service is not None:
            referrer_name = None
            if self.user_repo is not None:
                referrer = self.user_repo.get(referrer_user_id, tenant_id)
                if referrer is not None:
                    referrer_name = f"{referrer.first_name} {referrer.last_name}"
            self.notification_service.notify(
                tenant_id,
                "referral_received",
                payload={
                    "job_id": str(job_id),
                    "job_title": job.title,
                    "company_name": self.company.name if self.company else None,
                    "company_slug": self.company.slug if self.company else None,
                    "referrer_name": referrer_name,
                },
                candidate_id=candidate.id,
                channels=["in_app"],
            )

        return referral

    def list_my_referrals(self, tenant_id, referrer_user_id):
        rows = (
            self.session.query(Referral, Job, Candidate, Application)
            .join(Job, Job.id == Referral.job_id)
            .join(Candidate, Candidate.id == Referral.candidate_id)
            .outerjoin(Application, Application.id == Referral.application_id)
            .filter(Referral.company_id == tenant_id, Referral.referred_by_user_id == referrer_user_id)
            .order_by(Referral.created_at.desc())
            .all()
        )
        return [
            {"referral": referral, "job": job, "candidate": candidate, "application": application}
            for referral, job, candidate, application in rows
        ]

    def list_open_jobs(self, tenant_id):
        return (
            self.job_repo.list(tenant_id)
            .filter(Job.status == "published")
            .order_by(Job.title)
            .all()
        )