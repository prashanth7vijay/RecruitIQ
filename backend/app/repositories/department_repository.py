from app.models.department import Department, Team, Location
from app.repositories.base_repository import TenantScopedRepository


class DepartmentRepository(TenantScopedRepository):
    model = Department

    def name_taken(self, tenant_id, name, exclude_id=None):
        query = self._base_query(tenant_id).filter(Department.name.ilike(name))
        if exclude_id is not None:
            query = query.filter(Department.id != exclude_id)
        return query.first() is not None


class TeamRepository(TenantScopedRepository):
    model = Team


class LocationRepository(TenantScopedRepository):
    model = Location

    def name_taken(self, tenant_id, name, exclude_id=None):
        query = self._base_query(tenant_id).filter(Location.name.ilike(name))
        if exclude_id is not None:
            query = query.filter(Location.id != exclude_id)
        return query.first() is not None
