from typing import Any

from app.database import init_db
from app.repositories.football_repository import (
    count_countries,
    count_league_seasons,
    count_leagues,
    save_countries,
    save_leagues,
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