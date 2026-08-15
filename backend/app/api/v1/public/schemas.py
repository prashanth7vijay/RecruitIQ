from marshmallow import Schema, fields


class PublicJobSchema(Schema):
    id = fields.UUID(dump_only=True)
    title = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True)
    employment_type = fields.Str(dump_only=True, allow_none=True)
    salary_min = fields.Decimal(dump_only=True, allow_none=True, as_string=True)
    salary_max = fields.Decimal(dump_only=True, allow_none=True, as_string=True)
    required_skills = fields.List(fields.Str(), dump_only=True)
    preferred_skills = fields.List(fields.Str(), dump_only=True)
    published_at = fields.DateTime(dump_only=True, allow_none=True)


class ApplySchema(Schema):
    email = fields.Email(required=True)
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    phone = fields.Str(required=False, allow_none=True)


class ApplicationConfirmationSchema(Schema):
    id = fields.UUID(dump_only=True)
    status = fields.Str(dump_only=True)
    applied_at = fields.DateTime(dump_only=True)
