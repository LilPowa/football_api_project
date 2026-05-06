from app.services.api_football_client import ApiFootballClient


def main() -> None:
    client = ApiFootballClient()

    print("Test de connexion à API-Football...")
    status = client.get_status()

    print("\nConnexion réussie.")
    print("Informations du compte :")
    print(status)

    print("\nTest récupération des pays...")
    countries = client.get_countries()

    print(f"Nombre de résultats : {countries.get('results')}")
    print("Exemple de réponse :")

    for country in countries.get("response", [])[:5]:
        print("-", country.get("name"))


if __name__ == "__main__":
    main()