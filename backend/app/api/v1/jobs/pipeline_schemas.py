from marshmallow import Schema, fields, validate


class CreateStageSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    stage_order = fields.Int(required=True, validate=validate.Range(min=0))
    stage_type = fields.Str(
        required=True,
        validate=validate.OneOf(["screening", "interview", "assessment", "offer", "terminal"]),
    )
    sla_hours = fields.Int(required=False, allow_none=True)


class CreatePipelineTemplateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    is_default = fields.Bool(load_default=False)
    stages = fields.List(fields.Nested(CreateStageSchema), required=True, validate=validate.Length(min=1))


class UpdatePipelineTemplateSchema(Schema):
    name = fields.Str(required=False, validate=validate.Length(min=1, max=150))
    is_default = fields.Bool(required=False)
    stages = fields.List(fields.Nested(CreateStageSchema), required=False, validate=validate.Length(min=1))


class StageSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.Str(dump_only=True)
    stage_order = fields.Int(dump_only=True)
    stage_type = fields.Str(dump_only=True)
    sla_hours = fields.Int(dump_only=True, allow_none=True)


class PipelineTemplateSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.Str(dump_only=True)
    is_default = fields.Bool(dump_only=True)
    stages = fields.List(fields.Nested(StageSchema), dump_only=True)
