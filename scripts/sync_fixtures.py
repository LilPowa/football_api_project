from app.database import init_db
from app.repositories.football_repository import list_fixtures_by_league_season
from app.services.sync_service import sync_fixtures


def main() -> None:
    init_db()

    league_id_input = input("ID de la ligue, ex: 61 pour Ligue 1 : ").strip()
    season_input = input("Saison accessible, ex: 2023 ou 2024 selon ton plan : ").strip()

    if not league_id_input.isdigit():
        print("Erreur : l'ID de ligue doit être un nombre.")
        return

    if not season_input.isdigit():
        print("Erreur : la saison doit être un nombre.")
        return

    league_id = int(league_id_input)
    season_year = int(season_input)

    print(
        f"Synchronisation des matchs pour league_id={league_id}, "
        f"season={season_year}..."
    )

    try:
        result = sync_fixtures(
            league_id=league_id,
            season_year=season_year,
            force_refresh=False,
        )
    except RuntimeError as error:
        print("\nErreur pendant la synchronisation.")
        print(error)
        print(
            "\nCe n'est pas bloquant : choisis une autre saison disponible "
            "avec ton plan Free."
        )
        return

    print(f"Source utilisée : {result['source']}")
    print(f"{result['saved_count']} match(s) récupéré(s).")
    print(f"{result['total_fixtures']} match(s) présent(s) en base locale.")

    fixtures = list_fixtures_by_league_season(
        league_id=league_id,
        season_year=season_year,
        limit=20,
    )

    if not fixtures:
        print(
            "\nAucun match trouvé. Essaie une autre saison pour cette ligue."
        )
        return

    print("\nExemples de matchs trouvés :")
    for fixture in fixtures:
        home_goals = fixture["home_goals"]
        away_goals = fixture["away_goals"]

        score = (
            f"{home_goals} - {away_goals}"
            if home_goals is not None and away_goals is not None
            else "à venir"
        )

        print(
            f"- [{fixture['fixture_id']}] {fixture['fixture_date']} | "
            f"{fixture['home_team_name']} {score} {fixture['away_team_name']} "
            f"| {fixture['status_short']}"
        )


if __name__ == "__main__":
    main()