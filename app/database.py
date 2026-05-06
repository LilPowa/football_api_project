import sqlite3
from pathlib import Path

from app.config import BASE_DIR, settings


def get_database_path() -> Path:
    database_path = Path(settings.DATABASE_PATH)

    if not database_path.is_absolute():
        database_path = BASE_DIR / database_path

    database_path.parent.mkdir(parents=True, exist_ok=True)

    return database_path


def get_connection() -> sqlite3.Connection:
    database_path = get_database_path()

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    return connection


def init_db() -> None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS api_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                params_hash TEXT NOT NULL,
                params_json TEXT NOT NULL,
                response_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                UNIQUE(endpoint, params_hash)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS countries (
                name TEXT PRIMARY KEY,
                code TEXT,
                flag TEXT,
                raw_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS leagues (
                league_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT,
                logo TEXT,
                country_name TEXT,
                country_code TEXT,
                country_flag TEXT,
                raw_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS league_seasons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                league_id INTEGER NOT NULL,
                season_year INTEGER NOT NULL,
                start_date TEXT,
                end_date TEXT,
                current INTEGER NOT NULL DEFAULT 0,
                coverage_json TEXT NOT NULL,
                raw_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(league_id, season_year),
                FOREIGN KEY (league_id) REFERENCES leagues(league_id)
            )
            """
        )

        connection.commit()