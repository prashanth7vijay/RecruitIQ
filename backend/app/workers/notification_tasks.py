from app.extensions import db
from app.workers.celery_app import celery_app


@celery_app.task
def dispatch_in_app_notification_task(notification_id):
    from app.models.notification import Notification

    notification = db.session.query(Notification).filter_by(id=notification_id).first()
    if notification is None:
        return
    # No-op today beyond existence — see docstring.


@celery_app.task
def trigger_onboarding_task(payload):
    from app.repositories.onboarding_repository import OnboardingRepository
    from app.services.onboarding_service import OnboardingService

    service = OnboardingService(OnboardingRepository(db.session))
    service.create_for_application(payload["application_id"])


@celery_app.task
def notify_interview_scheduled_task(payload):
    from app.models.interview import Interview
    from app.models.application import Application
    from app.models.job import Job
    from app.models.candidate import Candidate
    from app.repositories.notification_repository import NotificationRepository
    from app.services.notification_service import NotificationService

    interview = db.session.query(Interview).filter_by(id=payload["interview_id"]).first()
    if interview is None:
        return

    application = db.session.query(Application).filter_by(id=interview.application_id).first()
    job = db.session.query(Job).filter_by(id=application.job_id).first() if application else None
    candidate = db.session.query(Candidate).filter_by(id=application.candidate_id).first() if application else None

    notification_service = NotificationService(NotificationRepository(db.session))

    if job is not None:
        for panelist in interview.panelists:
            notification_service.notify(
                tenant_id=interview.company_id,
                notification_type="interview_scheduled",
                payload={"job_title": job.title, "round_name": interview.round_name, "candidate_name": candidate.full_name if candidate else ""},
                user_id=panelist.user_id,
                channels=["in_app"],
            )

    if candidate is not None and job is not None:
        notification_service.notify(
            tenant_id=interview.company_id,
            notification_type="interview_scheduled",
            payload={"first_name": candidate.first_name, "job_title": job.title, "round_name": interview.round_name},
            candidate_id=candidate.id,
            channels=["email"],
        )


@celery_app.task
def notify_stage_change_task(payload):
    from app.models.application import Application
    from app.models.job import Job
    from app.models.pipeline import PipelineStage
    from app.models.candidate import Candidate
    from app.repositories.notification_repository import NotificationRepository
    from app.services.notification_service import NotificationService

    application = db.session.query(Application).filter_by(id=payload["application_id"]).first()
    if application is None:
        return

    job = db.session.query(Job).filter_by(id=application.job_id).first()
    stage = db.session.query(PipelineStage).filter_by(id=payload["to_stage_id"]).first()
    candidate = db.session.query(Candidate).filter_by(id=application.candidate_id).first()

    notification_service = NotificationService(NotificationRepository(db.session))

    if job is not None and stage is not None:
        notification_service.notify(
            tenant_id=application.company_id,
            notification_type="application_stage_changed",
            payload={"job_title": job.title, "stage_name": stage.name, "candidate_name": candidate.full_name if candidate else ""},
            user_id=job.created_by,
            channels=["in_app"],
        )

    if candidate is not None and job is not None and stage is not None:
        notification_service.notify(
            tenant_id=application.company_id,
            notification_type="application_stage_changed",
            payload={"first_name": candidate.first_name, "job_title": job.title, "stage_name": stage.name},
            candidate_id=candidate.id,
            channels=["email"],
        )
