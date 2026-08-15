from marshmallow import Schema, fields, validate


class CandidateSignupSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=10))
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    phone = fields.Str(required=False, allow_none=True, validate=validate.Length(max=30))


class CandidateLoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)
