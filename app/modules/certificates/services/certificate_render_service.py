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

from app.modules.certificates.constants import TRACKS, TRACK_KEYS, TRACK_COLORS

log = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).parent.parent / "assets"
TEMPLATES_DIR = ASSETS_DIR / "templates"
STYLES_DIR = ASSETS_DIR / "styles"
FONTS_DIR = ASSETS_DIR / "fonts"
LOGOS_DIR = ASSETS_DIR / "logos"

# Map CSS font-family names to their TTF files
_FONT_MAP = {
    "Space Grotesk": {
        400: "SpaceGrotesk-Regular.ttf",
        500: "SpaceGrotesk-Medium.ttf",
        600: "SpaceGrotesk-SemiBold.ttf",
        700: "SpaceGrotesk-Bold.ttf",
    },
    "Inter": {
        300: "Inter-Light.ttf",
        400: "Inter-Regular.ttf",
        500: "Inter-Medium.ttf",
        600: "Inter-SemiBold.ttf",
        700: "Inter-Bold.ttf",
    },
}

_fonts_registered = False


def _register_fonts() -> None:
    """Register all TTF fonts with reportlab for xhtml2pdf rendering."""
    global _fonts_registered
    if _fonts_registered:
        return

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.fonts import addMapping

    for family, weights in _FONT_MAP.items():
        for weight, filename in weights.items():
            font_path = FONTS_DIR / filename
            if not font_path.exists():
                continue
            bold = 1 if weight >= 700 else 0
            italic = 0
            font_name = f"{family}_{bold}_{italic}"
            try:
                pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
                log.debug("Registered font %s from %s", font_name, filename)
            except Exception as exc:
                log.warning("Failed to register font %s: %s", font_name, exc)
        # Map family name to bold/italic variants so CSS font-family works
        addMapping(family, 0, 0, f"{family}_0_0")
        addMapping(family, 1, 0, f"{family}_1_0")
        addMapping(family, 0, 1, f"{family}_0_0")
        addMapping(family, 1, 1, f"{family}_1_0")

    _fonts_registered = True


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
            return f"url(data:font/ttf;base64,{b64})"
        return match.group(0)

    return re.sub(r"url\('(assests/fonts/[^']+)'\)", _replace_url, css)


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

    for m in re.finditer(r"--([\\w-]+)\\s*:\\s*([^;]+)", html):
        name, val = m.group(1), m.group(2).strip()
        val = val.replace("!important", "").strip()
        if val.startswith("#") or val.startswith("rgb") or val.startswith("'") or val.startswith('"'):
            vars_map[name] = val

    root_block = re.search(r":root\s*\{([^}]+)\}", html, re.DOTALL)
    if root_block:
        for m in re.finditer(r"--([\\w-]+)\\s*:\\s*([^;]+)", root_block.group(1)):
            name, val = m.group(1), m.group(2).strip()
            if name not in vars_map and (val.startswith("#") or val.startswith("rgb") or val.startswith("'") or val.startswith('"')):
                vars_map[name] = val

    if not vars_map:
        return html

    def _replace_var(m: re.Match) -> str:
        var_name = m.group(1)
        return vars_map.get(var_name, m.group(0))

    return re.sub(r"var\(--([\\w-]+)\)", _replace_var, html)


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


# ─────────────────────────────────────────────────────────────────────────────
# PDF-native HTML builder
# xhtml2pdf (Reportlab) has very limited CSS support: no CSS variables,
# no flexbox/grid, no ::before/::after, no color-mix(), etc.
# We build a dedicated, table-layout HTML with all values hardcoded.
# ─────────────────────────────────────────────────────────────────────────────

def _build_pdf_html(
    student_name: str,
    course_name: str,
    course_track: str,
    level: str,
    issue_date,
    branch: str,
    cert_id: str,
    instructor: Optional[str],
    director: Optional[str],
    accent: str,
    accent_light: str,
    company_b64: str,
    track_b64: str,
    qr_b64: str,
) -> str:
    """Build an xhtml2pdf-compatible HTML for the certificate PDF.

    Uses HTML tables for layout (no flex/grid) and hardcoded color values
    (no CSS custom properties).  All values that would normally come from
    CSS vars are resolved from Python before building the string.
    """
    import datetime

    date_str = (
        issue_date.strftime("%d/%m/%Y")
        if isinstance(issue_date, datetime.date)
        else str(issue_date)
    )

    # Palette — hardcoded resolved values (no CSS vars)
    primary       = "#0a0e1a"
    on_bg         = "#0b1c30"
    on_muted      = "#5A6070"
    on_variant    = "#7a8090"
    surface_low   = "#eff4ff"

    company_img_tag = (
        f'<img src="{company_b64}" width="70" height="70" />'
        if company_b64 else '<div style="width:70px;"></div>'
    )
    track_img_tag = (
        f'<img src="{track_b64}" width="65" height="65" />'
        if track_b64 else '<div style="width:65px;"></div>'
    )
    qr_img_tag = (
        f'<img src="{qr_b64}" width="60" height="60" />'
        if qr_b64 else ""
    )

    # Signature blocks
    sig_cells = ""
    if instructor:
        sig_cells += f"""
        <td style="text-align:center; width:50%;">
          <div style="width:130px; height:1px; background:{on_muted}; margin:0 auto 4px;"></div>
          <div style="font-family:Inter,Arial,sans-serif; font-size:9pt; font-weight:bold; color:{on_bg};">{instructor}</div>
          <div style="font-family:Inter,Arial,sans-serif; font-size:7.5pt; color:{on_muted};">Instructor</div>
        </td>"""
    if director:
        sig_cells += f"""
        <td style="text-align:center; width:50%;">
          <div style="width:130px; height:1px; background:{on_muted}; margin:0 auto 4px;"></div>
          <div style="font-family:Inter,Arial,sans-serif; font-size:9pt; font-weight:bold; color:{on_bg};">{director}</div>
          <div style="font-family:Inter,Arial,sans-serif; font-size:7.5pt; color:{on_muted};">Academic Director</div>
        </td>"""

    sig_row = (
        f'<table width="100%" style="margin-top:6px;"><tr>{sig_cells}</tr></table>'
        if sig_cells else ""
    )

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<style>
  @page {{ size: 297mm 210mm landscape; margin: 0; }}
  body {{
    margin: 0;
    padding: 0;
    background: #ffffff;
    font-family: Inter, Arial, sans-serif;
  }}
  .page {{
    width: 297mm;
    height: 210mm;
    background: #ffffff;
    position: relative;
    padding: 0;
    margin: 0;
  }}
  .outer-border {{
    position: absolute;
    top: 8mm;
    left: 8mm;
    right: 8mm;
    bottom: 8mm;
    border: 2px solid {accent};
  }}
  .inner-border {{
    position: absolute;
    top: 12mm;
    left: 12mm;
    right: 12mm;
    bottom: 12mm;
    border: 1px solid {accent_light};
  }}
  /* Corner ornaments via small absolute divs */
  .co {{ position: absolute; width: 24px; height: 3px; background: {accent}; }}
  .cov {{ position: absolute; width: 3px; height: 24px; background: {accent}; }}
  .content {{
    position: absolute;
    top: 16mm;
    left: 16mm;
    right: 16mm;
    bottom: 12mm;
  }}
  .power-bar {{
    position: absolute;
    bottom: 10mm;
    left: 20mm;
    right: 20mm;
    height: 2px;
    background: {accent};
  }}
</style>
</head>
<body>
<div class="page">

  <!-- Outer decorative border -->
  <div class="outer-border"></div>
  <div class="inner-border"></div>

  <!-- Corner ornaments: top-left -->
  <div class="co" style="top:12mm; left:12mm;"></div>
  <div class="cov" style="top:12mm; left:12mm;"></div>
  <!-- top-right -->
  <div class="co" style="top:12mm; right:12mm;"></div>
  <div class="cov" style="top:12mm; right:12mm;"></div>
  <!-- bottom-left -->
  <div class="co" style="bottom:12mm; left:12mm;"></div>
  <div class="cov" style="bottom:12mm; left:12mm;"></div>
  <!-- bottom-right -->
  <div class="co" style="bottom:12mm; right:12mm;"></div>
  <div class="cov" style="bottom:12mm; right:12mm;"></div>

  <!-- Gradient accent bar -->
  <div class="power-bar"></div>

  <!-- Main content -->
  <div class="content">

    <!-- ── HEADER: QR | Logo+Name | Track ── -->
    <table width="100%" cellpadding="0" cellspacing="0"
           style="margin-bottom:3mm;">
      <tr>
        <!-- QR code -->
        <td width="80" style="vertical-align:top; text-align:left;">
          {qr_img_tag}
          <div style="font-family:Inter,Arial,sans-serif; font-size:5pt;
                      color:{on_muted}; text-align:center; margin-top:2px;">
            Scan to Verify
          </div>
        </td>
        <!-- Company logo + name -->
        <td style="text-align:center; vertical-align:middle;">
          {company_img_tag}
          <div style="font-family:'Space Grotesk',Arial,sans-serif;
                      font-size:12pt; font-weight:bold; color:{primary};
                      margin-top:2px;">
            TECHNO FUTURE
          </div>
          <div style="font-family:Inter,Arial,sans-serif; font-size:7.5pt;
                      font-weight:bold; color:{accent}; margin-top:1px;">
            Empowering Tomorrow's Innovators
          </div>
        </td>
        <!-- Track logo -->
        <td width="80" style="vertical-align:top; text-align:right;">
          {track_img_tag}
        </td>
      </tr>
    </table>

    <!-- ── TITLE BLOCK ── -->
    <div style="text-align:center; margin-bottom:3mm;">
      <div style="font-family:'Space Grotesk',Arial,sans-serif;
                  font-size:30pt; font-weight:bold; color:{primary};">
        TECHNO FUTURE
      </div>
      <div style="font-family:'Space Grotesk',Arial,sans-serif;
                  font-size:12pt; font-weight:bold; color:{accent};
                  margin-top:1mm;">
        Certificate of Achievement
      </div>
      <!-- Underline bar -->
      <div style="width:70px; height:3px; background:{accent};
                  margin:2mm auto 0;"></div>
    </div>

    <!-- ── BODY: recipient ── -->
    <div style="text-align:center; margin-bottom:3mm;">
      <div style="font-family:Inter,Arial,sans-serif; font-size:8pt;
                  font-weight:bold; color:{on_muted};">
        THIS CERTIFICATE IS PROUDLY PRESENTED TO
      </div>
      <div style="font-family:'Space Grotesk',Arial,sans-serif;
                  font-size:20pt; font-weight:bold; color:{primary};
                  border-bottom:2px solid {accent};
                  display:inline-block; padding-bottom:2px; margin-top:2mm;">
        {student_name}
      </div>
      <div style="font-family:'Space Grotesk',Arial,sans-serif;
                  font-size:13pt; font-weight:bold; color:{accent};
                  margin-top:2mm;">
        {course_name}
      </div>
      <div style="font-family:Inter,Arial,sans-serif; font-size:9pt;
                  color:{on_muted}; margin-top:1mm;">
        {level}
      </div>
      <div style="font-family:Inter,Arial,sans-serif; font-size:8.5pt;
                  color:{on_muted}; margin-top:2mm; max-width:480px;
                  margin-left:auto; margin-right:auto;">
        For successfully completing all required coursework and demonstrating
        excellence in the concepts and practical skills covered in this program.
      </div>
    </div>

    <!-- ── META ROW: Date &amp; Branch ── -->
    <table width="60%" cellpadding="0" cellspacing="0"
           style="margin:0 auto 3mm;">
      <tr>
        <td style="text-align:center; width:50%;">
          <div style="font-family:Inter,Arial,sans-serif; font-size:7pt;
                      font-weight:bold; color:{on_variant};">DATE</div>
          <div style="font-family:Inter,Arial,sans-serif; font-size:10pt;
                      font-weight:bold; color:{on_bg};">{date_str}</div>
        </td>
        <td style="text-align:center; width:50%;">
          <div style="font-family:Inter,Arial,sans-serif; font-size:7pt;
                      font-weight:bold; color:{on_variant};">BRANCH</div>
          <div style="font-family:Inter,Arial,sans-serif; font-size:10pt;
                      font-weight:bold; color:{on_bg};">{branch}</div>
        </td>
      </tr>
    </table>

    <!-- ── SIGNATURES ── -->
    {sig_row}

    <!-- ── FOOTER ── -->
    <div style="text-align:center; margin-top:4mm;">
      <div style="font-family:Inter,Arial,sans-serif; font-size:7pt;
                  color:{on_variant};">
        Techno Future — Official Academic Document
      </div>
      <div style="display:inline-block; font-family:Arial,monospace;
                  font-size:7pt; font-weight:bold; color:{primary};
                  background:{surface_low}; padding:2px 8px; margin-top:2px;">
        ID: {cert_id}
      </div>
    </div>

  </div><!-- /content -->
</div><!-- /page -->
</body>
</html>"""


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


def render_pdf(
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
) -> bytes:
    """Render certificate PDF via headless Chromium (Playwright).

    Builds the same HTML that render_html() produces (pixel-perfect browser
    output) and prints it to PDF using a real Chromium instance — so the PDF
    is identical to what you see in the browser.
    """
    # Build the same high-fidelity HTML used for browser preview
    html_content = render_html(
        student_name=student_name,
        course_name=course_name,
        course_track=course_track,
        level=level,
        issue_date=issue_date,
        branch=branch,
        cert_id=cert_id,
        instructor=instructor,
        director=director,
        custom_color=custom_color,
        verify_url=verify_url,
    )

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()

            # Load HTML directly — all assets are already base64-embedded
            page.set_content(html_content, wait_until="networkidle")

            # Print to PDF: landscape A4, no browser margins, background graphics on
            pdf_bytes = page.pdf(
                format="A4",
                landscape=True,
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            browser.close()
            return pdf_bytes

    except Exception as exc:
        log.error("Playwright PDF rendering failed: %s", exc)
        raise RuntimeError(f"PDF rendering failed: {exc}") from exc


