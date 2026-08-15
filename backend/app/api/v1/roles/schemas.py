from marshmallow import Schema, fields, validate, EXCLUDE


class PermissionSchema(Schema):
    id = fields.UUID(dump_only=True)
    code = fields.Str(dump_only=True)


class RoleSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.Str(dump_only=True)
    is_system_role = fields.Bool(dump_only=True)
    company_id = fields.UUID(dump_only=True, allow_none=True)
    permissions = fields.Method("get_permission_codes", dump_only=True)

    def get_permission_codes(self, role):
        return sorted(p.code for p in role.permissions)


class CreateRoleSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    permission_codes = fields.List(fields.Str(), required=False, load_default=list)


class UpdateRoleSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(required=False, validate=validate.Length(min=1, max=100))
    permission_codes = fields.List(fields.Str(), required=False)
