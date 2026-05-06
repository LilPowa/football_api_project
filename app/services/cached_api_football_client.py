from typing import Any

from app.config import settings
from app.repositories.api_cache_repository import (
    get_cached_response,
    save_cached_response,
)
from app.services.api_football_client import ApiFootballClient


class CachedApiFootballClient:
    def __init__(self) -> None:
        self.api_client = ApiFootballClient()
        self.last_cache_hit = False

    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        cache_ttl_seconds: int | None = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        ttl_seconds = cache_ttl_seconds or settings.DEFAULT_CACHE_SECONDS

        self.last_cache_hit = False

        if not force_refresh and ttl_seconds > 0:
            cached_response = get_cached_response(endpoint, params)

            if cached_response is not None:
                self.last_cache_hit = True
                return cached_response

        api_response = self.api_client.get(endpoint, params=params)

        if ttl_seconds > 0:
            save_cached_response(
                endpoint=endpoint,
                params=params,
                response=api_response,
                ttl_seconds=ttl_seconds,
            )

        return api_response

    def get_countries(self, force_refresh: bool = False) -> dict[str, Any]:
        return self.get(
            endpoint="countries",
            cache_ttl_seconds=7 * 24 * 60 * 60,
            force_refresh=force_refresh,
        )

    def get_leagues(
        self,
        country: str | None = None,
        season: int | None = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}

        if country:
            params["country"] = country

        if season:
            params["season"] = season

        return self.get(
            endpoint="leagues",
            params=params,
            cache_ttl_seconds=24 * 60 * 60,
            force_refresh=force_refresh,
        )
        
    def get_teams(
        self,
        league_id: int,
        season: int,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        params = {
            "league": league_id,
            "season": season,
        }

        return self.get(
            endpoint="teams",
            params=params,
            cache_ttl_seconds=7 * 24 * 60 * 60,
            force_refresh=force_refresh,
        )
    
    def get_fixtures(
        self,
        league_id: int,
        season: int,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        params = {
            "league": league_id,
            "season": season,
        }

        return self.get(
            endpoint="fixtures",
            params=params,
            cache_ttl_seconds=6 * 60 * 60,
            force_refresh=force_refresh,
        )
    
    def get_standings(
        self,
        league_id: int,
        season: int,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        params = {
            "league": league_id,
            "season": season,
        }

        return self.get(
            endpoint="standings",
            params=params,
            cache_ttl_seconds=60 * 60,
            force_refresh=force_refresh,
        )