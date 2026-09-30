"""Validated API and Gemini extraction contracts."""

from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TriState(StrEnum):
    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"


class DocumentType(StrEnum):
    WILL = "will"
    BANK_NOMINATION = "bank_nomination"
    INSURANCE_NOMINATION = "insurance_nomination"
    MUTUAL_FUND_NOMINATION = "mutual_fund_nomination"
    NPS_NOMINATION = "nps_nomination"
    UNKNOWN = "unknown"


class AssetType(StrEnum):
    BANK_ACCOUNT = "bank_account"
    INSURANCE_POLICY = "insurance_policy"
    MUTUAL_FUND_FOLIO = "mutual_fund_folio"
    NPS_ACCOUNT = "nps_account"
    OTHER = "other"


class MechanismType(StrEnum):
    NOMINEE = "nominee"
    BEQUEST = "bequest"
    BENEFICIARY_NOMINEE = "beneficiary_nominee"


class RegistrationStatus(StrEnum):
    CONFIRMED = "confirmed"
    UNCONFIRMED = "unconfirmed"
    NOT_REGISTERED = "not_registered"
    UNKNOWN = "unknown"


class NominationAction(StrEnum):
    NONE = "none"
    CHANGE = "change"
    CANCEL = "cancel"


class PolicyKind(StrEnum):
    LIFE = "life"
    OTHER = "other"
    UNKNOWN = "unknown"


class AssignmentStatus(StrEnum):
    ACTIVE = "active"
    NONE = "none"
    UNKNOWN = "unknown"


class HoldingPattern(StrEnum):
    SINGLE = "single"
    JOINT = "joint"
    UNKNOWN = "unknown"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    FAILED = "failed"


class PersonaCreate(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    owner_has_family: TriState = TriState.UNKNOWN
    marriage_date: date | None = None
    family_context_source_text: str | None = Field(default=None, max_length=1000)
    manually_confirmed_aliases: list[tuple[str, str]] = Field(default_factory=list)
    synthetic_confirmed: Literal[True]

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be blank")
        return cleaned


class PersonaRead(StrictModel):
    id: int
    name: str
    description: str | None
    owner_has_family: TriState
    marriage_date: date | None
    family_context_source_text: str | None
    manually_confirmed_aliases: list[tuple[str, str]]
    created_at: str


class ExtractedField(StrictModel):
    document_group_id: str = Field(min_length=1, max_length=80)
    asset_type: AssetType
    institution_name: str = Field(max_length=200)
    asset_reference: str = Field(max_length=200)
    named_person: str = Field(max_length=200)
    relationship: str = Field(max_length=100)
    mechanism_type: MechanismType
    share_percent: float | None = Field(default=None, ge=0, le=100)
    source_text: str = Field(min_length=1, max_length=4000)
    source_locator: str = Field(min_length=1, max_length=200)
    confidence: float = Field(ge=0, le=1)
    registration_status: RegistrationStatus
    registration_date: date | None = None
    explicit_nomination_action: NominationAction
    policy_kind: PolicyKind
    mwpa_section_6_applies: TriState
    assignment_status: AssignmentStatus
    holding_pattern: HoldingPattern

    @field_validator(
        "document_group_id",
        "institution_name",
        "asset_reference",
        "named_person",
        "relationship",
        "source_text",
        "source_locator",
    )
    @classmethod
    def trim_strings(cls, value: str) -> str:
        return value.strip()


class ExtractionResult(StrictModel):
    document_type: DocumentType
    classification_confidence: float = Field(ge=0, le=1)
    document_date: date | None = None
    fields: list[ExtractedField] = Field(max_length=50)
    warnings: list[str] = Field(max_length=20)


class ExtractedFieldRead(ExtractedField):
    id: int
    document_id: int
    is_user_edited: bool
    holding_pattern: HoldingPattern = HoldingPattern.UNKNOWN


class DocumentRead(StrictModel):
    id: int
    persona_id: int
    original_filename: str
    mime_type: str
    content_sha256: str
    size_bytes: int
    synthetic_confirmed: bool
    document_type: DocumentType | None
    document_date: date | None
    status: DocumentStatus
    extraction_source: str | None
    model_name: str | None
    error_code: str | None
    retry_count: int
    uploaded_at: str
    extracted_at: str | None
    classification_confidence: float | None
    warnings: list[str]
    fields: list[ExtractedFieldRead]
    disclaimer: str


class ExtractionFailureRead(StrictModel):
    code: str
    message: str
    document_id: int
    retryable: bool


class DocumentListRead(StrictModel):
    documents: list[DocumentRead]


class FindingType(StrEnum):
    REVIEW_CONFLICT = "review_conflict"
    VALIDITY_WARNING = "validity_warning"
    SCOPE_GAP = "scope_gap"


class Severity(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExplanationSource(StrEnum):
    GEMINI = "gemini"
    UNAVAILABLE = "unavailable"


class FindingSourceRead(StrictModel):
    label: str
    locator: str
    text: str
    field_id: int | None


class FindingRead(StrictModel):
    id: int
    rule_id: str
    rules_version: str
    finding_type: FindingType
    severity: Severity
    asset_type: str
    asset_reference: str
    summary: str
    legal_scope_note: str
    suggested_actions: list[str]
    source_a: FindingSourceRead
    source_b: FindingSourceRead | None
    explanation: str | None
    suggested_fix: str | None
    explanation_source: ExplanationSource | None
    disclaimer: str


class DetectionRunRead(StrictModel):
    id: int
    persona_id: int
    rules_version: str
    readiness_score: int | None
    score_breakdown: dict[str, int]
    run_at: str
    disclaimer: str
    conflicts: list[FindingRead]
    scope_gaps: list[FindingRead]


class PersonaListRead(StrictModel):
    personas: list[PersonaRead]


class FieldUpdate(StrictModel):
    named_person: str | None = Field(default=None, max_length=200)
    relationship: str | None = Field(default=None, max_length=100)

    @field_validator("named_person", "relationship")
    @classmethod
    def reject_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must not be blank")
        return cleaned


class EstateCaseItemRead(StrictModel):
    institution_name: str
    asset_type: str
    asset_type_label: str
    asset_reference: str
    named_people: list[str]
    has_nomination_on_record: bool
    illustrative_steps: list[str]


class EstateCaseRead(StrictModel):
    """Phase 7 stretch concept. Never a working institution integration."""

    concept: Literal[True]
    label: str
    notice: str
    disclaimer: str
    unresolved_conflicts: int
    readiness_score: int | None
    items: list[EstateCaseItemRead]
