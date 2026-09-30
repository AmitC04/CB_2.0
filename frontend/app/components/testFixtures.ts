import type {
  DetectionRun,
  DocumentRecord,
  ExtractedField,
  Finding,
} from "../lib/api";

export const DISCLAIMER =
  "Synthetic demo data only. Not legal advice. A licensed advisor should review real conflicts.";

export function makeField(overrides: Partial<ExtractedField> = {}): ExtractedField {
  return {
    id: 1,
    document_id: 10,
    asset_type: "bank_account",
    institution_name: "Demo Bank",
    asset_reference: "SB-DEMO-4821",
    named_person: "Kavya Demo-Mehta",
    relationship: "daughter",
    mechanism_type: "nominee",
    share_percent: null,
    source_text: "Nominee: Kavya Demo-Mehta (daughter)",
    source_locator: "page 1",
    registration_status: "confirmed",
    is_user_edited: false,
    holding_pattern: "single",
    ...overrides,
  };
}

export function makeDocument(overrides: Partial<DocumentRecord> = {}): DocumentRecord {
  return {
    id: 10,
    original_filename: "bank_nomination.pdf",
    document_type: "bank_nomination",
    document_date: "2021-04-02",
    status: "extracted",
    extraction_source: "gemini",
    model_name: "gemini-3.1-flash-lite",
    error_code: null,
    fields: [makeField()],
    ...overrides,
  };
}

export function makeFinding(overrides: Partial<Finding> = {}): Finding {
  return {
    id: 1,
    rule_id: "BANK-WILL-001",
    rules_version: "1.0.0-candidate",
    finding_type: "review_conflict",
    severity: "high",
    asset_type: "bank_account",
    asset_reference: "SB-DEMO-4821",
    summary: "The bank nomination and the will name different people.",
    legal_scope_note: "Documented rule scope note.",
    suggested_actions: ["Confirm the intended person with an advisor."],
    source_a: {
      label: "Bank nomination",
      locator: "page 1",
      text: "Kavya Demo-Mehta (daughter)",
      field_id: 1,
    },
    source_b: {
      label: "Will",
      locator: "clause 3.1",
      text: "Anika Demo-Mehta (daughter)",
      field_id: 2,
    },
    explanation: null,
    suggested_fix: null,
    explanation_source: null,
    disclaimer: DISCLAIMER,
    ...overrides,
  };
}

export function makeRun(overrides: Partial<DetectionRun> = {}): DetectionRun {
  return {
    id: 1,
    persona_id: 1,
    rules_version: "1.0.0-candidate",
    readiness_score: 75,
    score_breakdown: {
      base: 100,
      high_conflicts: 1,
      medium_conflicts: 0,
      gaps: 0,
      deduction: 25,
    },
    run_at: "2026-09-29T00:00:00.000Z",
    disclaimer: DISCLAIMER,
    conflicts: [makeFinding()],
    scope_gaps: [],
    ...overrides,
  };
}
