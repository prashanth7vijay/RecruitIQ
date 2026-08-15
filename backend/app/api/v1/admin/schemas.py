from marshmallow import Schema, fields, validate


class AdminUserSchema(Schema):
    id = fields.UUID(dump_only=True)
    first_name = fields.Str(dump_only=True)
    last_name = fields.Str(dump_only=True)
    email = fields.Email(dump_only=True)
    status = fields.Str(dump_only=True)
    role_id = fields.UUID(dump_only=True)
    role_name = fields.Method("get_role_name", dump_only=True)
    department_id = fields.UUID(dump_only=True, allow_none=True)
    team_id = fields.UUID(dump_only=True, allow_none=True)
    manager_id = fields.UUID(dump_only=True, allow_none=True)
    location_id = fields.UUID(dump_only=True, allow_none=True)
    must_change_password = fields.Bool(dump_only=True)

    def get_role_name(self, user):
        return user.role.name if user.role else None


class CreateUserSchema(Schema):
    email = fields.Email(required=True)
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    role_id = fields.UUID(required=True)


class CreatedUserSchema(Schema):

    id = fields.UUID(dump_only=True)
    email = fields.Email(dump_only=True)
    first_name = fields.Str(dump_only=True)
    last_name = fields.Str(dump_only=True)
    status = fields.Str(dump_only=True)
    role_id = fields.UUID(dump_only=True)
    must_change_password = fields.Bool(dump_only=True)


class UpdateUserRoleSchema(Schema):
    role_id = fields.UUID(required=True)


class UpdateUserStatusSchema(Schema):
    status = fields.Str(required=True, validate=validate.OneOf(["active", "locked", "disabled"]))


class AuditLogEntrySchema(Schema):
    id = fields.UUID(dump_only=True)
    actor_id = fields.UUID(dump_only=True, allow_none=True)
    actor_type = fields.Str(dump_only=True)
    entity_type = fields.Str(dump_only=True)
    entity_id = fields.UUID(dump_only=True)
    action = fields.Str(dump_only=True)
    old_value = fields.Dict(dump_only=True, allow_none=True)
    new_value = fields.Dict(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)


class SystemHealthSchema(Schema):
    status = fields.Str(dump_only=True)
    database = fields.Str(dump_only=True)
    user_count = fields.Int(dump_only=True)
    active_job_count = fields.Int(dump_only=True)
