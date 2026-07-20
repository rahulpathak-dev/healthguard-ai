import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from app.dashboard.models import MedicalRecord
from app.records.security import metadata_safe_tags, sanitize_filename, validate_file
from app.records.service import signed_access
from app.records.storage import LocalPrivateStorage


def test_filename_validation_blocks_path_traversal() -> None:
    with pytest.raises(ValueError):
        sanitize_filename("../lab.pdf")
    with pytest.raises(ValueError):
        sanitize_filename("..\\lab.pdf")
    assert sanitize_filename("Lab Report 2026.pdf") == "Lab Report 2026.pdf"


def test_file_validation_requires_extension_mime_and_signature_match() -> None:
    valid = validate_file("report.pdf", "application/pdf", b"%PDF-1.7 content")
    assert valid.extension == ".pdf"
    with pytest.raises(ValueError, match="MIME"):
        validate_file("report.pdf", "text/plain", b"%PDF-1.7 content")
    with pytest.raises(ValueError, match="signature"):
        validate_file("report.pdf", "application/pdf", b"not a pdf")
    with pytest.raises(ValueError, match="extension"):
        validate_file("script.exe", "application/octet-stream", b"MZ")


def test_text_upload_rejects_binary_signature() -> None:
    with pytest.raises(ValueError, match="Text file signature"):
        validate_file("notes.txt", "text/plain", b"hello\x00world")


def test_metadata_tags_are_normalized_and_bounded() -> None:
    result = metadata_safe_tags([" Lab ", "lab", "Very Long Tag Name That Should Be Trimmed"])
    assert result == ["lab", "very long tag name that should be trimmed"[:40]]


def test_signed_storage_url_expires_and_detects_tampering(tmp_path) -> None:
    store = LocalPrivateStorage(str(tmp_path))
    url = store.signed_url("quarantine/record/file.pdf")
    query = dict(item.split("=") for item in url.split("?", 1)[1].split("&"))
    assert store.validate_signature(query["path"], int(query["expires"]), query["signature"])
    assert not store.validate_signature(
        "quarantine/other/file.pdf", int(query["expires"]), query["signature"]
    )
    expired = int((datetime.now(UTC) - timedelta(minutes=1)).timestamp())
    assert not store.validate_signature(query["path"], expired, query["signature"])


def test_quarantined_records_do_not_receive_download_links() -> None:
    record = MedicalRecord(
        id=uuid.uuid4(),
        profile_id=uuid.uuid4(),
        owner_user_id=uuid.uuid4(),
        title="Lab",
        record_type="lab_report",
        original_filename="lab.pdf",
        mime_type="application/pdf",
        file_size_bytes=20,
        storage_path="quarantine/record/lab.pdf",
        sha256="a" * 64,
        status="quarantined",
        scan_status="pending",
        tags_json=[],
        metadata_json={},
        occurred_at=None,
        created_at=datetime.now(UTC),
    )
    with pytest.raises(HTTPException):
        signed_access(record)
