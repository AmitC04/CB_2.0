PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS personas (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    owner_has_family TEXT NOT NULL DEFAULT 'unknown'
        CHECK (owner_has_family IN ('true', 'false', 'unknown')),
    marriage_date TEXT,
    family_context_source_text TEXT,
    manually_confirmed_aliases_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    persona_id INTEGER NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    content_sha256 TEXT NOT NULL CHECK (length(content_sha256) = 64),
    size_bytes INTEGER NOT NULL CHECK (size_bytes > 0),
    synthetic_confirmed INTEGER NOT NULL CHECK (synthetic_confirmed = 1),
    doc_type TEXT CHECK (
        doc_type IS NULL OR doc_type IN (
            'will', 'bank_nomination', 'insurance_nomination',
            'mutual_fund_nomination', 'nps_nomination', 'unknown'
        )
    ),
    document_date TEXT,
    status TEXT NOT NULL DEFAULT 'uploaded'
        CHECK (status IN ('uploaded', 'extracting', 'extracted', 'failed')),
    extraction_source TEXT CHECK (
        extraction_source IS NULL OR extraction_source IN ('gemini', 'manual_fallback')
    ),
    model_name TEXT,
    raw_extraction_json TEXT,
    error_code TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
    uploaded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    extracted_at TEXT
);

CREATE TABLE IF NOT EXISTS extracted_fields (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    document_group_id TEXT NOT NULL,
    asset_type TEXT NOT NULL CHECK (
        asset_type IN (
            'bank_account', 'insurance_policy', 'mutual_fund_folio',
            'nps_account', 'other'
        )
    ),
    institution_name TEXT NOT NULL,
    asset_reference TEXT NOT NULL,
    person_name TEXT NOT NULL,
    relationship TEXT NOT NULL,
    mechanism TEXT NOT NULL CHECK (
        mechanism IN ('nominee', 'bequest', 'beneficiary_nominee')
    ),
    share_percent REAL CHECK (share_percent IS NULL OR share_percent BETWEEN 0 AND 100),
    source_text TEXT NOT NULL CHECK (length(trim(source_text)) > 0),
    source_locator TEXT NOT NULL,
    confidence REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    registration_status TEXT NOT NULL CHECK (
        registration_status IN ('confirmed', 'unconfirmed', 'not_registered', 'unknown')
    ),
    registration_date TEXT,
    explicit_nomination_action TEXT NOT NULL CHECK (
        explicit_nomination_action IN ('none', 'change', 'cancel')
    ),
    policy_kind TEXT NOT NULL CHECK (policy_kind IN ('life', 'other', 'unknown')),
    mwpa_section_6_applies TEXT NOT NULL CHECK (
        mwpa_section_6_applies IN ('true', 'false', 'unknown')
    ),
    assignment_status TEXT NOT NULL CHECK (
        assignment_status IN ('active', 'none', 'unknown')
    ),
    holding_pattern TEXT NOT NULL DEFAULT 'unknown' CHECK (
        holding_pattern IN ('single', 'joint', 'unknown')
    ),
    is_user_edited INTEGER NOT NULL DEFAULT 0 CHECK (is_user_edited IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS detection_runs (
    id INTEGER PRIMARY KEY,
    persona_id INTEGER NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    rules_version TEXT NOT NULL,
    readiness_score INTEGER CHECK (readiness_score BETWEEN 0 AND 100),
    run_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS conflicts (
    id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES detection_runs(id) ON DELETE CASCADE,
    rules_version TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    finding_type TEXT NOT NULL CHECK (
        finding_type IN ('review_conflict', 'validity_warning', 'scope_gap')
    ),
    severity TEXT NOT NULL CHECK (severity IN ('high', 'medium', 'low')),
    asset_type TEXT NOT NULL,
    asset_reference TEXT NOT NULL,
    field_a_id INTEGER REFERENCES extracted_fields(id) ON DELETE SET NULL,
    source_a_label TEXT NOT NULL,
    source_a_locator TEXT NOT NULL,
    source_a_text TEXT NOT NULL,
    field_b_id INTEGER REFERENCES extracted_fields(id) ON DELETE SET NULL,
    source_b_label TEXT,
    source_b_locator TEXT,
    source_b_text TEXT,
    summary TEXT NOT NULL CHECK (length(trim(summary)) > 0),
    legal_scope_note TEXT NOT NULL CHECK (length(trim(legal_scope_note)) > 0),
    suggested_actions_json TEXT NOT NULL,
    explanation TEXT,
    suggested_fix TEXT,
    explanation_source TEXT CHECK (
        explanation_source IS NULL OR explanation_source IN ('gemini', 'unavailable')
    ),
    disclaimer TEXT NOT NULL CHECK (length(trim(disclaimer)) > 0),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS field_edits (
    id INTEGER PRIMARY KEY,
    field_id INTEGER NOT NULL REFERENCES extracted_fields(id) ON DELETE CASCADE,
    previous_person_name TEXT NOT NULL,
    previous_relationship TEXT NOT NULL,
    new_person_name TEXT NOT NULL,
    new_relationship TEXT NOT NULL,
    undone_at TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_documents_persona_id ON documents(persona_id);
CREATE INDEX IF NOT EXISTS idx_field_edits_field_id ON field_edits(field_id);
CREATE INDEX IF NOT EXISTS idx_documents_sha256 ON documents(content_sha256);
CREATE INDEX IF NOT EXISTS idx_extracted_fields_document_id ON extracted_fields(document_id);
CREATE INDEX IF NOT EXISTS idx_detection_runs_persona_id ON detection_runs(persona_id);
CREATE INDEX IF NOT EXISTS idx_conflicts_run_id ON conflicts(run_id);
