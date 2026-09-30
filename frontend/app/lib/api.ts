export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Severity = "high" | "medium" | "low";

export type FindingSource = {
  label: string;
  locator: string;
  text: string;
  field_id: number | null;
};

export type Finding = {
  id: number;
  rule_id: string;
  rules_version: string;
  finding_type: "review_conflict" | "validity_warning" | "scope_gap";
  severity: Severity;
  asset_type: string;
  asset_reference: string;
  summary: string;
  legal_scope_note: string;
  suggested_actions: string[];
  source_a: FindingSource;
  source_b: FindingSource | null;
  explanation: string | null;
  suggested_fix: string | null;
  explanation_source: "gemini" | "unavailable" | null;
  disclaimer: string;
};

export type DetectionRun = {
  id: number;
  persona_id: number;
  rules_version: string;
  readiness_score: number | null;
  score_breakdown: Record<string, number>;
  run_at: string;
  disclaimer: string;
  conflicts: Finding[];
  scope_gaps: Finding[];
};

export type ExtractedField = {
  id: number;
  document_id: number;
  asset_type: string;
  institution_name: string;
  asset_reference: string;
  named_person: string;
  relationship: string;
  mechanism_type: string;
  share_percent: number | null;
  source_text: string;
  source_locator: string;
  registration_status: string;
  is_user_edited: boolean;
  holding_pattern: "single" | "joint" | "unknown";
};

export type DocumentRecord = {
  id: number;
  original_filename: string;
  document_type: string | null;
  document_date: string | null;
  status: string;
  extraction_source: string | null;
  model_name: string | null;
  error_code: string | null;
  fields: ExtractedField[];
};

export type Persona = {
  id: number;
  name: string;
  description: string | null;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    cache: "no-store",
    headers: init?.body ? { "Content-Type": "application/json" } : undefined,
    ...init,
  });
  if (!response.ok) {
    throw new Error(`Request to ${path} failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

export function listPersonas() {
  return request<{ personas: Persona[] }>("/personas");
}

export function listDocuments(personaId: number) {
  return request<{ documents: DocumentRecord[] }>(
    `/personas/${personaId}/documents`,
  );
}

export function latestDetection(personaId: number) {
  return request<DetectionRun>(`/personas/${personaId}/detections/latest`);
}

export function runDetection(personaId: number, explain = true) {
  return request<DetectionRun>(
    `/personas/${personaId}/detections?explain=${explain}`,
    { method: "POST" },
  );
}

export function updateField(fieldId: number, namedPerson: string) {
  return request<DocumentRecord>(`/fields/${fieldId}`, {
    method: "PATCH",
    body: JSON.stringify({ named_person: namedPerson }),
  });
}

export function undoField(fieldId: number) {
  return request<DocumentRecord>(`/fields/${fieldId}/undo`, { method: "POST" });
}

export type EstateCaseItem = {
  institution_name: string;
  asset_type: string;
  asset_type_label: string;
  asset_reference: string;
  named_people: string[];
  has_nomination_on_record: boolean;
  illustrative_steps: string[];
};

export type EstateCase = {
  concept: true;
  label: string;
  notice: string;
  disclaimer: string;
  unresolved_conflicts: number;
  readiness_score: number | null;
  items: EstateCaseItem[];
};

export function estateCaseConcept(personaId: number) {
  return request<EstateCase>(`/personas/${personaId}/estate-case`);
}
