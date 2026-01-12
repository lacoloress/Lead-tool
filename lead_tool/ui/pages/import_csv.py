"""Import CSV page - US2: Upload existing leads from CSV."""

import uuid
from datetime import datetime, timezone
from io import StringIO

import polars as pl
import streamlit as st

from lead_tool.models import Lead
from lead_tool.services import CompanyAnalyzer, LeadsService


def render() -> None:
    """Render the import CSV page."""
    st.title("Import Leads from CSV")
    st.caption("Upload your existing lead list for analysis and scoring")

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        help="Upload a CSV file containing your leads",
    )

    # Expected format info
    with st.expander("Expected CSV Format"):
        st.markdown("""
        | Column | Required | Description |
        |--------|----------|-------------|
        | `name` | Yes | Full name of the lead |
        | `email` | No | Email address |
        | `company` | No | Company name |
        | `position` | No | Job title |
        | `linkedin_url` | No | LinkedIn profile URL |
        | `company_website` | No | Company website URL |
        | `location` | No | Geographic location |
        | `phone` | No | Phone number |
        | `industry` | No | Industry (for scoring) |
        | `company_size` | No | Company size (for scoring) |
        | `revenue` | No | Revenue (for scoring) |
        """)

    if uploaded_file is not None:
        try:
            # Read CSV
            content = StringIO(uploaded_file.getvalue().decode("utf-8"))
            df = pl.read_csv(content)

            st.divider()
            st.subheader("Preview")

            # Validation
            if "name" not in df.columns:
                st.error("CSV must contain a 'name' column")
                return

            # Stats
            col1, col2, col3 = st.columns(3)
            total_rows = len(df)
            valid_rows = df.filter(pl.col("name").is_not_null() & (pl.col("name") != "")).height
            error_rows = total_rows - valid_rows

            with col1:
                st.metric("Total Rows", total_rows)
            with col2:
                st.metric("Valid", valid_rows)
            with col3:
                st.metric("Errors", error_rows, delta_color="inverse" if error_rows > 0 else "off")

            # Preview with scoring
            analyzer = CompanyAnalyzer()
            preview_data = []

            for row in df.head(10).iter_rows(named=True):
                analysis = analyzer.analyze(
                    industry=row.get("industry", ""),
                    size=row.get("company_size", ""),
                    revenue=row.get("revenue", ""),
                )
                preview_data.append({
                    "Name": row.get("name", ""),
                    "Email": row.get("email", ""),
                    "Company": row.get("company", ""),
                    "Position": row.get("position", ""),
                    "Score": analysis.score,
                    "Tier": analysis.tier.value,
                })

            st.dataframe(preview_data, use_container_width=True, hide_index=True)

            if total_rows > 10:
                st.caption(f"Showing 10 of {total_rows} rows")

            # Import button
            st.divider()

            if st.button(
                f"📥 Import {valid_rows} Leads",
                type="primary",
                use_container_width=True,
                disabled=valid_rows == 0,
            ):
                with st.spinner("Importing leads..."):
                    leads_to_import = []

                    for row in df.iter_rows(named=True):
                        name = row.get("name", "")
                        if not name:
                            continue

                        analysis = analyzer.analyze(
                            industry=row.get("industry", ""),
                            size=row.get("company_size", ""),
                            revenue=row.get("revenue", ""),
                        )

                        lead = Lead(
                            id=str(uuid.uuid4()),
                            name=name,
                            email=row.get("email", "") or "",
                            company=row.get("company", "") or "",
                            position=row.get("position", "") or "",
                            linkedin_url=row.get("linkedin_url", "") or "",
                            company_website=row.get("company_website", "") or "",
                            location=row.get("location", "") or "",
                            phone=row.get("phone", "") or "",
                            analysis=analysis,
                            source="csv_upload",
                            email_verified=False,
                            created_at=datetime.now(timezone.utc),
                        )
                        leads_to_import.append(lead)

                    # Save to database
                    service = LeadsService()
                    service.add_many(leads_to_import)

                st.success(f"Successfully imported {len(leads_to_import)} leads!")
                st.balloons()

                if st.button("👥 View Imported Leads"):
                    st.switch_page("leads")

        except Exception as e:
            st.error(f"Error reading CSV: {e}")
