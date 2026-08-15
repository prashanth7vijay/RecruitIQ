from app.exceptions.base import PermissionDeniedError, ValidationError

ASSET_KEY_FIELDS = {
    "logo": "logo_key",
    "favicon": "favicon_key",
    "cover": "cover_image_key",
}
ALLOWED_FONTS = {
    "inter", "fraunces", "poppins", "sora",
    "ibm-plex-sans", "merriweather", "playfair-display", "space-grotesk",
}

BRANDING_TEXT_FIELDS = {
    "primary_color", "secondary_color", "font_heading", "font_body",
    "mission", "vision", "culture", "careers_headline",
    "careers_description", "social_links", "seo_title", "seo_description",
}


class CompanyService:
    def __init__(self, company_repo):
        self.company_repo = company_repo

    def get_own_company(self, tenant_id):
        return self.company_repo.get_or_404(tenant_id)

    def update_settings(self, tenant_id, requester_tenant_id, **fields):
        if str(tenant_id) != str(requester_tenant_id):
            raise PermissionDeniedError("Cannot modify another company's settings")

        company = self.company_repo.get_or_404(tenant_id)
        for key, value in fields.items():
            if value is not None:
                setattr(company, key, value)
        self.company_repo.commit()
        return company


    def get_branding(self, tenant_id, storage=None):

        company = self.company_repo.get_or_404(tenant_id)
        branding = dict((company.settings or {}).get("branding", {}))

        for asset_type, key_field in ASSET_KEY_FIELDS.items():
            storage_key = branding.get(key_field)
            url_field = f"{asset_type if asset_type != 'cover' else 'cover_image'}_url"
            if storage_key and storage is not None:
                branding[url_field] = storage.get_url(storage_key, expires_in=60 * 60 * 24 * 365)
            else:
                branding[url_field] = None

        return branding

    def update_branding(self, tenant_id, requester_tenant_id, **fields):
        if str(tenant_id) != str(requester_tenant_id):
            raise PermissionDeniedError("Cannot modify another company's settings")

        if "font_heading" in fields and fields["font_heading"] not in ALLOWED_FONTS | {None}:
            raise ValidationError("Unsupported font choice")
        if "font_body" in fields and fields["font_body"] not in ALLOWED_FONTS | {None}:
            raise ValidationError("Unsupported font choice")

        company = self.company_repo.get_or_404(tenant_id)
        settings = dict(company.settings or {})
        branding = dict(settings.get("branding", {}))
        for key in BRANDING_TEXT_FIELDS:
            if key in fields and fields[key] is not None:
                branding[key] = fields[key]
        settings["branding"] = branding
        company.settings = settings

        self.company_repo.commit()
        return company

    def set_branding_asset(self, tenant_id, requester_tenant_id, asset_type, storage_key):
        if str(tenant_id) != str(requester_tenant_id):
            raise PermissionDeniedError("Cannot modify another company's settings")
        if asset_type not in ASSET_KEY_FIELDS:
            raise ValidationError(f"Unknown branding asset type: {asset_type}")

        company = self.company_repo.get_or_404(tenant_id)
        settings = dict(company.settings or {})
        branding = dict(settings.get("branding", {}))
        branding[ASSET_KEY_FIELDS[asset_type]] = storage_key
        settings["branding"] = branding
        company.settings = settings

        self.company_repo.commit()
        return company
