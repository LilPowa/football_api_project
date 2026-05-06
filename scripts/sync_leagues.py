from app.database import init_db
from app.repositories.football_repository import (
    count_league_seasons,
    count_leagues,
    list_current_league_seasons,
    list_leagues,
    save_leagues,
)
from app.services.cached_api_football_client import CachedApiFootballClient


def main() -> None:
    print("Initialisation de la base locale...")
    init_db()

    print("Récupération des ligues depuis API-Football...")
    client = CachedApiFootballClient()

    api_response = client.get_leagues()

    source = "cache local" if client.last_cache_hit else "API-Football"
    print(f"Source utilisée : {source}")

    saved_count = save_leagues(api_response)
    total_leagues = count_leagues()
    total_seasons = count_league_seasons()

    print(f"{saved_count} ligues récupérées depuis la source.")
    print(f"{total_leagues} ligues présentes en base locale.")
    print(f"{total_seasons} saisons de ligues présentes en base locale.")

    print("\nExemples de ligues en base locale :")
    for league in list_leagues(limit=15):
        print(
            f"- [{league['league_id']}] {league['name']} "
            f"({league['country_name']}) - {league['type']}"
        )

    print("\nExemples de saisons courantes :")
    for season in list_current_league_seasons(limit=15):
        print(
            f"- [{season['league_id']}] {season['name']} "
            f"({season['country_name']}) - saison {season['season_year']}"
        )


if __name__ == "__main__":
    main()