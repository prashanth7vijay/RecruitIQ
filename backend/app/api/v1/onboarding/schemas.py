from marshmallow import Schema, fields


class AssignOnboardingSchema(Schema):
    buddy_user_id = fields.UUID(required=False, allow_none=True)
    manager_user_id = fields.UUID(required=False, allow_none=True)
    joining_date = fields.Date(required=False, allow_none=True)


class OnboardingTaskSchema(Schema):
    id = fields.UUID(dump_only=True)
    title = fields.Str(dump_only=True)
    is_completed = fields.Bool(dump_only=True)
    completed_at = fields.DateTime(dump_only=True, allow_none=True)


class OnboardingChecklistSchema(Schema):
    id = fields.UUID(dump_only=True)
    application_id = fields.UUID(dump_only=True)
    buddy_user_id = fields.UUID(dump_only=True, allow_none=True)
    manager_user_id = fields.UUID(dump_only=True, allow_none=True)
    joining_date = fields.Date(dump_only=True, allow_none=True)
    status = fields.Str(dump_only=True)
    tasks = fields.List(fields.Nested(OnboardingTaskSchema), dump_only=True)
