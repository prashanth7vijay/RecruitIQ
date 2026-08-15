from marshmallow import Schema, fields, validate, EXCLUDE


class ApprovalChainStepSchema(Schema):
    role_id = fields.UUID(dump_only=True)
    role_name = fields.Method("get_role_name", dump_only=True)
    step_order = fields.Int(dump_only=True)

    def get_role_name(self, step):
        return step.role.name if step.role else None


class ApprovalChainSchema(Schema):
    id = fields.UUID(dump_only=True)
    entity_type = fields.Str(dump_only=True)
    steps = fields.List(fields.Nested(ApprovalChainStepSchema), dump_only=True)


class SetApprovalChainSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    role_ids = fields.List(fields.UUID(), required=True, validate=validate.Length(min=1))
