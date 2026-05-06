import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from app.database import get_connection


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_params(params: dict[str, Any] | None = None) -> dict[str, Any]:
    return params or {}


def get_params_json(params: dict[str, Any] | None = None) -> str:
    return json.dumps(
        normalize_params(params),
        sort_keys=True,
        ensure_ascii=False
    )


def get_params_hash(params: dict[str, Any] | None = None) -> str:
    params_json = get_params_json(params)
    return hashlib.sha256(params_json.encode("utf-8")).hexdigest()


def get_cached_response(
    endpoint: str,
    params: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    params_hash = get_params_hash(params)
    now = get_utc_now()

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT response_json, expires_at
            FROM api_cache
            WHERE endpoint = ?
            AND params_hash = ?
            """,
            (endpoint, params_hash),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        expires_at = row["expires_at"]

        if expires_at:
            expires_at_datetime = datetime.fromisoformat(expires_at)

            if expires_at_datetime <= now:
                cursor.execute(
                    """
                    DELETE FROM api_cache
                    WHERE endpoint = ?
                    AND params_hash = ?
                    """,
                    (endpoint, params_hash),
                )
                connection.commit()
                return None

        return json.loads(row["response_json"])


def save_cached_response(
    endpoint: str,
    params: dict[str, Any] | None,
    response: dict[str, Any],
    ttl_seconds: int
) -> None:
    created_at = get_utc_now()
    expires_at = created_at + timedelta(seconds=ttl_seconds)

    params_json = get_params_json(params)
    params_hash = get_params_hash(params)

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO api_cache (
                endpoint,
                params_hash,
                params_json,
                response_json,
                created_at,
                expires_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(endpoint, params_hash) DO UPDATE SET
                params_json = excluded.params_json,
                response_json = excluded.response_json,
                created_at = excluded.created_at,
                expires_at = excluded.expires_at
            """,
            (
                endpoint,
                params_hash,
                params_json,
                json.dumps(response, ensure_ascii=False),
                created_at.isoformat(),
                expires_at.isoformat(),
            ),
        )

        connection.commit()


def count_cache_entries() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM api_cache")
        row = cursor.fetchone()

        return int(row["total"])