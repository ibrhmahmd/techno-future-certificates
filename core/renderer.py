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

    instructor_sig = (
        f'<div class="cert-signature">'
        f'<div class="cert-signature-line"></div>'
        f'<div class="cert-signature-name">{instructor}</div>'
        f'<div class="cert-signature-role">Instructor</div>'
        f'</div>'
        if instructor
        else ""
    )
    director_sig = (
        f'<div class="cert-signature">'
        f'<div class="cert-signature-line"></div>'
        f'<div class="cert-signature-name">{director}</div>'
        f'<div class="cert-signature-role">Academic Director</div>'
        f'</div>'
        if director
        else ""
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
        instructor_sig=instructor_sig,
        director_sig=director_sig,
        cert_id=cert_id,
    )


def build_html_from_db(cert_data: dict) -> str:
    """Build certificate HTML from a database row dict."""
    try:
        dt = datetime.datetime.strptime(cert_data["issue_date"], "%Y-%m-%d").date()
    except (ValueError, KeyError):
        dt = datetime.date.today()
    branch_val = cert_data.get("branch") or cert_data.get("center", "Main Branch")
    return build_html(
        student_name=cert_data["student_name"],
        course_name=cert_data["course_name"],
        level=cert_data["level"],
        date=dt,
        branch=branch_val,
        cert_id=cert_data["cert_id"],
        instructor=cert_data["instructor"],
        director=cert_data["director"],
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


def _sanitize_for_xhtml2pdf(html: str) -> str:
    """Strip CSS features xhtml2pdf cannot render."""
    # Remove @font-face blocks (local fonts won't resolve on server; numeric weights error)
    html = re.sub(r"@font-face\s*\{[^}]*\}", "", html)

    # Remove @page and @media print blocks (balanced brace matching)
    html = re.sub(r"@page\s*\{[^}]*\}", "", html)

    def _remove_balanced_at(html: str, pattern: str) -> str:
        """Remove an at-rule including nested {} blocks."""
        m = re.search(pattern, html)
        if not m:
            return html
        depth, i = 0, m.end() - 1
        while i < len(html):
            if html[i] == "{":
                depth += 1
            elif html[i] == "}":
                depth -= 1
                if depth == 0:
                    return html[: m.start()] + html[i + 1 :]
            i += 1
        return html

    html = _remove_balanced_at(html, r"@media\s+print\s*\{")

    # Resolve color-mix(in srgb, COLOR PCT%, transparent) → base color
    def _resolve_color_mix(m: re.Match) -> str:
        inner = m.group(1)
        colors = re.findall(r"#[0-9a-fA-F]{3,8}|rgb\([^)]+\)", inner)
        return colors[0] if colors else "transparent"

    html = re.sub(
        r"color-mix\(in\s+srgb\s*,\s*([^)]+)\)", _resolve_color_mix, html
    )

    # Resolve linear-gradient(...) → first non-transparent color stop
    def _resolve_gradient(m: re.Match) -> str:
        colors = re.findall(r"#[0-9a-fA-F]{3,8}|rgb\([^)]+\)", m.group(0))
        return colors[0] if colors else "transparent"

    html = re.sub(r"linear-gradient\([^)]+\)", _resolve_gradient, html)

    # display:grid → display:block (xhtml2pdf has no grid support)
    html = re.sub(r"display\s*:\s*grid", "display:block", html)

    # Remove gap property
    html = re.sub(r"gap\s*:\s*[^;]+;", "", html)

    # inset:N → top:N;right:N;bottom:N;left:N
    def _resolve_inset(m: re.Match) -> str:
        val = m.group(1).strip()
        return f"top:{val};right:{val};bottom:{val};left:{val};"

    html = re.sub(r"inset\s*:\s*([^;]+);", _resolve_inset, html)

    # Remove unsupported properties
    for prop in (
        "box-shadow",
        "object-fit",
        "text-transform",
        "letter-spacing",
        "border-radius",
        "font-display",
        "overflow",
        "pointer-events",
    ):
        html = re.sub(rf"{prop}\s*:\s*[^;]+;", "", html)

    # Numeric font-weight → normal / bold
    def _resolve_font_weight(m: re.Match) -> str:
        w = int(m.group(1))
        return f"font-weight:{'bold' if w >= 600 else 'normal'}"

    html = re.sub(r"font-weight\s*:\s*(\d+)", _resolve_font_weight, html)

    return html


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
            safe_html = _sanitize_for_xhtml2pdf(flat_html)
            result_buf = BytesIO()
            pisa_status = pisa.CreatePDF(safe_html, dest=result_buf)
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
