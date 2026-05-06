from app.database import init_db
from app.repositories.football_repository import list_player_season_statistics
from app.services.sync_service import sync_players_statistics


def main() -> None:
    init_db()

    league_input = input("ID de la ligue, ex: 61 pour Ligue 1 : ").strip()
    season_input = input("Saison, ex: 2023 : ").strip()
    team_input = input("ID équipe optionnel, vide pour toute la ligue : ").strip()

    if not league_input.isdigit():
        print("Erreur : l'ID de ligue doit être un nombre.")
        return

    if not season_input.isdigit():
        print("Erreur : la saison doit être un nombre.")
        return

    league_id = int(league_input)
    season_year = int(season_input)
    team_id = int(team_input) if team_input.isdigit() else None

    print(
        f"Synchronisation stats joueurs pour league_id={league_id}, "
        f"season={season_year}, team_id={team_id or 'toutes'}..."
    )

    try:
        result = sync_players_statistics(
            league_id=league_id,
            season_year=season_year,
            team_id=team_id,
            force_refresh=False,
        )
    except RuntimeError as error:
        print("\nErreur pendant la synchronisation des stats joueurs saison.")
        print(error)
        return

    print(f"\nSource utilisée : {result['source']}")
    print(f"{result['saved_count']} ligne(s) récupérée(s).")
    print(
        f"{result['total_player_season_statistics']} ligne(s) "
        "présente(s) en base locale."
    )

    players = list_player_season_statistics(
        league_id=league_id,
        season_year=season_year,
        team_id=team_id,
        limit=20,
    )

    if not players:
        print("\nAucune statistique joueur trouvée.")
        return

    print("\nTop joueurs :")

    for player in players:
        print(
            f"- {player['player_name']} | {player['team_name']} "
            f"| Buts: {player['goals_total'] or 0} "
            f"| Passes déc.: {player['goals_assists'] or 0} "
            f"| Note: {player['games_rating'] or 'N/A'}"
        )


if __name__ == "__main__":
    main()