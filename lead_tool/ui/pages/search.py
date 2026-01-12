"""Search Leads page - US1: Search for new leads via LinkedIn."""

import streamlit as st

from lead_tool.config import settings
from lead_tool.models import CompanySize, FundingStage, Industry, SearchParams
from lead_tool.services import LeadsService, ScraperService


def render() -> None:
    """Render the search leads page."""
    st.title("Search for Leads")
    st.caption("Find targeted B2B leads based on your criteria")

    # Check if Apify is configured
    if not settings.apify_api_token or not settings.apify_actor_id:
        st.warning(
            "Apify is not configured. Please set APIFY_API_TOKEN and APIFY_ACTOR_ID "
            "in your .env file to enable lead search."
        )

    # Search form
    with st.form("search_form"):
        col1, col2 = st.columns(2)

        with col1:
            job_titles = st.text_input(
                "Job Titles",
                placeholder="CEO, CTO, Founder",
                help="Enter job titles separated by commas",
            )

            industries = st.multiselect(
                "Industries",
                options=[i.value.replace("_", " ").title() for i in Industry],
                help="Select target industries",
            )

            company_sizes = st.multiselect(
                "Company Size",
                options=[s.value for s in CompanySize],
                help="Select company size ranges",
            )

        with col2:
            locations = st.text_input(
                "Locations",
                placeholder="United States, Canada, UK",
                help="Enter locations separated by commas",
            )

            funding_stages = st.multiselect(
                "Funding Stage",
                options=[f.value.replace("_", " ").title() for f in FundingStage],
                help="Select funding stages",
            )

            number_of_leads = st.slider(
                "Number of Leads",
                min_value=50,
                max_value=5000,
                value=100,
                step=50,
                help="How many leads to fetch",
            )

        submitted = st.form_submit_button(
            "🔍 Start Search",
            use_container_width=True,
            type="primary",
            disabled=not settings.apify_api_token or not settings.apify_actor_id,
        )

    if submitted:
        # Validate at least one criterion
        has_criteria = bool(job_titles.strip() or locations.strip() or industries)

        if not has_criteria:
            st.error("Please enter at least one search criterion (Job Titles, Locations, or Industries)")
        else:
            _run_search(
                job_titles=job_titles,
                locations=locations,
                industries=industries,
                company_sizes=company_sizes,
                funding_stages=funding_stages,
                number_of_leads=number_of_leads,
            )


def _run_search(
    job_titles: str,
    locations: str,
    industries: list[str],
    company_sizes: list[str],
    funding_stages: list[str],
    number_of_leads: int,
) -> None:
    """Execute the search and display results."""
    # Parse inputs
    job_titles_list = [t.strip() for t in job_titles.split(",") if t.strip()]
    locations_list = [loc.strip() for loc in locations.split(",") if loc.strip()]

    # Map display values back to enum values
    industry_map = {i.value.replace("_", " ").title(): i for i in Industry}
    size_map = {s.value: s for s in CompanySize}
    funding_map = {f.value.replace("_", " ").title(): f for f in FundingStage}

    params = SearchParams(
        job_titles=job_titles_list,
        locations=locations_list,
        industries=[industry_map[i] for i in industries if i in industry_map],
        company_sizes=[size_map[s] for s in company_sizes if s in size_map],
        funding_stages=[funding_map[f] for f in funding_stages if f in funding_map],
        number_of_leads=number_of_leads,
    )

    # Show search parameters
    with st.expander("Search Parameters", expanded=False):
        st.json({
            "job_titles": params.job_titles,
            "locations": params.locations,
            "industries": [i.value for i in params.industries],
            "company_sizes": [s.value for s in params.company_sizes],
            "funding_stages": [f.value for f in params.funding_stages],
            "number_of_leads": params.number_of_leads,
        })

    # Execute search with progress indicator
    with st.status("Searching for leads...", expanded=True) as status:
        st.write("Connecting to Apify actor...")

        try:
            scraper = ScraperService()
            st.write("Running search query...")

            leads = scraper.search(params)

            if not leads:
                status.update(label="No leads found", state="complete")
                st.warning("No leads were found matching your criteria. Try broadening your search.")
                return

            st.write(f"Found {len(leads)} leads. Saving to database...")

            # Save leads to database
            leads_service = LeadsService()
            leads_service.add_many(leads)

            status.update(label=f"Found {len(leads)} leads!", state="complete")

        except Exception as e:
            status.update(label="Search failed", state="error")
            st.error(f"An error occurred during search: {e}")
            return

    # Show results summary
    st.success(f"Successfully imported {len(leads)} leads!")

    # Display preview of results
    st.subheader("Results Preview")

    preview_data = [
        {
            "Name": lead.name,
            "Company": lead.company,
            "Position": lead.position,
            "Score": lead.analysis.score,
            "Tier": lead.analysis.tier.value,
        }
        for lead in leads[:20]
    ]

    st.dataframe(preview_data, use_container_width=True, hide_index=True)

    if len(leads) > 20:
        st.caption(f"Showing 20 of {len(leads)} leads")

    # Navigation button
    if st.button("👥 View All Leads", use_container_width=True):
        st.switch_page(st.session_state.pages["leads"])
