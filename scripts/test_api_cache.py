from app.database import init_db
from app.repositories.api_cache_repository import count_cache_entries
from app.services.cached_api_football_client import CachedApiFootballClient


def main() -> None:
    init_db()

    client = CachedApiFootballClient()

    print("Premier appel vers /countries...")
    response_1 = client.get_countries()
    source_1 = "cache local" if client.last_cache_hit else "API-Football"

    print(f"Source premier appel : {source_1}")
    print(f"Nombre de pays reçus : {response_1.get('results')}")

    print("\nDeuxième appel vers /countries...")
    response_2 = client.get_countries()
    source_2 = "cache local" if client.last_cache_hit else "API-Football"

    print(f"Source deuxième appel : {source_2}")
    print(f"Nombre de pays reçus : {response_2.get('results')}")

    print(f"\nEntrées présentes dans api_cache : {count_cache_entries()}")


if __name__ == "__main__":
    main()