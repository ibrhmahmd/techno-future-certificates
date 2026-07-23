"""
Tab 3 — Certificate Registry.
Streamlit UI for browsing, filtering, exporting, and re-downloading certificates.
"""

import datetime
import logging

import altair as alt
import pandas as pd
import streamlit as st

from core.config import TRACK_LOGOS
from core.database import get_certificate, list_certificates
from core.renderer import build_html_from_db, render_pdf
from core.utils import build_download_filename

log = logging.getLogger(__name__)


def _metrics_row(df: pd.DataFrame) -> None:
    """Render top-level KPI cards."""
    total = len(df)
    today = datetime.date.today()
    month_df = df[df["Issue Date"].str.startswith(today.strftime("%Y-%m"))]
    this_month = len(month_df)

    if "Track / Course" in df.columns and not df["Track / Course"].empty:
        top_track = df["Track / Course"].value_counts().idxmax()
    else:
        top_track = "\u2014"

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Certificates", total)
    c2.metric("Issued This Month", this_month)
    c3.metric("Most Popular Track", top_track)


def _track_chart(df: pd.DataFrame) -> None:
    """Altair bar chart of certificates per track."""
    if "Track / Course" not in df.columns:
        return
    counts = df["Track / Course"].value_counts().reset_index()
    counts.columns = ["Track", "Count"]

    chart = (
        alt.Chart(counts)
        .mark_bar(color="#006a61", cornerRadiusEnd=4)
        .encode(
            x=alt.X("Count:Q", title="Certificates"),
            y=alt.Y("Track:N", title=None, sort="-x"),
            tooltip=["Track", "Count"],
        )
        .properties(height=max(200, len(counts) * 28))
    )
    st.altair_chart(chart, width="stretch")


def render() -> None:
    st.subheader("Certificate Registry")

    all_certs = list_certificates()
    if not all_certs:
        st.info(
            "No certificates generated yet. "
            "Issued certificates will appear here automatically."
        )
        return

    df = pd.DataFrame(all_certs)
    rename_dict = {
        "cert_id": "Certificate ID",
        "student_name": "Student Name",
        "course_name": "Track / Course",
        "level": "Level",
        "issue_date": "Issue Date",
        "instructor": "Instructor",
        "director": "Director",
        "created_at": "Database Created",
    }
    if "branch" in df.columns:
        rename_dict["branch"] = "Branch"
    elif "center" in df.columns:
        rename_dict["center"] = "Branch"

    df.rename(columns=rename_dict, inplace=True)

    _metrics_row(df)

    st.markdown("---")

    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search_query = st.text_input(
            "Filter by Student Name or ID", placeholder="Search..."
        )
    with col_filter:
        track_filter = st.selectbox(
            "Filter Track", ["All Tracks"] + list(TRACK_LOGOS.keys())
        )

    filtered_df = df.copy()
    if search_query.strip():
        q = search_query.strip().lower()
        filtered_df = filtered_df[
            filtered_df["Student Name"].str.lower().str.contains(q)
            | filtered_df["Certificate ID"].str.lower().str.contains(q)
        ]
    if track_filter != "All Tracks":
        filtered_df = filtered_df[filtered_df["Track / Course"] == track_filter]

    _track_chart(filtered_df)

    st.markdown("---")

    for _, row in filtered_df.iterrows():
        cert_id = row["Certificate ID"]
        with st.expander(f"{row['Student Name']}  \u2014  `{cert_id}`"):
            mc1, mc2 = st.columns([3, 1])
            with mc1:
                st.markdown(f"""
                - **Track**: {row['Track / Course']}
                - **Level**: {row['Level']}
                - **Date**: {row['Issue Date']}
                - **Branch**: {row.get('Branch', '\u2014')}
                - **Instructor**: {row['Instructor']}
                - **Director**: {row['Director']}
                """)
            with mc2:
                if st.button("View Certificate", key=f"view_{cert_id}"):
                    cert_data = get_certificate(cert_id)
                    if cert_data:
                        cert_html = build_html_from_db(cert_data)
                        st.iframe(cert_html, height=500)

                if st.button("Download PDF", key=f"dl_{cert_id}"):
                    cert_data = get_certificate(cert_id)
                    if cert_data:
                        cert_html = build_html_from_db(cert_data)
                        with st.spinner("Generating PDF..."):
                            try:
                                pdf_bytes = render_pdf(cert_html)
                                fn = build_download_filename(
                                    cert_data["student_name"],
                                    cert_data["course_name"],
                                    "pdf",
                                )
                                st.download_button(
                                    label=f"Save {fn}",
                                    data=pdf_bytes,
                                    file_name=fn,
                                    mime="application/pdf",
                                    key=f"save_{cert_id}",
                                )
                            except Exception as exc:
                                log.warning("PDF render failed for %s: %s", cert_id, exc)
                                st.warning("PDF engine unavailable.")

    st.markdown("---")
    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Export Registry CSV",
        data=csv,
        file_name=f"certificates_registry_{datetime.date.today()}.csv",
        mime="text/csv",
    )
