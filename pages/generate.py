"""
Tab 1 — Generate Certificate.
Streamlit UI for the certificate creation form, live preview, and downloads.
"""

import datetime

import streamlit as st

from core.config import LEVEL_LABELS, TRACK_DATA_ATTR, TRACK_DEFAULT_COLORS, TRACK_LOGOS
from core.database import save_certificate
from core.renderer import build_html, pdf_engine_status, render_pdf
from core.utils import build_download_filename, generate_cert_id


def _render_preview(
    html_content: str,
    student_name: str,
    course_name: str,
    cert_id: str,
    cert_date: datetime.date,
    level: str,
    branch: str,
    instructor: str,
    director: str,
) -> None:
    """Confirm card, preview with zoom, and download buttons."""
    with st.expander("Review before saving", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"**{student_name}**")
            st.caption(f"{course_name}")
        with c2:
            st.markdown(f"Level: **{level}**")
            st.caption(f"Date: {cert_date}")
        with c3:
            st.markdown(f"Branch: **{branch}**")
            st.caption(f"Instructor: {instructor}")

    zoom = st.slider("Preview zoom", 50, 100, 75, step=5, key="preview_zoom")

    scaled_height = int(520 * (zoom / 100))
    st.iframe(html_content, height=scaled_height)

    st.markdown("---")
    fn_html = build_download_filename(student_name, course_name, "html")
    fn_pdf = build_download_filename(student_name, course_name, "pdf")

    b1, b2 = st.columns(2)
    with b1:
        st.download_button(
            label="Download HTML",
            data=html_content,
            file_name=fn_html,
            mime="text/html",
            width="stretch",
        )
    with b2:
        with st.spinner("Generating PDF..."):
            try:
                pdf_bytes = render_pdf(html_content)
                st.download_button(
                    label="Download PDF",
                    data=pdf_bytes,
                    file_name=fn_pdf,
                    mime="application/pdf",
                    type="primary",
                    width="stretch",
                )
            except Exception:
                status = pdf_engine_status()
                engines = [k for k, v in status.items() if v]
                missing = [k for k, v in status.items() if not v]
                msg = "PDF engine unavailable."
                if engines:
                    msg += f" Working: {', '.join(engines)}."
                if missing:
                    msg += f" Missing: {', '.join(missing)}."
                st.warning(msg + " Use HTML download or Ctrl+P to print.")


def render() -> None:
    col_form, col_preview = st.columns([2, 3], gap="large")

    with col_form:
        st.subheader("Certificate Details")
        with st.form("cert_form", clear_on_submit=False):
            student_name = st.text_input(
                "Student Full Name *",
                placeholder="Ahmed Hassan Ali",
                help="Enter the student's full legal name as it should appear on the certificate",
            )
            c1, c2 = st.columns(2)
            with c1:
                course_name = st.selectbox(
                    "Course / Track *",
                    list(TRACK_LOGOS.keys()),
                    help="Select the course or robotics track",
                )
                branch = st.text_input(
                    "Branch *",
                    value="Main Branch",
                    help="Center or branch location",
                )
                instructor = st.text_input(
                    "Instructor Name *",
                    value="Ms. Sara Mahmoud",
                    help="Name of the completing instructor",
                )
            with c2:
                level = st.selectbox(
                    "Level *",
                    list(LEVEL_LABELS.keys()),
                    help="Junior, Intermediate, or Advanced",
                )
                cert_date = st.date_input(
                    "Completion Date *",
                    value=datetime.date.today(),
                    help="Date the student completed the course",
                )
                director = st.text_input(
                    "Academic Director *",
                    value="Mr. Ibrahim Ahmed",
                    help="Academic director who signs the certificate",
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
            st.metric("Certificate ID", cert_id)

            submitted = st.form_submit_button(
                "Generate & Save Certificate",
                type="primary",
                width="stretch",
            )

    with col_preview:
        st.subheader("Live Preview")
        if submitted:
            if not student_name.strip():
                st.error("Please enter the student name before generating.")
                return

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
            st.toast(f"Certificate saved — {cert_id}", icon="\u2705")

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

            _render_preview(
                html_content=html_content,
                student_name=student_name.strip(),
                course_name=course_name,
                cert_id=cert_id,
                cert_date=cert_date,
                level=level,
                branch=branch.strip() or "Main Branch",
                instructor=instructor.strip() or "Instructor",
                director=director.strip() or "Academic Director",
            )
        else:
            st.info(
                "Fill out the form and click **Generate & Save Certificate** "
                "to see a live preview and download options."
            )
