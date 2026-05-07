from app.database import init_db
from app.repositories.football_repository import (
    get_team_by_id,
    list_coaches_by_team_id,
)
from app.services.sync_service import sync_coaches


def main() -> None:
    init_db()

    team_input = input("ID équipe, ex: 85 pour PSG : ").strip()

    if not team_input.isdigit():
        print("Erreur : l'ID équipe doit être un nombre.")
        return

    team_id = int(team_input)
    team = get_team_by_id(team_id)

    if team:
        print(f"Équipe sélectionnée : {team['name']}")
    else:
        print("Équipe non trouvée en base, mais on tente quand même l'appel API.")

    try:
        result = sync_coaches(
            team_id=team_id,
            force_refresh=False,
        )
    except RuntimeError as error:
        print("\nErreur pendant la synchronisation des coachs.")
        print(error)
        return

    print(f"\nSource utilisée : {result['source']}")
    print(f"{result['saved_count']} coach(s) récupéré(s).")
    print(f"{result['total_coaches']} coach(s) présent(s) en base locale.")
    print(f"{result['total_coach_careers']} carrière(s) coach présentes en base locale.")

    coaches = list_coaches_by_team_id(team_id)

    if not coaches:
        print("\nAucun coach trouvé pour cette équipe.")
        return

    print("\nCoachs liés à cette équipe :")

    for coach in coaches:
        end_date = coach["end_date"] or "actuel"

        print(
            f"- {coach['name']} | Nationalité : {coach['nationality'] or 'N/A'} "
            f"| Début : {coach['start_date'] or 'N/A'} "
            f"| Fin : {end_date}"
        )


if __name__ == "__main__":
    main()