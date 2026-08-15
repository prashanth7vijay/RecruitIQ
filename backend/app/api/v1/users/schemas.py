from marshmallow import Schema, fields


class UserDirectoryEntrySchema(Schema):
    id = fields.UUID(dump_only=True)
    first_name = fields.Str(dump_only=True)
    last_name = fields.Str(dump_only=True)
    email = fields.Email(dump_only=True)
    role_name = fields.Method("get_role_name", dump_only=True)

    def get_role_name(self, user):
        return user.role.name if user.role else None
