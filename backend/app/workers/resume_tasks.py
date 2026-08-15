from app.extensions import db
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def parse_resume_task(self, payload):
    from app.models.resume import Resume

    resume_id = payload["resume_id"]
    resume = db.session.query(Resume).filter_by(id=resume_id).first()
    if resume is None:
        return  # resume was deleted before the task ran — nothing to do

    if resume.parse_status == "done":
        return  # idempotency guard per Phase 15.3 — safe to re-run

    resume.parse_status = "processing"
    db.session.commit()

    try:
        resume.parsed_data = {
            "extraction_method": "stub",
            "note": "Real parsing deferred to the AI Assist milestone",
        }
        resume.completeness_score = 50.0  # placeholder — a real score needs real extraction
        resume.parse_status = "done"
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        resume.parse_status = "failed"
        db.session.commit()
        raise self.retry(exc=exc)
