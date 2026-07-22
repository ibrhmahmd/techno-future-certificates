"""
Tab 2 — Validate Certificate.
Streamlit UI for certificate lookup and authenticity verification.
"""

import datetime

import streamlit as st

from core.database import get_certificate
from core.renderer import build_html


def render(verify_id: str | None = None) -> None:
    st.subheader("Certificate Authenticity Verification")
    st.caption("Verify official Techno Future certificates by ID")

    search_id_input = st.text_input(
        "Enter Certificate ID",
        value=verify_id or "",
        placeholder="e.g. TKTF-HTM-20260722-A3F1",
    )

    if search_id_input.strip():
        cert_data = get_certificate(search_id_input.strip())
        if cert_data:
            st.success("OFFICIAL CERTIFICATE VERIFIED — AUTHENTIC")

            v1, v2 = st.columns([1, 2], gap="medium")
            with v1:
                branch_val = cert_data.get("branch") or cert_data.get(
                    "center", "Main Branch"
                )
                st.markdown(f"""
                ### Certificate Details
                - **Certificate ID**: `{cert_data["cert_id"]}`
                - **Student Name**: **{cert_data["student_name"]}**
                - **Track / Course**: {cert_data["course_name"]}
                - **Level**: {cert_data["level"]}
                - **Issue Date**: {cert_data["issue_date"]}
                - **Branch**: {branch_val}
                - **Instructor**: {cert_data["instructor"]}
                - **Academic Director**: {cert_data["director"]}
                - **Record Created**: `{cert_data["created_at"]}`
                """)

            with v2:
                try:
                    dt = datetime.datetime.strptime(
                        cert_data["issue_date"], "%Y-%m-%d"
                    ).date()
                except Exception:
                    dt = datetime.date.today()

                branch_val = cert_data.get("branch") or cert_data.get(
                    "center", "Main Branch"
                )
                cert_html = build_html(
                    student_name=cert_data["student_name"],
                    course_name=cert_data["course_name"],
                    level=cert_data["level"],
                    date=dt,
                    branch=branch_val,
                    cert_id=cert_data["cert_id"],
                    instructor=cert_data["instructor"],
                    director=cert_data["director"],
                )
                st.components.v1.html(cert_html, height=500, scrolling=True)
        else:
            st.error(
                f"Certificate ID **{search_id_input.strip()}** was not found "
                f"in the official registry."
            )
