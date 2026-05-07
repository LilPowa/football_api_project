from app.database import init_db
from app.repositories.football_repository import list_top_player_statistics
from app.services.sync_service import sync_top_player_statistics


CATEGORIES = {
    "1": "top_scorers",
    "2": "top_assists",
    "3": "top_yellow_cards",
    "4": "top_red_cards",
}


def main() -> None:
    init_db()

    league_input = input("ID de la ligue, ex: 61 pour Ligue 1 : ").strip()
    season_input = input("Saison, ex: 2023 : ").strip()

    print("\nCatégories disponibles :")
    print("1 - Meilleurs buteurs")
    print("2 - Meilleurs passeurs")
    print("3 - Cartons jaunes")
    print("4 - Cartons rouges")

    category_input = input("Choix catégorie : ").strip()

    if not league_input.isdigit():
        print("Erreur : l'ID de ligue doit être un nombre.")
        return

    if not season_input.isdigit():
        print("Erreur : la saison doit être un nombre.")
        return

    if category_input not in CATEGORIES:
        print("Erreur : catégorie inconnue.")
        return

    league_id = int(league_input)
    season_year = int(season_input)
    category = CATEGORIES[category_input]

    print(
        f"Synchronisation {category} pour league_id={league_id}, "
        f"season={season_year}..."
    )

    try:
        result = sync_top_player_statistics(
            category=category,
            league_id=league_id,
            season_year=season_year,
            force_refresh=False,
        )
    except RuntimeError as error:
        print("\nErreur pendant la synchronisation du top joueurs.")
        print(error)
        return

    print(f"\nSource utilisée : {result['source']}")
    print(f"{result['saved_count']} joueur(s) récupéré(s).")
    print(
        f"{result['total_top_player_statistics']} ligne(s) top joueurs "
        "présente(s) en base locale."
    )

    players = list_top_player_statistics(
        category=category,
        league_id=league_id,
        season_year=season_year,
        limit=20,
    )

    if not players:
        print("\nAucun joueur trouvé.")
        return

    print("\nRésultats :")

    for index, player in enumerate(players, start=1):
        print(
            f"{index}. {player['player_name']} | {player['team_name']} "
            f"| Buts: {player['goals_total'] or 0} "
            f"| Passes: {player['goals_assists'] or 0} "
            f"| Jaunes: {player['cards_yellow'] or 0} "
            f"| Rouges: {player['cards_red'] or 0}"
        )


if __name__ == "__main__":
    main()