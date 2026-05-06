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

# -------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------

def save_fixtures(
    api_response: dict[str, Any],
    league_id: int,
    season_year: int,
) -> int:
    fixtures = api_response.get("response", [])
    updated_at = get_utc_now()

    with get_connection() as connection:
        cursor = connection.cursor()

        for item in fixtures:
            fixture = item.get("fixture", {})
            league = item.get("league", {})
            teams = item.get("teams", {})
            goals = item.get("goals", {})
            score = item.get("score", {})

            venue = fixture.get("venue", {})
            status = fixture.get("status", {})
            home_team = teams.get("home", {})
            away_team = teams.get("away", {})

            halftime = score.get("halftime", {})
            fulltime = score.get("fulltime", {})
            extratime = score.get("extratime", {})
            penalty = score.get("penalty", {})

            fixture_id = fixture.get("id")

            if fixture_id is None:
                continue

            cursor.execute(
                """
                INSERT INTO fixtures (
                    fixture_id,
                    league_id,
                    season_year,
                    round,
                    referee,
                    timezone,
                    fixture_date,
                    fixture_timestamp,
                    venue_id,
                    venue_name,
                    venue_city,
                    status_long,
                    status_short,
                    elapsed,
                    home_team_id,
                    home_team_name,
                    home_team_logo,
                    home_team_winner,
                    away_team_id,
                    away_team_name,
                    away_team_logo,
                    away_team_winner,
                    home_goals,
                    away_goals,
                    halftime_home,
                    halftime_away,
                    fulltime_home,
                    fulltime_away,
                    extratime_home,
                    extratime_away,
                    penalty_home,
                    penalty_away,
                    raw_json,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(fixture_id) DO UPDATE SET
                    league_id = excluded.league_id,
                    season_year = excluded.season_year,
                    round = excluded.round,
                    referee = excluded.referee,
                    timezone = excluded.timezone,
                    fixture_date = excluded.fixture_date,
                    fixture_timestamp = excluded.fixture_timestamp,
                    venue_id = excluded.venue_id,
                    venue_name = excluded.venue_name,
                    venue_city = excluded.venue_city,
                    status_long = excluded.status_long,
                    status_short = excluded.status_short,
                    elapsed = excluded.elapsed,
                    home_team_id = excluded.home_team_id,
                    home_team_name = excluded.home_team_name,
                    home_team_logo = excluded.home_team_logo,
                    home_team_winner = excluded.home_team_winner,
                    away_team_id = excluded.away_team_id,
                    away_team_name = excluded.away_team_name,
                    away_team_logo = excluded.away_team_logo,
                    away_team_winner = excluded.away_team_winner,
                    home_goals = excluded.home_goals,
                    away_goals = excluded.away_goals,
                    halftime_home = excluded.halftime_home,
                    halftime_away = excluded.halftime_away,
                    fulltime_home = excluded.fulltime_home,
                    fulltime_away = excluded.fulltime_away,
                    extratime_home = excluded.extratime_home,
                    extratime_away = excluded.extratime_away,
                    penalty_home = excluded.penalty_home,
                    penalty_away = excluded.penalty_away,
                    raw_json = excluded.raw_json,
                    updated_at = excluded.updated_at
                """,
                (
                    fixture_id,
                    league.get("id") or league_id,
                    league.get("season") or season_year,
                    league.get("round"),
                    fixture.get("referee"),
                    fixture.get("timezone"),
                    fixture.get("date"),
                    fixture.get("timestamp"),
                    venue.get("id"),
                    venue.get("name"),
                    venue.get("city"),
                    status.get("long"),
                    status.get("short"),
                    status.get("elapsed"),
                    home_team.get("id"),
                    home_team.get("name"),
                    home_team.get("logo"),
                    1 if home_team.get("winner") else 0 if home_team.get("winner") is False else None,
                    away_team.get("id"),
                    away_team.get("name"),
                    away_team.get("logo"),
                    1 if away_team.get("winner") else 0 if away_team.get("winner") is False else None,
                    goals.get("home"),
                    goals.get("away"),
                    halftime.get("home"),
                    halftime.get("away"),
                    fulltime.get("home"),
                    fulltime.get("away"),
                    extratime.get("home"),
                    extratime.get("away"),
                    penalty.get("home"),
                    penalty.get("away"),
                    json.dumps(item, ensure_ascii=False),
                    updated_at,
                ),
            )

        connection.commit()

    return len(fixtures)


def count_fixtures() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM fixtures")
        row = cursor.fetchone()

        return int(row["total"])


def list_fixtures_by_league_season(
    league_id: int,
    season_year: int,
    limit: int = 200,
) -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                fixture_id,
                league_id,
                season_year,
                round,
                fixture_date,
                status_long,
                status_short,
                elapsed,
                home_team_id,
                home_team_name,
                home_team_logo,
                away_team_id,
                away_team_name,
                away_team_logo,
                home_goals,
                away_goals,
                venue_name,
                venue_city,
                updated_at
            FROM fixtures
            WHERE league_id = ?
            AND season_year = ?
            ORDER BY fixture_timestamp ASC
            LIMIT ?
            """,
            (league_id, season_year, limit),
        )

        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def list_fixture_teams_filter(
    league_id: int,
    season_year: int,
) -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT DISTINCT
                home_team_id AS team_id,
                home_team_name AS team_name
            FROM fixtures
            WHERE league_id = ?
            AND season_year = ?
            AND home_team_id IS NOT NULL

            UNION

            SELECT DISTINCT
                away_team_id AS team_id,
                away_team_name AS team_name
            FROM fixtures
            WHERE league_id = ?
            AND season_year = ?
            AND away_team_id IS NOT NULL

            ORDER BY team_name ASC
            """,
            (league_id, season_year, league_id, season_year),
        )

        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def list_fixtures_filtered(
    league_id: int,
    season_year: int,
    team_id: int | None = None,
    status_short: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    query = """
        SELECT
            fixture_id,
            league_id,
            season_year,
            round,
            fixture_date,
            status_long,
            status_short,
            elapsed,
            home_team_id,
            home_team_name,
            home_team_logo,
            away_team_id,
            away_team_name,
            away_team_logo,
            home_goals,
            away_goals,
            venue_name,
            venue_city,
            updated_at
        FROM fixtures
        WHERE league_id = ?
        AND season_year = ?
    """

    params: list[Any] = [league_id, season_year]

    if team_id is not None:
        query += " AND (home_team_id = ? OR away_team_id = ?)"
        params.extend([team_id, team_id])

    if status_short and status_short != "Tous":
        query += " AND status_short = ?"
        params.append(status_short)

    query += """
        ORDER BY fixture_timestamp ASC
        LIMIT ?
    """
    params.append(limit)

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_fixture_by_id(fixture_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                fixture_id,
                league_id,
                season_year,
                round,
                referee,
                timezone,
                fixture_date,
                fixture_timestamp,
                venue_id,
                venue_name,
                venue_city,
                status_long,
                status_short,
                elapsed,
                home_team_id,
                home_team_name,
                home_team_logo,
                home_team_winner,
                away_team_id,
                away_team_name,
                away_team_logo,
                away_team_winner,
                home_goals,
                away_goals,
                halftime_home,
                halftime_away,
                fulltime_home,
                fulltime_away,
                extratime_home,
                extratime_away,
                penalty_home,
                penalty_away,
                raw_json,
                updated_at
            FROM fixtures
            WHERE fixture_id = ?
            """,
            (fixture_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    result = dict(row)
    result["raw"] = json.loads(result.pop("raw_json"))

    return result

# -------------------------------------------------------------------
# Standings
# -------------------------------------------------------------------

def save_standings(
    api_response: dict[str, Any],
    league_id: int,
    season_year: int,
) -> int:
    response_items = api_response.get("response", [])
    updated_at = get_utc_now()
    saved_count = 0

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM standings
            WHERE league_id = ?
            AND season_year = ?
            """,
            (league_id, season_year),
        )

        for item in response_items:
            league = item.get("league", {})
            standings_groups = league.get("standings", [])

            for group in standings_groups:
                for standing in group:
                    team = standing.get("team", {})
                    all_stats = standing.get("all", {})
                    home_stats = standing.get("home", {})
                    away_stats = standing.get("away", {})

                    all_goals = all_stats.get("goals", {})
                    home_goals = home_stats.get("goals", {})
                    away_goals = away_stats.get("goals", {})

                    team_id = team.get("id")
                    group_name = standing.get("group")

                    if team_id is None:
                        continue

                    cursor.execute(
                        """
                        INSERT INTO standings (
                            league_id,
                            season_year,
                            group_name,
                            position,
                            team_id,
                            team_name,
                            team_logo,
                            points,
                            goals_diff,
                            form,
                            status,
                            description,
                            all_played,
                            all_win,
                            all_draw,
                            all_lose,
                            all_goals_for,
                            all_goals_against,
                            home_played,
                            home_win,
                            home_draw,
                            home_lose,
                            home_goals_for,
                            home_goals_against,
                            away_played,
                            away_win,
                            away_draw,
                            away_lose,
                            away_goals_for,
                            away_goals_against,
                            raw_json,
                            updated_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(league_id, season_year, group_name, team_id) DO UPDATE SET
                            position = excluded.position,
                            team_name = excluded.team_name,
                            team_logo = excluded.team_logo,
                            points = excluded.points,
                            goals_diff = excluded.goals_diff,
                            form = excluded.form,
                            status = excluded.status,
                            description = excluded.description,
                            all_played = excluded.all_played,
                            all_win = excluded.all_win,
                            all_draw = excluded.all_draw,
                            all_lose = excluded.all_lose,
                            all_goals_for = excluded.all_goals_for,
                            all_goals_against = excluded.all_goals_against,
                            home_played = excluded.home_played,
                            home_win = excluded.home_win,
                            home_draw = excluded.home_draw,
                            home_lose = excluded.home_lose,
                            home_goals_for = excluded.home_goals_for,
                            home_goals_against = excluded.home_goals_against,
                            away_played = excluded.away_played,
                            away_win = excluded.away_win,
                            away_draw = excluded.away_draw,
                            away_lose = excluded.away_lose,
                            away_goals_for = excluded.away_goals_for,
                            away_goals_against = excluded.away_goals_against,
                            raw_json = excluded.raw_json,
                            updated_at = excluded.updated_at
                        """,
                        (
                            league.get("id") or league_id,
                            league.get("season") or season_year,
                            group_name,
                            standing.get("rank"),
                            team_id,
                            team.get("name"),
                            team.get("logo"),
                            standing.get("points"),
                            standing.get("goalsDiff"),
                            standing.get("form"),
                            standing.get("status"),
                            standing.get("description"),
                            all_stats.get("played"),
                            all_stats.get("win"),
                            all_stats.get("draw"),
                            all_stats.get("lose"),
                            all_goals.get("for"),
                            all_goals.get("against"),
                            home_stats.get("played"),
                            home_stats.get("win"),
                            home_stats.get("draw"),
                            home_stats.get("lose"),
                            home_goals.get("for"),
                            home_goals.get("against"),
                            away_stats.get("played"),
                            away_stats.get("win"),
                            away_stats.get("draw"),
                            away_stats.get("lose"),
                            away_goals.get("for"),
                            away_goals.get("against"),
                            json.dumps(standing, ensure_ascii=False),
                            updated_at,
                        ),
                    )

                    saved_count += 1

        connection.commit()

    return saved_count


def count_standings() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM standings")
        row = cursor.fetchone()

        return int(row["total"])


def list_standings_by_league_season(
    league_id: int,
    season_year: int,
) -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                league_id,
                season_year,
                group_name,
                position,
                team_id,
                team_name,
                team_logo,
                points,
                goals_diff,
                form,
                status,
                description,
                all_played,
                all_win,
                all_draw,
                all_lose,
                all_goals_for,
                all_goals_against,
                home_played,
                home_win,
                home_draw,
                home_lose,
                home_goals_for,
                home_goals_against,
                away_played,
                away_win,
                away_draw,
                away_lose,
                away_goals_for,
                away_goals_against,
                updated_at
            FROM standings
            WHERE league_id = ?
            AND season_year = ?
            ORDER BY group_name ASC, position ASC
            """,
            (league_id, season_year),
        )

        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_standing_by_id(standing_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                league_id,
                season_year,
                group_name,
                position,
                team_id,
                team_name,
                team_logo,
                points,
                goals_diff,
                form,
                status,
                description,
                all_played,
                all_win,
                all_draw,
                all_lose,
                all_goals_for,
                all_goals_against,
                home_played,
                home_win,
                home_draw,
                home_lose,
                home_goals_for,
                home_goals_against,
                away_played,
                away_win,
                away_draw,
                away_lose,
                away_goals_for,
                away_goals_against,
                raw_json,
                updated_at
            FROM standings
            WHERE id = ?
            """,
            (standing_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    result = dict(row)
    result["raw"] = json.loads(result.pop("raw_json"))

    return result

# -------------------------------------------------------------------
# Fixture statistics
# -------------------------------------------------------------------

def save_fixture_statistics(
    api_response: dict[str, Any],
    fixture_id: int,
) -> int:
    response_items = api_response.get("response", [])
    updated_at = get_utc_now()
    saved_count = 0

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM fixture_statistics
            WHERE fixture_id = ?
            """,
            (fixture_id,),
        )

        for item in response_items:
            team = item.get("team", {})
            statistics = item.get("statistics", [])

            team_id = team.get("id")

            if team_id is None:
                continue

            for statistic in statistics:
                stat_type = statistic.get("type")
                stat_value = statistic.get("value")

                if not stat_type:
                    continue

                cursor.execute(
                    """
                    INSERT INTO fixture_statistics (
                        fixture_id,
                        team_id,
                        team_name,
                        team_logo,
                        stat_type,
                        stat_value,
                        raw_json,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(fixture_id, team_id, stat_type) DO UPDATE SET
                        team_name = excluded.team_name,
                        team_logo = excluded.team_logo,
                        stat_value = excluded.stat_value,
                        raw_json = excluded.raw_json,
                        updated_at = excluded.updated_at
                    """,
                    (
                        fixture_id,
                        team_id,
                        team.get("name"),
                        team.get("logo"),
                        stat_type,
                        None if stat_value is None else str(stat_value),
                        json.dumps(statistic, ensure_ascii=False),
                        updated_at,
                    ),
                )

                saved_count += 1

        connection.commit()

    return saved_count


def count_fixture_statistics() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM fixture_statistics")
        row = cursor.fetchone()

        return int(row["total"])


def list_fixture_statistics_by_fixture_id(
    fixture_id: int,
) -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                fixture_id,
                team_id,
                team_name,
                team_logo,
                stat_type,
                stat_value,
                updated_at
            FROM fixture_statistics
            WHERE fixture_id = ?
            ORDER BY team_name ASC, stat_type ASC
            """,
            (fixture_id,),
        )

        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_fixture_statistics_as_comparison(
    fixture_id: int,
) -> list[dict[str, Any]]:
    statistics = list_fixture_statistics_by_fixture_id(fixture_id)

    if not statistics:
        return []

    teams = []
    stat_map: dict[str, dict[str, Any]] = {}

    for stat in statistics:
        team_name = stat["team_name"]

        if team_name not in teams:
            teams.append(team_name)

        stat_type = stat["stat_type"]

        if stat_type not in stat_map:
            stat_map[stat_type] = {
                "Statistique": stat_type,
            }

        stat_map[stat_type][team_name] = stat["stat_value"]

    return list(stat_map.values())

# -------------------------------------------------------------------
# Fixture events
# -------------------------------------------------------------------

def save_fixture_events(
    api_response: dict[str, Any],
    fixture_id: int,
) -> int:
    events = api_response.get("response", [])
    updated_at = get_utc_now()
    saved_count = 0

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM fixture_events
            WHERE fixture_id = ?
            """,
            (fixture_id,),
        )

        for index, item in enumerate(events):
            time_data = item.get("time", {})
            team = item.get("team", {})
            player = item.get("player", {})
            assist = item.get("assist", {})

            cursor.execute(
                """
                INSERT INTO fixture_events (
                    fixture_id,
                    event_index,
                    elapsed,
                    extra,
                    team_id,
                    team_name,
                    team_logo,
                    player_id,
                    player_name,
                    assist_id,
                    assist_name,
                    event_type,
                    event_detail,
                    comments,
                    raw_json,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(fixture_id, event_index) DO UPDATE SET
                    elapsed = excluded.elapsed,
                    extra = excluded.extra,
                    team_id = excluded.team_id,
                    team_name = excluded.team_name,
                    team_logo = excluded.team_logo,
                    player_id = excluded.player_id,
                    player_name = excluded.player_name,
                    assist_id = excluded.assist_id,
                    assist_name = excluded.assist_name,
                    event_type = excluded.event_type,
                    event_detail = excluded.event_detail,
                    comments = excluded.comments,
                    raw_json = excluded.raw_json,
                    updated_at = excluded.updated_at
                """,
                (
                    fixture_id,
                    index,
                    time_data.get("elapsed"),
                    time_data.get("extra"),
                    team.get("id"),
                    team.get("name"),
                    team.get("logo"),
                    player.get("id"),
                    player.get("name"),
                    assist.get("id"),
                    assist.get("name"),
                    item.get("type"),
                    item.get("detail"),
                    item.get("comments"),
                    json.dumps(item, ensure_ascii=False),
                    updated_at,
                ),
            )

            saved_count += 1

        connection.commit()

    return saved_count


def count_fixture_events() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM fixture_events")
        row = cursor.fetchone()

        return int(row["total"])


def list_fixture_events_by_fixture_id(
    fixture_id: int,
) -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                fixture_id,
                event_index,
                elapsed,
                extra,
                team_id,
                team_name,
                team_logo,
                player_id,
                player_name,
                assist_id,
                assist_name,
                event_type,
                event_detail,
                comments,
                updated_at
            FROM fixture_events
            WHERE fixture_id = ?
            ORDER BY
                COALESCE(elapsed, 0) ASC,
                COALESCE(extra, 0) ASC,
                event_index ASC
            """,
            (fixture_id,),
        )

        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_fixture_event_by_id(event_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                fixture_id,
                event_index,
                elapsed,
                extra,
                team_id,
                team_name,
                team_logo,
                player_id,
                player_name,
                assist_id,
                assist_name,
                event_type,
                event_detail,
                comments,
                raw_json,
                updated_at
            FROM fixture_events
            WHERE id = ?
            """,
            (event_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    result = dict(row)
    result["raw"] = json.loads(result.pop("raw_json"))

    return result

# -------------------------------------------------------------------
# Fixture lineups
# -------------------------------------------------------------------

def save_fixture_lineups(
    api_response: dict[str, Any],
    fixture_id: int,
) -> int:
    lineups = api_response.get("response", [])
    updated_at = get_utc_now()
    saved_count = 0

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM fixture_lineup_players
            WHERE fixture_id = ?
            """,
            (fixture_id,),
        )

        cursor.execute(
            """
            DELETE FROM fixture_lineups
            WHERE fixture_id = ?
            """,
            (fixture_id,),
        )

        for item in lineups:
            team = item.get("team", {})
            coach = item.get("coach", {})
            team_id = team.get("id")

            if team_id is None:
                continue

            cursor.execute(
                """
                INSERT INTO fixture_lineups (
                    fixture_id,
                    team_id,
                    team_name,
                    team_logo,
                    coach_id,
                    coach_name,
                    coach_photo,
                    formation,
                    team_colors_json,
                    raw_json,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(fixture_id, team_id) DO UPDATE SET
                    team_name = excluded.team_name,
                    team_logo = excluded.team_logo,
                    coach_id = excluded.coach_id,
                    coach_name = excluded.coach_name,
                    coach_photo = excluded.coach_photo,
                    formation = excluded.formation,
                    team_colors_json = excluded.team_colors_json,
                    raw_json = excluded.raw_json,
                    updated_at = excluded.updated_at
                """,
                (
                    fixture_id,
                    team_id,
                    team.get("name"),
                    team.get("logo"),
                    coach.get("id"),
                    coach.get("name"),
                    coach.get("photo"),
                    item.get("formation"),
                    json.dumps(item.get("team", {}).get("colors", {}), ensure_ascii=False),
                    json.dumps(item, ensure_ascii=False),
                    updated_at,
                ),
            )

            start_xi = item.get("startXI", [])
            substitutes = item.get("substitutes", [])

            for index, player_item in enumerate(start_xi):
                player = player_item.get("player", {})

                cursor.execute(
                    """
                    INSERT INTO fixture_lineup_players (
                        fixture_id,
                        team_id,
                        lineup_type,
                        player_index,
                        player_id,
                        player_name,
                        player_number,
                        player_position,
                        player_grid,
                        raw_json,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(fixture_id, team_id, lineup_type, player_index) DO UPDATE SET
                        player_id = excluded.player_id,
                        player_name = excluded.player_name,
                        player_number = excluded.player_number,
                        player_position = excluded.player_position,
                        player_grid = excluded.player_grid,
                        raw_json = excluded.raw_json,
                        updated_at = excluded.updated_at
                    """,
                    (
                        fixture_id,
                        team_id,
                        "startXI",
                        index,
                        player.get("id"),
                        player.get("name"),
                        player.get("number"),
                        player.get("pos"),
                        player.get("grid"),
                        json.dumps(player_item, ensure_ascii=False),
                        updated_at,
                    ),
                )

                saved_count += 1

            for index, player_item in enumerate(substitutes):
                player = player_item.get("player", {})

                cursor.execute(
                    """
                    INSERT INTO fixture_lineup_players (
                        fixture_id,
                        team_id,
                        lineup_type,
                        player_index,
                        player_id,
                        player_name,
                        player_number,
                        player_position,
                        player_grid,
                        raw_json,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(fixture_id, team_id, lineup_type, player_index) DO UPDATE SET
                        player_id = excluded.player_id,
                        player_name = excluded.player_name,
                        player_number = excluded.player_number,
                        player_position = excluded.player_position,
                        player_grid = excluded.player_grid,
                        raw_json = excluded.raw_json,
                        updated_at = excluded.updated_at
                    """,
                    (
                        fixture_id,
                        team_id,
                        "substitute",
                        index,
                        player.get("id"),
                        player.get("name"),
                        player.get("number"),
                        player.get("pos"),
                        player.get("grid"),
                        json.dumps(player_item, ensure_ascii=False),
                        updated_at,
                    ),
                )

                saved_count += 1

        connection.commit()

    return saved_count


def count_fixture_lineups() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM fixture_lineups")
        row = cursor.fetchone()

        return int(row["total"])


def count_fixture_lineup_players() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM fixture_lineup_players")
        row = cursor.fetchone()

        return int(row["total"])


def list_fixture_lineups_by_fixture_id(
    fixture_id: int,
) -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                fixture_id,
                team_id,
                team_name,
                team_logo,
                coach_id,
                coach_name,
                coach_photo,
                formation,
                team_colors_json,
                updated_at
            FROM fixture_lineups
            WHERE fixture_id = ?
            ORDER BY team_name ASC
            """,
            (fixture_id,),
        )

        rows = cursor.fetchall()

    results = []

    for row in rows:
        item = dict(row)
        item["team_colors"] = json.loads(item.pop("team_colors_json") or "{}")
        results.append(item)

    return results


def list_fixture_lineup_players(
    fixture_id: int,
    team_id: int,
    lineup_type: str | None = None,
) -> list[dict[str, Any]]:
    query = """
        SELECT
            id,
            fixture_id,
            team_id,
            lineup_type,
            player_index,
            player_id,
            player_name,
            player_number,
            player_position,
            player_grid,
            updated_at
        FROM fixture_lineup_players
        WHERE fixture_id = ?
        AND team_id = ?
    """

    params: list[Any] = [fixture_id, team_id]

    if lineup_type:
        query += " AND lineup_type = ?"
        params.append(lineup_type)

    query += """
        ORDER BY lineup_type ASC, player_index ASC
    """

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_fixture_lineup_by_id(lineup_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                fixture_id,
                team_id,
                team_name,
                team_logo,
                coach_id,
                coach_name,
                coach_photo,
                formation,
                team_colors_json,
                raw_json,
                updated_at
            FROM fixture_lineups
            WHERE id = ?
            """,
            (lineup_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    result = dict(row)
    result["team_colors"] = json.loads(result.pop("team_colors_json") or "{}")
    result["raw"] = json.loads(result.pop("raw_json"))

    return result