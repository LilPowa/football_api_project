from app.database import init_db
from app.repositories.football_repository import list_teams_by_league_season
from app.services.sync_service import sync_teams


def main() -> None:
    init_db()

    league_id_input = input("ID de la ligue, ex: 61 pour Ligue 1 : ").strip()
    season_input = input("Saison, ex: 2025 : ").strip()

    if not league_id_input.isdigit():
        print("Erreur : l'ID de ligue doit être un nombre.")
        return

    if not season_input.isdigit():
        print("Erreur : la saison doit être un nombre.")
        return

    league_id = int(league_id_input)
    season_year = int(season_input)

    print(
        f"Synchronisation des équipes pour league_id={league_id}, "
        f"season={season_year}..."
    )

    result = sync_teams(
        league_id=league_id,
        season_year=season_year,
        force_refresh=False,
    )

    print(f"Source utilisée : {result['source']}")
    print(f"{result['saved_count']} équipes récupérées.")
    print(f"{result['total_teams']} équipes présentes en base locale.")
    print(
        f"{result['total_team_links']} relations équipe/ligue/saison "
        "présentes en base locale."
    )

    teams = list_teams_by_league_season(
        league_id=league_id,
        season_year=season_year,
    )

    print("\nÉquipes trouvées :")
    for team in teams:
        print(
            f"- [{team['team_id']}] {team['name']} "
            f"| Stade : {team['venue_name']} "
            f"| Ville : {team['venue_city']}"
        )


if __name__ == "__main__":
    main()