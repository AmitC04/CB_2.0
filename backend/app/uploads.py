"""Synthetic-only upload validation and local storage."""

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

DEFAULT_UPLOAD_DIR = Path(__file__).resolve().parents[1] / "data" / "uploads"
DEFAULT_MAX_UPLOAD_BYTES = 10 * 1024 * 1024
CHUNK_SIZE = 64 * 1024

ALLOWED_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".txt": "text/plain",
}


class UploadValidationError(ValueError):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class ValidatedUpload:
    original_filename: str
    mime_type: str
    extension: str
    content: bytes
    content_sha256: str

    @property
    def size_bytes(self) -> int:
        return len(self.content)


def get_upload_dir() -> Path:
    return Path(os.getenv("UPLOAD_DIR", str(DEFAULT_UPLOAD_DIR)))


def get_max_upload_bytes() -> int:
    try:
        value = int(os.getenv("MAX_UPLOAD_BYTES", str(DEFAULT_MAX_UPLOAD_BYTES)))
    except ValueError as exc:
        raise RuntimeError("MAX_UPLOAD_BYTES must be an integer") from exc
    if value <= 0:
        raise RuntimeError("MAX_UPLOAD_BYTES must be positive")
    return value


def _validate_filename(filename: str | None) -> tuple[str, str]:
    if not filename or filename in {".", ".."}:
        raise UploadValidationError("invalid_filename", "A safe filename is required.")
    if any(character in filename for character in ("/", "\\", "\x00")):
        raise UploadValidationError(
            "invalid_filename",
            "Path components are not allowed in filenames.",
        )
    if len(filename) > 255:
        raise UploadValidationError("invalid_filename", "Filename is too long.")

    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_TYPES:
        raise UploadValidationError(
            "unsupported_file_type",
            "Allowed extensions: PDF, PNG, JPG, JPEG, WEBP, and TXT.",
            415,
        )
    return filename, extension


def _validate_signature(content: bytes, extension: str) -> None:
    valid = False
    if extension == ".pdf":
        valid = content.startswith(b"%PDF-")
    elif extension == ".png":
        valid = content.startswith(b"\x89PNG\r\n\x1a\n")
    elif extension in {".jpg", ".jpeg"}:
        valid = content.startswith(b"\xff\xd8\xff")
    elif extension == ".webp":
        valid = (
            len(content) >= 12
            and content.startswith(b"RIFF")
            and content[8:12] == b"WEBP"
        )
    elif extension == ".txt":
        try:
            decoded = content.decode("utf-8")
            valid = "\x00" not in decoded
        except UnicodeDecodeError:
            valid = False

    if not valid:
        raise UploadValidationError(
            "invalid_file_signature",
            "File contents do not match the declared type.",
            415,
        )


async def validate_upload(upload: UploadFile) -> ValidatedUpload:
    filename, extension = _validate_filename(upload.filename)
    declared_type = (upload.content_type or "").split(";", maxsplit=1)[0].strip().lower()
    expected_type = ALLOWED_TYPES[extension]
    if declared_type != expected_type:
        raise UploadValidationError(
            "mime_type_mismatch",
            f"Expected content type {expected_type} for {extension}.",
            415,
        )

    limit = get_max_upload_bytes()
    chunks: list[bytes] = []
    total = 0
    try:
        while chunk := await upload.read(CHUNK_SIZE):
            total += len(chunk)
            if total > limit:
                raise UploadValidationError(
                    "file_too_large",
                    f"File exceeds the {limit}-byte upload limit.",
                    413,
                )
            chunks.append(chunk)
    finally:
        await upload.close()

    content = b"".join(chunks)
    if not content:
        raise UploadValidationError("empty_file", "The uploaded file is empty.")
    _validate_signature(content, extension)

    return ValidatedUpload(
        original_filename=filename,
        mime_type=expected_type,
        extension=extension,
        content=content,
        content_sha256=hashlib.sha256(content).hexdigest(),
    )


def store_upload(upload: ValidatedUpload) -> str:
    upload_dir = get_upload_dir().resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    storage_key = f"{uuid4().hex}{upload.extension}"
    destination = (upload_dir / storage_key).resolve()
    if destination.parent != upload_dir:
        raise RuntimeError("Generated upload path escaped the upload directory")
    destination.write_bytes(upload.content)
    return storage_key


def load_upload(storage_key: str) -> bytes:
    if Path(storage_key).name != storage_key:
        raise RuntimeError("Invalid stored upload key")
    upload_dir = get_upload_dir().resolve()
    source = (upload_dir / storage_key).resolve()
    if source.parent != upload_dir:
        raise RuntimeError("Stored upload path escaped the upload directory")
    return source.read_bytes()


def remove_upload(storage_key: str) -> None:
    if Path(storage_key).name == storage_key:
        (get_upload_dir().resolve() / storage_key).unlink(missing_ok=True)
