"""My Leads page - US3 (export) + US4 (view details)."""

from io import StringIO

import polars as pl
import streamlit as st

from lead_tool.models import Tier
from lead_tool.services import LeadsService


def render() -> None:
    """Render the leads management page."""
    st.title("My Leads")

    service = LeadsService()
    all_leads = service.get_all()

    if not all_leads:
        st.info("No leads yet. Import a CSV or search for leads to get started.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Search Leads", use_container_width=True):
                st.switch_page(st.session_state.pages["search"])
        with col2:
            if st.button("📁 Import CSV", use_container_width=True):
                st.switch_page(st.session_state.pages["import"])
        return

    # Filters
    st.subheader("Filters")
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

    with filter_col1:
        tier_filter = st.selectbox(
            "Tier",
            options=["All"] + [t.value for t in Tier],
            index=0,
        )

    with filter_col2:
        score_range = st.slider(
            "Score Range",
            min_value=0,
            max_value=100,
            value=(0, 100),
        )

    with filter_col3:
        source_filter = st.selectbox(
            "Source",
            options=["All", "search", "csv_upload"],
            index=0,
        )

    with filter_col4:
        search_query = st.text_input(
            "Search",
            placeholder="Name or company...",
        )

    # Apply filters
    filtered_leads = all_leads

    if tier_filter != "All":
        filtered_leads = [lead for lead in filtered_leads if lead.analysis.tier.value == tier_filter]

    filtered_leads = [
        lead for lead in filtered_leads
        if score_range[0] <= lead.analysis.score <= score_range[1]
    ]

    if source_filter != "All":
        filtered_leads = [lead for lead in filtered_leads if lead.source == source_filter]

    if search_query:
        query_lower = search_query.lower()
        filtered_leads = [
            lead for lead in filtered_leads
            if query_lower in lead.name.lower() or query_lower in lead.company.lower()
        ]

    st.divider()

    # Header with count and export
    header_col1, header_col2 = st.columns([3, 1])

    with header_col1:
        st.caption(f"Showing {len(filtered_leads)} of {len(all_leads)} leads")

    with header_col2:
        # Export CSV
        if filtered_leads:
            csv_data = _leads_to_csv(filtered_leads)
            st.download_button(
                "📥 Export CSV",
                data=csv_data,
                file_name="leads_export.csv",
                mime="text/csv",
                use_container_width=True,
            )

    # Lead list
    if not filtered_leads:
        st.warning("No leads match the current filters.")
        return

    # Create dataframe for display
    df_data = [
        {
            "id": lead.id,
            "Name": lead.name,
            "Company": lead.company,
            "Position": lead.position,
            "Score": lead.analysis.score,
            "Tier": lead.analysis.tier.value,
            "Email": lead.email,
            "Source": lead.source,
        }
        for lead in filtered_leads
    ]

    # Display dataframe with selection
    event = st.dataframe(
        df_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": None,  # Hide ID column
            "Score": st.column_config.ProgressColumn(
                "Score",
                min_value=0,
                max_value=100,
                format="%d",
            ),
        },
        on_select="rerun",
        selection_mode="single-row",
    )

    # Lead details panel
    selected_rows = event.selection.rows if event.selection else []

    if selected_rows:
        selected_idx = selected_rows[0]
        selected_lead = filtered_leads[selected_idx]

        st.divider()
        st.subheader("Lead Details")

        detail_col1, detail_col2 = st.columns(2)

        with detail_col1:
            st.markdown(f"### {selected_lead.name}")
            st.markdown(f"**{selected_lead.position}** @ {selected_lead.company}")
            st.markdown(f"📍 {selected_lead.location}" if selected_lead.location else "")

            st.divider()

            # Score display
            score_color = _get_score_color(selected_lead.analysis.score)
            st.markdown(f"**Score:** :{score_color}[{selected_lead.analysis.score}/100]")
            st.markdown(f"**Tier:** {selected_lead.analysis.tier.value}")
            st.markdown(f"**Category:** {selected_lead.analysis.category.value}")
            st.markdown(f"**Qualified:** {'✅ Yes' if selected_lead.analysis.qualified else '❌ No'}")

        with detail_col2:
            st.markdown("#### Contact Information")

            if selected_lead.email:
                verified_badge = " ✅" if selected_lead.email_verified else ""
                st.markdown(f"📧 {selected_lead.email}{verified_badge}")

            if selected_lead.phone:
                st.markdown(f"📞 {selected_lead.phone}")

            if selected_lead.linkedin_url:
                st.markdown(f"🔗 [LinkedIn]({selected_lead.linkedin_url})")

            if selected_lead.company_website:
                st.markdown(f"🌐 [{selected_lead.company_website}]({selected_lead.company_website})")

            st.divider()

            st.markdown("#### Scoring Insights")
            if selected_lead.analysis.insights:
                for insight in selected_lead.analysis.insights:
                    st.markdown(f"• {insight}")
            else:
                st.caption("No specific scoring factors detected")

        # Delete button
        st.divider()
        if st.button("🗑️ Delete Lead", type="secondary"):
            service.delete(selected_lead.id)
            st.success("Lead deleted")
            st.rerun()


def _leads_to_csv(leads: list) -> str:
    """Convert leads to CSV string."""
    data = [
        {
            "name": lead.name,
            "email": lead.email,
            "company": lead.company,
            "position": lead.position,
            "linkedin_url": lead.linkedin_url,
            "company_website": lead.company_website,
            "location": lead.location,
            "phone": lead.phone,
            "score": lead.analysis.score,
            "tier": lead.analysis.tier.value,
            "category": lead.analysis.category.value,
        }
        for lead in leads
    ]

    df = pl.DataFrame(data)
    buffer = StringIO()
    df.write_csv(buffer)
    return buffer.getvalue()


def _get_score_color(score: int) -> str:
    """Get color name for score."""
    if score >= 80:
        return "green"
    if score >= 60:
        return "blue"
    if score >= 40:
        return "orange"
    return "red"
