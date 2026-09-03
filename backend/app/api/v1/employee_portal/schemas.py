from marshmallow import Schema, fields


class OpenJobSchema(Schema):
    id = fields.UUID(dump_only=True)
    title = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True)
    department_id = fields.UUID(dump_only=True, allow_none=True)


class SubmitReferralSchema(Schema):
    job_id = fields.UUID(required=True)
    email = fields.Email(required=True)


class MyReferralSchema(Schema):
    id = fields.Method("get_id", dump_only=True)
    job_title = fields.Method("get_job_title", dump_only=True)
    candidate_email = fields.Method("get_candidate_email", dump_only=True)
    candidate_name = fields.Method("get_candidate_name", dump_only=True)
    status = fields.Method("get_status", dump_only=True)
    created_at = fields.Method("get_created_at", dump_only=True)

    def get_id(self, row):
        return str(row["referral"].id)

    def get_job_title(self, row):
        return row["job"].title

    def get_candidate_email(self, row):
        return row["candidate"].email

    def get_candidate_name(self, row):
        candidate = row["candidate"]
        if not candidate.first_name and not candidate.last_name:
            return candidate.email
        return f"{candidate.first_name} {candidate.last_name}"

    def get_status(self, row):
        if row["application"] is None:
            return "invited"  # referred, notified, hasn't applied yet
        return row["application"].status

    def get_created_at(self, row):
        return row["referral"].created_at.isoformat() if row["referral"].created_at else None