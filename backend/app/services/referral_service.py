from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.referral import Referral


class ReferralService:
    def __init__(self, session, referral_repo, application_service, job_repo):
        self.session = session
        self.referral_repo = referral_repo
        self.application_service = application_service
        self.job_repo = job_repo

    def submit_referral(self, tenant_id, referrer_user_id, job_id, email, first_name, last_name, phone=None):
        # The "job must be published" check happens inside apply()
        # itself, so a referral to a draft/closed job fails with the
        # same message a direct apply attempt would — one rule, one
        # place it's enforced.
        application = self.application_service.apply(
            tenant_id, job_id, email, first_name, last_name, phone=phone, source="referral"
        )

        referral = self.referral_repo.model(
            company_id=tenant_id, application_id=application.id, referred_by_user_id=referrer_user_id
        )
        self.referral_repo.add(referral)
        self.referral_repo.commit()
        return referral, application

    def list_my_referrals(self, tenant_id, referrer_user_id):
        rows = (
            self.session.query(Referral, Application, Job, Candidate)
            .join(Application, Application.id == Referral.application_id)
            .join(Job, Job.id == Application.job_id)
            .join(Candidate, Candidate.id == Application.candidate_id)
            .filter(Referral.company_id == tenant_id, Referral.referred_by_user_id == referrer_user_id)
            .order_by(Referral.created_at.desc())
            .all()
        )
        return [
            {"referral": referral, "application": application, "job": job, "candidate": candidate}
            for referral, application, job, candidate in rows
        ]

    def list_open_jobs(self, tenant_id):
        return (
            self.job_repo.list(tenant_id)
            .filter(Job.status == "published")
            .order_by(Job.title)
            .all()
        )
