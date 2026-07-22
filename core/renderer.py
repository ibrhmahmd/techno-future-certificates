"""
Certificate HTML builder and PDF renderer.
Pure Python — zero Streamlit imports.
"""

import datetime
from io import BytesIO

from core.config import (
    COMPANY_LOGO,
    CSS_PATH,
    TEMPLATE_PATH,
    TRACK_DATA_ATTR,
    TRACK_DEFAULT_COLORS,
    TRACK_LOGOS,
)
from core.utils import (
    PLAYWRIGHT_AVAILABLE,
    QRCODE_AVAILABLE,
    WEASYPRINT_AVAILABLE,
    XHTML2PDF_AVAILABLE,
    embed_fonts,
    generate_qr_code,
    get_logo_base64,
    lighten_hex,
)


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
        COMPANY_LOGO.parent.parent / TRACK_LOGOS.get(course_name, "assests/html_logo.png")
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
            '<style>.certificate-page{'
            "--track-accent:#006a61!important;"
            "--track-accent-light:#89f5e7!important;"
            "}</style>"
        )
    elif custom_accent:
        light = lighten_hex(custom_accent)
        accent_override = (
            f'<style>.certificate-page{{'
            f"--track-accent:{custom_accent}!important;"
            f"--track-accent-light:{light}!important;"
            f"}}</style>"
        )

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    return template.format(
        css=css,
        accent_override=accent_override,
        track_attr=track_attr,
        qr_img=qr_img,
        company_img=company_img,
        track_img=track_img,
        student_name=student_name,
        course_name=course_name,
        level=level,
        date_str=date_str,
        branch=branch,
        instructor=instructor,
        director=director,
        cert_id=cert_id,
    )


def render_pdf(html_content: str) -> bytes:
    if PLAYWRIGHT_AVAILABLE:
        try:
            from playwright.sync_api import sync_playwright

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
            from weasyprint import HTML

            return HTML(string=html_content).write_pdf()
        except Exception:
            pass

    if XHTML2PDF_AVAILABLE:
        try:
            from xhtml2pdf import pisa

            result_buf = BytesIO()
            pisa_status = pisa.CreatePDF(html_content, dest=result_buf)
            if not pisa_status.err:
                return result_buf.getvalue()
        except Exception:
            pass

    raise RuntimeError("No working PDF engine available.")
