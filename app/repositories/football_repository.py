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

# -------------------------------------------------------------------
# Fixture player statistics
# -------------------------------------------------------------------

def save_fixture_player_statistics(
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
            DELETE FROM fixture_player_statistics
            WHERE fixture_id = ?
            """,
            (fixture_id,),
        )

        for team_item in response_items:
            team = team_item.get("team", {})
            players = team_item.get("players", [])

            team_id = team.get("id")

            if team_id is None:
                continue

            for player_item in players:
                player = player_item.get("player", {})
                statistics = player_item.get("statistics", [])

                player_id = player.get("id")

                for stat_index, stat in enumerate(statistics):
                    games = stat.get("games", {})
                    offsides = stat.get("offsides")
                    shots = stat.get("shots", {})
                    goals = stat.get("goals", {})
                    passes = stat.get("passes", {})
                    tackles = stat.get("tackles", {})
                    duels = stat.get("duels", {})
                    dribbles = stat.get("dribbles", {})
                    fouls = stat.get("fouls", {})
                    cards = stat.get("cards", {})
                    penalty = stat.get("penalty", {})

                    cursor.execute(
                        """
                        INSERT INTO fixture_player_statistics (
                            fixture_id,
                            team_id,
                            team_name,
                            team_logo,
                            player_id,
                            player_name,
                            player_photo,
                            stat_index,

                            games_minutes,
                            games_number,
                            games_position,
                            games_rating,
                            games_captain,
                            games_substitute,

                            offsides,

                            shots_total,
                            shots_on,

                            goals_total,
                            goals_conceded,
                            goals_assists,
                            goals_saves,

                            passes_total,
                            passes_key,
                            passes_accuracy,

                            tackles_total,
                            tackles_blocks,
                            tackles_interceptions,

                            duels_total,
                            duels_won,

                            dribbles_attempts,
                            dribbles_success,
                            dribbles_past,

                            fouls_drawn,
                            fouls_committed,

                            cards_yellow,
                            cards_red,

                            penalty_won,
                            penalty_commited,
                            penalty_scored,
                            penalty_missed,
                            penalty_saved,

                            raw_json,
                            updated_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(fixture_id, team_id, player_id, stat_index) DO UPDATE SET
                            team_name = excluded.team_name,
                            team_logo = excluded.team_logo,
                            player_name = excluded.player_name,
                            player_photo = excluded.player_photo,

                            games_minutes = excluded.games_minutes,
                            games_number = excluded.games_number,
                            games_position = excluded.games_position,
                            games_rating = excluded.games_rating,
                            games_captain = excluded.games_captain,
                            games_substitute = excluded.games_substitute,

                            offsides = excluded.offsides,

                            shots_total = excluded.shots_total,
                            shots_on = excluded.shots_on,

                            goals_total = excluded.goals_total,
                            goals_conceded = excluded.goals_conceded,
                            goals_assists = excluded.goals_assists,
                            goals_saves = excluded.goals_saves,

                            passes_total = excluded.passes_total,
                            passes_key = excluded.passes_key,
                            passes_accuracy = excluded.passes_accuracy,

                            tackles_total = excluded.tackles_total,
                            tackles_blocks = excluded.tackles_blocks,
                            tackles_interceptions = excluded.tackles_interceptions,

                            duels_total = excluded.duels_total,
                            duels_won = excluded.duels_won,

                            dribbles_attempts = excluded.dribbles_attempts,
                            dribbles_success = excluded.dribbles_success,
                            dribbles_past = excluded.dribbles_past,

                            fouls_drawn = excluded.fouls_drawn,
                            fouls_committed = excluded.fouls_committed,

                            cards_yellow = excluded.cards_yellow,
                            cards_red = excluded.cards_red,

                            penalty_won = excluded.penalty_won,
                            penalty_commited = excluded.penalty_commited,
                            penalty_scored = excluded.penalty_scored,
                            penalty_missed = excluded.penalty_missed,
                            penalty_saved = excluded.penalty_saved,

                            raw_json = excluded.raw_json,
                            updated_at = excluded.updated_at
                        """,
                        (
                            fixture_id,
                            team_id,
                            team.get("name"),
                            team.get("logo"),
                            player_id,
                            player.get("name"),
                            player.get("photo"),
                            stat_index,

                            games.get("minutes"),
                            games.get("number"),
                            games.get("position"),
                            games.get("rating"),
                            1 if games.get("captain") else 0 if games.get("captain") is False else None,
                            1 if games.get("substitute") else 0 if games.get("substitute") is False else None,

                            offsides,

                            shots.get("total"),
                            shots.get("on"),

                            goals.get("total"),
                            goals.get("conceded"),
                            goals.get("assists"),
                            goals.get("saves"),

                            passes.get("total"),
                            passes.get("key"),
                            None if passes.get("accuracy") is None else str(passes.get("accuracy")),

                            tackles.get("total"),
                            tackles.get("blocks"),
                            tackles.get("interceptions"),

                            duels.get("total"),
                            duels.get("won"),

                            dribbles.get("attempts"),
                            dribbles.get("success"),
                            dribbles.get("past"),

                            fouls.get("drawn"),
                            fouls.get("committed"),

                            cards.get("yellow"),
                            cards.get("red"),

                            penalty.get("won"),
                            penalty.get("commited"),
                            penalty.get("scored"),
                            penalty.get("missed"),
                            penalty.get("saved"),

                            json.dumps(
                                {
                                    "player": player,
                                    "statistics": stat,
                                },
                                ensure_ascii=False,
                            ),
                            updated_at,
                        ),
                    )

                    saved_count += 1

        connection.commit()

    return saved_count


def count_fixture_player_statistics() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM fixture_player_statistics")
        row = cursor.fetchone()

        return int(row["total"])


def list_fixture_player_statistics_by_fixture_id(
    fixture_id: int,
    team_id: int | None = None,
) -> list[dict[str, Any]]:
    query = """
        SELECT
            id,
            fixture_id,
            team_id,
            team_name,
            team_logo,
            player_id,
            player_name,
            player_photo,
            stat_index,

            games_minutes,
            games_number,
            games_position,
            games_rating,
            games_captain,
            games_substitute,

            offsides,

            shots_total,
            shots_on,

            goals_total,
            goals_conceded,
            goals_assists,
            goals_saves,

            passes_total,
            passes_key,
            passes_accuracy,

            tackles_total,
            tackles_blocks,
            tackles_interceptions,

            duels_total,
            duels_won,

            dribbles_attempts,
            dribbles_success,
            dribbles_past,

            fouls_drawn,
            fouls_committed,

            cards_yellow,
            cards_red,

            penalty_won,
            penalty_commited,
            penalty_scored,
            penalty_missed,
            penalty_saved,

            updated_at
        FROM fixture_player_statistics
        WHERE fixture_id = ?
    """

    params: list[Any] = [fixture_id]

    if team_id is not None:
        query += " AND team_id = ?"
        params.append(team_id)

    query += """
        ORDER BY team_name ASC, games_number ASC, player_name ASC
    """

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_fixture_player_statistic_by_id(
    fixture_player_statistic_id: int,
) -> dict[str, Any] | None:
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
                player_id,
                player_name,
                player_photo,
                stat_index,

                games_minutes,
                games_number,
                games_position,
                games_rating,
                games_captain,
                games_substitute,

                offsides,

                shots_total,
                shots_on,

                goals_total,
                goals_conceded,
                goals_assists,
                goals_saves,

                passes_total,
                passes_key,
                passes_accuracy,

                tackles_total,
                tackles_blocks,
                tackles_interceptions,

                duels_total,
                duels_won,

                dribbles_attempts,
                dribbles_success,
                dribbles_past,

                fouls_drawn,
                fouls_committed,

                cards_yellow,
                cards_red,

                penalty_won,
                penalty_commited,
                penalty_scored,
                penalty_missed,
                penalty_saved,

                raw_json,
                updated_at
            FROM fixture_player_statistics
            WHERE id = ?
            """,
            (fixture_player_statistic_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    result = dict(row)
    result["raw"] = json.loads(result.pop("raw_json"))

    return result

# -------------------------------------------------------------------
# Head-to-head
# -------------------------------------------------------------------

def get_pair_key(team_a_id: int, team_b_id: int) -> str:
    first_id, second_id = sorted([team_a_id, team_b_id])
    return f"{first_id}-{second_id}"


def save_head_to_head_matches(
    api_response: dict[str, Any],
    team_a_id: int,
    team_b_id: int,
) -> int:
    matches = api_response.get("response", [])
    updated_at = get_utc_now()
    pair_key = get_pair_key(team_a_id, team_b_id)
    saved_count = 0

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM head_to_head_matches
            WHERE pair_key = ?
            """,
            (pair_key,),
        )

        for item in matches:
            fixture = item.get("fixture", {})
            league = item.get("league", {})
            teams = item.get("teams", {})
            goals = item.get("goals", {})

            venue = fixture.get("venue", {})
            status = fixture.get("status", {})

            home_team = teams.get("home", {})
            away_team = teams.get("away", {})

            fixture_id = fixture.get("id")

            if fixture_id is None:
                continue

            home_winner = home_team.get("winner")
            away_winner = away_team.get("winner")

            winner_team_id = None
            winner_team_name = None

            if home_winner is True:
                winner_team_id = home_team.get("id")
                winner_team_name = home_team.get("name")
            elif away_winner is True:
                winner_team_id = away_team.get("id")
                winner_team_name = away_team.get("name")

            cursor.execute(
                """
                INSERT INTO head_to_head_matches (
                    pair_key,
                    team_a_id,
                    team_b_id,
                    fixture_id,

                    league_id,
                    league_name,
                    league_country,
                    season_year,
                    round,

                    fixture_date,
                    fixture_timestamp,
                    status_long,
                    status_short,

                    venue_name,
                    venue_city,

                    home_team_id,
                    home_team_name,
                    home_team_logo,
                    away_team_id,
                    away_team_name,
                    away_team_logo,

                    home_goals,
                    away_goals,

                    winner_team_id,
                    winner_team_name,

                    raw_json,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(pair_key, fixture_id) DO UPDATE SET
                    team_a_id = excluded.team_a_id,
                    team_b_id = excluded.team_b_id,

                    league_id = excluded.league_id,
                    league_name = excluded.league_name,
                    league_country = excluded.league_country,
                    season_year = excluded.season_year,
                    round = excluded.round,

                    fixture_date = excluded.fixture_date,
                    fixture_timestamp = excluded.fixture_timestamp,
                    status_long = excluded.status_long,
                    status_short = excluded.status_short,

                    venue_name = excluded.venue_name,
                    venue_city = excluded.venue_city,

                    home_team_id = excluded.home_team_id,
                    home_team_name = excluded.home_team_name,
                    home_team_logo = excluded.home_team_logo,
                    away_team_id = excluded.away_team_id,
                    away_team_name = excluded.away_team_name,
                    away_team_logo = excluded.away_team_logo,

                    home_goals = excluded.home_goals,
                    away_goals = excluded.away_goals,

                    winner_team_id = excluded.winner_team_id,
                    winner_team_name = excluded.winner_team_name,

                    raw_json = excluded.raw_json,
                    updated_at = excluded.updated_at
                """,
                (
                    pair_key,
                    team_a_id,
                    team_b_id,
                    fixture_id,

                    league.get("id"),
                    league.get("name"),
                    league.get("country"),
                    league.get("season"),
                    league.get("round"),

                    fixture.get("date"),
                    fixture.get("timestamp"),
                    status.get("long"),
                    status.get("short"),

                    venue.get("name"),
                    venue.get("city"),

                    home_team.get("id"),
                    home_team.get("name"),
                    home_team.get("logo"),
                    away_team.get("id"),
                    away_team.get("name"),
                    away_team.get("logo"),

                    goals.get("home"),
                    goals.get("away"),

                    winner_team_id,
                    winner_team_name,

                    json.dumps(item, ensure_ascii=False),
                    updated_at,
                ),
            )

            saved_count += 1

        connection.commit()

    return saved_count


def count_head_to_head_matches() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM head_to_head_matches")
        row = cursor.fetchone()

        return int(row["total"])


def list_head_to_head_matches(
    team_a_id: int,
    team_b_id: int,
    limit: int = 50,
) -> list[dict[str, Any]]:
    pair_key = get_pair_key(team_a_id, team_b_id)

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                pair_key,
                team_a_id,
                team_b_id,
                fixture_id,

                league_id,
                league_name,
                league_country,
                season_year,
                round,

                fixture_date,
                fixture_timestamp,
                status_long,
                status_short,

                venue_name,
                venue_city,

                home_team_id,
                home_team_name,
                home_team_logo,
                away_team_id,
                away_team_name,
                away_team_logo,

                home_goals,
                away_goals,

                winner_team_id,
                winner_team_name,

                updated_at
            FROM head_to_head_matches
            WHERE pair_key = ?
            ORDER BY fixture_timestamp DESC
            LIMIT ?
            """,
            (pair_key, limit),
        )

        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_head_to_head_match_by_id(
    head_to_head_match_id: int,
) -> dict[str, Any] | None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                pair_key,
                team_a_id,
                team_b_id,
                fixture_id,

                league_id,
                league_name,
                league_country,
                season_year,
                round,

                fixture_date,
                fixture_timestamp,
                status_long,
                status_short,

                venue_name,
                venue_city,

                home_team_id,
                home_team_name,
                home_team_logo,
                away_team_id,
                away_team_name,
                away_team_logo,

                home_goals,
                away_goals,

                winner_team_id,
                winner_team_name,

                raw_json,
                updated_at
            FROM head_to_head_matches
            WHERE id = ?
            """,
            (head_to_head_match_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    result = dict(row)
    result["raw"] = json.loads(result.pop("raw_json"))

    return result


def get_head_to_head_summary(
    team_a_id: int,
    team_b_id: int,
) -> dict[str, Any]:
    matches = list_head_to_head_matches(team_a_id, team_b_id, limit=500)

    team_a_wins = 0
    team_b_wins = 0
    draws = 0
    total_goals = 0
    played_matches = 0

    for match in matches:
        home_goals = match["home_goals"]
        away_goals = match["away_goals"]

        if home_goals is None or away_goals is None:
            continue

        played_matches += 1
        total_goals += home_goals + away_goals

        winner_team_id = match["winner_team_id"]

        if winner_team_id == team_a_id:
            team_a_wins += 1
        elif winner_team_id == team_b_id:
            team_b_wins += 1
        else:
            draws += 1

    average_goals = (
        round(total_goals / played_matches, 2)
        if played_matches > 0
        else 0
    )

    return {
        "matches_count": len(matches),
        "played_matches": played_matches,
        "team_a_wins": team_a_wins,
        "team_b_wins": team_b_wins,
        "draws": draws,
        "total_goals": total_goals,
        "average_goals": average_goals,
    }

# -------------------------------------------------------------------
# Players squads
# -------------------------------------------------------------------

def save_player_squad(
    api_response: dict[str, Any],
    team_id: int,
) -> int:
    response_items = api_response.get("response", [])
    updated_at = get_utc_now()
    saved_count = 0

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM team_squad_players
            WHERE team_id = ?
            """,
            (team_id,),
        )

        for item in response_items:
            team = item.get("team", {})
            players = item.get("players", [])

            api_team_id = team.get("id") or team_id

            for player in players:
                player_id = player.get("id")

                if player_id is None:
                    continue

                cursor.execute(
                    """
                    INSERT INTO players (
                        player_id,
                        name,
                        age,
                        photo,
                        raw_json,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(player_id) DO UPDATE SET
                        name = excluded.name,
                        age = excluded.age,
                        photo = excluded.photo,
                        raw_json = excluded.raw_json,
                        updated_at = excluded.updated_at
                    """,
                    (
                        player_id,
                        player.get("name"),
                        player.get("age"),
                        player.get("photo"),
                        json.dumps(player, ensure_ascii=False),
                        updated_at,
                    ),
                )

                cursor.execute(
                    """
                    INSERT INTO team_squad_players (
                        team_id,
                        player_id,
                        player_name,
                        player_age,
                        player_number,
                        player_position,
                        player_photo,
                        raw_json,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(team_id, player_id) DO UPDATE SET
                        player_name = excluded.player_name,
                        player_age = excluded.player_age,
                        player_number = excluded.player_number,
                        player_position = excluded.player_position,
                        player_photo = excluded.player_photo,
                        raw_json = excluded.raw_json,
                        updated_at = excluded.updated_at
                    """,
                    (
                        api_team_id,
                        player_id,
                        player.get("name"),
                        player.get("age"),
                        player.get("number"),
                        player.get("position"),
                        player.get("photo"),
                        json.dumps(player, ensure_ascii=False),
                        updated_at,
                    ),
                )

                saved_count += 1

        connection.commit()

    return saved_count


def count_players() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM players")
        row = cursor.fetchone()

        return int(row["total"])


def count_team_squad_players() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM team_squad_players")
        row = cursor.fetchone()

        return int(row["total"])


def list_squad_players_by_team_id(
    team_id: int,
) -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                team_id,
                player_id,
                player_name,
                player_age,
                player_number,
                player_position,
                player_photo,
                updated_at
            FROM team_squad_players
            WHERE team_id = ?
            ORDER BY
                player_position ASC,
                player_number ASC,
                player_name ASC
            """,
            (team_id,),
        )

        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_player_by_id(player_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                player_id,
                name,
                age,
                photo,
                raw_json,
                updated_at
            FROM players
            WHERE player_id = ?
            """,
            (player_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    result = dict(row)
    result["raw"] = json.loads(result.pop("raw_json"))

    return result


def get_squad_player_by_id(squad_player_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                team_id,
                player_id,
                player_name,
                player_age,
                player_number,
                player_position,
                player_photo,
                raw_json,
                updated_at
            FROM team_squad_players
            WHERE id = ?
            """,
            (squad_player_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    result = dict(row)
    result["raw"] = json.loads(result.pop("raw_json"))

    return result

# -------------------------------------------------------------------
# Player season statistics
# -------------------------------------------------------------------

def save_player_season_statistics(
    api_response: dict[str, Any],
    league_id: int,
    season_year: int,
) -> int:
    response_items = api_response.get("response", [])
    updated_at = get_utc_now()
    saved_count = 0

    with get_connection() as connection:
        cursor = connection.cursor()

        for item in response_items:
            player = item.get("player", {})
            statistics = item.get("statistics", [])

            player_id = player.get("id")

            if player_id is None:
                continue

            cursor.execute(
                """
                INSERT INTO players (
                    player_id,
                    name,
                    age,
                    photo,
                    raw_json,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(player_id) DO UPDATE SET
                    name = excluded.name,
                    age = excluded.age,
                    photo = excluded.photo,
                    raw_json = excluded.raw_json,
                    updated_at = excluded.updated_at
                """,
                (
                    player_id,
                    player.get("name"),
                    player.get("age"),
                    player.get("photo"),
                    json.dumps(player, ensure_ascii=False),
                    updated_at,
                ),
            )

            birth = player.get("birth", {})

            for stat in statistics:
                team = stat.get("team", {})
                league = stat.get("league", {})
                games = stat.get("games", {})
                substitutes = stat.get("substitutes", {})
                shots = stat.get("shots", {})
                goals = stat.get("goals", {})
                passes = stat.get("passes", {})
                tackles = stat.get("tackles", {})
                duels = stat.get("duels", {})
                dribbles = stat.get("dribbles", {})
                fouls = stat.get("fouls", {})
                cards = stat.get("cards", {})
                penalty = stat.get("penalty", {})

                api_team_id = team.get("id")
                api_league_id = league.get("id") or league_id
                api_season = league.get("season") or season_year

                cursor.execute(
                    """
                    INSERT INTO player_season_statistics (
                        player_id,
                        player_name,
                        player_firstname,
                        player_lastname,
                        player_age,
                        player_birth_date,
                        player_birth_place,
                        player_birth_country,
                        player_nationality,
                        player_height,
                        player_weight,
                        player_injured,
                        player_photo,

                        team_id,
                        team_name,
                        team_logo,

                        league_id,
                        league_name,
                        league_country,
                        league_logo,
                        league_flag,
                        season_year,

                        games_appearences,
                        games_lineups,
                        games_minutes,
                        games_number,
                        games_position,
                        games_rating,
                        games_captain,

                        substitutes_in,
                        substitutes_out,
                        substitutes_bench,

                        shots_total,
                        shots_on,

                        goals_total,
                        goals_conceded,
                        goals_assists,
                        goals_saves,

                        passes_total,
                        passes_key,
                        passes_accuracy,

                        tackles_total,
                        tackles_blocks,
                        tackles_interceptions,

                        duels_total,
                        duels_won,

                        dribbles_attempts,
                        dribbles_success,
                        dribbles_past,

                        fouls_drawn,
                        fouls_committed,

                        cards_yellow,
                        cards_yellowred,
                        cards_red,

                        penalty_won,
                        penalty_commited,
                        penalty_scored,
                        penalty_missed,
                        penalty_saved,

                        raw_json,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(player_id, team_id, league_id, season_year) DO UPDATE SET
                        player_name = excluded.player_name,
                        player_firstname = excluded.player_firstname,
                        player_lastname = excluded.player_lastname,
                        player_age = excluded.player_age,
                        player_birth_date = excluded.player_birth_date,
                        player_birth_place = excluded.player_birth_place,
                        player_birth_country = excluded.player_birth_country,
                        player_nationality = excluded.player_nationality,
                        player_height = excluded.player_height,
                        player_weight = excluded.player_weight,
                        player_injured = excluded.player_injured,
                        player_photo = excluded.player_photo,

                        team_name = excluded.team_name,
                        team_logo = excluded.team_logo,

                        league_name = excluded.league_name,
                        league_country = excluded.league_country,
                        league_logo = excluded.league_logo,
                        league_flag = excluded.league_flag,

                        games_appearences = excluded.games_appearences,
                        games_lineups = excluded.games_lineups,
                        games_minutes = excluded.games_minutes,
                        games_number = excluded.games_number,
                        games_position = excluded.games_position,
                        games_rating = excluded.games_rating,
                        games_captain = excluded.games_captain,

                        substitutes_in = excluded.substitutes_in,
                        substitutes_out = excluded.substitutes_out,
                        substitutes_bench = excluded.substitutes_bench,

                        shots_total = excluded.shots_total,
                        shots_on = excluded.shots_on,

                        goals_total = excluded.goals_total,
                        goals_conceded = excluded.goals_conceded,
                        goals_assists = excluded.goals_assists,
                        goals_saves = excluded.goals_saves,

                        passes_total = excluded.passes_total,
                        passes_key = excluded.passes_key,
                        passes_accuracy = excluded.passes_accuracy,

                        tackles_total = excluded.tackles_total,
                        tackles_blocks = excluded.tackles_blocks,
                        tackles_interceptions = excluded.tackles_interceptions,

                        duels_total = excluded.duels_total,
                        duels_won = excluded.duels_won,

                        dribbles_attempts = excluded.dribbles_attempts,
                        dribbles_success = excluded.dribbles_success,
                        dribbles_past = excluded.dribbles_past,

                        fouls_drawn = excluded.fouls_drawn,
                        fouls_committed = excluded.fouls_committed,

                        cards_yellow = excluded.cards_yellow,
                        cards_yellowred = excluded.cards_yellowred,
                        cards_red = excluded.cards_red,

                        penalty_won = excluded.penalty_won,
                        penalty_commited = excluded.penalty_commited,
                        penalty_scored = excluded.penalty_scored,
                        penalty_missed = excluded.penalty_missed,
                        penalty_saved = excluded.penalty_saved,

                        raw_json = excluded.raw_json,
                        updated_at = excluded.updated_at
                    """,
                    (
                        player_id,
                        player.get("name"),
                        player.get("firstname"),
                        player.get("lastname"),
                        player.get("age"),
                        birth.get("date"),
                        birth.get("place"),
                        birth.get("country"),
                        player.get("nationality"),
                        player.get("height"),
                        player.get("weight"),
                        1 if player.get("injured") else 0 if player.get("injured") is False else None,
                        player.get("photo"),

                        api_team_id,
                        team.get("name"),
                        team.get("logo"),

                        api_league_id,
                        league.get("name"),
                        league.get("country"),
                        league.get("logo"),
                        league.get("flag"),
                        api_season,

                        games.get("appearences"),
                        games.get("lineups"),
                        games.get("minutes"),
                        games.get("number"),
                        games.get("position"),
                        games.get("rating"),
                        1 if games.get("captain") else 0 if games.get("captain") is False else None,

                        substitutes.get("in"),
                        substitutes.get("out"),
                        substitutes.get("bench"),

                        shots.get("total"),
                        shots.get("on"),

                        goals.get("total"),
                        goals.get("conceded"),
                        goals.get("assists"),
                        goals.get("saves"),

                        passes.get("total"),
                        passes.get("key"),
                        None if passes.get("accuracy") is None else str(passes.get("accuracy")),

                        tackles.get("total"),
                        tackles.get("blocks"),
                        tackles.get("interceptions"),

                        duels.get("total"),
                        duels.get("won"),

                        dribbles.get("attempts"),
                        dribbles.get("success"),
                        dribbles.get("past"),

                        fouls.get("drawn"),
                        fouls.get("committed"),

                        cards.get("yellow"),
                        cards.get("yellowred"),
                        cards.get("red"),

                        penalty.get("won"),
                        penalty.get("commited"),
                        penalty.get("scored"),
                        penalty.get("missed"),
                        penalty.get("saved"),

                        json.dumps(item, ensure_ascii=False),
                        updated_at,
                    ),
                )

                saved_count += 1

        connection.commit()

    return saved_count


def count_player_season_statistics() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM player_season_statistics")
        row = cursor.fetchone()

        return int(row["total"])


def list_player_season_statistics(
    league_id: int,
    season_year: int,
    team_id: int | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    query = """
        SELECT
            id,
            player_id,
            player_name,
            player_age,
            player_nationality,
            player_height,
            player_weight,
            player_photo,

            team_id,
            team_name,
            team_logo,

            league_id,
            league_name,
            season_year,

            games_appearences,
            games_lineups,
            games_minutes,
            games_position,
            games_rating,

            goals_total,
            goals_assists,
            shots_total,
            shots_on,

            passes_total,
            passes_key,
            passes_accuracy,

            duels_total,
            duels_won,
            dribbles_attempts,
            dribbles_success,

            cards_yellow,
            cards_red,

            updated_at
        FROM player_season_statistics
        WHERE league_id = ?
        AND season_year = ?
    """

    params: list[Any] = [league_id, season_year]

    if team_id is not None:
        query += " AND team_id = ?"
        params.append(team_id)

    query += """
        ORDER BY
            goals_total DESC,
            goals_assists DESC,
            games_rating DESC,
            player_name ASC
        LIMIT ?
    """
    params.append(limit)

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_player_season_statistic_by_id(
    player_season_statistic_id: int,
) -> dict[str, Any] | None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                *
            FROM player_season_statistics
            WHERE id = ?
            """,
            (player_season_statistic_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    result = dict(row)
    result["raw"] = json.loads(result.pop("raw_json"))

    return result

# -------------------------------------------------------------------
# Top player statistics
# -------------------------------------------------------------------

TOP_PLAYER_CATEGORIES = {
    "top_scorers": "players/topscorers",
    "top_assists": "players/topassists",
    "top_yellow_cards": "players/topyellowcards",
    "top_red_cards": "players/topredcards",
}


def save_top_player_statistics(
    api_response: dict[str, Any],
    category: str,
    league_id: int,
    season_year: int,
) -> int:
    response_items = api_response.get("response", [])
    updated_at = get_utc_now()
    endpoint = TOP_PLAYER_CATEGORIES.get(category, category)
    saved_count = 0

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM top_player_statistics
            WHERE category = ?
            AND league_id = ?
            AND season_year = ?
            """,
            (category, league_id, season_year),
        )

        for item in response_items:
            player = item.get("player", {})
            statistics = item.get("statistics", [])

            player_id = player.get("id")

            if player_id is None:
                continue

            cursor.execute(
                """
                INSERT INTO players (
                    player_id,
                    name,
                    age,
                    photo,
                    raw_json,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(player_id) DO UPDATE SET
                    name = excluded.name,
                    age = excluded.age,
                    photo = excluded.photo,
                    raw_json = excluded.raw_json,
                    updated_at = excluded.updated_at
                """,
                (
                    player_id,
                    player.get("name"),
                    player.get("age"),
                    player.get("photo"),
                    json.dumps(player, ensure_ascii=False),
                    updated_at,
                ),
            )

            birth = player.get("birth", {})

            if not statistics:
                continue

            stat = statistics[0]

            team = stat.get("team", {})
            league = stat.get("league", {})
            games = stat.get("games", {})
            goals = stat.get("goals", {})
            cards = stat.get("cards", {})

            api_team_id = team.get("id")
            api_league_id = league.get("id") or league_id
            api_season = league.get("season") or season_year

            cursor.execute(
                """
                INSERT INTO top_player_statistics (
                    category,
                    endpoint,

                    player_id,
                    player_name,
                    player_firstname,
                    player_lastname,
                    player_age,
                    player_birth_date,
                    player_birth_place,
                    player_birth_country,
                    player_nationality,
                    player_height,
                    player_weight,
                    player_injured,
                    player_photo,

                    team_id,
                    team_name,
                    team_logo,

                    league_id,
                    league_name,
                    league_country,
                    league_logo,
                    league_flag,
                    season_year,

                    games_appearences,
                    games_lineups,
                    games_minutes,
                    games_number,
                    games_position,
                    games_rating,
                    games_captain,

                    goals_total,
                    goals_assists,

                    cards_yellow,
                    cards_yellowred,
                    cards_red,

                    raw_json,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(category, player_id, team_id, league_id, season_year) DO UPDATE SET
                    endpoint = excluded.endpoint,

                    player_name = excluded.player_name,
                    player_firstname = excluded.player_firstname,
                    player_lastname = excluded.player_lastname,
                    player_age = excluded.player_age,
                    player_birth_date = excluded.player_birth_date,
                    player_birth_place = excluded.player_birth_place,
                    player_birth_country = excluded.player_birth_country,
                    player_nationality = excluded.player_nationality,
                    player_height = excluded.player_height,
                    player_weight = excluded.player_weight,
                    player_injured = excluded.player_injured,
                    player_photo = excluded.player_photo,

                    team_name = excluded.team_name,
                    team_logo = excluded.team_logo,

                    league_name = excluded.league_name,
                    league_country = excluded.league_country,
                    league_logo = excluded.league_logo,
                    league_flag = excluded.league_flag,

                    games_appearences = excluded.games_appearences,
                    games_lineups = excluded.games_lineups,
                    games_minutes = excluded.games_minutes,
                    games_number = excluded.games_number,
                    games_position = excluded.games_position,
                    games_rating = excluded.games_rating,
                    games_captain = excluded.games_captain,

                    goals_total = excluded.goals_total,
                    goals_assists = excluded.goals_assists,

                    cards_yellow = excluded.cards_yellow,
                    cards_yellowred = excluded.cards_yellowred,
                    cards_red = excluded.cards_red,

                    raw_json = excluded.raw_json,
                    updated_at = excluded.updated_at
                """,
                (
                    category,
                    endpoint,

                    player_id,
                    player.get("name"),
                    player.get("firstname"),
                    player.get("lastname"),
                    player.get("age"),
                    birth.get("date"),
                    birth.get("place"),
                    birth.get("country"),
                    player.get("nationality"),
                    player.get("height"),
                    player.get("weight"),
                    1 if player.get("injured") else 0 if player.get("injured") is False else None,
                    player.get("photo"),

                    api_team_id,
                    team.get("name"),
                    team.get("logo"),

                    api_league_id,
                    league.get("name"),
                    league.get("country"),
                    league.get("logo"),
                    league.get("flag"),
                    api_season,

                    games.get("appearences"),
                    games.get("lineups"),
                    games.get("minutes"),
                    games.get("number"),
                    games.get("position"),
                    games.get("rating"),
                    1 if games.get("captain") else 0 if games.get("captain") is False else None,

                    goals.get("total"),
                    goals.get("assists"),

                    cards.get("yellow"),
                    cards.get("yellowred"),
                    cards.get("red"),

                    json.dumps(item, ensure_ascii=False),
                    updated_at,
                ),
            )

            saved_count += 1

        connection.commit()

    return saved_count


def count_top_player_statistics() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM top_player_statistics")
        row = cursor.fetchone()

        return int(row["total"])


def list_top_player_statistics(
    category: str,
    league_id: int,
    season_year: int,
    limit: int = 50,
) -> list[dict[str, Any]]:
    order_by_by_category = {
        "top_scorers": "goals_total DESC, goals_assists DESC",
        "top_assists": "goals_assists DESC, goals_total DESC",
        "top_yellow_cards": "cards_yellow DESC, cards_yellowred DESC",
        "top_red_cards": "cards_red DESC, cards_yellowred DESC",
    }

    order_by = order_by_by_category.get(
        category,
        "goals_total DESC, goals_assists DESC"
    )

    query = f"""
        SELECT
            id,
            category,
            endpoint,

            player_id,
            player_name,
            player_age,
            player_nationality,
            player_photo,

            team_id,
            team_name,
            team_logo,

            league_id,
            league_name,
            season_year,

            games_appearences,
            games_minutes,
            games_position,
            games_rating,

            goals_total,
            goals_assists,

            cards_yellow,
            cards_yellowred,
            cards_red,

            updated_at
        FROM top_player_statistics
        WHERE category = ?
        AND league_id = ?
        AND season_year = ?
        ORDER BY {order_by}
        LIMIT ?
    """

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            query,
            (category, league_id, season_year, limit),
        )
        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_top_player_statistic_by_id(
    top_player_statistic_id: int,
) -> dict[str, Any] | None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM top_player_statistics
            WHERE id = ?
            """,
            (top_player_statistic_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    result = dict(row)
    result["raw"] = json.loads(result.pop("raw_json"))

    return result

# -------------------------------------------------------------------
# Injuries and sidelined
# -------------------------------------------------------------------

def save_injuries(
    api_response: dict[str, Any],
) -> int:
    response_items = api_response.get("response", [])
    updated_at = get_utc_now()
    saved_count = 0

    with get_connection() as connection:
        cursor = connection.cursor()

        for item in response_items:
            player = item.get("player", {})
            team = item.get("team", {})
            fixture = item.get("fixture", {})
            league = item.get("league", {})

            player_id = player.get("id")
            team_id = team.get("id")
            fixture_id = fixture.get("id")
            league_id = league.get("id")
            season_year = league.get("season")

            cursor.execute(
                """
                INSERT INTO injuries (
                    player_id,
                    player_name,
                    player_photo,
                    injury_type,
                    reason,

                    team_id,
                    team_name,
                    team_logo,

                    fixture_id,
                    fixture_timezone,
                    fixture_date,
                    fixture_timestamp,

                    league_id,
                    league_name,
                    league_country,
                    league_logo,
                    league_flag,
                    season_year,

                    raw_json,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(
                    player_id,
                    team_id,
                    fixture_id,
                    league_id,
                    season_year,
                    injury_type,
                    reason
                ) DO UPDATE SET
                    player_name = excluded.player_name,
                    player_photo = excluded.player_photo,
                    team_name = excluded.team_name,
                    team_logo = excluded.team_logo,
                    fixture_timezone = excluded.fixture_timezone,
                    fixture_date = excluded.fixture_date,
                    fixture_timestamp = excluded.fixture_timestamp,
                    league_name = excluded.league_name,
                    league_country = excluded.league_country,
                    league_logo = excluded.league_logo,
                    league_flag = excluded.league_flag,
                    raw_json = excluded.raw_json,
                    updated_at = excluded.updated_at
                """,
                (
                    player_id,
                    player.get("name"),
                    player.get("photo"),
                    player.get("type"),
                    player.get("reason"),

                    team_id,
                    team.get("name"),
                    team.get("logo"),

                    fixture_id,
                    fixture.get("timezone"),
                    fixture.get("date"),
                    fixture.get("timestamp"),

                    league_id,
                    league.get("name"),
                    league.get("country"),
                    league.get("logo"),
                    league.get("flag"),
                    season_year,

                    json.dumps(item, ensure_ascii=False),
                    updated_at,
                ),
            )

            saved_count += 1

        connection.commit()

    return saved_count


def count_injuries() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM injuries")
        row = cursor.fetchone()

        return int(row["total"])


def list_injuries(
    league_id: int | None = None,
    season_year: int | None = None,
    team_id: int | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    query = """
        SELECT
            id,
            player_id,
            player_name,
            player_photo,
            injury_type,
            reason,

            team_id,
            team_name,
            team_logo,

            fixture_id,
            fixture_date,

            league_id,
            league_name,
            league_country,
            season_year,

            updated_at
        FROM injuries
        WHERE 1 = 1
    """

    params: list[Any] = []

    if league_id is not None:
        query += " AND league_id = ?"
        params.append(league_id)

    if season_year is not None:
        query += " AND season_year = ?"
        params.append(season_year)

    if team_id is not None:
        query += " AND team_id = ?"
        params.append(team_id)

    query += """
        ORDER BY fixture_date DESC, team_name ASC, player_name ASC
        LIMIT ?
    """
    params.append(limit)

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_injury_by_id(injury_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM injuries
            WHERE id = ?
            """,
            (injury_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    result = dict(row)
    result["raw"] = json.loads(result.pop("raw_json"))

    return result


def save_player_sidelined(
    api_response: dict[str, Any],
    player_id: int,
) -> int:
    response_items = api_response.get("response", [])
    updated_at = get_utc_now()
    saved_count = 0

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM sidelined_records
            WHERE entity_type = ?
            AND entity_id = ?
            """,
            ("player", player_id),
        )

        for item in response_items:
            cursor.execute(
                """
                INSERT INTO sidelined_records (
                    entity_type,
                    entity_id,
                    sidelined_type,
                    start_date,
                    end_date,
                    raw_json,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(
                    entity_type,
                    entity_id,
                    sidelined_type,
                    start_date,
                    end_date
                ) DO UPDATE SET
                    raw_json = excluded.raw_json,
                    updated_at = excluded.updated_at
                """,
                (
                    "player",
                    player_id,
                    item.get("type"),
                    item.get("start"),
                    item.get("end"),
                    json.dumps(item, ensure_ascii=False),
                    updated_at,
                ),
            )

            saved_count += 1

        connection.commit()

    return saved_count


def count_sidelined_records() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM sidelined_records")
        row = cursor.fetchone()

        return int(row["total"])


def list_player_sidelined_records(
    player_id: int,
) -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                entity_type,
                entity_id,
                sidelined_type,
                start_date,
                end_date,
                updated_at
            FROM sidelined_records
            WHERE entity_type = ?
            AND entity_id = ?
            ORDER BY start_date DESC
            """,
            ("player", player_id),
        )

        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_sidelined_record_by_id(record_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM sidelined_records
            WHERE id = ?
            """,
            (record_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    result = dict(row)
    result["raw"] = json.loads(result.pop("raw_json"))

    return result

# -------------------------------------------------------------------
# Coaches
# -------------------------------------------------------------------

def save_coaches(
    api_response: dict[str, Any],
) -> int:
    response_items = api_response.get("response", [])
    updated_at = get_utc_now()
    saved_count = 0

    with get_connection() as connection:
        cursor = connection.cursor()

        for coach in response_items:
            coach_id = coach.get("id")

            if coach_id is None:
                continue

            birth = coach.get("birth", {})
            career = coach.get("career", [])

            cursor.execute(
                """
                INSERT INTO coaches (
                    coach_id,
                    name,
                    firstname,
                    lastname,
                    age,
                    birth_date,
                    birth_place,
                    birth_country,
                    nationality,
                    height,
                    weight,
                    photo,
                    raw_json,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(coach_id) DO UPDATE SET
                    name = excluded.name,
                    firstname = excluded.firstname,
                    lastname = excluded.lastname,
                    age = excluded.age,
                    birth_date = excluded.birth_date,
                    birth_place = excluded.birth_place,
                    birth_country = excluded.birth_country,
                    nationality = excluded.nationality,
                    height = excluded.height,
                    weight = excluded.weight,
                    photo = excluded.photo,
                    raw_json = excluded.raw_json,
                    updated_at = excluded.updated_at
                """,
                (
                    coach_id,
                    coach.get("name"),
                    coach.get("firstname"),
                    coach.get("lastname"),
                    coach.get("age"),
                    birth.get("date"),
                    birth.get("place"),
                    birth.get("country"),
                    coach.get("nationality"),
                    coach.get("height"),
                    coach.get("weight"),
                    coach.get("photo"),
                    json.dumps(coach, ensure_ascii=False),
                    updated_at,
                ),
            )

            for career_item in career:
                team = career_item.get("team", {})
                team_id = team.get("id")
                start_date = career_item.get("start") or ""
                end_date = career_item.get("end") or ""

                cursor.execute(
                    """
                    INSERT INTO coach_careers (
                        coach_id,
                        team_id,
                        team_name,
                        team_logo,
                        start_date,
                        end_date,
                        raw_json,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(coach_id, team_id, start_date, end_date) DO UPDATE SET
                        team_name = excluded.team_name,
                        team_logo = excluded.team_logo,
                        raw_json = excluded.raw_json,
                        updated_at = excluded.updated_at
                    """,
                    (
                        coach_id,
                        team_id,
                        team.get("name"),
                        team.get("logo"),
                        start_date,
                        end_date,
                        json.dumps(career_item, ensure_ascii=False),
                        updated_at,
                    ),
                )

            saved_count += 1

        connection.commit()

    return saved_count


def count_coaches() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM coaches")
        row = cursor.fetchone()

        return int(row["total"])


def count_coach_careers() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM coach_careers")
        row = cursor.fetchone()

        return int(row["total"])


def list_coaches_by_team_id(
    team_id: int,
) -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                c.coach_id,
                c.name,
                c.firstname,
                c.lastname,
                c.age,
                c.nationality,
                c.photo,
                cc.team_id,
                cc.team_name,
                cc.team_logo,
                cc.start_date,
                cc.end_date,
                cc.updated_at
            FROM coach_careers cc
            JOIN coaches c ON c.coach_id = cc.coach_id
            WHERE cc.team_id = ?
            ORDER BY
                CASE WHEN cc.end_date = '' THEN 0 ELSE 1 END ASC,
                cc.start_date DESC
            """,
            (team_id,),
        )

        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def list_coach_careers_by_coach_id(
    coach_id: int,
) -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                coach_id,
                team_id,
                team_name,
                team_logo,
                start_date,
                end_date,
                updated_at
            FROM coach_careers
            WHERE coach_id = ?
            ORDER BY
                CASE WHEN end_date = '' THEN 0 ELSE 1 END ASC,
                start_date DESC
            """,
            (coach_id,),
        )

        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_coach_by_id(coach_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                coach_id,
                name,
                firstname,
                lastname,
                age,
                birth_date,
                birth_place,
                birth_country,
                nationality,
                height,
                weight,
                photo,
                raw_json,
                updated_at
            FROM coaches
            WHERE coach_id = ?
            """,
            (coach_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    result = dict(row)
    result["raw"] = json.loads(result.pop("raw_json"))

    return result