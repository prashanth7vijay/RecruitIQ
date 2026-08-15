from marshmallow import Schema, fields, validate


class OpenJobSchema(Schema):
    id = fields.UUID(dump_only=True)
    title = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True)
    department_id = fields.UUID(dump_only=True, allow_none=True)


class SubmitReferralSchema(Schema):
    job_id = fields.UUID(required=True)
    email = fields.Email(required=True)
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    phone = fields.Str(required=False, allow_none=True, validate=validate.Length(max=30))


class MyReferralSchema(Schema):
    id = fields.Method("get_id", dump_only=True)
    job_title = fields.Method("get_job_title", dump_only=True)
    candidate_name = fields.Method("get_candidate_name", dump_only=True)
    status = fields.Method("get_status", dump_only=True)
    created_at = fields.Method("get_created_at", dump_only=True)

    def get_id(self, row):
        return str(row["referral"].id)

    def get_job_title(self, row):
        return row["job"].title

    def get_candidate_name(self, row):
        return f"{row['candidate'].first_name} {row['candidate'].last_name}"

    def get_status(self, row):
        return row["application"].status

    def get_created_at(self, row):
        return row["referral"].created_at.isoformat() if row["referral"].created_at else None
