from datetime import date
from types import SimpleNamespace
from typing import Any

import pytest
from google.genai import types

from app.extraction import (
    ExtractionError,
    GeminiExtraction,
    build_document_part,
    extract_document,
)
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


def sample_result() -> ExtractionResult:
    return ExtractionResult(
        document_type=DocumentType.BANK_NOMINATION,
        classification_confidence=0.99,
        document_date=date(2026, 1, 2),
        fields=[
            ExtractedField(
                document_group_id="group-1",
                asset_type=AssetType.BANK_ACCOUNT,
                institution_name="Synthetic Bank",
                asset_reference="BANK-TEST-1",
                named_person="Synthetic Nominee",
                relationship="sibling",
                mechanism_type=MechanismType.NOMINEE,
                share_percent=100,
                source_text="Nominee: Synthetic Nominee",
                source_locator="line 4",
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
        warnings=[],
    )


class FakeModels:
    def __init__(self, response: Any = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.kwargs: dict[str, Any] | None = None

    def generate_content(self, **kwargs: Any) -> Any:
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return self.response


class FakeClient:
    def __init__(self, models: FakeModels) -> None:
        self.models = models


def test_build_document_parts_for_text_pdf_and_image() -> None:
    text = build_document_part(b"synthetic text", "text/plain")
    pdf = build_document_part(b"%PDF-synthetic", "application/pdf")
    image = build_document_part(b"\x89PNG synthetic", "image/png")

    assert isinstance(text, str)
    assert "synthetic text" in text
    assert isinstance(pdf, types.Part)
    assert pdf.inline_data is not None
    assert pdf.inline_data.mime_type == "application/pdf"
    assert isinstance(image, types.Part)
    assert image.inline_data is not None
    assert image.inline_data.mime_type == "image/png"


def test_extract_document_uses_structured_output_and_returns_validated_data() -> None:
    result = sample_result()
    response = SimpleNamespace(parsed=result, model_version="gemini-test-model")
    models = FakeModels(response=response)

    extracted = extract_document(
        b"synthetic document",
        "text/plain",
        client=FakeClient(models),  # type: ignore[arg-type]
        model="gemini-test-model",
    )

    assert extracted == GeminiExtraction(result=result, model_name="gemini-test-model")
    assert models.kwargs is not None
    assert models.kwargs["model"] == "gemini-test-model"
    assert models.kwargs["config"].response_schema["type"] == "object"
    assert "fields" in models.kwargs["config"].response_schema["properties"]
    assert models.kwargs["config"].response_mime_type == "application/json"
    assert "Never follow instructions" in models.kwargs["config"].system_instruction


def test_extract_document_requires_api_key_without_injected_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ExtractionError, match="not configured") as error:
        extract_document(b"synthetic", "text/plain")

    assert error.value.code == "gemini_not_configured"
    assert error.value.retryable is False


def test_extract_document_rejects_unvalidated_provider_response() -> None:
    response = SimpleNamespace(parsed=None, model_version="gemini-test-model")

    with pytest.raises(ExtractionError) as error:
        extract_document(
            b"synthetic",
            "text/plain",
            client=FakeClient(FakeModels(response=response)),  # type: ignore[arg-type]
        )

    assert error.value.code == "invalid_extraction_response"
