from app.database import init_db
from app.repositories.football_repository import (
    get_head_to_head_summary,
    list_head_to_head_matches,
)
from app.services.sync_service import sync_head_to_head


def main() -> None:
    init_db()

    team_a_input = input("ID équipe A : ").strip()
    team_b_input = input("ID équipe B : ").strip()
    last_input = input("Nombre de matchs à récupérer, ex: 10, ou vide : ").strip()

    if not team_a_input.isdigit():
        print("Erreur : l'ID de l'équipe A doit être un nombre.")
        return

    if not team_b_input.isdigit():
        print("Erreur : l'ID de l'équipe B doit être un nombre.")
        return

    team_a_id = int(team_a_input)
    team_b_id = int(team_b_input)
    last = int(last_input) if last_input.isdigit() else None

    print(
        f"Synchronisation head-to-head pour {team_a_id} vs {team_b_id}..."
    )

    try:
        result = sync_head_to_head(
            team_a_id=team_a_id,
            team_b_id=team_b_id,
            last=last,
            force_refresh=False,
        )
    except RuntimeError as error:
        print("\nErreur pendant la synchronisation du head-to-head.")
        print(error)
        return

    print(f"\nSource utilisée : {result['source']}")
    print(f"{result['saved_count']} confrontation(s) récupérée(s).")
    print(
        f"{result['total_head_to_head_matches']} confrontation(s) "
        "présente(s) en base locale."
    )

    summary = get_head_to_head_summary(team_a_id, team_b_id)

    print("\nRésumé :")
    print(f"- Matchs récupérés : {summary['matches_count']}")
    print(f"- Matchs joués : {summary['played_matches']}")
    print(f"- Victoires équipe A : {summary['team_a_wins']}")
    print(f"- Victoires équipe B : {summary['team_b_wins']}")
    print(f"- Nuls : {summary['draws']}")
    print(f"- Total buts : {summary['total_goals']}")
    print(f"- Moyenne buts/match : {summary['average_goals']}")

    matches = list_head_to_head_matches(team_a_id, team_b_id, limit=20)

    if not matches:
        print("\nAucune confrontation trouvée.")
        return

    print("\nDernières confrontations :")

    for match in matches:
        score = (
            f"{match['home_goals']} - {match['away_goals']}"
            if match["home_goals"] is not None and match["away_goals"] is not None
            else "score indisponible"
        )

        print(
            f"- {match['fixture_date']} | "
            f"{match['home_team_name']} {score} {match['away_team_name']} "
            f"| {match['league_name']} | {match['status_short']}"
        )


if __name__ == "__main__":
    main()