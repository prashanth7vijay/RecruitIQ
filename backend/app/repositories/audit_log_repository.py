from app.models.audit_log import AuditLog


class AuditLogRepository:

    def __init__(self, session):
        self.session = session

    def add(self, obj):
        self.session.add(obj)
        return obj

    def commit(self):
        self.session.commit()

    def list_for_company(self, company_id, entity_type=None):
        query = self.session.query(AuditLog).filter(AuditLog.company_id == company_id)
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        return query.order_by(AuditLog.created_at.desc())
