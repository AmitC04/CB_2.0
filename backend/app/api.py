"""Phase 2 persona and synthetic-document API routes."""

import asyncio

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.detection import SCOPE_GAP, detect, finalize
from app.estate_case import build_estate_case
from app.explanations import ExplanationError, generate_explanation
from app.extraction import ExtractionError, extract_document
from app.models import (
    DetectionRunRead,
    DocumentListRead,
    DocumentRead,
    EstateCaseItemRead,
    EstateCaseRead,
    ExtractionFailureRead,
    FieldUpdate,
    PersonaCreate,
    PersonaListRead,
    PersonaRead,
)
from app.scoring import completeness_gaps, readiness_score
from app.repository import (
    ExtractionInProgressError,
    NoEditToUndoError,
    RecordNotFoundError,
    create_document,
    create_persona,
    get_detection_run,
    get_document,
    get_document_storage,
    get_latest_detection_run,
    get_persona,
    has_user_edited_fields,
    list_documents,
    list_personas,
    load_field_records,
    load_persona_context,
    mark_extraction_failed,
    mark_extracting,
    save_detection_run,
    save_extraction,
    undo_last_field_edit,
    update_extracted_field,
)
from app.uploads import (
    UploadValidationError,
    ValidatedUpload,
    load_upload,
    remove_upload,
    store_upload,
    validate_upload,
)

router = APIRouter()

# Explanations are optional wording, so cap the per-request AI fan-out. Findings beyond
# the cap are still returned with their deterministic summary, actions, and disclaimer.
MAX_EXPLAINED_FINDINGS = 10


def not_found(exc: RecordNotFoundError) -> HTTPException:
    return HTTPException(status_code=404, detail=str(exc))


def extraction_failure_response(
    document_id: int,
    error: ExtractionError,
) -> JSONResponse:
    body = ExtractionFailureRead(
        code=error.code,
        message=error.safe_message,
        document_id=document_id,
        retryable=error.retryable,
    )
    return JSONResponse(status_code=error.http_status, content=body.model_dump(mode="json"))


async def run_extraction(
    document_id: int,
    content: bytes,
    mime_type: str,
    *,
    retry: bool,
) -> DocumentRead | JSONResponse:
    try:
        mark_extracting(document_id, retry=retry)
    except ExtractionInProgressError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    try:
        extracted = await asyncio.to_thread(extract_document, content, mime_type)
    except ExtractionError as exc:
        mark_extraction_failed(document_id, exc.code)
        return extraction_failure_response(document_id, exc)

    try:
        save_extraction(
            document_id,
            extracted.result,
            model_name=extracted.model_name,
        )
    except Exception as exc:
        mark_extraction_failed(document_id, "extraction_persistence_error")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "extraction_persistence_error",
                "message": "Extraction could not be stored; stale fields were removed.",
            },
        ) from exc
    return get_document(document_id)


@router.post(
    "/personas",
    response_model=PersonaRead,
    status_code=status.HTTP_201_CREATED,
    tags=["personas"],
)
def create_synthetic_persona(payload: PersonaCreate) -> PersonaRead:
    """Create a persona only after explicit synthetic-data attestation."""
    return create_persona(payload)


@router.get("/personas/{persona_id}", response_model=PersonaRead, tags=["personas"])
def read_persona(persona_id: int) -> PersonaRead:
    try:
        return get_persona(persona_id)
    except RecordNotFoundError as exc:
        raise not_found(exc) from exc


@router.get(
    "/personas/{persona_id}/documents",
    response_model=DocumentListRead,
    tags=["documents"],
)
def read_persona_documents(persona_id: int) -> DocumentListRead:
    try:
        return DocumentListRead(documents=list_documents(persona_id))
    except RecordNotFoundError as exc:
        raise not_found(exc) from exc


@router.post(
    "/personas/{persona_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    responses={503: {"model": ExtractionFailureRead}},
    tags=["documents"],
)
async def upload_synthetic_document(
    persona_id: int,
    file: UploadFile = File(...),
    synthetic_confirmed: bool = Form(...),
) -> DocumentRead | JSONResponse:
    """Store and extract a document explicitly confirmed as synthetic."""
    if not synthetic_confirmed:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "synthetic_confirmation_required",
                "message": "Only synthetic documents are allowed in this demo.",
            },
        )
    try:
        get_persona(persona_id)
    except RecordNotFoundError as exc:
        raise not_found(exc) from exc

    try:
        validated = await validate_upload(file)
    except UploadValidationError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": exc.message},
        ) from exc

    storage_key = store_upload(validated)
    try:
        document_id = create_document(persona_id, validated, storage_key)
    except Exception:
        remove_upload(storage_key)
        raise

    return await run_extraction(
        document_id,
        validated.content,
        validated.mime_type,
        retry=False,
    )


@router.post(
    "/documents/{document_id}/extract",
    response_model=DocumentRead,
    responses={503: {"model": ExtractionFailureRead}},
    tags=["documents"],
)
async def retry_document_extraction(
    document_id: int,
    force: bool = False,
) -> DocumentRead | JSONResponse:
    """Retry Gemini extraction using the already-stored synthetic upload.

    Re-extraction replaces every extracted field for the document, which would discard
    simulated fixes. That requires an explicit ``force=true``.
    """
    if not force and has_user_edited_fields(document_id):
        raise HTTPException(
            status_code=409,
            detail={
                "code": "user_edits_would_be_discarded",
                "message": (
                    "This document has simulated fixes. Re-extraction would replace them. "
                    "Repeat with force=true to discard the fixes."
                ),
            },
        )
    try:
        storage_key, mime_type = get_document_storage(document_id)
        content = load_upload(storage_key)
    except RecordNotFoundError as exc:
        raise not_found(exc) from exc
    except OSError as exc:
        mark_extraction_failed(document_id, "stored_upload_missing")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "stored_upload_missing",
                "message": "The stored upload is unavailable; extraction cannot be retried.",
            },
        ) from exc

    return await run_extraction(
        document_id,
        content,
        mime_type,
        retry=True,
    )


@router.get("/documents/{document_id}", response_model=DocumentRead, tags=["documents"])
def read_document(document_id: int) -> DocumentRead:
    try:
        return get_document(document_id)
    except RecordNotFoundError as exc:
        raise not_found(exc) from exc


@router.post(
    "/personas/{persona_id}/detections",
    response_model=DetectionRunRead,
    status_code=status.HTTP_201_CREATED,
    tags=["detection"],
)
async def run_conflict_detection(
    persona_id: int,
    explain: bool = True,
) -> DetectionRunRead:
    """Run the deterministic rule engine, then optionally add plain-language wording.

    Rule matching, severity, and sources are decided entirely in Python. Gemini is
    called only after a finding is fixed, and a failed call never hides the finding.
    """
    try:
        context = load_persona_context(persona_id)
        records = load_field_records(persona_id)
    except RecordNotFoundError as exc:
        raise not_found(exc) from exc

    result = detect(records, context)
    all_findings = finalize(
        result.findings + completeness_gaps(records, result.findings)
    )
    score = readiness_score(all_findings)
    explained_budget = MAX_EXPLAINED_FINDINGS
    paired: list[tuple[object, tuple[str | None, str | None, str | None] | None]] = []
    for finding in all_findings:
        explanation: tuple[str | None, str | None, str | None] | None = None
        if explain and finding.finding_type != SCOPE_GAP and explained_budget > 0:
            explained_budget -= 1
            try:
                generated = await asyncio.to_thread(generate_explanation, finding)
                explanation = (
                    generated.plain_language,
                    generated.suggested_fix,
                    "gemini",
                )
            except ExplanationError:
                explanation = (None, None, "unavailable")
        paired.append((finding, explanation))

    run_id = save_detection_run(persona_id, paired, readiness_score=score)  # type: ignore[arg-type]
    return get_detection_run(run_id)


@router.get(
    "/personas/{persona_id}/detections/latest",
    response_model=DetectionRunRead,
    tags=["detection"],
)
def read_latest_detection(persona_id: int) -> DetectionRunRead:
    try:
        return get_latest_detection_run(persona_id)
    except RecordNotFoundError as exc:
        raise not_found(exc) from exc


@router.get("/personas", response_model=PersonaListRead, tags=["personas"])
def read_personas() -> PersonaListRead:
    return PersonaListRead(personas=list_personas())


@router.patch(
    "/fields/{field_id}",
    response_model=DocumentRead,
    tags=["documents"],
)
def apply_simulated_fix(field_id: int, payload: FieldUpdate) -> DocumentRead:
    """Apply a synthetic correction to one extracted field.

    This edits the extracted synthetic record only. It does not change any uploaded
    document and has no effect on any real institution.
    """
    if payload.named_person is None and payload.relationship is None:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "no_field_values",
                "message": "Provide named_person or relationship to apply a fix.",
            },
        )
    try:
        _, document_id = update_extracted_field(
            field_id,
            named_person=payload.named_person,
            relationship=payload.relationship,
        )
        return get_document(document_id)
    except RecordNotFoundError as exc:
        raise not_found(exc) from exc


@router.get(
    "/personas/{persona_id}/estate-case",
    response_model=EstateCaseRead,
    tags=["concept"],
)
def read_estate_case_concept(persona_id: int) -> EstateCaseRead:
    """Concept / future feature: an illustrative per-institution settlement checklist.

    Nothing here is an institution integration. The steps are generic illustrations
    derived from the synthetic vault, and no request is made to any third party.
    """
    try:
        records = load_field_records(persona_id)
    except RecordNotFoundError as exc:
        raise not_found(exc) from exc

    unresolved = 0
    score: int | None = None
    try:
        latest = get_latest_detection_run(persona_id)
        unresolved = len(latest.conflicts)
        score = latest.readiness_score
    except RecordNotFoundError:
        unresolved = 0

    case = build_estate_case(
        records,
        unresolved_conflicts=unresolved,
        readiness_score=score,
    )
    return EstateCaseRead(
        concept=True,
        label=case.label,
        notice=case.notice,
        disclaimer=case.disclaimer,
        unresolved_conflicts=case.unresolved_conflicts,
        readiness_score=case.readiness_score,
        items=[
            EstateCaseItemRead(
                institution_name=item.institution_name,
                asset_type=item.asset_type,
                asset_type_label=item.asset_type_label,
                asset_reference=item.asset_reference,
                named_people=list(item.named_people),
                has_nomination_on_record=item.has_nomination_on_record,
                illustrative_steps=list(item.illustrative_steps),
            )
            for item in case.items
        ],
    )


@router.post(
    "/fields/{field_id}/undo",
    response_model=DocumentRead,
    tags=["documents"],
)
def undo_simulated_fix(field_id: int) -> DocumentRead:
    """Revert the most recent simulated fix for one extracted field."""
    try:
        _, document_id = undo_last_field_edit(field_id)
        return get_document(document_id)
    except NoEditToUndoError as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": "no_edit_to_undo", "message": str(exc)},
        ) from exc
    except RecordNotFoundError as exc:
        raise not_found(exc) from exc
