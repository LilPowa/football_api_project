import json
from datetime import datetime, timezone
from typing import Any

from app.database import get_connection


def get_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_countries(api_response: dict[str, Any]) -> int:
    countries = api_response.get("response", [])
    updated_at = get_utc_now()

    with get_connection() as connection:
        cursor = connection.cursor()

        for country in countries:
            cursor.execute(
                """
                INSERT INTO countries (
                    name,
                    code,
                    flag,
                    raw_json,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    code = excluded.code,
                    flag = excluded.flag,
                    raw_json = excluded.raw_json,
                    updated_at = excluded.updated_at
                """,
                (
                    country.get("name"),
                    country.get("code"),
                    country.get("flag"),
                    json.dumps(country, ensure_ascii=False),
                    updated_at,
                ),
            )

        connection.commit()

    return len(countries)


def count_countries() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM countries")
        row = cursor.fetchone()

        return int(row["total"])


def list_countries(limit: int = 10) -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT name, code, flag, updated_at
            FROM countries
            ORDER BY name ASC
            LIMIT ?
            """,
            (limit,),
        )

        rows = cursor.fetchall()

    return [dict(row) for row in rows]