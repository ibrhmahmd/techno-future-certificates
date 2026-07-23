"""
Pure helpers — cert ID generation, filenames, base64 encoding, QR, color utils.
Zero Streamlit imports.
"""

import base64
import datetime
import os
import re
import uuid
from io import BytesIO
from pathlib import Path

from core.config import COMPANY_LOGO, FONTS_DIR, TRACK_DATA_ATTR, TRACK_LOGOS

# ─── Library availability flags ───
QRCODE_AVAILABLE = False
try:
    import qrcode  # noqa: F401
    QRCODE_AVAILABLE = True
except ImportError:
    pass

PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.sync_api import sync_playwright  # noqa: F401
    PLAYWRIGHT_AVAILABLE = True
except Exception:
    pass

XHTML2PDF_AVAILABLE = False
try:
    from xhtml2pdf import pisa  # noqa: F401
    XHTML2PDF_AVAILABLE = True
except Exception:
    pass


# ─── Cert ID ───
def generate_cert_id(track_name: str, date: datetime.date) -> str:
    short = track_name.split("\u2014")[0].strip()[:3].upper()
    date_str = date.strftime("%Y%m%d")
    uid = uuid.uuid4().hex[:4].upper()
    return f"TKTF-{short}-{date_str}-{uid}"


# ─── Filenames ───
def sanitize_filename(text: str) -> str:
    clean = re.sub(r"[^\w\s-]", "", text).strip()
    clean = re.sub(r"[\s_]+", "_", clean)
    return clean or "Certificate"


def build_download_filename(student_name: str, course_name: str, ext: str) -> str:
    safe_student = sanitize_filename(student_name)
    safe_course = sanitize_filename(course_name)
    return f"{safe_student}_{safe_course}_Certificate.{ext.lstrip('.')}"


# ─── Base64 / Assets ───
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


# ─── QR Code ───
def generate_qr_code(text: str) -> str:
    if not QRCODE_AVAILABLE:
        return ""
    import qrcode as _qrcode

    qr = _qrcode.QRCode(version=1, box_size=4, border=1)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0a0e1a", back_color="#ffffff")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"


# ─── Color Utility ───
def lighten_hex(hex_color: str, factor: float = 0.55) -> str:
    """Derive a printable-friendly lighter variant by blending toward white."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    lr = int(r + (255 - r) * factor)
    lg = int(g + (255 - g) * factor)
    lb = int(b + (255 - b) * factor)
    return f"#{lr:02x}{lg:02x}{lb:02x}"
