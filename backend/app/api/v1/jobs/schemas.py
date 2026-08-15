from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class CreateJobSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(required=False, allow_none=True)
    department_id = fields.UUID(required=False, allow_none=True)
    pipeline_template_id = fields.UUID(required=False, allow_none=True)
    employment_type = fields.Str(
        required=False, validate=validate.OneOf(["remote", "hybrid", "onsite"])
    )
    salary_min = fields.Decimal(required=False, allow_none=True)
    salary_max = fields.Decimal(required=False, allow_none=True)
    experience_min = fields.Decimal(required=False, allow_none=True)
    experience_max = fields.Decimal(required=False, allow_none=True)
    required_skills = fields.List(fields.Str(), load_default=list)
    preferred_skills = fields.List(fields.Str(), load_default=list)
    hiring_target_count = fields.Int(required=False, load_default=1, validate=validate.Range(min=1))

    @validates_schema
    def validate_salary_range(self, data, **kwargs):
        lo, hi = data.get("salary_min"), data.get("salary_max")
        if lo is not None and hi is not None and lo > hi:
            raise ValidationError("salary_min cannot exceed salary_max", field_name="salary_min")


class UpdateJobSchema(Schema):
    # Explicitly no `status` field — status changes go through the
    # dedicated /status endpoints only. See Phase 11.6.
    title = fields.Str(required=False, validate=validate.Length(min=1, max=255))
    description = fields.Str(required=False, allow_none=True)
    department_id = fields.UUID(required=False, allow_none=True)
    salary_min = fields.Decimal(required=False, allow_none=True)
    salary_max = fields.Decimal(required=False, allow_none=True)
    required_skills = fields.List(fields.Str(), required=False)
    preferred_skills = fields.List(fields.Str(), required=False)


class ApprovalActionSchema(Schema):
    comment = fields.Str(required=False, allow_none=True)


class ApprovalStepSchema(Schema):
    id = fields.UUID(dump_only=True)
    approver_role_id = fields.UUID(dump_only=True, allow_none=True)
    approver_role_name = fields.Method("get_approver_role_name", dump_only=True)
    status = fields.Str(dump_only=True)
    comment = fields.Str(dump_only=True, allow_none=True)
    step_order = fields.Int(dump_only=True)
    acted_at = fields.DateTime(dump_only=True, allow_none=True)

    def get_approver_role_name(self, step):
        return step.approver_role.name if step.approver_role else None


class JobSchema(Schema):
    id = fields.UUID(dump_only=True)
    title = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True)
    status = fields.Str(dump_only=True)
    department_id = fields.UUID(dump_only=True, allow_none=True)
    pipeline_template_id = fields.UUID(dump_only=True, allow_none=True)
    employment_type = fields.Str(dump_only=True, allow_none=True)
    salary_min = fields.Decimal(dump_only=True, allow_none=True, as_string=True)
    salary_max = fields.Decimal(dump_only=True, allow_none=True, as_string=True)
    required_skills = fields.List(fields.Str(), dump_only=True)
    preferred_skills = fields.List(fields.Str(), dump_only=True)
    hiring_target_count = fields.Int(dump_only=True)
    published_at = fields.DateTime(dump_only=True, allow_none=True)
    closed_at = fields.DateTime(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
