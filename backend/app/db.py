"""Small SQLite helpers for the hackathon build."""

import os
import sqlite3
from pathlib import Path

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "jeevansetu.db"
SCHEMA_PATH = Path(__file__).with_name("schema.sql")
SCHEMA_VERSION = 4
REQUIRED_COLUMNS = {
    "documents": "content_sha256",
    "conflicts": "rules_version",
    "extracted_fields": "holding_pattern",
}


class SchemaVersionError(RuntimeError):
    """Raised when a resettable legacy synthetic database needs explicit removal."""


def get_database_path() -> Path:
    """Return the configured SQLite path, evaluated at call time for tests."""
    return Path(os.getenv("DATABASE_PATH", str(DEFAULT_DATABASE_PATH)))


def get_connection() -> sqlite3.Connection:
    """Open a connection with foreign-key enforcement enabled."""
    database_path = get_database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}


def init_db() -> None:
    """Apply the schema, rejecting legacy shapes that require an explicit reset."""
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_connection() as connection:
        existing_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        database_initialized = bool(_table_columns(connection, "documents"))
        if database_initialized and 0 < existing_version < SCHEMA_VERSION:
            raise SchemaVersionError(
                f"Synthetic database schema version {existing_version} is older than "
                f"{SCHEMA_VERSION}. Stop the backend, delete {get_database_path()}, and "
                "restart to create the current schema."
            )
        for table, required_column in REQUIRED_COLUMNS.items():
            columns = _table_columns(connection, table)
            if columns and required_column not in columns:
                raise SchemaVersionError(
                    f"Legacy synthetic database detected (table '{table}' is missing "
                    f"'{required_column}'). Stop the backend, delete "
                    f"{get_database_path()}, and restart to create the current schema."
                )
        connection.executescript(schema)
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        connection.execute(
            """
            UPDATE documents
            SET status = 'failed', error_code = 'extraction_interrupted'
            WHERE status = 'extracting'
            """
        )
