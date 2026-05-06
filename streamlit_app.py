import json

import streamlit as st

from app.database import init_db
from app.repositories.api_cache_repository import count_cache_entries
from app.repositories.football_repository import (
    count_countries,
    count_league_seasons,
    count_leagues,
    get_league_by_id,
    list_all_countries,
    list_league_seasons_by_league_id,
    list_leagues_filtered,
)
from app.services.sync_service import sync_countries, sync_leagues


APP_VERSION = "0.1.0"


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

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Pays", count_countries())
    col2.metric("Ligues", count_leagues())
    col3.metric("Saisons", count_league_seasons())
    col4.metric("Entrées cache API", count_cache_entries())


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


def main() -> None:
    initialize_app()
    render_header()
    render_sync_buttons()
    st.divider()
    render_metrics()
    st.divider()
    render_league_explorer()


if __name__ == "__main__":
    main()