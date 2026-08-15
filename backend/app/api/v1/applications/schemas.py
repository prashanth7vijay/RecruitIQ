from marshmallow import Schema, fields


class MoveStageSchema(Schema):
    target_stage_id = fields.UUID(required=True)
    note = fields.Str(required=False, allow_none=True)


class RejectApplicationSchema(Schema):
    reason = fields.Str(required=False, allow_none=True)


class CandidateSummarySchema(Schema):
    first_name = fields.Str(dump_only=True)
    last_name = fields.Str(dump_only=True)
    email = fields.Email(dump_only=True)


class ApplicationSchema(Schema):
    id = fields.UUID(dump_only=True)
    job_id = fields.UUID(dump_only=True)
    candidate = fields.Nested(CandidateSummarySchema, dump_only=True)
    current_stage_id = fields.UUID(dump_only=True)
    status = fields.Str(dump_only=True)
    match_score = fields.Float(dump_only=True, allow_none=True)
    applied_at = fields.DateTime(dump_only=True)
    rejected_at = fields.DateTime(dump_only=True, allow_none=True)
    rejection_reason = fields.Str(dump_only=True, allow_none=True)


class StageHistoryEntrySchema(Schema):
    id = fields.UUID(dump_only=True)
    from_stage_id = fields.UUID(dump_only=True, allow_none=True)
    to_stage_id = fields.UUID(dump_only=True)
    moved_by = fields.UUID(dump_only=True, allow_none=True)
    note = fields.Str(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
