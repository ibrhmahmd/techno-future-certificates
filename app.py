"""
Certificate Generator — Techno Kids, Techno Future
Streamlit app for generating A4 landscape PDF certificates with SQLite database tracking,
validation interface, and QR code embedding following Precision Engine v3.0 design system.
"""

import streamlit as st
import datetime
import uuid
import base64
import sqlite3
import re
import os
import pandas as pd
from pathlib import Path
from io import BytesIO

# ─── PDF & QR Library Imports ───
try:
    import qrcode

    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.sync_api import sync_playwright

    PLAYWRIGHT_AVAILABLE = True
except Exception:
    PLAYWRIGHT_AVAILABLE = False

WEASYPRINT_AVAILABLE = False
try:
    import sys
    import io
    import logging

    logging.getLogger("weasyprint").setLevel(logging.CRITICAL)
    _stderr = sys.stderr
    _stdout = sys.stdout
    sys.stderr = io.StringIO()
    sys.stdout = io.StringIO()
    try:
        from weasyprint import HTML

        WEASYPRINT_AVAILABLE = True
    finally:
        sys.stderr = _stderr
        sys.stdout = _stdout
except Exception:
    WEASYPRINT_AVAILABLE = False

try:
    from xhtml2pdf import pisa

    XHTML2PDF_AVAILABLE = True
except Exception:
    XHTML2PDF_AVAILABLE = False

# ─── Config & Paths ───
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = (BASE_DIR / "certificates.db").resolve()
COMPANY_LOGO = (BASE_DIR / "assests" / "logo.png").resolve()
CSS_PATH = (BASE_DIR / "certificate_style.css").resolve()

TRACK_LOGOS = {
    "HTML — Web Structure": "assests/html_logo.png",
    "CSS — Styling & Layout": "assests/css_logo.png",
    "JavaScript — Interactivity": "assests/js_logo.png",
    "Python — Programming": "assests/python_logo.png",
    "Advanced — Full Stack": "assests/js_logo.png",
    "Problem Solving — Logic": "assests/python_logo.png",
    "Robotics — WeDo 2.0": "assests/wedo2.0_logo.png",
    "Robotics — SPIKE Essential": "assests/spike-ess_logo.png",
    "Robotics — SPIKE Prime": "assests/spike-prime_logo.png",
    "Robotics — EV3": "assests/ev3_logo.png",
    "Robotics — Arduino": "assests/pictoblox_logo.png",
    "Scratch — Visual Programming": "assests/scratch_logo.png",
    "Scratch Jr — Early Learning": "assests/scratch-jr_logo.png",
}

TRACK_DATA_ATTR = {
    "HTML — Web Structure":               "html",
    "CSS — Styling & Layout":             "css",
    "JavaScript — Interactivity":         "javascript",
    "Python — Programming":               "python",
    "Advanced — Full Stack":              "advanced",
    "Problem Solving — Logic":            "problem_solving",
    "Robotics — WeDo 2.0":               "robotics-wedo",
    "Robotics — SPIKE Essential":         "robotics-spike-essential",
    "Robotics — SPIKE Prime":             "robotics-spike-prime",
    "Robotics — EV3":                     "robotics-ev3",
    "Robotics — Arduino":                 "robotics-arduino",
    "Scratch — Visual Programming":       "scratch",
    "Scratch Jr — Early Learning":        "scratch-jr",
}

TRACK_DEFAULT_COLORS = {
    "html":              ("#c62828", "#ff6659"),
    "css":               ("#1565c0", "#5e92f3"),
    "javascript":        ("#f9a825", "#ffd95a"),
    "python":            ("#2e7d32", "#60ad5e"),
    "advanced":          ("#6a1b9a", "#9c4dcc"),
    "problem_solving":   ("#e65100", "#ff833a"),
    "robotics-wedo":     ("#7c4dff", "#b388ff"),
    "robotics-spike-essential": ("#00c853", "#69f0ae"),
    "robotics-spike-prime":     ("#388e3c", "#81c784"),
    "robotics-ev3":      ("#1976d2", "#64b5f6"),
    "robotics-arduino":  ("#ff6d00", "#ffab40"),
    "scratch":           ("#ffab19", "#ffc966"),
    "scratch-jr":        ("#4d97ff", "#85b8ff"),
}


def lighten_hex(hex_color: str, factor: float = 0.55) -> str:
    """Derive a printable-friendly lighter variant by blending toward white."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    lr = int(r + (255 - r) * factor)
    lg = int(g + (255 - g) * factor)
    lb = int(b + (255 - b) * factor)
    return f"#{lr:02x}{lg:02x}{lb:02x}"


LEVEL_LABELS = {
    "Level 1 — Junior": "Level 1 — Junior",
    "Level 2 — Intermediate": "Level 2 — Intermediate",
    "Level 3 — Advanced": "Level 3 — Advanced",
}


# ─── SQLite Database Layer ───
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS certificates (
            cert_id TEXT PRIMARY KEY,
            student_name TEXT NOT NULL,
            course_name TEXT NOT NULL,
            level TEXT NOT NULL,
            issue_date TEXT NOT NULL,
            branch TEXT NOT NULL,
            instructor TEXT NOT NULL,
            director TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Auto-migrate legacy schemas (e.g., 'center' column or missing columns)
    c.execute("PRAGMA table_info(certificates)")
    columns = [row[1] for row in c.fetchall()]

    if "branch" not in columns:
        if "center" in columns:
            c.execute("ALTER TABLE certificates RENAME COLUMN center TO branch")
        else:
            c.execute(
                "ALTER TABLE certificates ADD COLUMN branch TEXT NOT NULL DEFAULT 'Main Branch'"
            )

    if "instructor" not in columns:
        c.execute(
            "ALTER TABLE certificates ADD COLUMN instructor TEXT NOT NULL DEFAULT 'Instructor'"
        )

    if "director" not in columns:
        c.execute(
            "ALTER TABLE certificates ADD COLUMN director TEXT NOT NULL DEFAULT 'Academic Director'"
        )

    if "level" not in columns:
        c.execute(
            "ALTER TABLE certificates ADD COLUMN level TEXT NOT NULL DEFAULT 'Level 1'"
        )

    if "issue_date" not in columns:
        c.execute(
            "ALTER TABLE certificates ADD COLUMN issue_date TEXT NOT NULL DEFAULT ''"
        )

    if "created_at" not in columns:
        c.execute(
            "ALTER TABLE certificates ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        )

    conn.commit()
    conn.close()


def save_certificate(
    cert_id: str,
    student_name: str,
    course_name: str,
    level: str,
    issue_date: datetime.date,
    branch: str,
    instructor: str,
    director: str,
):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT OR REPLACE INTO certificates
        (cert_id, student_name, course_name, level, issue_date, branch, instructor, director)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            cert_id,
            student_name,
            course_name,
            level,
            str(issue_date),
            branch,
            instructor,
            director,
        ),
    )
    conn.commit()
    conn.close()


def get_certificate(cert_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM certificates WHERE cert_id = ?", (cert_id.strip(),))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def list_certificates():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        "SELECT cert_id, student_name, course_name, level, issue_date, branch, instructor, director, created_at FROM certificates ORDER BY created_at DESC"
    )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# Initialize database table on app launch
init_db()


# ─── Helper Functions ───
def generate_cert_id(track_name: str, date: datetime.date) -> str:
    short = track_name.split("—")[0].strip()[:3].upper()
    date_str = date.strftime("%Y%m%d")
    uid = uuid.uuid4().hex[:4].upper()
    return f"TKTF-{short}-{date_str}-{uid}"


def sanitize_filename(text: str) -> str:
    clean = re.sub(r"[^\w\s-]", "", text).strip()
    clean = re.sub(r"[\s_]+", "_", clean)
    return clean or "Certificate"


def build_download_filename(student_name: str, course_name: str, ext: str) -> str:
    safe_student = sanitize_filename(student_name)
    safe_course = sanitize_filename(course_name)
    return f"{safe_student}_{safe_course}_Certificate.{ext.lstrip('.')}"


def get_logo_base64(path: Path) -> str:
    if path.exists():
        data = path.read_bytes()
        ext = path.suffix.lstrip(".").lower()
        mime = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "svg": "image/svg+xml",
        }.get(ext, "image/png")
        return f"data:{mime};base64,{base64.b64encode(data).decode()}"
    return ""


FONTS_DIR = (BASE_DIR / "assests" / "fonts").resolve()


def embed_fonts(css: str) -> str:
    """Replace local font url() references with base64 data URIs for PDF engines."""
    def _replace_url(match):
        filename = os.path.basename(match.group(1))
        font_path = (FONTS_DIR / filename).resolve()
        if font_path.exists():
            data = font_path.read_bytes()
            b64 = base64.b64encode(data).decode()
            return f"url(data:font/truetype;base64,{b64})"
        return match.group(0)

    return re.sub(r"url\('(assests/fonts/[^']+)'\)", _replace_url, css)


def generate_qr_code(text: str) -> str:
    if not QRCODE_AVAILABLE:
        return ""
    qr = qrcode.QRCode(version=1, box_size=4, border=1)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0a0e1a", back_color="#ffffff")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"


def build_html(
    student_name: str,
    course_name: str,
    level: str,
    date: datetime.date,
    branch: str,
    cert_id: str,
    instructor: str,
    director: str,
    verify_url: str = "",
    custom_accent: str | None = None,
    original_theme: bool = False,
) -> str:
    track_attr = TRACK_DATA_ATTR.get(course_name, "html")
    date_str = (
        date.strftime("%d/%m/%Y") if isinstance(date, datetime.date) else str(date)
    )

    css = embed_fonts(CSS_PATH.read_text(encoding="utf-8")) if CSS_PATH.exists() else ""

    company_b64 = get_logo_base64(COMPANY_LOGO)
    track_logo_path = (
        BASE_DIR / TRACK_LOGOS.get(course_name, "assests/html_logo.png")
    ).resolve()
    track_b64 = get_logo_base64(track_logo_path)

    target_url = verify_url or f"http://localhost:8501/?verify={cert_id}"
    qr_b64 = generate_qr_code(target_url)

    company_img = (
        f'<img src="{company_b64}" alt="Techno Future" class="cert-logo cert-logo--company">'
        if company_b64
        else '<div style="width:90px;"></div>'
    )
    track_img = (
        f'<img src="{track_b64}" alt="Track Logo" class="cert-logo cert-logo--track">'
        if track_b64
        else '<div style="width:80px;"></div>'
    )
    qr_img = (
        f'''
      <div class="cert-qr-box">
        <img src="{qr_b64}" alt="QR Validation" class="cert-qr-img">
        <div class="cert-qr-label">Scan to Verify</div>
      </div>
    '''
        if qr_b64
        else '<div style="width:65px;"></div>'
    )

    accent_override = ""
    if original_theme:
        accent_override = (
            f'<style>.certificate-page{{'
            f'--track-accent:#006a61!important;'
            f'--track-accent-light:#89f5e7!important;'
            f'}}></style>'
        )
    elif custom_accent:
        light = lighten_hex(custom_accent)
        accent_override = (
            f'<style>.certificate-page{{'
            f'--track-accent:{custom_accent}!important;'
            f'--track-accent-light:{light}!important;'
            f'}}></style>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>{css}</style>
{accent_override}
</head>
<body style="margin:0;padding:0;background:#fff;">
<div class="certificate-page" data-track="{track_attr}">
  <div class="certificate-border"></div>
  <div class="corner-ornament corner-ornament--tl"></div>
  <div class="corner-ornament corner-ornament--tr"></div>
  <div class="corner-ornament corner-ornament--bl"></div>
  <div class="corner-ornament corner-ornament--br"></div>
  <div class="cert-power-bar"></div>
  <div class="certificate-inner">
    <div class="cert-header">
      <div class="cert-header-left">
        {qr_img}
      </div>
      <div class="cert-header-center">
        {company_img}
        <div class="cert-company-title">Techno Future</div>
        <div class="cert-company-sub">Empowering Tomorrow's Innovators</div>
      </div>
      <div class="cert-header-right">
        {track_img}
      </div>
    </div>
    <div class="cert-title-block">
      <h1 class="cert-academy-title">Techno Future</h1>
      <div class="cert-title-sub">Certificate of Achievement</div>
      <div class="cert-title-underline"></div>
    </div>
    <div class="cert-body">
      <div class="cert-recipient-label">This certificate is proudly presented to</div>
      <div class="cert-recipient-name">{student_name}</div>
      <div class="cert-course-name">{course_name}</div>
      <div class="cert-course-level">{level}</div>
      <p class="cert-description">
        For successfully completing all required coursework and demonstrating excellence
        in the concepts and practical skills covered in this program.
      </p>
    </div>
    <div class="cert-meta-row">
      <div class="cert-meta-item">
        <div class="cert-meta-label">Date</div>
        <div class="cert-meta-value">{date_str}</div>
      </div>
      <div class="cert-meta-item">
        <div class="cert-meta-label">Branch</div>
        <div class="cert-meta-value">{branch}</div>
      </div>
    </div>
    <div class="cert-signatures">
      <div class="cert-signature">
        <div class="cert-signature-line"></div>
        <div class="cert-signature-name">{instructor}</div>
        <div class="cert-signature-role">Instructor</div>
      </div>
      <div class="cert-signature">
        <div class="cert-signature-line"></div>
        <div class="cert-signature-name">{director}</div>
        <div class="cert-signature-role">Academic Director</div>
      </div>
    </div>
    <div class="cert-footer">
      <div class="cert-footer-text">Techno Future — Official Academic Document</div>
      <div class="cert-id-badge">ID: {cert_id}</div>
    </div>
  </div>
</div>
</body>
</html>"""


def render_pdf(html_content: str) -> bytes:
    if PLAYWRIGHT_AVAILABLE:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_content(html_content, wait_until="load", timeout=15000)
                pdf_bytes = page.pdf(
                    format="A4",
                    landscape=True,
                    print_background=True,
                    margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                )
                browser.close()
                return pdf_bytes
        except Exception:
            pass

    if WEASYPRINT_AVAILABLE:
        try:
            return HTML(string=html_content).write_pdf()
        except Exception:
            pass

    if XHTML2PDF_AVAILABLE:
        try:
            result_buf = BytesIO()
            pisa_status = pisa.CreatePDF(html_content, dest=result_buf)
            if not pisa_status.err:
                return result_buf.getvalue()
        except Exception:
            pass

    raise RuntimeError("No working PDF engine available.")


# ─── Streamlit UI Configuration ───
st.set_page_config(
    page_title="Certificate System — Techno Future", page_icon="🎓", layout="wide"
)

# Handle deep-link validation from QR code URL parameters
query_params = st.query_params
deep_verify_id = query_params.get("verify") or query_params.get("cert_id")

st.title("🎓 Certificate System — Techno Future")
st.caption(
    "Official certificate generator, database registry, and instant ID verification portal"
)

tab1, tab2, tab3 = st.tabs(
    ["🎓 Generate Certificate", "🔍 Validate Certificate", "📜 Certificate Registry"]
)

# ─────────────────────────────────────────────────────────────
# TAB 1: GENERATE CERTIFICATE
# ─────────────────────────────────────────────────────────────
with tab1:
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
                default_color = TRACK_DEFAULT_COLORS.get(default_track_attr, ("#006a61", "#89f5e7"))[0]
                custom_accent_hex = st.color_picker(
                    "Accent Color",
                    value=default_color,
                    label_visibility="collapsed",
                )

            cert_id = generate_cert_id(course_name, cert_date)

            st.markdown("---")
            st.metric("Generated Certificate ID", cert_id)

            submitted = st.form_submit_button(
                "🎓 Generate & Save Certificate",
                type="primary",
                use_container_width=True,
            )

    with col_preview:
        st.subheader("Live Preview & Downloads")
        if submitted:
            if not student_name.strip():
                st.error("Please enter the student name before generating.")
            else:
                # Save record to SQLite database
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
                st.success(f"✅ Certificate saved to database! ID: **{cert_id}**")

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
                        label="📄 Download HTML File",
                        data=html_content,
                        file_name=fn_html,
                        mime="text/html",
                        use_container_width=True,
                    )
                with b2:
                    try:
                        pdf_bytes = render_pdf(html_content)
                        st.download_button(
                            label="📥 Download Vector PDF",
                            data=pdf_bytes,
                            file_name=fn_pdf,
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.warning(
                            f"Direct PDF engine unavailable. Use HTML download or Ctrl+P to print."
                        )
        else:
            st.info(
                "👈 Fill out the form on the left and click **Generate & Save Certificate** to view live preview and downloads."
            )


# ─────────────────────────────────────────────────────────────
# TAB 2: VALIDATE CERTIFICATE
# ─────────────────────────────────────────────────────────────
with tab2:
    st.subheader("🔍 Certificate Authenticity Verification")
    st.caption("Verify official Techno Future certificates by ID")

    search_id_input = st.text_input(
        "Enter Certificate ID",
        value=deep_verify_id or "",
        placeholder="e.g. TKTF-HTM-20260722-A3F1",
    )

    if search_id_input.strip():
        cert_data = get_certificate(search_id_input.strip())
        if cert_data:
            st.success("✅ OFFICIAL CERTIFICATE VERIFIED — AUTHENTIC")

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
                f"❌ Certificate ID **{search_id_input.strip()}** was not found in the official registry."
            )


# ─────────────────────────────────────────────────────────────
# TAB 3: CERTIFICATE REGISTRY
# ─────────────────────────────────────────────────────────────
with tab3:
    st.subheader("📜 Issued Certificates Database Registry")

    all_certs = list_certificates()
    if all_certs:
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
            label="📥 Export Registry CSV",
            data=csv,
            file_name=f"certificates_registry_{datetime.date.today()}.csv",
            mime="text/csv",
        )
    else:
        st.info(
            "No certificates generated yet. Issued certificates will automatically be stored here."
        )
