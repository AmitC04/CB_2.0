import asyncio
import io
from pathlib import Path

import pytest
from fastapi import UploadFile

from app.uploads import (
    UploadValidationError,
    load_upload,
    store_upload,
    validate_upload,
)


def make_upload(filename: str, content_type: str, content: bytes) -> UploadFile:
    return UploadFile(
        filename=filename,
        file=io.BytesIO(content),
        headers={"content-type": content_type},
    )


def test_validate_and_store_utf8_text(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    upload = make_upload("synthetic.txt", "text/plain", b"synthetic only")

    validated = asyncio.run(validate_upload(upload))
    storage_key = store_upload(validated)

    assert validated.original_filename == "synthetic.txt"
    assert validated.content_sha256
    assert Path(storage_key).name == storage_key
    assert load_upload(storage_key) == b"synthetic only"


def test_rejects_path_components() -> None:
    upload = make_upload("../private.txt", "text/plain", b"synthetic")

    with pytest.raises(UploadValidationError) as error:
        asyncio.run(validate_upload(upload))

    assert error.value.code == "invalid_filename"


def test_rejects_mismatched_file_signature() -> None:
    upload = make_upload("fake.pdf", "application/pdf", b"not a pdf")

    with pytest.raises(UploadValidationError) as error:
        asyncio.run(validate_upload(upload))

    assert error.value.code == "invalid_file_signature"


def test_rejects_file_over_configured_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "4")
    upload = make_upload("synthetic.txt", "text/plain", b"12345")

    with pytest.raises(UploadValidationError) as error:
        asyncio.run(validate_upload(upload))

    assert error.value.code == "file_too_large"
    assert error.value.status_code == 413


def test_accepts_supported_binary_signatures() -> None:
    fixtures = [
        ("synthetic.pdf", "application/pdf", b"%PDF-1.4\nsynthetic"),
        ("synthetic.png", "image/png", b"\x89PNG\r\n\x1a\nsynthetic"),
        ("synthetic.jpg", "image/jpeg", b"\xff\xd8\xffsynthetic"),
        ("synthetic.webp", "image/webp", b"RIFF0000WEBPsynthetic"),
    ]

    for filename, mime_type, content in fixtures:
        validated = asyncio.run(validate_upload(make_upload(filename, mime_type, content)))
        assert validated.mime_type == mime_type
