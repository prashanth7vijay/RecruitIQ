from marshmallow import Schema, fields


class NotificationSchema(Schema):
    id = fields.UUID(dump_only=True)
    type = fields.Str(dump_only=True)
    channel = fields.Str(dump_only=True)
    payload = fields.Dict(dump_only=True)
    read_at = fields.DateTime(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
