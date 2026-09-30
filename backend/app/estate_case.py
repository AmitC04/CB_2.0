"""Phase 7 stretch: an illustrative estate-case view.

This is a **concept / future feature**. It derives a generic, illustrative settlement
checklist from the synthetic vault records so the interface can show what the later
settlement product might look like.

Hard limits, enforced here and stated in every response:

* No institution is integrated. Nothing is submitted, checked, or retrieved anywhere.
* The steps are generic placeholders, not any institution's actual requirements, and
  are not legal or procedural advice.
* Nothing in this module feeds the conflict engine or the readiness score.
"""

from dataclasses import dataclass, field as dataclass_field

from app.detection import DISCLAIMER, FieldRecord, normalize_text

CONCEPT_LABEL = "Concept / Future Feature"
CONCEPT_NOTICE = (
    "This view is a concept, not a working feature. No bank, insurer, asset management "
    "company, or the NPS is connected to this demo. The steps below are generic "
    "illustrations from synthetic records, not any institution's real requirements."
)

ASSET_LABELS = {
    "bank_account": "Bank deposit account",
    "insurance_policy": "Life insurance policy",
    "mutual_fund_folio": "Mutual fund folio",
    "nps_account": "NPS account",
    "other": "Other asset",
}

ILLUSTRATIVE_STEPS = {
    "bank_account": (
        "Inform the bank branch that holds the account.",
        "Provide a death certificate.",
        "Complete the bank's own claim form.",
        "Provide claimant identity documents.",
        "The bank settles according to the nomination it has on record.",
    ),
    "insurance_policy": (
        "Intimate the claim to the insurer.",
        "Provide a death certificate.",
        "Provide the policy document or its number.",
        "Provide claimant identity and bank details.",
        "The insurer settles according to the nomination it has registered.",
    ),
    "mutual_fund_folio": (
        "Notify the asset management company or its registrar.",
        "Provide a death certificate.",
        "Submit a transmission request form.",
        "Complete the nominee's KYC.",
        "The AMC transmits the units to the nominee on record.",
    ),
    "nps_account": (
        "Inform the nodal office or point of presence.",
        "Provide a death certificate.",
        "Submit the withdrawal or claim form.",
        "Provide claimant identity and bank details.",
        "The central recordkeeping agency processes the claim.",
    ),
    "other": (
        "Identify which institution holds this asset.",
        "Ask that institution what its settlement process requires.",
    ),
}

NOMINATION_MECHANISMS = {"nominee", "beneficiary_nominee"}


@dataclass(frozen=True)
class EstateCaseItem:
    institution_name: str
    asset_type: str
    asset_type_label: str
    asset_reference: str
    named_people: tuple[str, ...]
    has_nomination_on_record: bool
    illustrative_steps: tuple[str, ...]


@dataclass
class EstateCase:
    concept: bool = True
    label: str = CONCEPT_LABEL
    notice: str = CONCEPT_NOTICE
    disclaimer: str = DISCLAIMER
    unresolved_conflicts: int = 0
    readiness_score: int | None = None
    items: list[EstateCaseItem] = dataclass_field(default_factory=list)


def build_estate_case(
    records: list[FieldRecord],
    *,
    unresolved_conflicts: int = 0,
    readiness_score: int | None = None,
) -> EstateCase:
    """Group synthetic vault records by asset and attach illustrative steps."""
    grouped: dict[tuple[str, str, str], list[FieldRecord]] = {}
    for record in records:
        if not normalize_text(record.asset_reference):
            continue
        key = (
            record.asset_type,
            normalize_text(record.institution_name),
            normalize_text(record.asset_reference),
        )
        grouped.setdefault(key, []).append(record)

    items: list[EstateCaseItem] = []
    for key in sorted(grouped):
        group = grouped[key]
        first = min(group, key=lambda record: record.field_id)
        asset_type = first.asset_type
        people = tuple(
            sorted({record.named_person for record in group if record.named_person})
        )
        items.append(
            EstateCaseItem(
                institution_name=first.institution_name or "Institution not stated",
                asset_type=asset_type,
                asset_type_label=ASSET_LABELS.get(asset_type, ASSET_LABELS["other"]),
                asset_reference=first.asset_reference,
                named_people=people,
                has_nomination_on_record=any(
                    record.mechanism_type in NOMINATION_MECHANISMS for record in group
                ),
                illustrative_steps=ILLUSTRATIVE_STEPS.get(
                    asset_type, ILLUSTRATIVE_STEPS["other"]
                ),
            )
        )

    return EstateCase(
        unresolved_conflicts=unresolved_conflicts,
        readiness_score=readiness_score,
        items=items,
    )
