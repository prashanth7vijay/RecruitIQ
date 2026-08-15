from marshmallow import Schema, fields


class JDSuggestionSchema(Schema):
    suggestion = fields.Str(dump_only=True)
    ai_request_id = fields.UUID(dump_only=True)
    status = fields.Str(dump_only=True, dump_default="suggested")


class ApplyJDSuggestionSchema(Schema):
    ai_request_id = fields.UUID(required=True)
    new_description = fields.Str(required=True)


class MatchScoreSchema(Schema):
    score = fields.Float(dump_only=True)
    explanation = fields.Str(dump_only=True)
    ai_request_id = fields.UUID(dump_only=True)
    status = fields.Str(dump_only=True, dump_default="suggested")
