from app.database import init_db
from app.repositories.football_repository import (
    count_countries,
    list_countries,
    save_countries,
)
from app.services.api_football_client import ApiFootballClient


def main() -> None:
    print("Initialisation de la base locale...")
    init_db()

    print("Récupération des pays depuis API-Football...")
    client = ApiFootballClient()
    api_response = client.get_countries()

    saved_count = save_countries(api_response)
    total_count = count_countries()

    print(f"{saved_count} pays récupérés depuis l'API.")
    print(f"{total_count} pays présents en base locale.")

    print("\nExemples en base locale :")
    for country in list_countries(limit=10):
        print(f"- {country['name']} ({country['code']})")


if __name__ == "__main__":
    main()