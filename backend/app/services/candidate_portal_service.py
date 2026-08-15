from app.exceptions.base import NotFoundError, PermissionDeniedError
from app.models.application import Application
from app.models.company import Company
from app.models.interview import Interview
from app.models.job import Job
from app.models.offer import Offer
from app.models.pipeline import PipelineStage


class CandidatePortalService:
    def __init__(self, session, offer_service):
        self.session = session
        # OfferService is still the one place accept/decline business
        # logic (state transitions, auto-triggering onboarding) lives —
        # this service only adds the candidate-ownership check in front
        # of it, rather than duplicating that logic.
        self.offer_service = offer_service

    def get_candidate(self, candidate_id):
        from app.models.candidate import Candidate

        candidate = self.session.query(Candidate).filter(Candidate.id == candidate_id).first()
        if candidate is None:
            raise NotFoundError("Candidate not found")
        return candidate

    def list_my_applications(self, candidate_id):
        rows = (
            self.session.query(Application, Job, Company, PipelineStage)
            .join(Job, Job.id == Application.job_id)
            .join(Company, Company.id == Application.company_id)
            .outerjoin(PipelineStage, PipelineStage.id == Application.current_stage_id)
            .filter(Application.candidate_id == candidate_id)
            .order_by(Application.applied_at.desc())
            .all()
        )
        return [
            {"application": app, "job": job, "company": company, "stage": stage}
            for app, job, company, stage in rows
        ]

    def get_my_application(self, candidate_id, application_id):
        application = self._owned_application(candidate_id, application_id)
        job = self.session.query(Job).filter(Job.id == application.job_id).first()
        company = self.session.query(Company).filter(Company.id == application.company_id).first()
        stage = (
            self.session.query(PipelineStage)
            .filter(PipelineStage.id == application.current_stage_id)
            .first()
        )
        return {"application": application, "job": job, "company": company, "stage": stage}

    def list_my_interviews(self, candidate_id, application_id):
        self._owned_application(candidate_id, application_id)  # ownership check, result unused
        return (
            self.session.query(Interview)
            .filter(Interview.application_id == application_id)
            .order_by(Interview.scheduled_at)
            .all()
        )

    def list_my_offers(self, candidate_id):
        rows = (
            self.session.query(Offer, Job, Company)
            .join(Application, Application.id == Offer.application_id)
            .join(Job, Job.id == Application.job_id)
            .join(Company, Company.id == Offer.company_id)
            .filter(Application.candidate_id == candidate_id)
            .filter(Offer.status.in_(["sent", "accepted", "rejected"]))
            .order_by(Offer.created_at.desc())
            .all()
        )
        return [{"offer": offer, "job": job, "company": company} for offer, job, company in rows]

    def accept_my_offer(self, candidate_id, offer_id):
        offer = self._owned_offer(candidate_id, offer_id)
        return self.offer_service.accept(offer.company_id, offer_id, acted_by=None)

    def decline_my_offer(self, candidate_id, offer_id):
        offer = self._owned_offer(candidate_id, offer_id)
        return self.offer_service.decline(offer.company_id, offer_id, acted_by=None)

    # --- internal ---------------------------------------------------

    def _owned_application(self, candidate_id, application_id):
        application = self.session.query(Application).filter(Application.id == application_id).first()
        if application is None:
            raise NotFoundError("Application not found")
        if str(application.candidate_id) != str(candidate_id):
            # 404, not 403 — same reasoning as TenantScopedRepository:
            # confirming "this application exists but isn't yours" leaks
            # more than a plain not-found does.
            raise NotFoundError("Application not found")
        return application

    def _owned_offer(self, candidate_id, offer_id):
        offer = self.session.query(Offer).filter(Offer.id == offer_id).first()
        if offer is None:
            raise NotFoundError("Offer not found")
        application = (
            self.session.query(Application).filter(Application.id == offer.application_id).first()
        )
        if application is None or str(application.candidate_id) != str(candidate_id):
            raise NotFoundError("Offer not found")
        return offer
