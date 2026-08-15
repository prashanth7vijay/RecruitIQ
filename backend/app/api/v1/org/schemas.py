from marshmallow import Schema, fields, validate


class CreateDepartmentSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    parent_id = fields.UUID(required=False, allow_none=True)


class RenameDepartmentSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=150))


class DepartmentSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.Str(dump_only=True)
    parent_id = fields.UUID(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)


class CreateTeamSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    department_id = fields.UUID(required=False, allow_none=True)


class UpdateTeamSchema(Schema):
    name = fields.Str(required=False, validate=validate.Length(min=1, max=150))
    department_id = fields.UUID(required=False, allow_none=True)


class TeamSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.Str(dump_only=True)
    department_id = fields.UUID(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)


class CreateLocationSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    city = fields.Str(required=False, allow_none=True, validate=validate.Length(max=150))
    country = fields.Str(required=False, allow_none=True, validate=validate.Length(max=150))
    is_remote = fields.Bool(required=False, load_default=False)


class UpdateLocationSchema(Schema):
    name = fields.Str(required=False, validate=validate.Length(min=1, max=150))
    city = fields.Str(required=False, allow_none=True, validate=validate.Length(max=150))
    country = fields.Str(required=False, allow_none=True, validate=validate.Length(max=150))
    is_remote = fields.Bool(required=False)


class LocationSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.Str(dump_only=True)
    city = fields.Str(dump_only=True, allow_none=True)
    country = fields.Str(dump_only=True, allow_none=True)
    is_remote = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class UpdateUserOrgPlacementSchema(Schema):
    department_id = fields.UUID(required=False, allow_none=True)
    team_id = fields.UUID(required=False, allow_none=True)
    manager_id = fields.UUID(required=False, allow_none=True)
    location_id = fields.UUID(required=False, allow_none=True)
