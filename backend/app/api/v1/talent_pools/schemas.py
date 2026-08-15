from marshmallow import Schema, fields, validate


class CreateTalentPoolSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    description = fields.Str(required=False, allow_none=True)


class AddCandidateToPoolSchema(Schema):
    candidate_profile_id = fields.UUID(required=True)


class TalentPoolSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)


class PoolMemberSchema(Schema):
    id = fields.UUID(dump_only=True)
    current_location = fields.Str(dump_only=True, allow_none=True)
    skills = fields.List(fields.Str(), dump_only=True)
