from marshmallow import Schema, fields


class SearchCandidateResultSchema(Schema):
    id = fields.UUID(dump_only=True)
    candidate = fields.Method("get_candidate", dump_only=True)

    def get_candidate(self, profile):
        c = profile.candidate
        return {"first_name": c.first_name, "last_name": c.last_name, "email": c.email} if c else None


class SearchJobResultSchema(Schema):
    id = fields.UUID(dump_only=True)
    title = fields.Str(dump_only=True)
    status = fields.Str(dump_only=True)
