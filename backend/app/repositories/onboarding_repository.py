from app.models.onboarding import OnboardingChecklist, OnboardingTask


class OnboardingRepository:

    def __init__(self, session):
        self.session = session

    def get_by_application(self, application_id):
        return (
            self.session.query(OnboardingChecklist)
            .filter(OnboardingChecklist.application_id == application_id)
            .first()
        )

    def get_or_404(self, checklist_id):
        from app.exceptions.base import NotFoundError
        checklist = self.session.query(OnboardingChecklist).filter_by(id=checklist_id).first()
        if checklist is None:
            raise NotFoundError("Onboarding checklist not found")
        return checklist

    def add(self, obj):
        self.session.add(obj)
        return obj

    def commit(self):
        self.session.commit()

    def add_task(self, checklist_id, title):
        task = OnboardingTask(onboarding_checklist_id=checklist_id, title=title)
        self.session.add(task)
        return task

    def get_task_or_404(self, task_id):
        from app.exceptions.base import NotFoundError
        task = self.session.query(OnboardingTask).filter_by(id=task_id).first()
        if task is None:
            raise NotFoundError("Onboarding task not found")
        return task
