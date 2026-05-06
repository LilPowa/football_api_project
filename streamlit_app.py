import json

from app.config import settings

import streamlit as st

from app.database import init_db
from app.repositories.api_cache_repository import count_cache_entries
from app.repositories.football_repository import (
    count_countries,
    count_fixture_events,
    count_fixture_lineup_players,
    count_fixture_lineups,
    count_fixture_player_statistics,
    count_fixture_statistics,
    count_fixtures,
    count_head_to_head_matches,
    count_league_seasons,
    count_leagues,
    count_standings,
    count_teams,
    get_fixture_by_id,
    get_fixture_event_by_id,
    get_fixture_lineup_by_id,
    get_fixture_player_statistic_by_id,
    get_fixture_statistics_as_comparison,
    get_head_to_head_match_by_id,
    get_head_to_head_summary,
    get_league_by_id,
    get_standing_by_id,
    list_all_countries,
    list_fixture_events_by_fixture_id,
    list_fixture_lineup_players,
    list_fixture_lineups_by_fixture_id,
    list_fixture_player_statistics_by_fixture_id,
    list_fixture_teams_filter,
    list_fixtures_filtered,
    list_head_to_head_matches,
    list_league_seasons_by_league_id,
    list_leagues_filtered,
    list_standings_by_league_season,
    list_teams_by_league_season,
)
from app.services.sync_service import (
    sync_countries,
    sync_fixture_events,
    sync_fixture_lineups,
    sync_fixture_players,
    sync_fixture_statistics,
    sync_fixtures,
    sync_head_to_head,
    sync_leagues,
    sync_standings,
    sync_teams,
)

APP_VERSION = "0.2.1"


st.set_page_config(
    page_title="Football API Dashboard",
    page_icon="⚽",
    layout="wide",
)


def initialize_app() -> None:
    init_db()


def render_header() -> None:
    st.title("⚽ Football API Dashboard")
    st.caption(f"Version {APP_VERSION}")
    st.write(
        "Interface locale pour explorer les données API-Football, "
        "avec cache et base SQLite."
    )

def render_sidebar() -> None:
    with st.sidebar:
        st.title("⚽ Menu")
        st.caption(f"Version {APP_VERSION}")

        st.markdown("---")
        st.markdown("### Base locale")

        st.metric("Pays", count_countries())
        st.metric("Ligues", count_leagues())
        st.metric("Équipes", count_teams())
        st.metric("Matchs", count_fixtures())
        st.metric("Stats matchs", count_fixture_statistics())
        st.metric("Événements", count_fixture_events())
        st.metric("Compositions", count_fixture_lineups())
        st.metric("Stats joueurs", count_fixture_player_statistics())
        st.metric("Head-to-head", count_head_to_head_matches())
        st.metric("Cache API", count_cache_entries())

        st.markdown("---")
        render_sidebar_sync_controls()

        st.markdown("---")
        st.info(
            "Les données sont d'abord lues depuis la base SQLite locale. "
            "Les boutons de synchronisation appellent l'API uniquement si nécessaire, "
            "sauf en refresh forcé."
        )

def render_dashboard_home() -> None:
    st.subheader("Tableau de bord")

    st.write(
        "Bienvenue dans le dashboard local API-Football. "
        "L'objectif est de centraliser les données foot dans une base locale, "
        "puis de les explorer sans consommer inutilement le quota API."
    )

    render_metrics()

    st.markdown("### État d'avancement du projet")

    roadmap_rows = [
        {
            "Phase": "Socle",
            "État": "Terminé",
            "Contenu": "Client API, configuration, cache, SQLite, Streamlit",
        },
        {
            "Phase": "Données principales",
            "État": "En cours",
            "Contenu": "Pays, ligues, saisons, équipes, matchs, classements",
        },
        {
            "Phase": "Détail des matchs",
            "État": "En cours",
            "Contenu": "Statistiques de match, événements, lineups, joueurs",
        },
        {
            "Phase": "Joueurs",
            "État": "À faire",
            "Contenu": "Effectifs, top scorers, top assists, cartons",
        },
        {
            "Phase": "Prédictions",
            "État": "À faire",
            "Contenu": "Predictions API, prédiction maison, comparaison",
        },
        {
            "Phase": "Cotes",
            "État": "À faire",
            "Contenu": "Odds, bookmakers, historique local des cotes",
        },
        {
            "Phase": "Industrialisation",
            "État": "À faire",
            "Contenu": "Logs, exports, tests, Docker, README",
        },
    ]

    st.dataframe(
        roadmap_rows,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Prochaine étape recommandée")

    st.info(
        "Prochaine brique : ajouter les événements d'un match avec "
        "`/fixtures/events`, afin d'afficher une timeline complète du match."
    )

def render_admin_page() -> None:
    st.subheader("Administration locale")

    st.write(
        "Cette page servira à gérer le cache, les quotas, les logs API "
        "et l'historique des synchronisations."
    )

    st.markdown("### État actuel")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Entrées cache API", count_cache_entries())
    col2.metric("Matchs stockés", count_fixtures())
    col3.metric("Stats match stockées", count_fixture_statistics())
    col4.metric("Événements stockés", count_fixture_events())

    col5, col6, col7, col8 = st.columns(4)

    col5.metric("Compositions stockées", count_fixture_lineups())
    col6.metric("Joueurs lineups", count_fixture_lineup_players())
    col7.metric("Stats joueurs", count_fixture_player_statistics())
    col8.metric("Classements", count_standings())

    col9, col10, col11, col12 = st.columns(4)

    col9.metric("Head-to-head", count_head_to_head_matches())
    col10.metric("Équipes", count_teams())
    col11.metric("Ligues", count_leagues())
    col12.metric("Pays", count_countries())

    st.info(
        "Pour l'instant, le cache est fonctionnel mais pas encore administrable "
        "depuis l'interface. On ajoutera plus tard : suppression du cache, "
        "historique des appels API, erreurs, quotas et logs."
    )

def render_sidebar_sync_controls() -> None:
    st.markdown("### Synchronisation")

    with st.expander("Synchronisations normales", expanded=False):
        if st.button("Synchroniser les pays", key="sidebar_sync_countries"):
            with st.spinner("Synchronisation des pays..."):
                result = sync_countries(force_refresh=False)

            st.success(
                f"Pays : {result['total_count']} en base "
                f"({result['source']})."
            )

        if st.button("Synchroniser les ligues", key="sidebar_sync_leagues"):
            with st.spinner("Synchronisation des ligues..."):
                result = sync_leagues(force_refresh=False)

            st.success(
                f"Ligues : {result['total_leagues']} en base "
                f"({result['source']})."
            )

    with st.expander("Refresh forcé", expanded=False):
        st.warning(
            "Le refresh forcé consomme directement ton quota API-Football."
        )

        if st.button("Forcer refresh pays", key="sidebar_force_countries"):
            with st.spinner("Refresh des pays..."):
                result = sync_countries(force_refresh=True)

            st.success(
                f"Pays rafraîchis : {result['total_count']} en base."
            )

        if st.button("Forcer refresh ligues", key="sidebar_force_leagues"):
            with st.spinner("Refresh des ligues..."):
                result = sync_leagues(force_refresh=True)

            st.success(
                f"Ligues rafraîchies : {result['total_leagues']} en base."
            )

def render_sync_buttons() -> None:
    st.subheader("Synchronisation des données")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Synchroniser les pays"):
            with st.spinner("Synchronisation des pays..."):
                result = sync_countries(force_refresh=False)

            st.success(
                f"Pays synchronisés depuis : {result['source']} — "
                f"{result['total_count']} pays en base."
            )

    with col2:
        if st.button("Forcer refresh pays"):
            with st.spinner("Refresh des pays depuis API-Football..."):
                result = sync_countries(force_refresh=True)

            st.warning(
                f"Pays rafraîchis depuis : {result['source']} — "
                f"{result['total_count']} pays en base."
            )

    with col3:
        if st.button("Synchroniser les ligues"):
            with st.spinner("Synchronisation des ligues..."):
                result = sync_leagues(force_refresh=False)

            st.success(
                f"Ligues synchronisées depuis : {result['source']} — "
                f"{result['total_leagues']} ligues, "
                f"{result['total_seasons']} saisons."
            )

    with col4:
        if st.button("Forcer refresh ligues"):
            with st.spinner("Refresh des ligues depuis API-Football..."):
                result = sync_leagues(force_refresh=True)

            st.warning(
                f"Ligues rafraîchies depuis : {result['source']} — "
                f"{result['total_leagues']} ligues, "
                f"{result['total_seasons']} saisons."
            )

def render_metrics() -> None:
    st.subheader("État de la base locale")

    row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)

    row1_col1.metric("Pays", count_countries())
    row1_col2.metric("Ligues", count_leagues())
    row1_col3.metric("Saisons", count_league_seasons())
    row1_col4.metric("Équipes", count_teams())

    row2_col1, row2_col2, row2_col3, row2_col4 = st.columns(4)

    row2_col1.metric("Matchs", count_fixtures())
    row2_col2.metric("Stats matchs", count_fixture_statistics())
    row2_col3.metric("Événements", count_fixture_events())
    row2_col4.metric("Compositions", count_fixture_lineups())

    row3_col1, row3_col2, row3_col3, row3_col4 = st.columns(4)

    row3_col1.metric("Joueurs lineups", count_fixture_lineup_players())
    row3_col2.metric("Stats joueurs", count_fixture_player_statistics())
    row3_col3.metric("Classements", count_standings())
    row3_col4.metric("Head-to-head", count_head_to_head_matches())

    row4_col1, row4_col2, row4_col3, row4_col4 = st.columns(4)

    row4_col1.metric("Cache API", count_cache_entries())
    row4_col2.metric("À venir", "Squads")
    row4_col3.metric("À venir", "Predictions")
    row4_col4.metric("À venir", "Odds")

def render_league_explorer() -> None:
    st.subheader("Exploration des ligues")

    countries = list_all_countries()
    country_names = ["Tous"] + [country["name"] for country in countries]

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        selected_country = st.selectbox(
            "Filtrer par pays",
            country_names,
            index=0,
        )

    with col2:
        search = st.text_input(
            "Rechercher une ligue",
            placeholder="Ex : Ligue 1, Premier League, Champions League..."
        )

    with col3:
        limit = st.number_input(
            "Limite",
            min_value=10,
            max_value=500,
            value=100,
            step=10,
        )

    leagues = list_leagues_filtered(
        country_name=selected_country,
        search=search.strip() if search else None,
        limit=int(limit),
    )

    st.write(f"{len(leagues)} ligue(s) affichée(s).")

    if not leagues:
        st.info(
            "Aucune ligue trouvée. Lance d'abord la synchronisation des ligues."
        )
        return

    league_options = {
        f"[{league['league_id']}] {league['name']} — {league['country_name']}": league["league_id"]
        for league in leagues
    }

    selected_label = st.selectbox(
        "Sélectionner une ligue pour voir ses saisons et son coverage",
        list(league_options.keys()),
    )

    selected_league_id = league_options[selected_label]

    selected_league = get_league_by_id(selected_league_id)
    seasons = list_league_seasons_by_league_id(selected_league_id)

    if selected_league is None:
        st.error("Impossible de charger les détails de cette ligue.")
        return

    col_info, col_logo = st.columns([3, 1])

    with col_info:
        st.markdown(f"### {selected_league['name']}")
        st.write(f"**ID API :** {selected_league['league_id']}")
        st.write(f"**Type :** {selected_league['type']}")
        st.write(f"**Pays :** {selected_league['country_name']}")
        st.write(f"**Dernière mise à jour locale :** {selected_league['updated_at']}")

    with col_logo:
        if selected_league.get("logo"):
            st.image(selected_league["logo"], width=120)

    if not seasons:
        st.info("Aucune saison trouvée pour cette ligue.")
        return

    st.markdown("### Saisons disponibles")

    season_labels = [
        f"{season['season_year']} {'(courante)' if season['current'] else ''}"
        for season in seasons
    ]

    selected_season_label = st.selectbox(
        "Choisir une saison",
        season_labels,
    )

    selected_index = season_labels.index(selected_season_label)
    selected_season = seasons[selected_index]

    col_a, col_b, col_c = st.columns(3)

    col_a.metric("Saison", selected_season["season_year"])
    col_b.metric("Début", selected_season["start_date"] or "N/A")
    col_c.metric("Fin", selected_season["end_date"] or "N/A")

    st.markdown("### Coverage API disponible")

    st.write(
        "Le coverage indique quelles données sont disponibles pour cette "
        "ligue et cette saison : événements, lineups, statistiques, joueurs, "
        "classements, blessures, cotes ou prédictions."
    )

    coverage = selected_season["coverage"]

    st.json(coverage)

    with st.expander("Voir le JSON brut de la ligue"):
        st.code(
            json.dumps(selected_league["raw"], indent=2, ensure_ascii=False),
            language="json",
        )

def render_team_explorer() -> None:
    st.subheader("Équipes par ligue et saison")

    leagues = list_leagues_filtered(limit=500)

    if not leagues:
        st.info("Aucune ligue disponible. Synchronise d'abord les ligues.")
        return

    league_options = {
        f"[{league['league_id']}] {league['name']} — {league['country_name']}": league["league_id"]
        for league in leagues
    }

    selected_league_label = st.selectbox(
        "Choisir une ligue",
        list(league_options.keys()),
        key="teams_league_select",
    )

    selected_league_id = league_options[selected_league_label]
    seasons = list_league_seasons_by_league_id(selected_league_id)

    if not seasons:
        st.info("Aucune saison disponible pour cette ligue.")
        return

    season_options = {
        f"{season['season_year']} {'(courante)' if season['current'] else ''}": season["season_year"]
        for season in seasons
    }

    selected_season_label = st.selectbox(
        "Choisir une saison",
        list(season_options.keys()),
        key="teams_season_select",
    )

    selected_season_year = season_options[selected_season_label]

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Synchroniser les équipes", key="sync_teams_button"):
            with st.spinner("Synchronisation des équipes..."):
                result = sync_teams(
                    league_id=selected_league_id,
                    season_year=selected_season_year,
                    force_refresh=False,
                )

            st.success(
                f"Équipes synchronisées depuis : {result['source']} — "
                f"{result['saved_count']} équipe(s) récupérée(s)."
            )

    with col2:
        if st.button("Forcer refresh équipes", key="force_sync_teams_button"):
            with st.spinner("Refresh des équipes depuis API-Football..."):
                result = sync_teams(
                    league_id=selected_league_id,
                    season_year=selected_season_year,
                    force_refresh=True,
                )

            st.warning(
                f"Équipes rafraîchies depuis : {result['source']} — "
                f"{result['saved_count']} équipe(s) récupérée(s)."
            )

    teams = list_teams_by_league_season(
        league_id=selected_league_id,
        season_year=selected_season_year,
    )

    st.write(
        f"{len(teams)} équipe(s) trouvée(s) pour cette ligue et cette saison."
    )

    if not teams:
        st.info("Aucune équipe en base pour cette sélection.")
        return

    for team in teams:
        with st.container(border=True):
            col_logo, col_info, col_venue = st.columns([1, 3, 3])

            with col_logo:
                if team.get("logo"):
                    st.image(team["logo"], width=80)

            with col_info:
                st.markdown(f"### {team['name']}")
                st.write(f"**ID API :** {team['team_id']}")
                st.write(f"**Code :** {team['code'] or 'N/A'}")
                st.write(f"**Pays :** {team['country'] or 'N/A'}")
                st.write(f"**Fondé en :** {team['founded'] or 'N/A'}")
                st.write(
                    f"**Équipe nationale :** "
                    f"{'Oui' if team['national'] else 'Non'}"
                )

            with col_venue:
                st.write(f"**Stade :** {team['venue_name'] or 'N/A'}")
                st.write(f"**Ville :** {team['venue_city'] or 'N/A'}")
                st.write(
                    f"**Capacité :** "
                    f"{team['venue_capacity'] or 'N/A'}"
                )
                st.write(
                    f"**Dernière mise à jour locale :** "
                    f"{team['updated_at']}"
                )

def render_fixture_statistics_section(fixture_id: int, status_short: str | None) -> None:
    st.markdown("### Statistiques détaillées du match")

    if status_short == "NS":
        st.info(
            "Ce match n'a pas encore commencé. "
            "Les statistiques risquent d'être vides."
        )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Synchroniser les statistiques du match",
            key=f"sync_fixture_stats_{fixture_id}",
        ):
            try:
                with st.spinner("Synchronisation des statistiques du match..."):
                    result = sync_fixture_statistics(
                        fixture_id=fixture_id,
                        force_refresh=False,
                    )

                st.success(
                    f"Statistiques synchronisées depuis : {result['source']} — "
                    f"{result['saved_count']} statistique(s) récupérée(s)."
                )
            except RuntimeError as error:
                st.error("La synchronisation des statistiques a échoué.")
                st.code(str(error))

    with col2:
        if st.button(
            "Forcer refresh stats match",
            key=f"force_sync_fixture_stats_{fixture_id}",
        ):
            try:
                with st.spinner("Refresh des statistiques depuis API-Football..."):
                    result = sync_fixture_statistics(
                        fixture_id=fixture_id,
                        force_refresh=True,
                    )

                st.warning(
                    f"Statistiques rafraîchies depuis : {result['source']} — "
                    f"{result['saved_count']} statistique(s) récupérée(s)."
                )
            except RuntimeError as error:
                st.error("Le refresh des statistiques a échoué.")
                st.code(str(error))

    comparison = get_fixture_statistics_as_comparison(fixture_id)

    if not comparison:
        st.info(
            "Aucune statistique en base pour ce match. "
            "Clique sur le bouton de synchronisation ou choisis un match terminé."
        )
        return

    st.dataframe(
        comparison,
        use_container_width=True,
        hide_index=True,
    )

def get_event_icon(event_type: str | None, event_detail: str | None) -> str:
    event_type = event_type or ""
    event_detail = event_detail or ""

    if event_type == "Goal":
        return "⚽"

    if event_type == "Card":
        if "Red" in event_detail:
            return "🟥"
        return "🟨"

    if event_type == "subst":
        return "🔁"

    if event_type == "Var":
        return "📺"

    return "•"


def format_event_minute(elapsed: int | None, extra: int | None) -> str:
    if elapsed is None:
        return "N/A"

    if extra is not None:
        return f"{elapsed}+{extra}'"

    return f"{elapsed}'"


def render_fixture_events_section(
    fixture_id: int,
    status_short: str | None,
) -> None:
    st.markdown("### Timeline des événements")

    if status_short == "NS":
        st.info(
            "Ce match n'a pas encore commencé. "
            "Les événements risquent d'être vides."
        )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Synchroniser les événements du match",
            key=f"sync_fixture_events_{fixture_id}",
        ):
            try:
                with st.spinner("Synchronisation des événements du match..."):
                    result = sync_fixture_events(
                        fixture_id=fixture_id,
                        force_refresh=False,
                    )

                st.success(
                    f"Événements synchronisés depuis : {result['source']} — "
                    f"{result['saved_count']} événement(s) récupéré(s)."
                )
            except RuntimeError as error:
                st.error("La synchronisation des événements a échoué.")
                st.code(str(error))

    with col2:
        if st.button(
            "Forcer refresh événements",
            key=f"force_sync_fixture_events_{fixture_id}",
        ):
            try:
                with st.spinner("Refresh des événements depuis API-Football..."):
                    result = sync_fixture_events(
                        fixture_id=fixture_id,
                        force_refresh=True,
                    )

                st.warning(
                    f"Événements rafraîchis depuis : {result['source']} — "
                    f"{result['saved_count']} événement(s) récupéré(s)."
                )
            except RuntimeError as error:
                st.error("Le refresh des événements a échoué.")
                st.code(str(error))

    events = list_fixture_events_by_fixture_id(fixture_id)

    if not events:
        st.info(
            "Aucun événement en base pour ce match. "
            "Clique sur le bouton de synchronisation ou choisis un match terminé."
        )
        return

    event_options = {}

    for event in events:
        minute = format_event_minute(event["elapsed"], event["extra"])
        icon = get_event_icon(event["event_type"], event["event_detail"])

        label = (
            f"{minute} {icon} "
            f"{event['event_type'] or 'Event'} - "
            f"{event['event_detail'] or 'N/A'} "
            f"| {event['player_name'] or 'N/A'}"
        )

        event_options[label] = event["id"]

        with st.container(border=True):
            col_minute, col_event, col_team = st.columns([1, 4, 3])

            with col_minute:
                st.markdown(f"### {minute}")

            with col_event:
                st.markdown(
                    f"**{icon} {event['event_type'] or 'Event'}**"
                )
                st.write(f"**Détail :** {event['event_detail'] or 'N/A'}")
                st.write(f"**Joueur :** {event['player_name'] or 'N/A'}")

                if event.get("assist_name"):
                    st.write(f"**Assist :** {event['assist_name']}")

                if event.get("comments"):
                    st.write(f"**Commentaire :** {event['comments']}")

            with col_team:
                if event.get("team_logo"):
                    st.image(event["team_logo"], width=45)

                st.write(f"**Équipe :** {event['team_name'] or 'N/A'}")

    selected_event_label = st.selectbox(
        "Voir le JSON brut d'un événement",
        list(event_options.keys()),
        key=f"fixture_event_detail_{fixture_id}",
    )

    selected_event_id = event_options[selected_event_label]
    event_detail = get_fixture_event_by_id(selected_event_id)

    if event_detail:
        with st.expander("JSON brut de l'événement sélectionné"):
            st.code(
                json.dumps(event_detail["raw"], indent=2, ensure_ascii=False),
                language="json",
            )

def render_player_list(
    title: str,
    players: list[dict],
) -> None:
    st.markdown(f"**{title}**")

    if not players:
        st.info("Aucun joueur trouvé.")
        return

    rows = []

    for player in players:
        rows.append(
            {
                "N°": player["player_number"],
                "Joueur": player["player_name"],
                "Poste": player["player_position"],
                "Grille": player["player_grid"],
            }
        )

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
    )


def render_fixture_lineups_section(
    fixture_id: int,
    status_short: str | None,
) -> None:
    st.markdown("### Compositions du match")

    if status_short == "NS":
        st.info(
            "Ce match n'a pas encore commencé. "
            "Les compositions peuvent être indisponibles."
        )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Synchroniser les compositions",
            key=f"sync_fixture_lineups_{fixture_id}",
        ):
            try:
                with st.spinner("Synchronisation des compositions du match..."):
                    result = sync_fixture_lineups(
                        fixture_id=fixture_id,
                        force_refresh=False,
                    )

                st.success(
                    f"Compositions synchronisées depuis : {result['source']} — "
                    f"{result['saved_count']} joueur(s) récupéré(s)."
                )
            except RuntimeError as error:
                st.error("La synchronisation des compositions a échoué.")
                st.code(str(error))

    with col2:
        if st.button(
            "Forcer refresh compositions",
            key=f"force_sync_fixture_lineups_{fixture_id}",
        ):
            try:
                with st.spinner("Refresh des compositions depuis API-Football..."):
                    result = sync_fixture_lineups(
                        fixture_id=fixture_id,
                        force_refresh=True,
                    )

                st.warning(
                    f"Compositions rafraîchies depuis : {result['source']} — "
                    f"{result['saved_count']} joueur(s) récupéré(s)."
                )
            except RuntimeError as error:
                st.error("Le refresh des compositions a échoué.")
                st.code(str(error))

    lineups = list_fixture_lineups_by_fixture_id(fixture_id)

    if not lineups:
        st.info(
            "Aucune composition en base pour ce match. "
            "Clique sur le bouton de synchronisation ou choisis un autre match."
        )
        return

    lineup_options = {
        f"{lineup['team_name']} - {lineup['formation'] or 'Formation inconnue'}": lineup["id"]
        for lineup in lineups
    }

    selected_lineup_label = st.selectbox(
        "Voir le JSON brut d'une composition",
        list(lineup_options.keys()),
        key=f"fixture_lineup_detail_{fixture_id}",
    )

    for lineup in lineups:
        with st.container(border=True):
            col_logo, col_info = st.columns([1, 4])

            with col_logo:
                if lineup.get("team_logo"):
                    st.image(lineup["team_logo"], width=80)

            with col_info:
                st.markdown(f"### {lineup['team_name']}")
                st.write(f"**Formation :** {lineup['formation'] or 'N/A'}")
                st.write(f"**Coach :** {lineup['coach_name'] or 'N/A'}")
                st.write(f"**Dernière mise à jour locale :** {lineup['updated_at']}")

            starters = list_fixture_lineup_players(
                fixture_id=fixture_id,
                team_id=lineup["team_id"],
                lineup_type="startXI",
            )

            substitutes = list_fixture_lineup_players(
                fixture_id=fixture_id,
                team_id=lineup["team_id"],
                lineup_type="substitute",
            )

            col_start, col_subs = st.columns(2)

            with col_start:
                render_player_list("Titulaires", starters)

            with col_subs:
                render_player_list("Remplaçants", substitutes)

    selected_lineup_id = lineup_options[selected_lineup_label]
    lineup_detail = get_fixture_lineup_by_id(selected_lineup_id)

    if lineup_detail:
        with st.expander("JSON brut de la composition sélectionnée"):
            st.code(
                json.dumps(lineup_detail["raw"], indent=2, ensure_ascii=False),
                language="json",
            )

def render_fixture_players_section(
    fixture_id: int,
    status_short: str | None,
) -> None:
    st.markdown("### Statistiques joueurs du match")

    if status_short == "NS":
        st.info(
            "Ce match n'a pas encore commencé. "
            "Les statistiques joueurs risquent d'être vides."
        )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Synchroniser les statistiques joueurs",
            key=f"sync_fixture_players_{fixture_id}",
        ):
            try:
                with st.spinner("Synchronisation des statistiques joueurs..."):
                    result = sync_fixture_players(
                        fixture_id=fixture_id,
                        force_refresh=False,
                    )

                st.success(
                    f"Stats joueurs synchronisées depuis : {result['source']} — "
                    f"{result['saved_count']} ligne(s) récupérée(s)."
                )
            except RuntimeError as error:
                st.error("La synchronisation des statistiques joueurs a échoué.")
                st.code(str(error))

    with col2:
        if st.button(
            "Forcer refresh stats joueurs",
            key=f"force_sync_fixture_players_{fixture_id}",
        ):
            try:
                with st.spinner("Refresh des statistiques joueurs depuis API-Football..."):
                    result = sync_fixture_players(
                        fixture_id=fixture_id,
                        force_refresh=True,
                    )

                st.warning(
                    f"Stats joueurs rafraîchies depuis : {result['source']} — "
                    f"{result['saved_count']} ligne(s) récupérée(s)."
                )
            except RuntimeError as error:
                st.error("Le refresh des statistiques joueurs a échoué.")
                st.code(str(error))

    all_player_stats = list_fixture_player_statistics_by_fixture_id(fixture_id)

    if not all_player_stats:
        st.info(
            "Aucune statistique joueur en base pour ce match. "
            "Clique sur le bouton de synchronisation ou choisis un autre match."
        )
        return

    team_options = {"Toutes les équipes": None}

    for stat in all_player_stats:
        team_options[stat["team_name"]] = stat["team_id"]

    selected_team_name = st.selectbox(
        "Filtrer par équipe",
        list(team_options.keys()),
        key=f"fixture_players_team_filter_{fixture_id}",
    )

    selected_team_id = team_options[selected_team_name]

    player_stats = list_fixture_player_statistics_by_fixture_id(
        fixture_id=fixture_id,
        team_id=selected_team_id,
    )

    table_rows = []

    for stat in player_stats:
        table_rows.append(
            {
                "Équipe": stat["team_name"],
                "N°": stat["games_number"],
                "Joueur": stat["player_name"],
                "Poste": stat["games_position"],
                "Minutes": stat["games_minutes"],
                "Note": stat["games_rating"],
                "Buts": stat["goals_total"],
                "Passes déc.": stat["goals_assists"],
                "Tirs": stat["shots_total"],
                "Tirs cadrés": stat["shots_on"],
                "Passes": stat["passes_total"],
                "Passes clés": stat["passes_key"],
                "Précision passes": stat["passes_accuracy"],
                "Duels": stat["duels_total"],
                "Duels gagnés": stat["duels_won"],
                "Dribbles tentés": stat["dribbles_attempts"],
                "Dribbles réussis": stat["dribbles_success"],
                "Fautes subies": stat["fouls_drawn"],
                "Fautes commises": stat["fouls_committed"],
                "Jaunes": stat["cards_yellow"],
                "Rouges": stat["cards_red"],
            }
        )

    st.dataframe(
        table_rows,
        use_container_width=True,
        hide_index=True,
    )

    player_options = {
        (
            f"{stat['team_name']} | "
            f"#{stat['games_number'] or 'N/A'} "
            f"{stat['player_name']}"
        ): stat["id"]
        for stat in player_stats
    }

    selected_player_label = st.selectbox(
        "Voir le détail JSON d'un joueur",
        list(player_options.keys()),
        key=f"fixture_player_stat_detail_{fixture_id}",
    )

    selected_player_stat_id = player_options[selected_player_label]
    player_stat_detail = get_fixture_player_statistic_by_id(selected_player_stat_id)

    if player_stat_detail:
        col_photo, col_info, col_stats = st.columns([1, 3, 3])

        with col_photo:
            if player_stat_detail.get("player_photo"):
                st.image(player_stat_detail["player_photo"], width=90)

        with col_info:
            st.markdown(f"### {player_stat_detail['player_name']}")
            st.write(f"**Équipe :** {player_stat_detail['team_name']}")
            st.write(f"**Poste :** {player_stat_detail['games_position'] or 'N/A'}")
            st.write(f"**Numéro :** {player_stat_detail['games_number'] or 'N/A'}")
            st.write(f"**Minutes :** {player_stat_detail['games_minutes'] or 'N/A'}")
            st.write(f"**Note :** {player_stat_detail['games_rating'] or 'N/A'}")

        with col_stats:
            st.write("**Résumé performance**")
            st.write(f"Buts : {player_stat_detail['goals_total'] or 0}")
            st.write(f"Passes décisives : {player_stat_detail['goals_assists'] or 0}")
            st.write(f"Tirs cadrés : {player_stat_detail['shots_on'] or 0}")
            st.write(f"Passes clés : {player_stat_detail['passes_key'] or 0}")
            st.write(f"Duels gagnés : {player_stat_detail['duels_won'] or 0}")

        with st.expander("JSON brut des statistiques joueur"):
            st.code(
                json.dumps(player_stat_detail["raw"], indent=2, ensure_ascii=False),
                language="json",
            )

def render_fixture_explorer() -> None:
    st.subheader("Matchs par ligue et saison")

    leagues = list_leagues_filtered(limit=500)

    if not leagues:
        st.info("Aucune ligue disponible. Synchronise d'abord les ligues.")
        return

    league_options = {
        f"[{league['league_id']}] {league['name']} — {league['country_name']}": league["league_id"]
        for league in leagues
    }

    selected_league_label = st.selectbox(
        "Choisir une ligue pour les matchs",
        list(league_options.keys()),
        key="fixtures_league_select",
    )

    selected_league_id = league_options[selected_league_label]
    seasons = list_league_seasons_by_league_id(selected_league_id)

    if not seasons:
        st.info("Aucune saison disponible pour cette ligue.")
        return

    season_options = {
        f"{season['season_year']} {'(courante)' if season['current'] else ''}": season["season_year"]
        for season in seasons
    }

    selected_season_label = st.selectbox(
        "Choisir une saison pour les matchs",
        list(season_options.keys()),
        key="fixtures_season_select",
    )

    selected_season_year = season_options[selected_season_label]

    st.info(
        "Avec le plan Free, certaines saisons peuvent être refusées par l'API. "
        "Si une synchronisation ne retourne rien ou affiche une erreur, choisis "
        "une autre saison disponible."
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Synchroniser les matchs", key="sync_fixtures_button"):
            try:
                with st.spinner("Synchronisation des matchs..."):
                    result = sync_fixtures(
                        league_id=selected_league_id,
                        season_year=selected_season_year,
                        force_refresh=False,
                    )

                st.success(
                    f"Matchs synchronisés depuis : {result['source']} — "
                    f"{result['saved_count']} match(s) récupéré(s)."
                )
            except RuntimeError as error:
                st.error("La synchronisation des matchs a échoué.")
                st.code(str(error))
                st.warning(
                    "Ce n'est pas forcément un problème de code : ton plan Free "
                    "peut limiter certaines saisons."
                )

    with col2:
        if st.button("Forcer refresh matchs", key="force_sync_fixtures_button"):
            try:
                with st.spinner("Refresh des matchs depuis API-Football..."):
                    result = sync_fixtures(
                        league_id=selected_league_id,
                        season_year=selected_season_year,
                        force_refresh=True,
                    )

                st.warning(
                    f"Matchs rafraîchis depuis : {result['source']} — "
                    f"{result['saved_count']} match(s) récupéré(s)."
                )
            except RuntimeError as error:
                st.error("Le refresh des matchs a échoué.")
                st.code(str(error))
                st.warning(
                    "Essaie une autre saison si ton plan Free refuse celle-ci."
                )

    teams = list_fixture_teams_filter(
        league_id=selected_league_id,
        season_year=selected_season_year,
    )

    team_options = {"Tous": None}

    for team in teams:
        team_options[team["team_name"]] = team["team_id"]

    col_filter_1, col_filter_2, col_filter_3 = st.columns(3)

    with col_filter_1:
        selected_team_name = st.selectbox(
            "Filtrer par équipe",
            list(team_options.keys()),
            key="fixtures_team_filter",
        )

    with col_filter_2:
        selected_status = st.selectbox(
            "Filtrer par statut",
            ["Tous", "NS", "1H", "HT", "2H", "FT", "AET", "PEN", "PST", "CANC"],
            key="fixtures_status_filter",
        )

    with col_filter_3:
        limit = st.number_input(
            "Nombre de matchs affichés",
            min_value=10,
            max_value=500,
            value=100,
            step=10,
            key="fixtures_limit",
        )

    selected_team_id = team_options[selected_team_name]

    fixtures = list_fixtures_filtered(
        league_id=selected_league_id,
        season_year=selected_season_year,
        team_id=selected_team_id,
        status_short=selected_status,
        limit=int(limit),
    )

    st.write(
        f"{len(fixtures)} match(s) affiché(s) pour cette ligue et cette saison."
    )

    if not fixtures:
        st.info(
            "Aucun match en base pour cette sélection. Lance une synchronisation "
            "ou choisis une autre saison."
        )
        return

    fixture_options = {
        (
            f"[{fixture['fixture_id']}] "
            f"{fixture['home_team_name']} vs {fixture['away_team_name']} "
            f"— {fixture['fixture_date']}"
        ): fixture["fixture_id"]
        for fixture in fixtures
    }

    selected_fixture_label = st.selectbox(
        "Sélectionner un match pour voir le détail JSON",
        list(fixture_options.keys()),
        key="fixture_detail_select",
    )

    selected_fixture_id = fixture_options[selected_fixture_label]

    for fixture in fixtures:
        with st.container(border=True):
            col_home, col_score, col_away, col_meta = st.columns([3, 2, 3, 3])

            with col_home:
                if fixture.get("home_team_logo"):
                    st.image(fixture["home_team_logo"], width=50)
                st.markdown(f"**{fixture['home_team_name']}**")

            with col_score:
                home_goals = fixture["home_goals"]
                away_goals = fixture["away_goals"]

                if home_goals is not None and away_goals is not None:
                    st.markdown(f"### {home_goals} - {away_goals}")
                else:
                    st.markdown("### À venir")

                st.write(f"Statut : {fixture['status_short']}")

            with col_away:
                if fixture.get("away_team_logo"):
                    st.image(fixture["away_team_logo"], width=50)
                st.markdown(f"**{fixture['away_team_name']}**")

            with col_meta:
                st.write(f"**Date :** {fixture['fixture_date']}")
                st.write(f"**Journée / tour :** {fixture['round'] or 'N/A'}")
                st.write(f"**Stade :** {fixture['venue_name'] or 'N/A'}")
                st.write(f"**Ville :** {fixture['venue_city'] or 'N/A'}")

    fixture_detail = get_fixture_by_id(selected_fixture_id)

    if fixture_detail:
        st.divider()

        detail_tab_stats, detail_tab_events, detail_tab_lineups, detail_tab_players, detail_tab_raw = st.tabs(
            [
                "📊 Statistiques",
                "⏱️ Événements",
                "🧩 Compositions",
                "👤 Joueurs",
                "🧾 JSON brut",
            ]
        )

        with detail_tab_stats:
            render_fixture_statistics_section(
                fixture_id=selected_fixture_id,
                status_short=fixture_detail.get("status_short"),
            )

        with detail_tab_events:
            render_fixture_events_section(
                fixture_id=selected_fixture_id,
                status_short=fixture_detail.get("status_short"),
            )
        
        with detail_tab_lineups:
            render_fixture_lineups_section(
                fixture_id=selected_fixture_id,
                status_short=fixture_detail.get("status_short"),
            )
        
        with detail_tab_players:
            render_fixture_players_section(
                fixture_id=selected_fixture_id,
                status_short=fixture_detail.get("status_short"),
            )

        with detail_tab_raw:
            st.code(
                json.dumps(fixture_detail["raw"], indent=2, ensure_ascii=False),
                language="json",
            )

def render_standings_explorer() -> None:
    st.subheader("Classements par ligue et saison")

    leagues = list_leagues_filtered(limit=500)

    if not leagues:
        st.info("Aucune ligue disponible. Synchronise d'abord les ligues.")
        return

    league_options = {
        f"[{league['league_id']}] {league['name']} — {league['country_name']}": league["league_id"]
        for league in leagues
    }

    selected_league_label = st.selectbox(
        "Choisir une ligue pour le classement",
        list(league_options.keys()),
        key="standings_league_select",
    )

    selected_league_id = league_options[selected_league_label]
    seasons = list_league_seasons_by_league_id(selected_league_id)

    if not seasons:
        st.info("Aucune saison disponible pour cette ligue.")
        return

    season_options = {
        f"{season['season_year']} {'(courante)' if season['current'] else ''}": season["season_year"]
        for season in seasons
    }

    selected_season_label = st.selectbox(
        "Choisir une saison pour le classement",
        list(season_options.keys()),
        key="standings_season_select",
    )

    selected_season_year = season_options[selected_season_label]

    st.info(
        "Le classement dépend du coverage de la ligue et des limites de ton plan. "
        "Si rien ne remonte, essaie une autre saison."
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Synchroniser le classement", key="sync_standings_button"):
            try:
                with st.spinner("Synchronisation du classement..."):
                    result = sync_standings(
                        league_id=selected_league_id,
                        season_year=selected_season_year,
                        force_refresh=False,
                    )

                st.success(
                    f"Classement synchronisé depuis : {result['source']} — "
                    f"{result['saved_count']} ligne(s) récupérée(s)."
                )
            except RuntimeError as error:
                st.error("La synchronisation du classement a échoué.")
                st.code(str(error))
                st.warning(
                    "Ce n'est pas forcément un problème de code : ton plan Free "
                    "ou le coverage de la ligue peuvent limiter cette donnée."
                )

    with col2:
        if st.button("Forcer refresh classement", key="force_sync_standings_button"):
            try:
                with st.spinner("Refresh du classement depuis API-Football..."):
                    result = sync_standings(
                        league_id=selected_league_id,
                        season_year=selected_season_year,
                        force_refresh=True,
                    )

                st.warning(
                    f"Classement rafraîchi depuis : {result['source']} — "
                    f"{result['saved_count']} ligne(s) récupérée(s)."
                )
            except RuntimeError as error:
                st.error("Le refresh du classement a échoué.")
                st.code(str(error))
                st.warning(
                    "Essaie une autre saison ou vérifie le coverage standings."
                )

    standings = list_standings_by_league_season(
        league_id=selected_league_id,
        season_year=selected_season_year,
    )

    st.write(
        f"{len(standings)} ligne(s) de classement affichée(s)."
    )

    if not standings:
        st.info(
            "Aucun classement en base pour cette sélection. Lance une "
            "synchronisation ou choisis une autre saison."
        )
        return

    groups = sorted(
        {
            standing["group_name"] or "Classement"
            for standing in standings
        }
    )

    selected_group = st.selectbox(
        "Groupe / classement",
        groups,
        key="standings_group_filter",
    )

    filtered_standings = [
        standing
        for standing in standings
        if (standing["group_name"] or "Classement") == selected_group
    ]

    table_rows = []

    for standing in filtered_standings:
        table_rows.append(
            {
                "Pos": standing["position"],
                "Équipe": standing["team_name"],
                "Pts": standing["points"],
                "MJ": standing["all_played"],
                "V": standing["all_win"],
                "N": standing["all_draw"],
                "D": standing["all_lose"],
                "BP": standing["all_goals_for"],
                "BC": standing["all_goals_against"],
                "Diff": standing["goals_diff"],
                "Forme": standing["form"],
                "Statut": standing["status"],
            }
        )

    st.dataframe(
        table_rows,
        use_container_width=True,
        hide_index=True,
    )

    standing_options = {
        f"{standing['position']}. {standing['team_name']}": standing["id"]
        for standing in filtered_standings
    }

    selected_standing_label = st.selectbox(
        "Sélectionner une équipe pour voir le détail",
        list(standing_options.keys()),
        key="standing_detail_select",
    )

    selected_standing_id = standing_options[selected_standing_label]
    standing_detail = get_standing_by_id(selected_standing_id)

    if standing_detail:
        col_logo, col_info, col_stats = st.columns([1, 3, 3])

        with col_logo:
            if standing_detail.get("team_logo"):
                st.image(standing_detail["team_logo"], width=90)

        with col_info:
            st.markdown(f"### {standing_detail['team_name']}")
            st.write(f"**Position :** {standing_detail['position']}")
            st.write(f"**Points :** {standing_detail['points']}")
            st.write(f"**Forme :** {standing_detail['form'] or 'N/A'}")
            st.write(f"**Statut :** {standing_detail['status'] or 'N/A'}")
            st.write(
                f"**Description :** "
                f"{standing_detail['description'] or 'N/A'}"
            )

        with col_stats:
            st.write("**Global**")
            st.write(
                f"{standing_detail['all_played']} match(s), "
                f"{standing_detail['all_win']} victoire(s), "
                f"{standing_detail['all_draw']} nul(s), "
                f"{standing_detail['all_lose']} défaite(s)"
            )
            st.write(
                f"Buts : {standing_detail['all_goals_for']} pour / "
                f"{standing_detail['all_goals_against']} contre"
            )
            st.write(f"Différence : {standing_detail['goals_diff']}")

        with st.expander("Voir le JSON brut de la ligne de classement"):
            st.code(
                json.dumps(standing_detail["raw"], indent=2, ensure_ascii=False),
                language="json",
            )
            
def render_head_to_head_page() -> None:
    st.subheader("Comparaison Head-to-Head")

    st.write(
        "Cette page permet de comparer deux équipes et de récupérer "
        "leurs confrontations directes."
    )

    leagues = list_leagues_filtered(limit=500)

    if not leagues:
        st.info("Aucune ligue disponible. Synchronise d'abord les ligues.")
        return

    league_options = {
        f"[{league['league_id']}] {league['name']} — {league['country_name']}": league["league_id"]
        for league in leagues
    }

    selected_league_label = st.selectbox(
        "Choisir une ligue pour filtrer les équipes",
        list(league_options.keys()),
        key="h2h_league_select",
    )

    selected_league_id = league_options[selected_league_label]
    seasons = list_league_seasons_by_league_id(selected_league_id)

    if not seasons:
        st.info("Aucune saison disponible pour cette ligue.")
        return

    season_options = {
        f"{season['season_year']} {'(courante)' if season['current'] else ''}": season["season_year"]
        for season in seasons
    }

    selected_season_label = st.selectbox(
        "Choisir une saison pour filtrer les équipes",
        list(season_options.keys()),
        key="h2h_season_select",
    )

    selected_season_year = season_options[selected_season_label]

    league_teams = list_teams_by_league_season(
        league_id=selected_league_id,
        season_year=selected_season_year,
    )

    if not league_teams:
        st.info(
            "Aucune équipe disponible pour cette ligue/saison. "
            "Va d'abord dans l'onglet Équipes et synchronise les équipes."
        )
        return

    team_options = {
        f"[{team['team_id']}] {team['name']}": team["team_id"]
        for team in league_teams
    }

    col_team_a, col_team_b, col_last = st.columns([2, 2, 1])

    with col_team_a:
        selected_team_a_label = st.selectbox(
            "Équipe A",
            list(team_options.keys()),
            key="h2h_team_a",
        )

    with col_team_b:
        selected_team_b_label = st.selectbox(
            "Équipe B",
            list(team_options.keys()),
            key="h2h_team_b",
        )

    with col_last:
        last = st.number_input(
            "Nombre max",
            min_value=1,
            max_value=50,
            value=10,
            step=1,
            key="h2h_last",
            disabled=not settings.API_FOOTBALL_ENABLE_H2H_LAST_PARAMETER,
        )

        if not settings.API_FOOTBALL_ENABLE_H2H_LAST_PARAMETER:
            st.caption("Désactivé avec le plan Free.")

    team_a_id = team_options[selected_team_a_label]
    team_b_id = team_options[selected_team_b_label]

    if team_a_id == team_b_id:
        st.warning("Choisis deux équipes différentes.")
        return

    col_sync, col_force = st.columns(2)

    with col_sync:
        if st.button("Synchroniser head-to-head", key="sync_h2h_button"):
            try:
                with st.spinner("Synchronisation du head-to-head..."):
                    result = sync_head_to_head(
                        team_a_id=team_a_id,
                        team_b_id=team_b_id,
                        last=int(last) if settings.API_FOOTBALL_ENABLE_H2H_LAST_PARAMETER else None,
                        force_refresh=False,
                    )

                st.success(
                    f"Head-to-head synchronisé depuis : {result['source']} — "
                    f"{result['saved_count']} match(s) récupéré(s)."
                )
            except RuntimeError as error:
                st.error("La synchronisation du head-to-head a échoué.")
                st.code(str(error))

    with col_force:
        if st.button("Forcer refresh head-to-head", key="force_sync_h2h_button"):
            try:
                with st.spinner("Refresh du head-to-head depuis API-Football..."):
                    result = sync_head_to_head(
                        team_a_id=team_a_id,
                        team_b_id=team_b_id,
                        last=int(last) if settings.API_FOOTBALL_ENABLE_H2H_LAST_PARAMETER else None,
                        force_refresh=True,
                    )

                st.warning(
                    f"Head-to-head rafraîchi depuis : {result['source']} — "
                    f"{result['saved_count']} match(s) récupéré(s)."
                )
            except RuntimeError as error:
                st.error("Le refresh du head-to-head a échoué.")
                st.code(str(error))

    summary = get_head_to_head_summary(team_a_id, team_b_id)
    matches = list_head_to_head_matches(team_a_id, team_b_id, limit=int(last))

    st.markdown("### Résumé des confrontations")

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Matchs joués", summary["played_matches"])
    col2.metric("Victoires A", summary["team_a_wins"])
    col3.metric("Victoires B", summary["team_b_wins"])
    col4.metric("Nuls", summary["draws"])
    col5.metric("Buts/match", summary["average_goals"])

    if not matches:
        st.info(
            "Aucune confrontation en base pour ces deux équipes. "
            "Clique sur Synchroniser head-to-head."
        )
        return

    st.markdown("### Dernières confrontations")

    match_options = {}

    for match in matches:
        score = (
            f"{match['home_goals']} - {match['away_goals']}"
            if match["home_goals"] is not None and match["away_goals"] is not None
            else "score indisponible"
        )

        label = (
            f"{match['fixture_date']} | "
            f"{match['home_team_name']} {score} {match['away_team_name']}"
        )

        match_options[label] = match["id"]

        with st.container(border=True):
            col_home, col_score, col_away, col_meta = st.columns([3, 2, 3, 3])

            with col_home:
                if match.get("home_team_logo"):
                    st.image(match["home_team_logo"], width=50)
                st.markdown(f"**{match['home_team_name']}**")

            with col_score:
                st.markdown(f"### {score}")
                st.write(f"Statut : {match['status_short'] or 'N/A'}")

            with col_away:
                if match.get("away_team_logo"):
                    st.image(match["away_team_logo"], width=50)
                st.markdown(f"**{match['away_team_name']}**")

            with col_meta:
                st.write(f"**Compétition :** {match['league_name'] or 'N/A'}")
                st.write(f"**Saison :** {match['season_year'] or 'N/A'}")
                st.write(f"**Date :** {match['fixture_date'] or 'N/A'}")
                st.write(f"**Stade :** {match['venue_name'] or 'N/A'}")

    selected_match_label = st.selectbox(
        "Voir le JSON brut d'une confrontation",
        list(match_options.keys()),
        key="h2h_match_detail",
    )

    selected_h2h_match_id = match_options[selected_match_label]
    match_detail = get_head_to_head_match_by_id(selected_h2h_match_id)

    if match_detail:
        with st.expander("JSON brut de la confrontation sélectionnée"):
            st.code(
                json.dumps(match_detail["raw"], indent=2, ensure_ascii=False),
                language="json",
            )

def main() -> None:
    initialize_app()
    render_header()
    render_sidebar()

    tab_dashboard, tab_leagues, tab_teams, tab_fixtures, tab_standings, tab_h2h, tab_admin = st.tabs(
        [
            "🏠 Dashboard",
            "🏆 Ligues",
            "👥 Équipes",
            "📅 Matchs",
            "📊 Classements",
            "⚔️ Head-to-Head",
            "⚙️ Admin",
        ]
    )

    with tab_dashboard:
        render_dashboard_home()

    with tab_leagues:
        render_league_explorer()

    with tab_teams:
        render_team_explorer()

    with tab_fixtures:
        render_fixture_explorer()

    with tab_standings:
        render_standings_explorer()
    
    with tab_h2h:
        render_head_to_head_page()

    with tab_admin:
        render_admin_page()

if __name__ == "__main__":
    main()