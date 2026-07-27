"""
Certificate render service — HTML and PDF rendering.
Adapted from core/renderer.py for the vertical slice architecture.
"""

import base64
import logging
import os
import re
from io import BytesIO
from pathlib import Path
from typing import Optional

from app.modules.certificates.constants import TRACKS, TRACK_KEYS

log = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).parent.parent / "assets"
TEMPLATES_DIR = ASSETS_DIR / "templates"
STYLES_DIR = ASSETS_DIR / "styles"
FONTS_DIR = ASSETS_DIR / "fonts"
LOGOS_DIR = ASSETS_DIR / "logos"


def _get_logo_base64(path: Path) -> str:
    """Read an image file and return a base64 data URI."""
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


def _embed_fonts(css: str) -> str:
    """Replace local font url() references with base64 data URIs."""
    def _replace_url(match: re.Match) -> str:
        filename = os.path.basename(match.group(1))
        font_path = FONTS_DIR / filename
        if font_path.exists():
            data = font_path.read_bytes()
            b64 = base64.b64encode(data).decode()
            return f"url(data:font/truetype;base64,{b64})"
        return match.group(0)

    return re.sub(r"url\('(assets/fonts/[^']+)'\)", _replace_url, css)


def _generate_qr_code(text: str) -> str:
    """Generate a QR code as a base64 data URI."""
    try:
        import qrcode as _qrcode
    except ImportError:
        return ""

    qr = _qrcode.QRCode(version=1, box_size=4, border=1)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0a0e1a", back_color="#ffffff")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"


def _lighten_hex(hex_color: str, factor: float = 0.55) -> str:
    """Derive a lighter variant by blending toward white."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    lr = int(r + (255 - r) * factor)
    lg = int(g + (255 - g) * factor)
    lb = int(b + (255 - b) * factor)
    return f"#{lr:02x}{lg:02x}{lb:02x}"


def _flatten_css_vars(html: str) -> str:
    """Replace var(--name) references with their actual values for xhtml2pdf."""
    vars_map: dict[str, str] = {}

    for m in re.finditer(r"--([\w-]+)\s*:\s*([^;]+)", html):
        name, val = m.group(1), m.group(2).strip()
        val = val.replace("!important", "").strip()
        if val.startswith("#") or val.startswith("rgb"):
            vars_map[name] = val

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
    html = re.sub(r"@font-face\s*\{[^}]*\}", "", html)
    html = re.sub(r"@page\s*\{[^}]*\}", "", html)

    def _remove_balanced_at(html: str, pattern: str) -> str:
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
                    return html[:m.start()] + html[i + 1 :]
            i += 1
        return html

    html = _remove_balanced_at(html, r"@media\s+print\s*\{")
    html = re.sub(r"\[data-track\s*=\s*\"[^\"]*\"\]\s*\{[^}]*\}", "", html)
    html = re.sub(r"::(?:before|after)\s*\{[^}]*\}", "", html)
    html = re.sub(r"\*\s*\{[^}]*\}", "", html)

    def _resolve_color_mix(m: re.Match) -> str:
        inner = m.group(1)
        colors = re.findall(r"#[0-9a-fA-F]{3,8}|rgb\([^)]+\)", inner)
        return colors[0] if colors else "transparent"

    html = re.sub(r"color-mix\(in\s+srgb\s*,\s*([^)]+)\)", _resolve_color_mix, html)

    def _resolve_gradient(m: re.Match) -> str:
        colors = re.findall(r"#[0-9a-fA-F]{3,8}|rgb\([^)]+\)", m.group(0))
        return colors[0] if colors else "transparent"

    html = re.sub(r"linear-gradient\([^)]+\)", _resolve_gradient, html)
    html = re.sub(r"display\s*:\s*grid", "display:block", html)
    html = re.sub(r"display\s*:\s*flex", "display:block", html)

    for prop in (
        "flex-direction", "flex-wrap", "flex-shrink", "flex",
        "justify-content", "align-items", "align-self", "align-content",
        "gap",
    ):
        html = re.sub(rf"{prop}\s*:\s*[^;]+;", "", html)

    def _resolve_inset(m: re.Match) -> str:
        val = m.group(1).strip()
        return f"top:{val};right:{val};bottom:{val};left:{val};"

    html = re.sub(r"inset\s*:\s*([^;]+);", _resolve_inset, html)
    html = re.sub(r"background-image\s*:\s*url\([^)]+\)\s*;?", "", html)

    for prop in (
        "box-shadow", "object-fit", "text-transform", "letter-spacing",
        "border-radius", "font-display", "overflow", "pointer-events",
        "box-sizing", "min-height", "min-width", "max-width", "opacity",
        "z-index", "white-space", "word-break", "line-height",
    ):
        html = re.sub(rf"{prop}\s*:\s*[^;]+;", "", html)

    def _resolve_font_weight(m: re.Match) -> str:
        w = int(m.group(1))
        return f"font-weight:{'bold' if w >= 600 else 'normal'}"

    html = re.sub(r"font-weight\s*:\s*(\d+)", _resolve_font_weight, html)
    return html


def render_html(
    student_name: str,
    course_name: str,
    course_track: str,
    level: str,
    issue_date,
    branch: str,
    cert_id: str,
    instructor: Optional[str] = None,
    director: Optional[str] = None,
    custom_color: Optional[str] = None,
    verify_url: Optional[str] = None,
) -> str:
    """Build certificate HTML with embedded assets."""
    import datetime

    # Get track metadata
    track_data = None
    for name, data in TRACKS.items():
        if data["key"] == course_track:
            track_data = data
            break

    if track_data is None:
        track_data = {"key": course_track, "data_attr": course_track, "logo": "html_logo.png"}

    track_attr = track_data["data_attr"]
    date_str = issue_date.strftime("%d/%m/%Y") if isinstance(issue_date, datetime.date) else str(issue_date)

    # Load and embed CSS
    css_path = STYLES_DIR / "certificate_style.css"
    css = _embed_fonts(css_path.read_text(encoding="utf-8")) if css_path.exists() else ""

    # Load logos
    company_logo = LOGOS_DIR.parent.parent.parent / "assests" / "logo.png"
    if not company_logo.exists():
        company_logo = LOGOS_DIR / "logo.png"
    company_b64 = _get_logo_base64(company_logo)

    track_logo = LOGOS_DIR / track_data.get("logo", "html_logo.png")
    if not track_logo.exists():
        track_logo = LOGOS_DIR.parent.parent.parent / "assests" / track_data.get("logo", "html_logo.png")
    track_b64 = _get_logo_base64(track_logo)

    # Generate QR code
    target_url = verify_url or f"http://localhost:8501/?verify={cert_id}"
    qr_b64 = _generate_qr_code(target_url)

    # Build image tags
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
        f'''<div class="cert-qr-box">
        <img src="{qr_b64}" alt="QR Validation" class="cert-qr-img">
        <div class="cert-qr-label">Scan to Verify</div>
      </div>'''
        if qr_b64
        else '<div style="width:65px;"></div>'
    )

    # Accent color override
    accent_override = ""
    if custom_color:
        light = _lighten_hex(custom_color)
        accent_override = (
            f'<style>.certificate-page{{'
            f"--track-accent:{custom_color}!important;"
            f"--track-accent-light:{light}!important;"
            f"}}</style>"
        )

    # Signature blocks
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

    # Load and fill template
    template_path = TEMPLATES_DIR / "certificate_template.html"
    if not template_path.exists():
        template_path = Path(__file__).parent.parent.parent.parent / "certificate_template.html"
    template = template_path.read_text(encoding="utf-8")

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


def render_pdf(html_content: str) -> bytes:
    """Render HTML to PDF using xhtml2pdf (pure Python)."""
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

    raise RuntimeError("PDF rendering failed. xhtml2pdf is the only available engine.")
