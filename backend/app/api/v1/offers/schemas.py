from marshmallow import Schema, fields, validate


class CreateOfferSchema(Schema):
    application_id = fields.UUID(required=True)
    salary_offered = fields.Decimal(required=True)
    joining_date = fields.Date(required=False, allow_none=True)
    expiry_date = fields.Date(required=False, allow_none=True)


class ApprovalActionSchema(Schema):
    comment = fields.Str(required=False, allow_none=True)


class OfferApprovalStepSchema(Schema):
    id = fields.UUID(dump_only=True)
    approver_role_id = fields.UUID(dump_only=True, allow_none=True)
    approver_role_name = fields.Method("get_approver_role_name", dump_only=True)
    status = fields.Str(dump_only=True)
    step_order = fields.Int(dump_only=True)

    def get_approver_role_name(self, step):
        return step.approver_role.name if step.approver_role else None


class OfferSchema(Schema):
    id = fields.UUID(dump_only=True)
    application_id = fields.UUID(dump_only=True)
    salary_offered = fields.Decimal(dump_only=True, as_string=True)
    joining_date = fields.Date(dump_only=True, allow_none=True)
    status = fields.Str(dump_only=True)
    expiry_date = fields.Date(dump_only=True, allow_none=True)
    sent_at = fields.DateTime(dump_only=True, allow_none=True)
    responded_at = fields.DateTime(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
