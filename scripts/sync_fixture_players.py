from app.database import init_db
from app.repositories.football_repository import (
    get_fixture_by_id,
    list_fixture_player_statistics_by_fixture_id,
)
from app.services.sync_service import sync_fixture_players


def main() -> None:
    init_db()

    fixture_id_input = input("ID du match / fixture_id : ").strip()

    if not fixture_id_input.isdigit():
        print("Erreur : le fixture_id doit être un nombre.")
        return

    fixture_id = int(fixture_id_input)

    fixture = get_fixture_by_id(fixture_id)

    if fixture is None:
        print(
            "Match introuvable en base locale. "
            "Synchronise d'abord les fixtures d'une ligue/saison."
        )
        return

    print(
        f"Match sélectionné : {fixture['home_team_name']} "
        f"vs {fixture['away_team_name']}"
    )
    print(f"Statut : {fixture['status_short']} - {fixture['status_long']}")

    if fixture["status_short"] == "NS":
        print(
            "\nCe match n'a pas encore commencé. "
            "Les statistiques joueurs risquent d'être vides."
        )

    try:
        result = sync_fixture_players(
            fixture_id=fixture_id,
            force_refresh=False,
        )
    except RuntimeError as error:
        print("\nErreur pendant la synchronisation des statistiques joueurs.")
        print(error)
        return

    print(f"\nSource utilisée : {result['source']}")
    print(f"{result['saved_count']} ligne(s) de stats joueur récupérée(s).")
    print(
        f"{result['total_fixture_player_statistics']} ligne(s) de stats joueur "
        "présente(s) en base locale."
    )

    player_stats = list_fixture_player_statistics_by_fixture_id(fixture_id)

    if not player_stats:
        print(
            "\nAucune statistique joueur trouvée. "
            "Essaie avec un match terminé ou avec une compétition mieux couverte."
        )
        return

    print("\nExemples de statistiques joueurs :")

    for stat in player_stats[:20]:
        print(
            f"- {stat['team_name']} | #{stat['games_number'] or 'N/A'} "
            f"{stat['player_name']} | Poste: {stat['games_position'] or 'N/A'} "
            f"| Note: {stat['games_rating'] or 'N/A'} "
            f"| Min: {stat['games_minutes'] or 'N/A'} "
            f"| Buts: {stat['goals_total'] or 0} "
            f"| Passes décisives: {stat['goals_assists'] or 0}"
        )


if __name__ == "__main__":
    main()