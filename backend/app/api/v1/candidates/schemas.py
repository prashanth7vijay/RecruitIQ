from marshmallow import Schema, fields, validate

class AddCandidateSchema(Schema):
    email = fields.Email(required=True)
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    phone = fields.Str(required=False, allow_none=True)
    source = fields.Str(required=False, allow_none=True)


class UpdateProfileSchema(Schema):
    skills = fields.List(fields.Str(), required=False)
    experience_years = fields.Decimal(required=False, allow_none=True)
    expected_salary = fields.Decimal(required=False, allow_none=True)
    notice_period_days = fields.Int(required=False, allow_none=True)
    current_location = fields.Str(required=False, allow_none=True)
    preferred_location = fields.Str(required=False, allow_none=True)


class CandidateSchema(Schema):
    id = fields.UUID(dump_only=True)
    email = fields.Email(dump_only=True)
    first_name = fields.Str(dump_only=True)
    last_name = fields.Str(dump_only=True)
    phone = fields.Str(dump_only=True, allow_none=True)


class ResumeSchema(Schema):
    id = fields.UUID(dump_only=True)
    original_filename = fields.Str(dump_only=True)
    version = fields.Int(dump_only=True)
    parse_status = fields.Str(dump_only=True)
    uploaded_at = fields.DateTime(dump_only=True)


class CandidateProfileSchema(Schema):
    id = fields.UUID(dump_only=True)
    candidate = fields.Nested(CandidateSchema, dump_only=True)
    skills = fields.List(fields.Str(), dump_only=True)
    experience_years = fields.Decimal(dump_only=True, allow_none=True, as_string=True)
    expected_salary = fields.Decimal(dump_only=True, allow_none=True, as_string=True)
    notice_period_days = fields.Int(dump_only=True, allow_none=True)
    current_location = fields.Str(dump_only=True, allow_none=True)
    preferred_location = fields.Str(dump_only=True, allow_none=True)
    source = fields.Str(dump_only=True, allow_none=True)
    resume_id = fields.UUID(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)


class AddNoteSchema(Schema):
    body = fields.Str(required=True, validate=validate.Length(min=1))


class NoteSchema(Schema):
    id = fields.UUID(dump_only=True)
    body = fields.Str(dump_only=True)
    author_id = fields.UUID(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class AddTagSchema(Schema):
    label = fields.Str(required=True, validate=validate.Length(min=1, max=50))


class TagSchema(Schema):
    id = fields.UUID(dump_only=True)
    label = fields.Str(dump_only=True)
