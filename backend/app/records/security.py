import re
from dataclasses import dataclass
from pathlib import PurePosixPath

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_TYPES = {
    ".pdf": ("application/pdf", b"%PDF-"),
    ".png": ("image/png", b"\x89PNG\r\n\x1a\n"),
    ".jpg": ("image/jpeg", b"\xff\xd8\xff"),
    ".jpeg": ("image/jpeg", b"\xff\xd8\xff"),
    ".txt": ("text/plain", b""),
}
SAFE_FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,179}$")


@dataclass(frozen=True)
class FileValidation:
    extension: str
    mime_type: str
    size_bytes: int
    safe_filename: str


def sanitize_filename(filename: str) -> str:
    raw = filename.strip()
    parts = PurePosixPath(raw.replace("\\", "/")).parts
    if "/" in raw or "\\" in raw or ".." in parts:
        raise ValueError("Filename is not allowed")
    cleaned = re.sub(r"\s+", " ", raw)
    if not cleaned or cleaned in {".", ".."} or not SAFE_FILENAME.fullmatch(cleaned):
        raise ValueError("Filename is not allowed")
    return cleaned


def validate_file(filename: str, content_type: str, data: bytes) -> FileValidation:
    safe_name = sanitize_filename(filename)
    extension = PurePosixPath(safe_name).suffix.lower()
    if extension not in ALLOWED_TYPES:
        raise ValueError("File extension is not allowed")
    expected_mime, signature = ALLOWED_TYPES[extension]
    if content_type != expected_mime:
        raise ValueError("MIME type does not match allowed type")
    if not data or len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("File size is not allowed")
    if signature and not data.startswith(signature):
        raise ValueError("File signature does not match file type")
    if extension == ".txt" and b"\x00" in data[:512]:
        raise ValueError("Text file signature is not allowed")
    return FileValidation(
        extension=extension,
        mime_type=expected_mime,
        size_bytes=len(data),
        safe_filename=safe_name,
    )


def metadata_safe_tags(tags: list[str]) -> list[str]:
    cleaned = [" ".join(tag.split()).lower()[:40] for tag in tags if tag and tag.strip()]
    return list(dict.fromkeys(cleaned))[:12]
