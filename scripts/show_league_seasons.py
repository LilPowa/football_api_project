import json

from app.database import init_db
from app.repositories.football_repository import list_league_seasons_by_league_id


def main() -> None:
    init_db()

    league_id_input = input("ID de la ligue à consulter, ex: 61 pour Ligue 1 : ").strip()

    if not league_id_input.isdigit():
        print("Erreur : l'ID de ligue doit être un nombre.")
        return

    league_id = int(league_id_input)
    seasons = list_league_seasons_by_league_id(league_id)

    if not seasons:
        print("Aucune saison trouvée pour cette ligue.")
        print("Pense à lancer d'abord : python -m scripts.sync_leagues")
        return

    print(f"\nSaisons trouvées pour la ligue {league_id} :")

    for season in seasons:
        print("\n" + "-" * 60)
        print(f"Saison : {season['season_year']}")
        print(f"Début : {season['start_date']}")
        print(f"Fin : {season['end_date']}")
        print(f"Saison courante : {'Oui' if season['current'] else 'Non'}")
        print("Coverage :")
        print(json.dumps(season["coverage"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()