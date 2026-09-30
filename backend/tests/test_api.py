import asyncio
from datetime import date
from pathlib import Path

import httpx
import pytest

import app.api as api_module
from app.extraction import GeminiExtraction, ExtractionError
from app.main import app
from app.models import (
    AssetType,
    AssignmentStatus,
    DocumentType,
    ExtractedField,
    ExtractionResult,
    HoldingPattern,
    MechanismType,
    NominationAction,
    PolicyKind,
    RegistrationStatus,
    TriState,
)


def extracted_result() -> ExtractionResult:
    return ExtractionResult(
        document_type=DocumentType.BANK_NOMINATION,
        classification_confidence=0.99,
        document_date=date(2026, 4, 1),
        fields=[
            ExtractedField(
                document_group_id="group-1",
                asset_type=AssetType.BANK_ACCOUNT,
                institution_name="Synthetic Bank",
                asset_reference="BANK-API-1",
                named_person="Synthetic Nominee",
                relationship="sibling",
                mechanism_type=MechanismType.NOMINEE,
                share_percent=100,
                source_text="Nominee: Synthetic Nominee",
                source_locator="line 5",
                confidence=0.98,
                registration_status=RegistrationStatus.UNCONFIRMED,
                registration_date=None,
                explicit_nomination_action=NominationAction.NONE,
                policy_kind=PolicyKind.UNKNOWN,
                mwpa_section_6_applies=TriState.UNKNOWN,
                assignment_status=AssignmentStatus.UNKNOWN,
                holding_pattern=HoldingPattern.SINGLE,
            )
        ],
        warnings=["Synthetic fixture"],
    )


def configure_storage(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "api.db"))
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))


async def create_persona(client: httpx.AsyncClient) -> int:
    response = await client.post(
        "/personas",
        json={
            "name": "Synthetic API Persona",
            "description": "No real person",
            "owner_has_family": "unknown",
            "marriage_date": None,
            "family_context_source_text": None,
            "manually_confirmed_aliases": [],
            "synthetic_confirmed": True,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_upload_extracts_and_persists_structured_fields(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_storage(monkeypatch, tmp_path)
    monkeypatch.setattr(
        api_module,
        "extract_document",
        lambda content, mime: GeminiExtraction(extracted_result(), "gemini-test"),
    )

    async def scenario() -> None:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                persona_id = await create_persona(client)
                response = await client.post(
                    f"/personas/{persona_id}/documents",
                    data={"synthetic_confirmed": "true"},
                    files={
                        "file": (
                            "synthetic.txt",
                            b"SYNTHETIC TEST DOCUMENT",
                            "text/plain",
                        )
                    },
                )
                assert response.status_code == 201
                document = response.json()
                assert document["status"] == "extracted"
                assert document["extraction_source"] == "gemini"
                assert document["model_name"] == "gemini-test"
                assert document["fields"][0]["asset_reference"] == "BANK-API-1"
                assert document["fields"][0]["source_text"]
                assert document["warnings"] == ["Synthetic fixture"]

                stored = await client.get(f"/documents/{document['id']}")
                assert stored.status_code == 200
                assert stored.json() == document

    asyncio.run(scenario())


def test_upload_requires_synthetic_confirmation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_storage(monkeypatch, tmp_path)

    async def scenario() -> None:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                persona_id = await create_persona(client)
                response = await client.post(
                    f"/personas/{persona_id}/documents",
                    data={"synthetic_confirmed": "false"},
                    files={"file": ("synthetic.txt", b"synthetic", "text/plain")},
                )
                assert response.status_code == 400
                assert response.json()["detail"]["code"] == (
                    "synthetic_confirmation_required"
                )
                assert not (tmp_path / "uploads").exists()

    asyncio.run(scenario())


def test_failed_extraction_is_visible_and_retryable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_storage(monkeypatch, tmp_path)

    def fail_extraction(content: bytes, mime_type: str) -> GeminiExtraction:
        raise ExtractionError(
            "gemini_api_error",
            "Synthetic provider failure.",
            retryable=True,
        )

    monkeypatch.setattr(api_module, "extract_document", fail_extraction)

    async def scenario() -> None:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                persona_id = await create_persona(client)
                failed = await client.post(
                    f"/personas/{persona_id}/documents",
                    data={"synthetic_confirmed": "true"},
                    files={"file": ("synthetic.txt", b"synthetic", "text/plain")},
                )
                assert failed.status_code == 503
                document_id = failed.json()["document_id"]

                stored_failed = await client.get(f"/documents/{document_id}")
                assert stored_failed.json()["status"] == "failed"
                assert stored_failed.json()["error_code"] == "gemini_api_error"
                assert stored_failed.json()["fields"] == []

                monkeypatch.setattr(
                    api_module,
                    "extract_document",
                    lambda content, mime: GeminiExtraction(
                        extracted_result(), "gemini-test"
                    ),
                )
                retried = await client.post(f"/documents/{document_id}/extract")
                assert retried.status_code == 200
                assert retried.json()["status"] == "extracted"
                assert retried.json()["retry_count"] == 1

    asyncio.run(scenario())


def test_persona_creation_requires_true_synthetic_attestation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_storage(monkeypatch, tmp_path)

    async def scenario() -> None:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                response = await client.post(
                    "/personas",
                    json={"name": "Unconfirmed", "synthetic_confirmed": False},
                )
                assert response.status_code == 422

    asyncio.run(scenario())


def test_failed_retry_removes_stale_successful_fields(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_storage(monkeypatch, tmp_path)
    monkeypatch.setattr(
        api_module,
        "extract_document",
        lambda content, mime: GeminiExtraction(extracted_result(), "gemini-test"),
    )

    async def scenario() -> None:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                persona_id = await create_persona(client)
                uploaded = await client.post(
                    f"/personas/{persona_id}/documents",
                    data={"synthetic_confirmed": "true"},
                    files={"file": ("synthetic.txt", b"synthetic", "text/plain")},
                )
                document_id = uploaded.json()["id"]
                assert uploaded.json()["fields"]

                def fail(content: bytes, mime_type: str) -> GeminiExtraction:
                    raise ExtractionError(
                        "gemini_api_error",
                        "Synthetic transient failure.",
                        retryable=True,
                    )

                monkeypatch.setattr(api_module, "extract_document", fail)
                failed = await client.post(f"/documents/{document_id}/extract")
                assert failed.status_code == 503
                assert failed.json()["retryable"] is True

                stored = await client.get(f"/documents/{document_id}")
                assert stored.json()["status"] == "failed"
                assert stored.json()["fields"] == []

    asyncio.run(scenario())
