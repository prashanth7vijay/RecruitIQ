from app.exceptions.base import NotFoundError


class TenantScopedRepository:
    model = None  # set by subclasses

    def __init__(self, session):
        if self.model is None:
            raise NotImplementedError("Subclasses must set `model`")
        self.session = session

    def _base_query(self, tenant_id):
        if tenant_id is None:
            raise ValueError(
                f"{self.__class__.__name__}: tenant_id is required and cannot be None. "
                "This guard exists specifically to prevent accidental cross-tenant queries."
            )
        return self.session.query(self.model).filter(self.model.company_id == tenant_id)

    def get_or_404(self, id, tenant_id):
        obj = self._base_query(tenant_id).filter(self.model.id == id).first()
        if obj is None:
            # Deliberately the same exception/status as "doesn't exist at all" —
            # see Phase 11.3 on why cross-tenant access returns 404, not 403.
            raise NotFoundError(f"{self.model.__name__} not found")
        return obj

    def get(self, id, tenant_id):
        return self._base_query(tenant_id).filter(self.model.id == id).first()

    def list(self, tenant_id, **filters):
        return self._base_query(tenant_id).filter_by(**filters)

    def add(self, obj):
        self.session.add(obj)
        return obj

    def commit(self):
        self.session.commit()

    def delete(self, obj):
        self.session.delete(obj)


class GlobalRepository:
    model = None

    def __init__(self, session):
        if self.model is None:
            raise NotImplementedError("Subclasses must set `model`")
        self.session = session

    def get_or_404(self, id):
        obj = self.session.query(self.model).filter(self.model.id == id).first()
        if obj is None:
            raise NotFoundError(f"{self.model.__name__} not found")
        return obj

    def get(self, id):
        return self.session.query(self.model).filter(self.model.id == id).first()

    def add(self, obj):
        self.session.add(obj)
        return obj

    def commit(self):
        self.session.commit()
