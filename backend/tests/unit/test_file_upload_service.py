import io

import pytest

from app.exceptions.base import ValidationError
from app.services.file_upload_service import FileUploadService


class _FakeStorage:
    def save(self, file_obj, key):
        return key


def _fake_file(content: bytes, filename="resume.pdf"):
    f = io.BytesIO(content)
    f.filename = filename
    return f


def test_accepts_valid_pdf_magic_bytes():
    service = FileUploadService(_FakeStorage())
    file_obj = _fake_file(b"%PDF-1.4 rest of a real pdf content here")

    key, filename = service.upload_resume(file_obj, tenant_id="tenant-1", candidate_id="cand-1")

    assert key == "tenant-1/resumes/cand-1/resume.pdf"
    assert filename == "resume.pdf"


def test_rejects_file_with_wrong_content_despite_pdf_extension():
    service = FileUploadService(_FakeStorage())
    file_obj = _fake_file(b"MZ\x90\x00this is actually an executable", filename="resume.pdf")

    with pytest.raises(ValidationError, match="does not appear to be a valid"):
        service.upload_resume(file_obj, tenant_id="tenant-1", candidate_id="cand-1")


def test_rejects_empty_file():
    service = FileUploadService(_FakeStorage())
    file_obj = _fake_file(b"")

    with pytest.raises(ValidationError, match="empty"):
        service.upload_resume(file_obj, tenant_id="tenant-1", candidate_id="cand-1")


def test_rejects_file_exceeding_size_limit():
    service = FileUploadService(_FakeStorage(), max_size_mb=1)
    oversized_content = b"%PDF-" + (b"a" * (2 * 1024 * 1024))
    file_obj = _fake_file(oversized_content)

    with pytest.raises(ValidationError, match="exceeds"):
        service.upload_resume(file_obj, tenant_id="tenant-1", candidate_id="cand-1")


def test_docx_magic_bytes_accepted():
    service = FileUploadService(_FakeStorage())
    file_obj = _fake_file(b"PK\x03\x04rest of a real docx zip content", filename="resume.docx")

    key, _ = service.upload_resume(file_obj, tenant_id="tenant-1", candidate_id="cand-1")
    assert key.endswith("resume.docx")
