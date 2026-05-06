from app.database import init_db
from app.repositories.football_repository import list_standings_by_league_season
from app.services.sync_service import sync_standings


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
        f"Synchronisation du classement pour league_id={league_id}, "
        f"season={season_year}..."
    )

    try:
        result = sync_standings(
            league_id=league_id,
            season_year=season_year,
            force_refresh=False,
        )
    except RuntimeError as error:
        print("\nErreur pendant la synchronisation.")
        print(error)
        print(
            "\nCe n'est pas forcément un problème de code : ton plan Free "
            "peut limiter certaines saisons ou certaines compétitions."
        )
        return

    print(f"Source utilisée : {result['source']}")
    print(f"{result['saved_count']} ligne(s) de classement récupérée(s).")
    print(
        f"{result['total_standings']} ligne(s) de classement "
        "présente(s) en base locale."
    )

    standings = list_standings_by_league_season(
        league_id=league_id,
        season_year=season_year,
    )

    if not standings:
        print(
            "\nAucun classement trouvé. Essaie une autre saison ou vérifie "
            "que le coverage standings est disponible."
        )
        return

    print("\nClassement :")
    for standing in standings:
        print(
            f"{standing['position']}. {standing['team_name']} "
            f"- {standing['points']} pts "
            f"- MJ: {standing['all_played']} "
            f"- Diff: {standing['goals_diff']} "
            f"- Forme: {standing['form'] or 'N/A'}"
        )


if __name__ == "__main__":
    main()