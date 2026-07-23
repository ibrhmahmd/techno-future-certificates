"""
Certificate HTML builder and PDF renderer.
Pure Python — zero Streamlit imports.
"""

import datetime
import logging
import re
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
    XHTML2PDF_AVAILABLE,
    embed_fonts,
    generate_qr_code,
    get_logo_base64,
    lighten_hex,
)

log = logging.getLogger(__name__)


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


def _flatten_css_vars(html: str) -> str:
    """Replace var(--name) references with their actual values for xhtml2pdf."""
    vars_map: dict[str, str] = {}

    # Extract from inline override: .certificate-page{--track-accent:#xxx!important;}
    for m in re.finditer(
        r"--([\w-]+)\s*:\s*([^;]+)", html
    ):
        name, val = m.group(1), m.group(2).strip()
        val = val.replace("!important", "").strip()
        if val.startswith("#") or val.startswith("rgb"):
            vars_map[name] = val

    # Extract from :root{--primary:#xxx;} in stylesheet
    root_block = re.search(r":root\{([^}]+)\}", html)
    if root_block:
        for m in re.finditer(r"--([\w-]+)\s*:\s*([^;]+)", root_block.group(1)):
            name, val = m.group(1), m.group(2).strip()
            if name not in vars_map and (val.startswith("#") or val.startswith("rgb")):
                vars_map[name] = val

    if not vars_map:
        return html

    def _replace_var(m: re.Match) -> str:
        var_name = m.group(1)
        return vars_map.get(var_name, m.group(0))

    return re.sub(r"var\(--([\w-]+)\)", _replace_var, html)


# ─── Playwright browser health check (cached) ───
_playwright_ok: bool | None = None


def _playwright_works() -> bool:
    """Test once whether Playwright can actually launch Chromium."""
    global _playwright_ok
    if _playwright_ok is not None:
        return _playwright_ok
    if not PLAYWRIGHT_AVAILABLE:
        _playwright_ok = False
        return False
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        _playwright_ok = True
    except Exception as exc:
        log.warning("Playwright launch failed: %s", exc)
        _playwright_ok = False
    return _playwright_ok


def render_pdf(html_content: str) -> bytes:
    """Try each PDF engine in order; return the first success."""

    # 1. Playwright (best quality, needs installed Chromium)
    if _playwright_works():
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
        except Exception as exc:
            log.warning("Playwright PDF failed: %s", exc)

    # 2. xhtml2pdf (pure Python, always works, moderate quality)
    if XHTML2PDF_AVAILABLE:
        try:
            from xhtml2pdf import pisa

            flat_html = _flatten_css_vars(html_content)
            result_buf = BytesIO()
            pisa_status = pisa.CreatePDF(flat_html, dest=result_buf)
            if not pisa_status.err:
                return result_buf.getvalue()
        except Exception as exc:
            log.warning("xhtml2pdf PDF failed: %s", exc)

    raise RuntimeError(
        "No working PDF engine. "
        "Install: playwright (playwright install chromium) or xhtml2pdf."
    )


def pdf_engine_status() -> dict[str, bool]:
    """Return which PDF engines are importable + functional."""
    return {
        "playwright": _playwright_works(),
        "xhtml2pdf": XHTML2PDF_AVAILABLE,
    }
