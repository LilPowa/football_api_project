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
    
    def get_fixture_statistics(
        self,
        fixture_id: int,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        params = {
            "fixture": fixture_id,
        }

        return self.get(
            endpoint="fixtures/statistics",
            params=params,
            cache_ttl_seconds=60 * 60,
            force_refresh=force_refresh,
        )
        
    def get_fixture_events(
        self,
        fixture_id: int,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        params = {
            "fixture": fixture_id,
        }

        return self.get(
            endpoint="fixtures/events",
            params=params,
            cache_ttl_seconds=60 * 60,
            force_refresh=force_refresh,
        )
    
    def get_fixture_lineups(
        self,
        fixture_id: int,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        params = {
            "fixture": fixture_id,
        }

        return self.get(
            endpoint="fixtures/lineups",
            params=params,
            cache_ttl_seconds=60 * 60,
            force_refresh=force_refresh,
        )
    
    def get_fixture_players(
        self,
        fixture_id: int,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        params = {
            "fixture": fixture_id,
        }

        return self.get(
            endpoint="fixtures/players",
            params=params,
            cache_ttl_seconds=60 * 60,
            force_refresh=force_refresh,
        )
    
    def get_head_to_head(
        self,
        team_a_id: int,
        team_b_id: int,
        last: int | None = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "h2h": f"{team_a_id}-{team_b_id}",
        }

        if settings.API_FOOTBALL_ENABLE_H2H_LAST_PARAMETER and last is not None:
            params["last"] = last

        return self.get(
            endpoint="fixtures/headtohead",
            params=params,
            cache_ttl_seconds=24 * 60 * 60,
            force_refresh=force_refresh,
        )
    
    def get_player_squad(
        self,
        team_id: int,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        params = {
            "team": team_id,
        }

        return self.get(
            endpoint="players/squads",
            params=params,
            cache_ttl_seconds=7 * 24 * 60 * 60,
            force_refresh=force_refresh,
        )
    
    def get_players_statistics(
        self,
        league_id: int,
        season: int,
        team_id: int | None = None,
        page: int | None = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "league": league_id,
            "season": season,
        }

        if team_id is not None:
            params["team"] = team_id

        if settings.API_FOOTBALL_ENABLE_PAGINATION_PARAMETER and page is not None:
            params["page"] = page

        return self.get(
            endpoint="players",
            params=params,
            cache_ttl_seconds=24 * 60 * 60,
            force_refresh=force_refresh,
        )
        
    def get_top_scorers(
        self,
        league_id: int,
        season: int,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        return self.get(
            endpoint="players/topscorers",
            params={
                "league": league_id,
                "season": season,
            },
            cache_ttl_seconds=24 * 60 * 60,
            force_refresh=force_refresh,
        )

    def get_top_assists(
        self,
        league_id: int,
        season: int,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        return self.get(
            endpoint="players/topassists",
            params={
                "league": league_id,
                "season": season,
            },
            cache_ttl_seconds=24 * 60 * 60,
            force_refresh=force_refresh,
        )

    def get_top_yellow_cards(
        self,
        league_id: int,
        season: int,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        return self.get(
            endpoint="players/topyellowcards",
            params={
                "league": league_id,
                "season": season,
            },
            cache_ttl_seconds=24 * 60 * 60,
            force_refresh=force_refresh,
        )

    def get_top_red_cards(
        self,
        league_id: int,
        season: int,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        return self.get(
            endpoint="players/topredcards",
            params={
                "league": league_id,
                "season": season,
            },
            cache_ttl_seconds=24 * 60 * 60,
            force_refresh=force_refresh,
        )
    
    def get_injuries(
        self,
        league_id: int | None = None,
        season: int | None = None,
        team_id: int | None = None,
        player_id: int | None = None,
        fixture_id: int | None = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}

        if league_id is not None:
            params["league"] = league_id

        if season is not None:
            params["season"] = season

        if team_id is not None:
            params["team"] = team_id

        if player_id is not None:
            params["player"] = player_id

        if fixture_id is not None:
            params["fixture"] = fixture_id

        return self.get(
            endpoint="injuries",
            params=params,
            cache_ttl_seconds=6 * 60 * 60,
            force_refresh=force_refresh,
        )

    def get_player_sidelined(
        self,
        player_id: int,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        params = {
            "player": player_id,
        }

        return self.get(
            endpoint="sidelined",
            params=params,
            cache_ttl_seconds=7 * 24 * 60 * 60,
            force_refresh=force_refresh,
        )
    
    def get_coaches(
        self,
        team_id: int | None = None,
        coach_id: int | None = None,
        search: str | None = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}

        if team_id is not None:
            params["team"] = team_id

        if coach_id is not None:
            params["id"] = coach_id

        if search:
            params["search"] = search

        return self.get(
            endpoint="coachs",
            params=params,
            cache_ttl_seconds=7 * 24 * 60 * 60,
            force_refresh=force_refresh,
        )