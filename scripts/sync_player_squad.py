from app.database import init_db
from app.repositories.football_repository import (
    get_team_by_id,
    list_squad_players_by_team_id,
)
from app.services.sync_service import sync_player_squad


def main() -> None:
    init_db()

    team_id_input = input("ID de l'équipe, ex: 85 pour PSG : ").strip()

    if not team_id_input.isdigit():
        print("Erreur : l'ID de l'équipe doit être un nombre.")
        return

    team_id = int(team_id_input)
    team = get_team_by_id(team_id)

    if team is None:
        print(
            "Équipe introuvable en base locale. "
            "Synchronise d'abord les équipes d'une ligue/saison."
        )
        return

    print(f"Équipe sélectionnée : {team['name']}")

    try:
        result = sync_player_squad(
            team_id=team_id,
            force_refresh=False,
        )
    except RuntimeError as error:
        print("\nErreur pendant la synchronisation de l'effectif.")
        print(error)
        return

    print(f"\nSource utilisée : {result['source']}")
    print(f"{result['saved_count']} joueur(s) récupéré(s).")
    print(f"{result['total_players']} joueur(s) présent(s) dans players.")
    print(
        f"{result['total_squad_players']} relation(s) équipe/joueur "
        "présente(s) en base locale."
    )

    players = list_squad_players_by_team_id(team_id)

    if not players:
        print("\nAucun joueur trouvé pour cette équipe.")
        return

    print("\nEffectif :")

    for player in players:
        print(
            f"- #{player['player_number'] or 'N/A'} "
            f"{player['player_name']} "
            f"| Poste : {player['player_position'] or 'N/A'} "
            f"| Âge : {player['player_age'] or 'N/A'}"
        )


if __name__ == "__main__":
    main()