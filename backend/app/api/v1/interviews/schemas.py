from marshmallow import Schema, fields, validate


class ScheduleInterviewSchema(Schema):
    application_id = fields.UUID(required=True)
    round_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    panelist_user_ids = fields.List(fields.UUID(), required=True, validate=validate.Length(min=1))
    scheduled_at = fields.DateTime(required=False, allow_none=True)
    duration_minutes = fields.Int(required=False, allow_none=True)
    meeting_link = fields.Str(required=False, allow_none=True)


class RescheduleInterviewSchema(Schema):
    scheduled_at = fields.DateTime(required=True)


class RubricScoreSchema(Schema):
    criterion = fields.Str(required=True)
    score = fields.Float(required=True)
    comment = fields.Str(required=False, allow_none=True)


class SubmitFeedbackSchema(Schema):
    rubric_scores = fields.List(fields.Nested(RubricScoreSchema), load_default=list)
    overall_rating = fields.Decimal(required=False, allow_none=True)
    recommendation = fields.Str(
        required=False, allow_none=True,
        validate=validate.OneOf(["strong_yes", "yes", "no", "strong_no"]),
    )
    notes = fields.Str(required=False, allow_none=True)


class InterviewSchema(Schema):
    id = fields.UUID(dump_only=True)
    application_id = fields.UUID(dump_only=True)
    round_name = fields.Str(dump_only=True)
    scheduled_at = fields.DateTime(dump_only=True, allow_none=True)
    duration_minutes = fields.Int(dump_only=True, allow_none=True)
    status = fields.Str(dump_only=True)
    meeting_link = fields.Str(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)


class InterviewFeedbackSchema(Schema):
    id = fields.UUID(dump_only=True)
    interview_id = fields.UUID(dump_only=True)
    interviewer_id = fields.UUID(dump_only=True)
    rubric_scores = fields.List(fields.Dict(), dump_only=True)
    overall_rating = fields.Decimal(dump_only=True, allow_none=True, as_string=True)
    recommendation = fields.Str(dump_only=True, allow_none=True)
    submitted_at = fields.DateTime(dump_only=True, allow_none=True)
