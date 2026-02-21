"""Apply SQL schema for local PostgreSQL setup."""

from __future__ import annotations

from pathlib import Path

from dndtracker.backend.config import load_settings


def main() -> None:
    settings = load_settings()
    if not settings.database_url:
        raise RuntimeError("DNDTRACKER_DATABASE_URL is required for migration")

    import psycopg

    schema_path = Path(__file__).with_name("db_schema.sql")
    schema_sql = schema_path.read_text(encoding="utf-8")

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.commit()


if __name__ == "__main__":
    main()
