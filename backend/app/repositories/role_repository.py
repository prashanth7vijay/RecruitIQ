from sqlalchemy import or_

from app.exceptions.base import NotFoundError
from app.models.role import Role, Permission


class RoleRepository:
    model = Role

    def __init__(self, session):
        self.session = session

    def get_system_role_by_name(self, name):
        return (
            self.session.query(Role)
            .filter(Role.company_id.is_(None), Role.name == name)
            .first()
        )

    def _visible_query(self, tenant_id):
        if tenant_id is None:
            raise ValueError("RoleRepository: tenant_id is required")
        return self.session.query(Role).filter(
            or_(Role.company_id.is_(None), Role.company_id == tenant_id)
        )

    def list_visible(self, tenant_id):
        """System roles + this tenant's own custom roles — what the
        Role Management UI and the user-role-assignment dropdown both
        need to offer."""
        return self._visible_query(tenant_id).order_by(Role.is_system_role.desc(), Role.name).all()

    def get_visible_or_404(self, role_id, tenant_id):
        role = self._visible_query(tenant_id).filter(Role.id == role_id).first()
        if role is None:
            # Same reasoning as TenantScopedRepository.get_or_404: a role
            # belonging to another tenant looks identical to a role that
            # doesn't exist — 404, not 403.
            raise NotFoundError("Role not found")
        return role

    def get_own_custom_or_404(self, role_id, tenant_id):
        """Stricter than get_visible_or_404: only a role this tenant
        actually owns, never a system role. Every mutation (update/
        delete) needs this; read access allows system roles too."""
        role = (
            self.session.query(Role)
            .filter(Role.id == role_id, Role.company_id == tenant_id)
            .first()
        )
        if role is None:
            raise NotFoundError("Role not found")
        return role

    def name_taken(self, tenant_id, name, exclude_role_id=None):
        query = self._visible_query(tenant_id).filter(Role.name.ilike(name))
        if exclude_role_id is not None:
            query = query.filter(Role.id != exclude_role_id)
        return query.first() is not None

    def add(self, obj):
        self.session.add(obj)
        return obj

    def commit(self):
        self.session.commit()

    def delete(self, obj):
        self.session.delete(obj)


class PermissionRepository:
    model = Permission

    def __init__(self, session):
        self.session = session

    def list_all(self):
        return self.session.query(Permission).order_by(Permission.code).all()

    def list_by_codes(self, codes):
        if not codes:
            return []
        return self.session.query(Permission).filter(Permission.code.in_(codes)).all()
