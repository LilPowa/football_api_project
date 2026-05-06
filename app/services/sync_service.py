from typing import Any

from app.database import init_db
from app.repositories.football_repository import (
    count_countries,
    count_fixture_events,
    count_fixture_lineup_players,
    count_fixture_lineups,
    count_fixture_player_statistics,
    count_fixture_statistics,
    count_fixtures,
    count_head_to_head_matches,
    count_league_seasons,
    count_leagues,
    count_standings,
    count_team_league_seasons,
    count_teams,
    save_countries,
    save_fixture_events,
    save_fixture_lineups,
    save_fixture_player_statistics,
    save_fixture_statistics,
    save_fixtures,
    save_head_to_head_matches,
    save_leagues,
    save_standings,
    save_teams,
    count_players,
    count_team_squad_players,
    save_player_squad,
    count_player_season_statistics,
    save_player_season_statistics,
)
from app.services.cached_api_football_client import CachedApiFootballClient


def sync_countries(force_refresh: bool = False) -> dict[str, Any]:
    init_db()

    client = CachedApiFootballClient()
    api_response = client.get_countries(force_refresh=force_refresh)

    saved_count = save_countries(api_response)
    total_count = count_countries()

    return {
        "source": "cache local" if client.last_cache_hit else "API-Football",
        "saved_count": saved_count,
        "total_count": total_count,
    }


def sync_leagues(force_refresh: bool = False) -> dict[str, Any]:
    init_db()

    client = CachedApiFootballClient()
    api_response = client.get_leagues(force_refresh=force_refresh)

    saved_count = save_leagues(api_response)
    total_leagues = count_leagues()
    total_seasons = count_league_seasons()

    return {
        "source": "cache local" if client.last_cache_hit else "API-Football",
        "saved_count": saved_count,
        "total_leagues": total_leagues,
        "total_seasons": total_seasons,
    }
    
def sync_teams(
    league_id: int,
    season_year: int,
    force_refresh: bool = False,
) -> dict[str, Any]:
    init_db()

    client = CachedApiFootballClient()
    api_response = client.get_teams(
        league_id=league_id,
        season=season_year,
        force_refresh=force_refresh,
    )

    saved_count = save_teams(
        api_response=api_response,
        league_id=league_id,
        season_year=season_year,
    )

    total_teams = count_teams()
    total_team_links = count_team_league_seasons()

    return {
        "source": "cache local" if client.last_cache_hit else "API-Football",
        "saved_count": saved_count,
        "total_teams": total_teams,
        "total_team_links": total_team_links,
    }

def sync_fixtures(
    league_id: int,
    season_year: int,
    force_refresh: bool = False,
) -> dict[str, Any]:
    init_db()

    client = CachedApiFootballClient()
    api_response = client.get_fixtures(
        league_id=league_id,
        season=season_year,
        force_refresh=force_refresh,
    )

    saved_count = save_fixtures(
        api_response=api_response,
        league_id=league_id,
        season_year=season_year,
    )

    total_fixtures = count_fixtures()

    return {
        "source": "cache local" if client.last_cache_hit else "API-Football",
        "saved_count": saved_count,
        "total_fixtures": total_fixtures,
    }
    
def sync_standings(
    league_id: int,
    season_year: int,
    force_refresh: bool = False,
) -> dict[str, Any]:
    init_db()

    client = CachedApiFootballClient()
    api_response = client.get_standings(
        league_id=league_id,
        season=season_year,
        force_refresh=force_refresh,
    )

    saved_count = save_standings(
        api_response=api_response,
        league_id=league_id,
        season_year=season_year,
    )

    total_standings = count_standings()

    return {
        "source": "cache local" if client.last_cache_hit else "API-Football",
        "saved_count": saved_count,
        "total_standings": total_standings,
    }

def sync_fixture_statistics(
    fixture_id: int,
    force_refresh: bool = False,
) -> dict[str, Any]:
    init_db()

    client = CachedApiFootballClient()
    api_response = client.get_fixture_statistics(
        fixture_id=fixture_id,
        force_refresh=force_refresh,
    )

    saved_count = save_fixture_statistics(
        api_response=api_response,
        fixture_id=fixture_id,
    )

    total_fixture_statistics = count_fixture_statistics()

    return {
        "source": "cache local" if client.last_cache_hit else "API-Football",
        "saved_count": saved_count,
        "total_fixture_statistics": total_fixture_statistics,
    }

def sync_fixture_events(
    fixture_id: int,
    force_refresh: bool = False,
) -> dict[str, Any]:
    init_db()

    client = CachedApiFootballClient()
    api_response = client.get_fixture_events(
        fixture_id=fixture_id,
        force_refresh=force_refresh,
    )

    saved_count = save_fixture_events(
        api_response=api_response,
        fixture_id=fixture_id,
    )

    total_fixture_events = count_fixture_events()

    return {
        "source": "cache local" if client.last_cache_hit else "API-Football",
        "saved_count": saved_count,
        "total_fixture_events": total_fixture_events,
    }

def sync_fixture_lineups(
    fixture_id: int,
    force_refresh: bool = False,
) -> dict[str, Any]:
    init_db()

    client = CachedApiFootballClient()
    api_response = client.get_fixture_lineups(
        fixture_id=fixture_id,
        force_refresh=force_refresh,
    )

    saved_count = save_fixture_lineups(
        api_response=api_response,
        fixture_id=fixture_id,
    )

    total_lineups = count_fixture_lineups()
    total_lineup_players = count_fixture_lineup_players()

    return {
        "source": "cache local" if client.last_cache_hit else "API-Football",
        "saved_count": saved_count,
        "total_lineups": total_lineups,
        "total_lineup_players": total_lineup_players,
    }

def sync_fixture_players(
    fixture_id: int,
    force_refresh: bool = False,
) -> dict[str, Any]:
    init_db()

    client = CachedApiFootballClient()
    api_response = client.get_fixture_players(
        fixture_id=fixture_id,
        force_refresh=force_refresh,
    )

    saved_count = save_fixture_player_statistics(
        api_response=api_response,
        fixture_id=fixture_id,
    )

    total_fixture_player_statistics = count_fixture_player_statistics()

    return {
        "source": "cache local" if client.last_cache_hit else "API-Football",
        "saved_count": saved_count,
        "total_fixture_player_statistics": total_fixture_player_statistics,
    }

def sync_head_to_head(
    team_a_id: int,
    team_b_id: int,
    last: int | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    init_db()

    client = CachedApiFootballClient()
    api_response = client.get_head_to_head(
        team_a_id=team_a_id,
        team_b_id=team_b_id,
        last=last,
        force_refresh=force_refresh,
    )

    saved_count = save_head_to_head_matches(
        api_response=api_response,
        team_a_id=team_a_id,
        team_b_id=team_b_id,
    )

    total_head_to_head_matches = count_head_to_head_matches()

    return {
        "source": "cache local" if client.last_cache_hit else "API-Football",
        "saved_count": saved_count,
        "total_head_to_head_matches": total_head_to_head_matches,
    }

def sync_player_squad(
    team_id: int,
    force_refresh: bool = False,
) -> dict[str, Any]:
    init_db()

    client = CachedApiFootballClient()
    api_response = client.get_player_squad(
        team_id=team_id,
        force_refresh=force_refresh,
    )

    saved_count = save_player_squad(
        api_response=api_response,
        team_id=team_id,
    )

    total_players = count_players()
    total_squad_players = count_team_squad_players()

    return {
        "source": "cache local" if client.last_cache_hit else "API-Football",
        "saved_count": saved_count,
        "total_players": total_players,
        "total_squad_players": total_squad_players,
    }

def sync_players_statistics(
    league_id: int,
    season_year: int,
    team_id: int | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    init_db()

    client = CachedApiFootballClient()
    api_response = client.get_players_statistics(
        league_id=league_id,
        season=season_year,
        team_id=team_id,
        page=None,
        force_refresh=force_refresh,
    )

    saved_count = save_player_season_statistics(
        api_response=api_response,
        league_id=league_id,
        season_year=season_year,
    )

    total_player_season_statistics = count_player_season_statistics()

    return {
        "source": "cache local" if client.last_cache_hit else "API-Football",
        "saved_count": saved_count,
        "total_player_season_statistics": total_player_season_statistics,
    }