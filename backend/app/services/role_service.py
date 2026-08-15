from app.exceptions.base import BusinessRuleViolationError, ConflictError, ValidationError


class RoleService:
    def __init__(self, role_repo, permission_repo, user_repo):
        self.role_repo = role_repo
        self.permission_repo = permission_repo
        self.user_repo = user_repo

    def list_roles(self, tenant_id):
        return self.role_repo.list_visible(tenant_id)

    def get_role(self, tenant_id, role_id):
        return self.role_repo.get_visible_or_404(role_id, tenant_id)

    def list_permissions(self):
        return self.permission_repo.list_all()

    def create_role(self, tenant_id, name, permission_codes):
        name = (name or "").strip()
        if not name:
            raise ValidationError("Role name is required")
        if self.role_repo.name_taken(tenant_id, name):
            raise ConflictError(f"A role named '{name}' already exists")

        permissions = self._resolve_permissions(permission_codes)

        role = self.role_repo.model(
            company_id=tenant_id, name=name, is_system_role=False, permissions=permissions
        )
        self.role_repo.add(role)
        self.role_repo.commit()
        return role

    def update_role(self, tenant_id, role_id, name=None, permission_codes=None):
        role = self._require_own_custom_role(tenant_id, role_id)

        if name is not None:
            name = name.strip()
            if not name:
                raise ValidationError("Role name is required")
            if self.role_repo.name_taken(tenant_id, name, exclude_role_id=role.id):
                raise ConflictError(f"A role named '{name}' already exists")
            role.name = name

        if permission_codes is not None:
            role.permissions = self._resolve_permissions(permission_codes)

        self.role_repo.commit()
        return role

    def delete_role(self, tenant_id, role_id):
        role = self._require_own_custom_role(tenant_id, role_id)

        assigned_count = self.user_repo.list(tenant_id, role_id=role.id).count()
        if assigned_count > 0:
            raise ConflictError(
                f"Cannot delete '{role.name}' — {assigned_count} user(s) currently hold this role. "
                "Reassign them first."
            )

        self.role_repo.delete(role)
        self.role_repo.commit()

    # --- internal ---------------------------------------------------

    def _require_own_custom_role(self, tenant_id, role_id):
        role = self.role_repo.get_own_custom_or_404(role_id, tenant_id)
        if role.is_system_role:
            # Belt-and-suspenders: get_own_custom_or_404 already filters
            # by company_id == tenant_id, which no system role ever has,
            # so this branch shouldn't be reachable — but the invariant
            # ("system roles are never mutated") is important enough to
            # assert explicitly rather than rely solely on the query shape.
            raise BusinessRuleViolationError("System roles cannot be modified")
        return role

    def _resolve_permissions(self, permission_codes):
        codes = list(dict.fromkeys(permission_codes or []))  # de-dupe, preserve order
        if not codes:
            return []
        found = self.permission_repo.list_by_codes(codes)
        found_codes = {p.code for p in found}
        unknown = [c for c in codes if c not in found_codes]
        if unknown:
            raise ValidationError(f"Unknown permission code(s): {', '.join(unknown)}")
        return found
