from marshmallow import Schema, fields, validate, EXCLUDE

HEX_COLOR = validate.Regexp(r"^#[0-9A-Fa-f]{6}$", error="Must be a hex color like #4F46E5")
SOCIAL_PLATFORMS = {"linkedin", "twitter", "instagram", "facebook", "glassdoor", "youtube"}


class SocialLinksField(fields.Dict):

    def __init__(self, **kwargs):
        super().__init__(
            keys=fields.Str(validate=validate.OneOf(SOCIAL_PLATFORMS)),
            values=fields.Url(),
            **kwargs,
        )


class UpdateCompanySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(required=False, validate=validate.Length(min=1, max=255))
    settings = fields.Dict(required=False)


class CompanySchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.Str(dump_only=True)
    slug = fields.Str(dump_only=True)
    plan = fields.Str(dump_only=True)
    settings = fields.Dict(dump_only=True)
    status = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class UpdateBrandingSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    primary_color = fields.Str(required=False, validate=HEX_COLOR)
    secondary_color = fields.Str(required=False, validate=HEX_COLOR)
    font_heading = fields.Str(required=False)  # allowlist enforced in the service
    font_body = fields.Str(required=False)
    mission = fields.Str(required=False, validate=validate.Length(max=2000))
    vision = fields.Str(required=False, validate=validate.Length(max=2000))
    culture = fields.Str(required=False, validate=validate.Length(max=2000))
    careers_headline = fields.Str(required=False, validate=validate.Length(max=200))
    careers_description = fields.Str(required=False, validate=validate.Length(max=5000))
    social_links = SocialLinksField(required=False)
    seo_title = fields.Str(required=False, validate=validate.Length(max=70))
    seo_description = fields.Str(required=False, validate=validate.Length(max=160))


class BrandingSchema(Schema):

    logo_url = fields.Str(dump_only=True, allow_none=True)
    favicon_url = fields.Str(dump_only=True, allow_none=True)
    cover_image_url = fields.Str(dump_only=True, allow_none=True)
    primary_color = fields.Str(dump_only=True, allow_none=True)
    secondary_color = fields.Str(dump_only=True, allow_none=True)
    font_heading = fields.Str(dump_only=True, allow_none=True)
    font_body = fields.Str(dump_only=True, allow_none=True)
    mission = fields.Str(dump_only=True, allow_none=True)
    vision = fields.Str(dump_only=True, allow_none=True)
    culture = fields.Str(dump_only=True, allow_none=True)
    careers_headline = fields.Str(dump_only=True, allow_none=True)
    careers_description = fields.Str(dump_only=True, allow_none=True)
    social_links = fields.Dict(dump_only=True)
    seo_title = fields.Str(dump_only=True, allow_none=True)
    seo_description = fields.Str(dump_only=True, allow_none=True)


class PublicCompanySchema(Schema):
    name = fields.Str(dump_only=True)
    slug = fields.Str(dump_only=True)
    branding = fields.Nested(BrandingSchema, dump_only=True)
