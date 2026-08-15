from app.models.audit_log import AuditLog


class AuditService:
    def __init__(self, audit_repo):
        self.audit_repo = audit_repo

    def log(self, company_id, entity_type, entity_id, action, actor_id=None, old_value=None, new_value=None):
        entry = AuditLog(
            company_id=company_id,
            actor_id=actor_id,
            actor_type="user" if actor_id else "system",
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
        )
        self.audit_repo.add(entry)
        self.audit_repo.commit()
        return entry

    def list_for_company(self, company_id, entity_type=None):
        return self.audit_repo.list_for_company(company_id, entity_type=entity_type)
