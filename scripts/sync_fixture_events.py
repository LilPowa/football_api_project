from app.database import init_db
from app.repositories.football_repository import (
    get_fixture_by_id,
    list_fixture_events_by_fixture_id,
)
from app.services.sync_service import sync_fixture_events


def format_minute(elapsed: int | None, extra: int | None) -> str:
    if elapsed is None:
        return "N/A"

    if extra is not None:
        return f"{elapsed}+{extra}'"

    return f"{elapsed}'"


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
            "Les événements risquent d'être vides."
        )

    try:
        result = sync_fixture_events(
            fixture_id=fixture_id,
            force_refresh=False,
        )
    except RuntimeError as error:
        print("\nErreur pendant la synchronisation des événements.")
        print(error)
        return

    print(f"\nSource utilisée : {result['source']}")
    print(f"{result['saved_count']} événement(s) récupéré(s).")
    print(
        f"{result['total_fixture_events']} événement(s) "
        "présent(s) en base locale."
    )

    events = list_fixture_events_by_fixture_id(fixture_id)

    if not events:
        print(
            "\nAucun événement trouvé. "
            "Essaie avec un match terminé ou en cours."
        )
        return

    print("\nTimeline du match :")

    for event in events:
        minute = format_minute(event["elapsed"], event["extra"])

        print(
            f"- {minute} | {event['team_name']} | "
            f"{event['event_type']} - {event['event_detail']} | "
            f"Joueur : {event['player_name'] or 'N/A'} | "
            f"Assist : {event['assist_name'] or 'N/A'}"
        )


if __name__ == "__main__":
    main()