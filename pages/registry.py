"""
Tab 3 — Certificate Registry.
Streamlit UI for browsing, filtering, and exporting issued certificates.
"""

import datetime

import pandas as pd
import streamlit as st

from core.config import TRACK_LOGOS
from core.database import list_certificates


def render() -> None:
    st.subheader("Issued Certificates Database Registry")

    all_certs = list_certificates()
    if not all_certs:
        st.info(
            "No certificates generated yet. "
            "Issued certificates will automatically be stored here."
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

    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search_query = st.text_input(
            "Filter Registry by Student Name or ID", placeholder="Search..."
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

    st.dataframe(filtered_df, use_container_width=True)

    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Export Registry CSV",
        data=csv,
        file_name=f"certificates_registry_{datetime.date.today()}.csv",
        mime="text/csv",
    )
