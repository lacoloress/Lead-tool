"""Main Streamlit application entry point."""

import streamlit as st

st.set_page_config(
    page_title="Lead Tool",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    """Run the Lead Tool application."""
    from lead_tool.ui.pages import dashboard, import_csv, leads, search

    # Create page objects and store in session_state for use in switch_page
    if "pages" not in st.session_state:
        st.session_state.pages = {
            "dashboard": st.Page(dashboard.render, title="Dashboard", icon="📊", url_path="dashboard", default=True),
            "search": st.Page(search.render, title="Search Leads", icon="🔍", url_path="search"),
            "import": st.Page(import_csv.render, title="Import CSV", icon="📁", url_path="import"),
            "leads": st.Page(leads.render, title="My Leads", icon="👥", url_path="leads"),
        }

    p = st.session_state.pages
    pages = {
        "Dashboard": [p["dashboard"]],
        "Lead Generation": [p["search"], p["import"]],
        "Lead Management": [p["leads"]],
    }

    nav = st.navigation(pages)
    nav.run()


if __name__ == "__main__":
    main()
