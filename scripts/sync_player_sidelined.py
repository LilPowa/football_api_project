from app.database import init_db
from app.repositories.football_repository import (
    get_player_by_id,
    list_player_sidelined_records,
)
from app.services.sync_service import sync_player_sidelined


def main() -> None:
    init_db()

    player_input = input("ID joueur : ").strip()

    if not player_input.isdigit():
        print("Erreur : l'ID joueur doit être un nombre.")
        return

    player_id = int(player_input)
    player = get_player_by_id(player_id)

    if player:
        print(f"Joueur sélectionné : {player['name']}")
    else:
        print("Joueur non trouvé dans la table players, mais on tente quand même l'appel API.")

    try:
        result = sync_player_sidelined(
            player_id=player_id,
            force_refresh=False,
        )
    except RuntimeError as error:
        print("\nErreur pendant la synchronisation des indisponibilités.")
        print(error)
        return

    print(f"\nSource utilisée : {result['source']}")
    print(f"{result['saved_count']} indisponibilité(s) récupérée(s).")
    print(
        f"{result['total_sidelined_records']} indisponibilité(s) "
        "présente(s) en base locale."
    )

    records = list_player_sidelined_records(player_id)

    if not records:
        print("\nAucune indisponibilité trouvée.")
        return

    print("\nIndisponibilités :")

    for record in records:
        print(
            f"- {record['sidelined_type'] or 'N/A'} "
            f"| Début: {record['start_date'] or 'N/A'} "
            f"| Fin: {record['end_date'] or 'N/A'}"
        )


if __name__ == "__main__":
    main()