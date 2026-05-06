from app.database import init_db
from app.repositories.football_repository import (
    get_fixture_by_id,
    list_fixture_lineup_players,
    list_fixture_lineups_by_fixture_id,
)
from app.services.sync_service import sync_fixture_lineups


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
            "Les compositions peuvent être indisponibles."
        )

    try:
        result = sync_fixture_lineups(
            fixture_id=fixture_id,
            force_refresh=False,
        )
    except RuntimeError as error:
        print("\nErreur pendant la synchronisation des compositions.")
        print(error)
        return

    print(f"\nSource utilisée : {result['source']}")
    print(f"{result['saved_count']} joueur(s) de composition récupéré(s).")
    print(f"{result['total_lineups']} composition(s) présente(s) en base locale.")
    print(f"{result['total_lineup_players']} joueur(s) de lineup en base locale.")

    lineups = list_fixture_lineups_by_fixture_id(fixture_id)

    if not lineups:
        print(
            "\nAucune composition trouvée. "
            "Essaie avec un match terminé ou proche du coup d'envoi."
        )
        return

    for lineup in lineups:
        print("\n" + "-" * 70)
        print(f"Équipe : {lineup['team_name']}")
        print(f"Formation : {lineup['formation'] or 'N/A'}")
        print(f"Coach : {lineup['coach_name'] or 'N/A'}")

        starters = list_fixture_lineup_players(
            fixture_id=fixture_id,
            team_id=lineup["team_id"],
            lineup_type="startXI",
        )

        substitutes = list_fixture_lineup_players(
            fixture_id=fixture_id,
            team_id=lineup["team_id"],
            lineup_type="substitute",
        )

        print("\nTitulaires :")
        for player in starters:
            print(
                f"- #{player['player_number'] or 'N/A'} "
                f"{player['player_name']} "
                f"({player['player_position'] or 'N/A'}) "
                f"grid={player['player_grid'] or 'N/A'}"
            )

        print("\nRemplaçants :")
        for player in substitutes:
            print(
                f"- #{player['player_number'] or 'N/A'} "
                f"{player['player_name']} "
                f"({player['player_position'] or 'N/A'})"
            )


if __name__ == "__main__":
    main()