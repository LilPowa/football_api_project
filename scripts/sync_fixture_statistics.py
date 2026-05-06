from app.database import init_db
from app.repositories.football_repository import (
    get_fixture_by_id,
    get_fixture_statistics_as_comparison,
)
from app.services.sync_service import sync_fixture_statistics


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
            "Les statistiques risquent d'être vides."
        )

    try:
        result = sync_fixture_statistics(
            fixture_id=fixture_id,
            force_refresh=False,
        )
    except RuntimeError as error:
        print("\nErreur pendant la synchronisation des statistiques.")
        print(error)
        return

    print(f"\nSource utilisée : {result['source']}")
    print(f"{result['saved_count']} statistique(s) récupérée(s).")
    print(
        f"{result['total_fixture_statistics']} statistique(s) "
        "présente(s) en base locale."
    )

    comparison = get_fixture_statistics_as_comparison(fixture_id)

    if not comparison:
        print(
            "\nAucune statistique trouvée. "
            "Essaie avec un match terminé ou en cours."
        )
        return

    print("\nStatistiques du match :")

    for row in comparison:
        print(row)


if __name__ == "__main__":
    main()