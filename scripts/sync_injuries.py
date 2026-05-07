from app.database import init_db
from app.repositories.football_repository import list_injuries
from app.services.sync_service import sync_injuries


def main() -> None:
    init_db()

    league_input = input("ID ligue, ex: 61, ou vide : ").strip()
    season_input = input("Saison, ex: 2023, ou vide : ").strip()
    team_input = input("ID équipe optionnel, ou vide : ").strip()

    league_id = int(league_input) if league_input.isdigit() else None
    season_year = int(season_input) if season_input.isdigit() else None
    team_id = int(team_input) if team_input.isdigit() else None

    print(
        f"Synchronisation blessures : league={league_id}, "
        f"season={season_year}, team={team_id}"
    )

    try:
        result = sync_injuries(
            league_id=league_id,
            season_year=season_year,
            team_id=team_id,
            force_refresh=False,
        )
    except RuntimeError as error:
        print("\nErreur pendant la synchronisation des blessures.")
        print(error)
        return

    print(f"\nSource utilisée : {result['source']}")
    print(f"{result['saved_count']} blessure(s) récupérée(s).")
    print(f"{result['total_injuries']} blessure(s) présente(s) en base locale.")

    injuries = list_injuries(
        league_id=league_id,
        season_year=season_year,
        team_id=team_id,
        limit=20,
    )

    if not injuries:
        print("\nAucune blessure trouvée.")
        return

    print("\nBlessures :")

    for injury in injuries:
        print(
            f"- {injury['player_name']} | {injury['team_name']} "
            f"| Type: {injury['injury_type'] or 'N/A'} "
            f"| Raison: {injury['reason'] or 'N/A'} "
            f"| Match: {injury['fixture_date'] or 'N/A'}"
        )


if __name__ == "__main__":
    main()