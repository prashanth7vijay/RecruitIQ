from datetime import datetime, timezone

from app.exceptions.base import BusinessRuleViolationError, PermissionDeniedError
from app.models.interview import Interview, InterviewPanelist
from app.models.interview_feedback import InterviewFeedback


class InterviewService:
    def __init__(self, interview_repo, feedback_repo, application_repo, event_bus=None):
        self.interview_repo = interview_repo
        self.feedback_repo = feedback_repo
        self.application_repo = application_repo
        self.event_bus = event_bus

    def schedule(self, tenant_id, application_id, round_name, created_by, panelist_user_ids,
                 scheduled_at=None, duration_minutes=None, meeting_link=None):
        application = self.application_repo.get_or_404(application_id, tenant_id)
        if application.status != "active":
            raise BusinessRuleViolationError(f"Cannot schedule an interview for a {application.status} application")

        interview = Interview(
            company_id=tenant_id,
            application_id=application_id,
            pipeline_stage_id=application.current_stage_id,  # snapshot at scheduling time
            round_name=round_name,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            meeting_link=meeting_link,
            created_by=created_by,
        )
        self.interview_repo.add(interview)
        self.interview_repo.commit()

        for user_id in panelist_user_ids:
            self.interview_repo.session.add(InterviewPanelist(interview_id=interview.id, user_id=user_id))
        self.interview_repo.commit()

        if self.event_bus is not None:
            self.event_bus.publish("interview.scheduled", {"interview_id": str(interview.id)})

        return interview

    def get(self, tenant_id, interview_id):
        return self.interview_repo.get_or_404(interview_id, tenant_id)

    def list_for_application(self, tenant_id, application_id):
        return self.interview_repo.list_for_application(tenant_id, application_id)

    def list_for_interviewer(self, tenant_id, user_id):
        return self.interview_repo.list_for_interviewer(tenant_id, user_id)

    def reschedule(self, tenant_id, interview_id, scheduled_at):
        interview = self.interview_repo.get_or_404(interview_id, tenant_id)
        if interview.status != "scheduled":
            raise BusinessRuleViolationError(f"Cannot reschedule a {interview.status} interview")
        interview.scheduled_at = scheduled_at
        self.interview_repo.commit()
        return interview

    def cancel(self, tenant_id, interview_id):
        interview = self.interview_repo.get_or_404(interview_id, tenant_id)
        if interview.status != "scheduled":
            raise BusinessRuleViolationError(f"Cannot cancel a {interview.status} interview")
        interview.status = "cancelled"
        self.interview_repo.commit()
        return interview

    def submit_feedback(self, tenant_id, interview_id, interviewer_id, rubric_scores,
                         overall_rating=None, recommendation=None, notes=None):
        interview = self.interview_repo.get_or_404(interview_id, tenant_id)
        is_panelist = any(str(p.user_id) == str(interviewer_id) for p in interview.panelists)
        if not is_panelist:
            raise PermissionDeniedError("Only an assigned panelist can submit feedback for this interview")

        feedback = self.feedback_repo.get_by_interview_and_interviewer(interview_id, interviewer_id)
        if feedback is None:
            feedback = InterviewFeedback(interview_id=interview_id, interviewer_id=interviewer_id)
            self.feedback_repo.add(feedback)

        feedback.rubric_scores = rubric_scores
        feedback.overall_rating = overall_rating
        feedback.recommendation = recommendation
        feedback.notes = notes
        feedback.submitted_at = datetime.now(timezone.utc)
        self.feedback_repo.commit()
        return feedback
