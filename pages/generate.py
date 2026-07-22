"""
Tab 1 — Generate Certificate.
Streamlit UI for the certificate creation form, live preview, and downloads.
"""

import datetime

import streamlit as st

from core.config import LEVEL_LABELS, TRACK_DATA_ATTR, TRACK_DEFAULT_COLORS, TRACK_LOGOS
from core.database import save_certificate
from core.renderer import build_html, render_pdf
from core.utils import build_download_filename, generate_cert_id


def render() -> None:
    col_form, col_preview = st.columns([1, 1], gap="large")

    with col_form:
        st.subheader("Certificate Details")
        with st.form("cert_form", clear_on_submit=False):
            student_name = st.text_input(
                "Student Full Name *", placeholder="Ahmed Hassan Ali"
            )
            c1, c2 = st.columns(2)
            with c1:
                course_name = st.selectbox("Course / Track *", list(TRACK_LOGOS.keys()))
                branch = st.text_input("Branch *", value="Main Branch")
                instructor = st.text_input(
                    "Instructor Name *", value="Ms. Sara Mahmoud"
                )
            with c2:
                level = st.selectbox("Level *", list(LEVEL_LABELS.keys()))
                cert_date = st.date_input(
                    "Completion Date *", value=datetime.date.today()
                )
                director = st.text_input(
                    "Academic Director *", value="Mr. Ibrahim Ahmed"
                )

            st.markdown("---")
            st.subheader("Accent Color")
            color_mode = st.radio(
                "Color Mode",
                ["Original Theme", "Custom Color"],
                horizontal=True,
                label_visibility="collapsed",
            )
            custom_accent_hex = None
            if color_mode == "Custom Color":
                default_track_attr = TRACK_DATA_ATTR.get(course_name, "html")
                default_color = TRACK_DEFAULT_COLORS.get(
                    default_track_attr, ("#006a61", "#89f5e7")
                )[0]
                custom_accent_hex = st.color_picker(
                    "Accent Color",
                    value=default_color,
                    label_visibility="collapsed",
                )

            cert_id = generate_cert_id(course_name, cert_date)

            st.markdown("---")
            st.metric("Generated Certificate ID", cert_id)

            submitted = st.form_submit_button(
                "Generate & Save Certificate",
                type="primary",
                use_container_width=True,
            )

    with col_preview:
        st.subheader("Live Preview & Downloads")
        if submitted:
            if not student_name.strip():
                st.error("Please enter the student name before generating.")
            else:
                save_certificate(
                    cert_id=cert_id,
                    student_name=student_name.strip(),
                    course_name=course_name,
                    level=level,
                    issue_date=cert_date,
                    branch=branch.strip() or "Main Branch",
                    instructor=instructor.strip() or "Instructor",
                    director=director.strip() or "Academic Director",
                )
                st.success(f"Certificate saved to database! ID: **{cert_id}**")

                html_content = build_html(
                    student_name=student_name.strip(),
                    course_name=course_name,
                    level=level,
                    date=cert_date,
                    branch=branch.strip() or "Main Branch",
                    cert_id=cert_id,
                    instructor=instructor.strip() or "Instructor",
                    director=director.strip() or "Academic Director",
                    custom_accent=custom_accent_hex,
                    original_theme=(color_mode == "Original Theme"),
                )

                st.components.v1.html(html_content, height=520, scrolling=True)

                st.markdown("---")
                fn_html = build_download_filename(
                    student_name.strip(), course_name, "html"
                )
                fn_pdf = build_download_filename(
                    student_name.strip(), course_name, "pdf"
                )

                b1, b2 = st.columns(2)
                with b1:
                    st.download_button(
                        label="Download HTML File",
                        data=html_content,
                        file_name=fn_html,
                        mime="text/html",
                        use_container_width=True,
                    )
                with b2:
                    try:
                        pdf_bytes = render_pdf(html_content)
                        st.download_button(
                            label="Download Vector PDF",
                            data=pdf_bytes,
                            file_name=fn_pdf,
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True,
                        )
                    except Exception:
                        st.warning(
                            "Direct PDF engine unavailable. "
                            "Use HTML download or Ctrl+P to print."
                        )
        else:
            st.info(
                "Fill out the form on the left and click "
                "**Generate & Save Certificate** to view live preview and downloads."
            )
