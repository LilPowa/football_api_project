import json

import streamlit as st

from app.database import init_db
from app.repositories.api_cache_repository import count_cache_entries
from app.repositories.football_repository import (
    count_countries,
    count_fixture_statistics,
    count_fixtures,
    count_league_seasons,
    count_leagues,
    count_standings,
    count_teams,
    get_fixture_by_id,
    get_fixture_statistics_as_comparison,
    get_league_by_id,
    get_standing_by_id,
    list_all_countries,
    list_fixture_teams_filter,
    list_fixtures_filtered,
    list_league_seasons_by_league_id,
    list_leagues_filtered,
    list_standings_by_league_season,
    list_teams_by_league_season,
)
from app.services.sync_service import (
    sync_countries,
    sync_fixture_statistics,
    sync_fixtures,
    sync_leagues,
    sync_standings,
    sync_teams,
)

APP_VERSION = "0.2.0"


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

    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)

    col1.metric("Pays", count_countries())
    col2.metric("Ligues", count_leagues())
    col3.metric("Saisons", count_league_seasons())
    col4.metric("Équipes", count_teams())
    col5.metric("Matchs", count_fixtures())
    col6.metric("Stats matchs", count_fixture_statistics())
    col7.metric("Classements", count_standings())
    col8.metric("Cache API", count_cache_entries())

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

        render_fixture_statistics_section(
            fixture_id=selected_fixture_id,
            status_short=fixture_detail.get("status_short"),
        )

        with st.expander("Voir le JSON brut du match sélectionné"):
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

def main() -> None:
    initialize_app()
    render_header()
    render_sync_buttons()
    st.divider()
    render_metrics()
    st.divider()
    render_league_explorer()
    st.divider()
    render_team_explorer()
    st.divider()
    render_fixture_explorer()
    st.divider()
    render_standings_explorer()

if __name__ == "__main__":
    main()