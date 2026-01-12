"""Dashboard page - Quick overview of lead database."""

import streamlit as st

from lead_tool.services import LeadsService


def render() -> None:
    """Render the dashboard page."""
    st.title("Dashboard")

    service = LeadsService()
    leads = service.get_all()

    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)

    total = len(leads)
    qualified = sum(1 for lead in leads if lead.analysis.qualified)
    avg_score = (
        round(sum(lead.analysis.score for lead in leads) / total) if total > 0 else 0
    )
    verified = sum(1 for lead in leads if lead.email_verified)

    with col1:
        st.metric("Total Leads", total)
    with col2:
        st.metric("Qualified", qualified, delta=f"{qualified/total*100:.0f}%" if total > 0 else None)
    with col3:
        st.metric("Avg Score", avg_score)
    with col4:
        st.metric("Verified Emails", verified)

    st.divider()

    # Two columns: Tier distribution and Recent leads
    col_chart, col_recent = st.columns(2)

    with col_chart:
        st.subheader("Tier Distribution")
        if leads:
            tier_counts = {}
            for lead in leads:
                tier = lead.analysis.tier.value
                tier_counts[tier] = tier_counts.get(tier, 0) + 1

            st.bar_chart(tier_counts)
        else:
            st.info("No leads yet. Import or search for leads to see distribution.")

    with col_recent:
        st.subheader("Recent Leads")
        if leads:
            recent = sorted(leads, key=lambda x: x.created_at, reverse=True)[:10]
            data = [
                {
                    "Name": lead.name,
                    "Company": lead.company,
                    "Score": lead.analysis.score,
                    "Tier": lead.analysis.tier.value,
                }
                for lead in recent
            ]
            st.dataframe(data, use_container_width=True, hide_index=True)
        else:
            st.info("No leads yet.")

    st.divider()

    # Quick actions
    st.subheader("Quick Actions")
    col_action1, col_action2, col_action3 = st.columns(3)

    with col_action1:
        if st.button("🔍 Search New Leads", use_container_width=True):
            st.switch_page(st.session_state.pages["search"])

    with col_action2:
        if st.button("📁 Import CSV", use_container_width=True):
            st.switch_page(st.session_state.pages["import"])

    with col_action3:
        if st.button("👥 View All Leads", use_container_width=True):
            st.switch_page(st.session_state.pages["leads"])
