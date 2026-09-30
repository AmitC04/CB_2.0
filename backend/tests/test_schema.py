import sqlite3
from pathlib import Path

import pytest

from app.db import SchemaVersionError, get_connection, init_db

EXPECTED_TABLES = {
    "conflicts",
    "detection_runs",
    "documents",
    "extracted_fields",
    "field_edits",
    "personas",
}


@pytest.fixture
def database(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    database_path = tmp_path / "schema.db"
    monkeypatch.setenv("DATABASE_PATH", str(database_path))
    init_db()
    return database_path


def test_schema_creates_expected_tables(database: Path) -> None:
    with get_connection() as connection:
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        }

    assert tables == EXPECTED_TABLES


def test_foreign_keys_reject_orphaned_extracted_field(database: Path) -> None:
    with get_connection() as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO extracted_fields (
                    document_id, document_group_id, asset_type, institution_name,
                    asset_reference, person_name, relationship, mechanism,
                    source_text, source_locator, confidence, registration_status,
                    explicit_nomination_action, policy_kind,
                    mwpa_section_6_applies, assignment_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    999,
                    "group-1",
                    "bank_account",
                    "Synthetic Bank",
                    "BANK-ORPHAN",
                    "Synthetic Nominee",
                    "sibling",
                    "nominee",
                    "Nominee: Synthetic Nominee",
                    "field nominee",
                    1.0,
                    "unconfirmed",
                    "none",
                    "unknown",
                    "unknown",
                    "unknown",
                ),
            )


def test_conflict_requires_non_empty_disclaimer(database: Path) -> None:
    with get_connection() as connection:
        persona_id = connection.execute(
            "INSERT INTO personas (name) VALUES (?)",
            ("Synthetic Test Persona",),
        ).lastrowid
        run_id = connection.execute(
            "INSERT INTO detection_runs (persona_id, rules_version) VALUES (?, ?)",
            (persona_id, "phase-0-draft"),
        ).lastrowid

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO conflicts (
                    run_id, rule_id, severity, summary, disclaimer
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, "TEST", "low", "Synthetic conflict", ""),
            )


def test_reapplying_schema_preserves_existing_data(database: Path) -> None:
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO personas (name) VALUES (?)",
            ("Synthetic Persistent Persona",),
        )

    init_db()

    with get_connection() as connection:
        count = connection.execute("SELECT COUNT(*) FROM personas").fetchone()[0]

    assert count == 1


def test_legacy_schema_fails_with_explicit_reset_instruction(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "legacy.db"
    monkeypatch.setenv("DATABASE_PATH", str(database_path))
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "CREATE TABLE documents (id INTEGER PRIMARY KEY, original_filename TEXT)"
        )

    with pytest.raises(SchemaVersionError, match="Legacy synthetic database"):
        init_db()


def test_startup_recovers_interrupted_extraction(database: Path) -> None:
    with get_connection() as connection:
        persona_id = connection.execute(
            "INSERT INTO personas (name) VALUES (?)",
            ("Synthetic Recovery Persona",),
        ).lastrowid
        connection.execute(
            """
            INSERT INTO documents (
                persona_id, original_filename, mime_type, storage_path,
                content_sha256, size_bytes, synthetic_confirmed, status
            ) VALUES (?, ?, ?, ?, ?, ?, 1, 'extracting')
            """,
            (
                persona_id,
                "synthetic.txt",
                "text/plain",
                "synthetic.txt",
                "a" * 64,
                9,
            ),
        )

    init_db()

    with get_connection() as connection:
        row = connection.execute(
            "SELECT status, error_code FROM documents WHERE persona_id = ?",
            (persona_id,),
        ).fetchone()
    assert tuple(row) == ("failed", "extraction_interrupted")


def test_legacy_conflicts_table_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "legacy_conflicts.db"
    monkeypatch.setenv("DATABASE_PATH", str(database_path))
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "CREATE TABLE documents (id INTEGER PRIMARY KEY, content_sha256 TEXT)"
        )
        connection.execute("CREATE TABLE conflicts (id INTEGER PRIMARY KEY, rule_id TEXT)")

    with pytest.raises(SchemaVersionError, match="conflicts"):
        init_db()


def test_older_schema_version_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "old_version.db"
    monkeypatch.setenv("DATABASE_PATH", str(database_path))
    init_db()
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA user_version = 1")

    with pytest.raises(SchemaVersionError, match="older than"):
        init_db()
