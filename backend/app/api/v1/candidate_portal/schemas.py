from marshmallow import Schema, fields


class CandidateMeSchema(Schema):
    id = fields.UUID(dump_only=True)
    email = fields.Email(dump_only=True)
    first_name = fields.Str(dump_only=True)
    last_name = fields.Str(dump_only=True)
    phone = fields.Str(dump_only=True, allow_none=True)


class MyApplicationSchema(Schema):
    id = fields.Method("get_id", dump_only=True)
    company_name = fields.Method("get_company_name", dump_only=True)
    job_title = fields.Method("get_job_title", dump_only=True)
    status = fields.Method("get_status", dump_only=True)
    stage_name = fields.Method("get_stage_name", dump_only=True)
    applied_at = fields.Method("get_applied_at", dump_only=True)

    def get_id(self, row):
        return str(row["application"].id)

    def get_company_name(self, row):
        return row["company"].name

    def get_job_title(self, row):
        return row["job"].title

    def get_status(self, row):
        return row["application"].status

    def get_stage_name(self, row):
        return row["stage"].name if row["stage"] else None

    def get_applied_at(self, row):
        return row["application"].applied_at.isoformat() if row["application"].applied_at else None


class MyInterviewSchema(Schema):
    id = fields.UUID(dump_only=True)
    round_name = fields.Str(dump_only=True)
    scheduled_at = fields.DateTime(dump_only=True, allow_none=True)
    duration_minutes = fields.Int(dump_only=True, allow_none=True)
    status = fields.Str(dump_only=True)
    meeting_link = fields.Str(dump_only=True, allow_none=True)


class MyOfferSchema(Schema):
    id = fields.Method("get_id", dump_only=True)
    company_name = fields.Method("get_company_name", dump_only=True)
    job_title = fields.Method("get_job_title", dump_only=True)
    status = fields.Method("get_status", dump_only=True)
    salary_offered = fields.Method("get_salary", dump_only=True)
    joining_date = fields.Method("get_joining_date", dump_only=True)

    def get_id(self, row):
        return str(row["offer"].id)

    def get_company_name(self, row):
        return row["company"].name

    def get_job_title(self, row):
        return row["job"].title

    def get_status(self, row):
        return row["offer"].status

    def get_salary(self, row):
        return str(row["offer"].salary_offered) if row["offer"].salary_offered is not None else None

    def get_joining_date(self, row):
        return row["offer"].joining_date.isoformat() if row["offer"].joining_date else None


class MyNotificationSchema(Schema):
    id = fields.UUID(dump_only=True)
    type = fields.Str(dump_only=True)
    payload = fields.Dict(dump_only=True)
    read_at = fields.DateTime(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)