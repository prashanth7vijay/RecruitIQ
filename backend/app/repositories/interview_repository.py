from app.models.interview import Interview, InterviewPanelist
from app.models.interview_feedback import InterviewFeedback
from app.repositories.base_repository import TenantScopedRepository


class InterviewRepository(TenantScopedRepository):
    model = Interview

    def list_for_application(self, tenant_id, application_id):
        return self._base_query(tenant_id).filter(Interview.application_id == application_id).all()

    def list_for_interviewer(self, tenant_id, user_id):
        return (
            self._base_query(tenant_id)
            .join(InterviewPanelist, InterviewPanelist.interview_id == Interview.id)
            .filter(InterviewPanelist.user_id == user_id)
            .all()
        )


class InterviewFeedbackRepository:

    model = InterviewFeedback

    def __init__(self, session):
        self.session = session

    def get_by_interview_and_interviewer(self, interview_id, interviewer_id):
        return (
            self.session.query(InterviewFeedback)
            .filter(
                InterviewFeedback.interview_id == interview_id,
                InterviewFeedback.interviewer_id == interviewer_id,
            )
            .first()
        )

    def add(self, obj):
        self.session.add(obj)
        return obj

    def commit(self):
        self.session.commit()
