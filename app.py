"""
Certificate Generator — Techno Kids, Techno Future
Gradio app: Generate, Validate, and Registry tabs.
All logic lives in core/. PDF via xhtml2pdf (no Playwright).
"""

import datetime
import logging
import tempfile
from pathlib import Path

import gradio as gr
import pandas as pd

from core.config import LEVEL_OPTIONS, TRACK_DATA_ATTR, TRACK_DEFAULT_COLORS, TRACK_LOGOS
from core.database import get_certificate, list_certificates, save_certificate
from core.renderer import (
    _flatten_css_vars,
    _sanitize_for_xhtml2pdf,
    build_html,
    build_html_from_db,
)
from core.utils import build_download_filename, generate_cert_id

log = logging.getLogger(__name__)


# ─── PDF rendering (xhtml2pdf only — no Playwright) ───
def render_pdf_xhtml2pdf(html_content: str) -> bytes:
    from xhtml2pdf import pisa

    flat = _flatten_css_vars(html_content)
    safe = _sanitize_for_xhtml2pdf(flat)
    buf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    status = pisa.CreatePDF(safe, dest=buf)
    if status.err:
        raise RuntimeError("xhtml2pdf rendering failed")
    buf.seek(0)
    data = buf.read()
    buf.close()
    return data


def _write_temp(data: bytes, suffix: str) -> str:
    f = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    f.write(data)
    f.close()
    return f.name


# ═══════════════════════════════════════════════════════════════
# Tab 1 — Generate
# ═══════════════════════════════════════════════════════════════

def generate_cert(
    student_name,
    course_name,
    level,
    cert_date,
    branch,
    instructor,
    director,
    color_mode,
    custom_accent,
):
    if not student_name or not student_name.strip():
        return gr.update(visible=False), None, None, gr.update(value="**Error:** Enter a student name.")

    try:
        cert_date = datetime.date.fromisoformat(cert_date) if isinstance(cert_date, str) else (cert_date or datetime.date.today())
    except (ValueError, TypeError):
        cert_date = datetime.date.today()
    custom_accent_hex = custom_accent if color_mode == "Custom Color" else None
    original_theme = color_mode == "Original Theme"
    branch_val = branch.strip() if branch and branch.strip() else "Main Branch"
    cert_id = generate_cert_id(course_name, cert_date)

    save_certificate(
        cert_id=cert_id,
        student_name=student_name.strip(),
        course_name=course_name,
        level=level,
        issue_date=cert_date,
        branch=branch_val,
        instructor=instructor.strip() if instructor else "",
        director=director.strip() if director else "",
    )

    html_content = build_html(
        student_name=student_name.strip(),
        course_name=course_name,
        level=level,
        date=cert_date,
        branch=branch_val,
        cert_id=cert_id,
        instructor=instructor.strip() if instructor else "",
        director=director.strip() if director else "",
        custom_accent=custom_accent_hex,
        original_theme=original_theme,
    )

    info = (
        f"### Certificate Generated\n"
        f"- **ID:** `{cert_id}`\n"
        f"- **Student:** {student_name.strip()}\n"
        f"- **Track:** {course_name}\n"
        f"- **Level:** {level}\n"
        f"- **Date:** {cert_date}\n"
        f"- **Branch:** {branch_val}"
    )

    html_path = _write_temp(html_content.encode(), ".html")
    pdf_path = None
    try:
        pdf_bytes = render_pdf_xhtml2pdf(html_content)
        pdf_path = _write_temp(pdf_bytes, ".pdf")
    except Exception as exc:
        log.warning("PDF render failed: %s", exc)

    return (
        gr.update(value=html_content, visible=True),
        html_path,
        pdf_path,
        gr.update(value=info),
    )


def build_generate_tab():
    with gr.Tab("Generate"):
        gr.Markdown("### Certificate Details")
        with gr.Row():
            with gr.Column(scale=2):
                student_name = gr.Textbox(
                    label="Student Full Name *",
                    placeholder="Ahmed Hassan Ali",
                )
                with gr.Row():
                    course_name = gr.Dropdown(
                        label="Course / Track *",
                        choices=list(TRACK_LOGOS.keys()),
                        value=list(TRACK_LOGOS.keys())[0],
                    )
                    branch = gr.Textbox(
                        label="Branch *",
                        value="Main Branch",
                        placeholder="Main Branch",
                    )
                with gr.Row():
                    instructor = gr.Textbox(
                        label="Instructor Name",
                        placeholder="Ms. Sara Mahmoud",
                    )
                    director = gr.Textbox(
                        label="Academic Director",
                        placeholder="Mr. Ibrahim Ahmed",
                    )
                with gr.Row():
                    level = gr.Dropdown(
                        label="Level *",
                        choices=list(LEVEL_OPTIONS),
                        value=LEVEL_OPTIONS[0],
                    )
                    cert_date = gr.Textbox(
                        label="Completion Date * (YYYY-MM-DD)",
                        value=str(datetime.date.today()),
                    )

                gr.Markdown("#### Accent Color")
                color_mode = gr.Radio(
                    ["Original Theme", "Custom Color"],
                    value="Original Theme",
                    label="Color Mode",
                )
                custom_accent = gr.ColorPicker(
                    label="Accent Color",
                    value="#006a61",
                    visible=False,
                )

                def toggle_color(mode):
                    return gr.update(visible=mode == "Custom Color")

                color_mode.change(toggle_color, inputs=[color_mode], outputs=[custom_accent])

                generate_btn = gr.Button(
                    "Generate & Save Certificate",
                    variant="primary",
                    size="lg",
                )

            with gr.Column(scale=3):
                cert_info = gr.Markdown("")
                cert_preview = gr.HTML(visible=False, label="Certificate Preview")
                with gr.Row():
                    html_file = gr.File(label="Download HTML", visible=False)
                    pdf_file = gr.File(label="Download PDF", visible=False)

        generate_btn.click(
            fn=generate_cert,
            inputs=[
                student_name, course_name, level, cert_date,
                branch, instructor, director, color_mode, custom_accent,
            ],
            outputs=[cert_preview, html_file, pdf_file, cert_info],
        )


# ═══════════════════════════════════════════════════════════════
# Tab 2 — Validate
# ═══════════════════════════════════════════════════════════════

def validate_cert(search_id):
    if not search_id or not search_id.strip():
        return gr.update(value=""), gr.update(visible=False), gr.update(visible=False)

    cert_data = get_certificate(search_id.strip())
    if not cert_data:
        return (
            gr.update(value=f"**Certificate `{search_id.strip()}` not found in the registry.**"),
            gr.update(visible=False),
            gr.update(visible=False),
        )

    branch_val = cert_data.get("branch") or cert_data.get("center", "Main Branch")
    info = (
        f"### OFFICIAL CERTIFICATE VERIFIED — AUTHENTIC\n\n"
        f"| Field | Value |\n|---|---|\n"
        f"| **Certificate ID** | `{cert_data['cert_id']}` |\n"
        f"| **Student Name** | **{cert_data['student_name']}** |\n"
        f"| **Track / Course** | {cert_data['course_name']} |\n"
        f"| **Level** | {cert_data['level']} |\n"
        f"| **Issue Date** | {cert_data['issue_date']} |\n"
        f"| **Branch** | {branch_val} |\n"
        f"| **Instructor** | {cert_data['instructor']} |\n"
        f"| **Academic Director** | {cert_data['director']} |\n"
        f"| **Record Created** | `{cert_data['created_at']}` |"
    )

    cert_html = build_html_from_db(cert_data)
    return gr.update(value=info), gr.update(value=cert_html, visible=True), gr.update(visible=False)


def build_validate_tab():
    with gr.Tab("Validate"):
        gr.Markdown("### Certificate Authenticity Verification")
        gr.Markdown("Verify official Techno Future certificates by ID")
        search_id = gr.Textbox(
            label="Enter Certificate ID",
            placeholder="e.g. TKTF-HTM-20260722-A3F1",
        )
        verify_btn = gr.Button("Verify Certificate", variant="primary")
        verify_result = gr.Markdown()
        cert_preview = gr.HTML(visible=False, label="Certificate Preview")

        verify_btn.click(
            fn=validate_cert,
            inputs=[search_id],
            outputs=[verify_result, cert_preview, gr.State()],
        )


# ═══════════════════════════════════════════════════════════════
# Tab 3 — Registry
# ═══════════════════════════════════════════════════════════════

def load_registry():
    certs = list_certificates()
    if not certs:
        return pd.DataFrame(), gr.update(value="No certificates generated yet.")
    df = pd.DataFrame(certs)
    rename = {
        "cert_id": "Certificate ID",
        "student_name": "Student Name",
        "course_name": "Track / Course",
        "level": "Level",
        "issue_date": "Issue Date",
        "branch": "Branch",
        "instructor": "Instructor",
        "director": "Director",
        "created_at": "Created At",
    }
    df.rename(columns={k: v for k, v in rename.items() if k in df.columns}, inplace=True)
    total = len(df)
    today = datetime.date.today()
    month_count = len(df[df["Issue Date"].str.startswith(today.strftime("%Y-%m"))]) if "Issue Date" in df else 0
    top_track = df["Track / Course"].value_counts().idxmax() if "Track / Course" in df and not df["Track / Course"].empty else "\u2014"
    summary = f"**Total:** {total} | **This Month:** {month_count} | **Top Track:** {top_track}"
    return df, gr.update(value=summary)


def export_csv(df):
    if df is None or df.empty:
        return None
    path = _write_temp(df.to_csv(index=False).encode(), ".csv")
    return path


def build_registry_tab():
    with gr.Tab("Registry"):
        gr.Markdown("### Certificate Registry")
        summary = gr.Markdown()
        refresh_btn = gr.Button("Refresh Registry", size="sm")
        registry_table = gr.Dataframe(interactive=False)
        csv_file = gr.File(label="Export CSV", visible=False)

        def on_load():
            df, summ = load_registry()
            csv_path = export_csv(df) if not df.empty else None
            return df, summ, gr.update(value=csv_path, visible=csv_path is not None)

        refresh_btn.click(fn=on_load, outputs=[registry_table, summary, csv_file])


# ═══════════════════════════════════════════════════════════════
# Build & Launch
# ═══════════════════════════════════════════════════════════════

with gr.Blocks(
    title="Certificate System — Techno Future",
) as demo:
    gr.Markdown("# Certificate System — Techno Future")
    gr.Markdown("Official certificate generator, database registry, and instant ID verification")
    build_generate_tab()
    build_validate_tab()
    build_registry_tab()

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())
