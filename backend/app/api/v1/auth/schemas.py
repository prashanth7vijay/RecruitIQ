import re

from marshmallow import Schema, fields, validate, validates, ValidationError as MarshmallowValidationError

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class SignupCompanySchema(Schema):

    company_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    company_slug = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=10))
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))

    @validates("company_slug")
    def validate_slug_format(self, value, **kwargs):
        if not SLUG_PATTERN.match(value):
            raise MarshmallowValidationError(
                "Must be lowercase letters, numbers, and hyphens only (e.g. 'acme-corp')"
            )


class ChangePasswordSchema(Schema):
    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=10))


class LoginSchema(Schema):
    company_slug = fields.Str(required=True)
    email = fields.Email(required=True)
    password = fields.Str(required=True)
    remember_me = fields.Bool(load_default=False)


class RefreshSchema(Schema):
    refresh_token = fields.Str(required=False)


class UserSchema(Schema):
    id = fields.UUID(dump_only=True)
    email = fields.Email(dump_only=True)
    first_name = fields.Str(dump_only=True)
    last_name = fields.Str(dump_only=True)
    status = fields.Str(dump_only=True)


class CompanySchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.Str(dump_only=True)
    slug = fields.Str(dump_only=True)


class LoginResponseSchema(Schema):
    access_token = fields.Str(dump_only=True)
    user = fields.Nested(UserSchema, dump_only=True)
