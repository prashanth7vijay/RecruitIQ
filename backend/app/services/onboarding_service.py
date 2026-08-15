from datetime import datetime, timezone

from app.models.onboarding import OnboardingChecklist


class OnboardingService:
    def __init__(self, onboarding_repo):
        self.onboarding_repo = onboarding_repo

    def create_for_application(self, application_id, default_tasks=None):
        existing = self.onboarding_repo.get_by_application(application_id)
        if existing is not None:
            return existing  # idempotent — matches the resume-parse-task pattern from Sprint 6

        checklist = OnboardingChecklist(application_id=application_id, status="pending")
        self.onboarding_repo.add(checklist)
        self.onboarding_repo.commit()

        for title in (default_tasks or ["Send welcome email", "Prepare workstation", "Assign buddy"]):
            self.onboarding_repo.add_task(checklist.id, title)
        self.onboarding_repo.commit()
        return checklist

    def get_by_application(self, application_id):
        return self.onboarding_repo.get_by_application(application_id)

    def assign(self, checklist_id, buddy_user_id=None, manager_user_id=None, joining_date=None):
        checklist = self.onboarding_repo.get_or_404(checklist_id)
        if buddy_user_id is not None:
            checklist.buddy_user_id = buddy_user_id
        if manager_user_id is not None:
            checklist.manager_user_id = manager_user_id
        if joining_date is not None:
            checklist.joining_date = joining_date
        self.onboarding_repo.commit()
        return checklist

    def complete_task(self, task_id):
        task = self.onboarding_repo.get_task_or_404(task_id)
        task.is_completed = True
        task.completed_at = datetime.now(timezone.utc)
        self.onboarding_repo.commit()

        checklist = self.onboarding_repo.get_or_404(task.onboarding_checklist_id)
        if all(t.is_completed for t in checklist.tasks):
            checklist.status = "complete"
        else:
            checklist.status = "in_progress"
        self.onboarding_repo.commit()
        return task
