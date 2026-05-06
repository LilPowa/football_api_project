import json
from datetime import datetime, timezone
from typing import Any

from app.database import get_connection


def get_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# -------------------------------------------------------------------
# Countries
# -------------------------------------------------------------------

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


# -------------------------------------------------------------------
# Leagues
# -------------------------------------------------------------------

def save_leagues(api_response: dict[str, Any]) -> int:
    leagues = api_response.get("response", [])
    updated_at = get_utc_now()

    with get_connection() as connection:
        cursor = connection.cursor()

        for item in leagues:
            league = item.get("league", {})
            country = item.get("country", {})
            seasons = item.get("seasons", [])

            league_id = league.get("id")

            if league_id is None:
                continue

            cursor.execute(
                """
                INSERT INTO leagues (
                    league_id,
                    name,
                    type,
                    logo,
                    country_name,
                    country_code,
                    country_flag,
                    raw_json,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(league_id) DO UPDATE SET
                    name = excluded.name,
                    type = excluded.type,
                    logo = excluded.logo,
                    country_name = excluded.country_name,
                    country_code = excluded.country_code,
                    country_flag = excluded.country_flag,
                    raw_json = excluded.raw_json,
                    updated_at = excluded.updated_at
                """,
                (
                    league_id,
                    league.get("name"),
                    league.get("type"),
                    league.get("logo"),
                    country.get("name"),
                    country.get("code"),
                    country.get("flag"),
                    json.dumps(item, ensure_ascii=False),
                    updated_at,
                ),
            )

            for season in seasons:
                season_year = season.get("year")

                if season_year is None:
                    continue

                cursor.execute(
                    """
                    INSERT INTO league_seasons (
                        league_id,
                        season_year,
                        start_date,
                        end_date,
                        current,
                        coverage_json,
                        raw_json,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(league_id, season_year) DO UPDATE SET
                        start_date = excluded.start_date,
                        end_date = excluded.end_date,
                        current = excluded.current,
                        coverage_json = excluded.coverage_json,
                        raw_json = excluded.raw_json,
                        updated_at = excluded.updated_at
                    """,
                    (
                        league_id,
                        season_year,
                        season.get("start"),
                        season.get("end"),
                        1 if season.get("current") else 0,
                        json.dumps(season.get("coverage", {}), ensure_ascii=False),
                        json.dumps(season, ensure_ascii=False),
                        updated_at,
                    ),
                )

        connection.commit()

    return len(leagues)


def count_leagues() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM leagues")
        row = cursor.fetchone()

        return int(row["total"])


def count_league_seasons() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM league_seasons")
        row = cursor.fetchone()

        return int(row["total"])


def list_leagues(limit: int = 20) -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                league_id,
                name,
                type,
                country_name,
                country_code,
                updated_at
            FROM leagues
            ORDER BY country_name ASC, name ASC
            LIMIT ?
            """,
            (limit,),
        )

        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def list_current_league_seasons(limit: int = 20) -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                l.league_id,
                l.name,
                l.type,
                l.country_name,
                s.season_year,
                s.start_date,
                s.end_date,
                s.current
            FROM league_seasons s
            JOIN leagues l ON l.league_id = s.league_id
            WHERE s.current = 1
            ORDER BY l.country_name ASC, l.name ASC
            LIMIT ?
            """,
            (limit,),
        )

        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def list_league_seasons_by_league_id(league_id: int) -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                season_year,
                start_date,
                end_date,
                current,
                coverage_json
            FROM league_seasons
            WHERE league_id = ?
            ORDER BY season_year DESC
            """,
            (league_id,),
        )

        rows = cursor.fetchall()

    results = []

    for row in rows:
        item = dict(row)
        item["coverage"] = json.loads(item.pop("coverage_json"))
        results.append(item)

    return results

def list_all_countries() -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT name, code, flag, updated_at
            FROM countries
            ORDER BY name ASC
            """
        )

        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def list_leagues_filtered(
    country_name: str | None = None,
    search: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = """
        SELECT
            league_id,
            name,
            type,
            logo,
            country_name,
            country_code,
            country_flag,
            updated_at
        FROM leagues
        WHERE 1 = 1
    """

    params: list[Any] = []

    if country_name and country_name != "Tous":
        query += " AND country_name = ?"
        params.append(country_name)

    if search:
        query += " AND name LIKE ?"
        params.append(f"%{search}%")

    query += """
        ORDER BY country_name ASC, name ASC
        LIMIT ?
    """
    params.append(limit)

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_league_by_id(league_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                league_id,
                name,
                type,
                logo,
                country_name,
                country_code,
                country_flag,
                raw_json,
                updated_at
            FROM leagues
            WHERE league_id = ?
            """,
            (league_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    result = dict(row)
    result["raw"] = json.loads(result.pop("raw_json"))

    return result

# -------------------------------------------------------------------
# Teams
# -------------------------------------------------------------------

def save_teams(
    api_response: dict[str, Any],
    league_id: int,
    season_year: int,
) -> int:
    teams = api_response.get("response", [])
    updated_at = get_utc_now()

    with get_connection() as connection:
        cursor = connection.cursor()

        for item in teams:
            team = item.get("team", {})
            venue = item.get("venue", {})

            team_id = team.get("id")

            if team_id is None:
                continue

            cursor.execute(
                """
                INSERT INTO teams (
                    team_id,
                    name,
                    code,
                    country,
                    founded,
                    national,
                    logo,
                    venue_id,
                    venue_name,
                    venue_address,
                    venue_city,
                    venue_capacity,
                    venue_surface,
                    venue_image,
                    raw_json,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(team_id) DO UPDATE SET
                    name = excluded.name,
                    code = excluded.code,
                    country = excluded.country,
                    founded = excluded.founded,
                    national = excluded.national,
                    logo = excluded.logo,
                    venue_id = excluded.venue_id,
                    venue_name = excluded.venue_name,
                    venue_address = excluded.venue_address,
                    venue_city = excluded.venue_city,
                    venue_capacity = excluded.venue_capacity,
                    venue_surface = excluded.venue_surface,
                    venue_image = excluded.venue_image,
                    raw_json = excluded.raw_json,
                    updated_at = excluded.updated_at
                """,
                (
                    team_id,
                    team.get("name"),
                    team.get("code"),
                    team.get("country"),
                    team.get("founded"),
                    1 if team.get("national") else 0,
                    team.get("logo"),
                    venue.get("id"),
                    venue.get("name"),
                    venue.get("address"),
                    venue.get("city"),
                    venue.get("capacity"),
                    venue.get("surface"),
                    venue.get("image"),
                    json.dumps(item, ensure_ascii=False),
                    updated_at,
                ),
            )

            cursor.execute(
                """
                INSERT INTO team_league_seasons (
                    team_id,
                    league_id,
                    season_year,
                    updated_at
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(team_id, league_id, season_year) DO UPDATE SET
                    updated_at = excluded.updated_at
                """,
                (
                    team_id,
                    league_id,
                    season_year,
                    updated_at,
                ),
            )

        connection.commit()

    return len(teams)


def count_teams() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM teams")
        row = cursor.fetchone()

        return int(row["total"])


def count_team_league_seasons() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM team_league_seasons")
        row = cursor.fetchone()

        return int(row["total"])


def list_teams_by_league_season(
    league_id: int,
    season_year: int,
) -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                t.team_id,
                t.name,
                t.code,
                t.country,
                t.founded,
                t.national,
                t.logo,
                t.venue_id,
                t.venue_name,
                t.venue_city,
                t.venue_capacity,
                tls.league_id,
                tls.season_year,
                tls.updated_at
            FROM team_league_seasons tls
            JOIN teams t ON t.team_id = tls.team_id
            WHERE tls.league_id = ?
            AND tls.season_year = ?
            ORDER BY t.name ASC
            """,
            (league_id, season_year),
        )

        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_team_by_id(team_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                team_id,
                name,
                code,
                country,
                founded,
                national,
                logo,
                venue_id,
                venue_name,
                venue_address,
                venue_city,
                venue_capacity,
                venue_surface,
                venue_image,
                raw_json,
                updated_at
            FROM teams
            WHERE team_id = ?
            """,
            (team_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    result = dict(row)
    result["raw"] = json.loads(result.pop("raw_json"))

    return result