from app.models.application import Application, ApplicationStageHistory
from app.repositories.base_repository import TenantScopedRepository


class ApplicationRepository(TenantScopedRepository):
    model = Application

    def get_by_job_and_candidate(self, tenant_id, job_id, candidate_id):
        return self._base_query(tenant_id).filter(
            Application.job_id == job_id, Application.candidate_id == candidate_id
        ).first()

    def list_active_for_job(self, tenant_id, job_id):
        return (
            self._base_query(tenant_id)
            .filter(Application.job_id == job_id, Application.status == "active")
            .all()
        )


class ApplicationStageHistoryRepository:

    model = ApplicationStageHistory

    def __init__(self, session):
        self.session = session

    def add(self, obj):
        self.session.add(obj)
        return obj

    def commit(self):
        self.session.commit()

    def list_for_application(self, application_id):
        return (
            self.session.query(ApplicationStageHistory)
            .filter(ApplicationStageHistory.application_id == application_id)
            .order_by(ApplicationStageHistory.created_at)
        )
