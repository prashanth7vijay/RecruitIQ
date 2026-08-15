from app.exceptions.base import ValidationError

MAGIC_BYTES = {
    b"%PDF-": "pdf",
    b"PK\x03\x04": "docx",  # docx/zip-based formats share this signature
}

ALLOWED_EXTENSIONS_FOR_DISPLAY = {"pdf", "docx", "doc"}

IMAGE_MAGIC_BYTES = {
    b"\x89PNG\r\n\x1a\n": "png",
    b"\xff\xd8\xff": "jpg",
    b"GIF87a": "gif",
    b"GIF89a": "gif",
}

IMAGE_ASSET_TYPES = {"logo", "favicon", "cover"}


class FileUploadService:
    def __init__(self, storage, max_size_mb: int = 15):
        self.storage = storage
        self.max_size_bytes = max_size_mb * 1024 * 1024

    def upload_resume(self, file_obj, tenant_id, candidate_id):
        self._validate_size(file_obj, max_size_mb=self.max_size_bytes // (1024 * 1024))
        self._validate_magic_bytes(file_obj)

        original_filename = file_obj.filename or "resume"
        key = self._build_key(tenant_id, candidate_id, original_filename)
        self.storage.save(file_obj, key)
        return key, original_filename

    # --- internal -----------------------------------------------------

    def _validate_size(self, file_obj, max_size_mb: int):
        max_size_bytes = max_size_mb * 1024 * 1024
        file_obj.seek(0, 2)  # seek to end
        size = file_obj.tell()
        file_obj.seek(0)
        if size == 0:
            raise ValidationError("Uploaded file is empty")
        if size > max_size_bytes:
            raise ValidationError(f"File exceeds the {max_size_mb}MB limit")

    def _validate_magic_bytes(self, file_obj):
        header = file_obj.read(8)
        file_obj.seek(0)

        for signature in MAGIC_BYTES:
            if header.startswith(signature):
                return

        raise ValidationError(
            "File does not appear to be a valid PDF or Word document "
            "(checked file content, not just the filename)"
        )

    def _build_key(self, tenant_id, candidate_id, filename):
        # {company_id}/resumes/{candidate_id}/{filename} — Phase 17.2:
        # tenant namespacing baked into the key itself, defense in depth
        # beyond the DB row's tenant scoping.
        safe_filename = filename.replace("/", "_").replace("\\", "_")
        return f"{tenant_id}/resumes/{candidate_id}/{safe_filename}"

    # --- images (Branding Center: logo/favicon/cover) ------------------
    #
    # Separate from upload_resume rather than a shared generic method with
    # a `kind` flag: the two have different magic-byte sets, different size
    # ceilings, and different key shapes. Keeping them distinct methods
    # means neither validation path can accidentally loosen to fit the
    # other (e.g. an image upload silently accepting a PDF signature).

    def upload_image(self, file_obj, tenant_id, asset_type, max_size_mb: int = 5):
        if asset_type not in IMAGE_ASSET_TYPES:
            raise ValidationError(f"Unknown branding asset type: {asset_type}")

        self._validate_size(file_obj, max_size_mb=max_size_mb)
        ext = self._validate_image_bytes(file_obj)

        key = f"{tenant_id}/branding/{asset_type}.{ext}"
        self.storage.save(file_obj, key)
        return key, ext

    def _validate_image_bytes(self, file_obj) -> str:
        header = file_obj.read(16)
        file_obj.seek(0)

        for signature, ext in IMAGE_MAGIC_BYTES.items():
            if header.startswith(signature):
                return ext

        if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
            return "webp"

        head_text = header.decode("utf-8", errors="ignore").lstrip()
        if head_text.startswith("<?xml") or head_text.startswith("<svg"):
            return "svg"

        raise ValidationError(
            "File does not appear to be a valid PNG, JPEG, WEBP, GIF, or SVG image "
            "(checked file content, not just the filename)"
        )
