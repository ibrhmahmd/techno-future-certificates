"""
Certificate validation helpers.
"""

import random
import string
from datetime import date, datetime

from app.modules.certificates.constants import (
    CERT_ID_PREFIX,
    TRACK_PREFIXES,
    TRACK_KEYS,
    LEVELS,
    TRACK_COLORS,
)


def validate_track_exists(track_key: str) -> bool:
    """Check if a track key is valid."""
    return track_key in TRACK_KEYS.values()


def validate_level_exists(level: str) -> bool:
    """Check if a level is valid."""
    return level in LEVELS


def validate_date_not_future(d: date) -> bool:
    """Check if a date is not in the future."""
    return d <= date.today()


def validate_hex_color(color: str) -> bool:
    """Check if a string is a valid hex color."""
    if not color.startswith("#") or len(color) != 7:
        return False
    try:
        int(color[1:], 16)
        return True
    except ValueError:
        return False


def validate_cert_id_format(cert_id: str) -> bool:
    """Check if a cert ID matches the expected format TKTF-XXX-YYYYMMDD-XXXX."""
    parts = cert_id.split("-")
    if len(parts) != 4:
        return False
    prefix, track, date_str, hex_part = parts
    if prefix != CERT_ID_PREFIX:
        return False
    if len(track) < 2 or not track.isalpha():
        return False
    if len(date_str) != 8 or not date_str.isdigit():
        return False
    if len(hex_part) != 4:
        return False
    try:
        int(hex_part, 16)
        return True
    except ValueError:
        return False


def generate_cert_id(course_track: str, issue_date: date) -> str:
    """
    Generate a unique certificate ID.
    Format: TKTF-{TRACK_PREFIX}-{YYYYMMDD}-{4HEX}
    """
    # Find prefix from track key
    prefix = None
    for name, key in TRACK_KEYS.items():
        if key == course_track:
            prefix = TRACK_PREFIXES[name]
            break

    if prefix is None:
        raise ValueError(f"Unknown track key: {course_track}")

    date_str = issue_date.strftime("%Y%m%d")
    hex_suffix = "".join(random.choices(string.hexdigits[:16], k=4)).upper()

    return f"{CERT_ID_PREFIX}-{prefix}-{date_str}-{hex_suffix}"


def get_track_display_name(track_key: str) -> str:
    """Get the display name for a track key."""
    for name, key in TRACK_KEYS.items():
        if key == track_key:
            return name
    raise ValueError(f"Unknown track key: {track_key}")


def get_track_color(track_key: str, custom_color: str | None = None) -> str:
    """Get the accent color for a track, with optional custom override."""
    if custom_color and validate_hex_color(custom_color):
        return custom_color
    colors = TRACK_COLORS.get(track_key)
    return colors[0] if colors else "#333333"
