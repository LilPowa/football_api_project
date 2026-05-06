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
        
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS teams (
                team_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                code TEXT,
                country TEXT,
                founded INTEGER,
                national INTEGER NOT NULL DEFAULT 0,
                logo TEXT,
                venue_id INTEGER,
                venue_name TEXT,
                venue_address TEXT,
                venue_city TEXT,
                venue_capacity INTEGER,
                venue_surface TEXT,
                venue_image TEXT,
                raw_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS team_league_seasons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                league_id INTEGER NOT NULL,
                season_year INTEGER NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(team_id, league_id, season_year),
                FOREIGN KEY (team_id) REFERENCES teams(team_id),
                FOREIGN KEY (league_id) REFERENCES leagues(league_id)
            )
            """
        )
        
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fixtures (
                fixture_id INTEGER PRIMARY KEY,
                league_id INTEGER,
                season_year INTEGER,
                round TEXT,
                referee TEXT,
                timezone TEXT,
                fixture_date TEXT,
                fixture_timestamp INTEGER,
                venue_id INTEGER,
                venue_name TEXT,
                venue_city TEXT,
                status_long TEXT,
                status_short TEXT,
                elapsed INTEGER,
                home_team_id INTEGER,
                home_team_name TEXT,
                home_team_logo TEXT,
                home_team_winner INTEGER,
                away_team_id INTEGER,
                away_team_name TEXT,
                away_team_logo TEXT,
                away_team_winner INTEGER,
                home_goals INTEGER,
                away_goals INTEGER,
                halftime_home INTEGER,
                halftime_away INTEGER,
                fulltime_home INTEGER,
                fulltime_away INTEGER,
                extratime_home INTEGER,
                extratime_away INTEGER,
                penalty_home INTEGER,
                penalty_away INTEGER,
                raw_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (league_id) REFERENCES leagues(league_id),
                FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
                FOREIGN KEY (away_team_id) REFERENCES teams(team_id)
            )
            """
        )
        
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS standings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                league_id INTEGER NOT NULL,
                season_year INTEGER NOT NULL,
                group_name TEXT,
                position INTEGER,
                team_id INTEGER,
                team_name TEXT,
                team_logo TEXT,
                points INTEGER,
                goals_diff INTEGER,
                form TEXT,
                status TEXT,
                description TEXT,
                all_played INTEGER,
                all_win INTEGER,
                all_draw INTEGER,
                all_lose INTEGER,
                all_goals_for INTEGER,
                all_goals_against INTEGER,
                home_played INTEGER,
                home_win INTEGER,
                home_draw INTEGER,
                home_lose INTEGER,
                home_goals_for INTEGER,
                home_goals_against INTEGER,
                away_played INTEGER,
                away_win INTEGER,
                away_draw INTEGER,
                away_lose INTEGER,
                away_goals_for INTEGER,
                away_goals_against INTEGER,
                raw_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(league_id, season_year, group_name, team_id),
                FOREIGN KEY (league_id) REFERENCES leagues(league_id),
                FOREIGN KEY (team_id) REFERENCES teams(team_id)
            )
            """
        )
        
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fixture_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fixture_id INTEGER NOT NULL,
                team_id INTEGER NOT NULL,
                team_name TEXT,
                team_logo TEXT,
                stat_type TEXT NOT NULL,
                stat_value TEXT,
                raw_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(fixture_id, team_id, stat_type),
                FOREIGN KEY (fixture_id) REFERENCES fixtures(fixture_id),
                FOREIGN KEY (team_id) REFERENCES teams(team_id)
            )
            """
        )
        
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fixture_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fixture_id INTEGER NOT NULL,
                event_index INTEGER NOT NULL,
                elapsed INTEGER,
                extra INTEGER,
                team_id INTEGER,
                team_name TEXT,
                team_logo TEXT,
                player_id INTEGER,
                player_name TEXT,
                assist_id INTEGER,
                assist_name TEXT,
                event_type TEXT,
                event_detail TEXT,
                comments TEXT,
                raw_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(fixture_id, event_index),
                FOREIGN KEY (fixture_id) REFERENCES fixtures(fixture_id),
                FOREIGN KEY (team_id) REFERENCES teams(team_id),
                FOREIGN KEY (player_id) REFERENCES teams(team_id)
            )
            """
        )
        
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fixture_lineups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fixture_id INTEGER NOT NULL,
                team_id INTEGER NOT NULL,
                team_name TEXT,
                team_logo TEXT,
                coach_id INTEGER,
                coach_name TEXT,
                coach_photo TEXT,
                formation TEXT,
                team_colors_json TEXT,
                raw_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(fixture_id, team_id),
                FOREIGN KEY (fixture_id) REFERENCES fixtures(fixture_id),
                FOREIGN KEY (team_id) REFERENCES teams(team_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fixture_lineup_players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fixture_id INTEGER NOT NULL,
                team_id INTEGER NOT NULL,
                lineup_type TEXT NOT NULL,
                player_index INTEGER NOT NULL,
                player_id INTEGER,
                player_name TEXT,
                player_number INTEGER,
                player_position TEXT,
                player_grid TEXT,
                raw_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(fixture_id, team_id, lineup_type, player_index),
                FOREIGN KEY (fixture_id) REFERENCES fixtures(fixture_id),
                FOREIGN KEY (team_id) REFERENCES teams(team_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fixture_player_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fixture_id INTEGER NOT NULL,
                team_id INTEGER NOT NULL,
                team_name TEXT,
                team_logo TEXT,
                player_id INTEGER,
                player_name TEXT,
                player_photo TEXT,
                stat_index INTEGER NOT NULL,

                games_minutes INTEGER,
                games_number INTEGER,
                games_position TEXT,
                games_rating TEXT,
                games_captain INTEGER,
                games_substitute INTEGER,

                offsides INTEGER,

                shots_total INTEGER,
                shots_on INTEGER,

                goals_total INTEGER,
                goals_conceded INTEGER,
                goals_assists INTEGER,
                goals_saves INTEGER,

                passes_total INTEGER,
                passes_key INTEGER,
                passes_accuracy TEXT,

                tackles_total INTEGER,
                tackles_blocks INTEGER,
                tackles_interceptions INTEGER,

                duels_total INTEGER,
                duels_won INTEGER,

                dribbles_attempts INTEGER,
                dribbles_success INTEGER,
                dribbles_past INTEGER,

                fouls_drawn INTEGER,
                fouls_committed INTEGER,

                cards_yellow INTEGER,
                cards_red INTEGER,

                penalty_won INTEGER,
                penalty_commited INTEGER,
                penalty_scored INTEGER,
                penalty_missed INTEGER,
                penalty_saved INTEGER,

                raw_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                UNIQUE(fixture_id, team_id, player_id, stat_index),
                FOREIGN KEY (fixture_id) REFERENCES fixtures(fixture_id),
                FOREIGN KEY (team_id) REFERENCES teams(team_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS head_to_head_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pair_key TEXT NOT NULL,
                team_a_id INTEGER NOT NULL,
                team_b_id INTEGER NOT NULL,
                fixture_id INTEGER NOT NULL,

                league_id INTEGER,
                league_name TEXT,
                league_country TEXT,
                season_year INTEGER,
                round TEXT,

                fixture_date TEXT,
                fixture_timestamp INTEGER,
                status_long TEXT,
                status_short TEXT,

                venue_name TEXT,
                venue_city TEXT,

                home_team_id INTEGER,
                home_team_name TEXT,
                home_team_logo TEXT,
                away_team_id INTEGER,
                away_team_name TEXT,
                away_team_logo TEXT,

                home_goals INTEGER,
                away_goals INTEGER,

                winner_team_id INTEGER,
                winner_team_name TEXT,

                raw_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                UNIQUE(pair_key, fixture_id),
                FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
                FOREIGN KEY (away_team_id) REFERENCES teams(team_id)
            )
            """
        )
                
        connection.commit()