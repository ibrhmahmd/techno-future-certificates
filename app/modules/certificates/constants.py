"""
Certificate module constants — single source of truth for tracks, levels, permissions.
"""

from typing import Literal

# ─── Certificate ID Format ───
CERT_ID_PREFIX = "TKTF"

# ─── Permission Keys ───
class Permissions:
    GENERATE = "certificates.generate"
    VERIFY = "certificates.verify"

# ─── Level Types ───
LevelType = Literal[
    "Level 1 — Junior",
    "Level 2 — Intermediate",
    "Level 3 — Advanced",
]

LEVELS: tuple[LevelType, ...] = (
    "Level 1 — Junior",
    "Level 2 — Intermediate",
    "Level 3 — Advanced",
)

# ─── Track Definitions ───
# Single source of truth: maps track display name to all metadata
TRACKS: dict[str, dict] = {
    "HTML — Web Structure": {
        "prefix": "HTM",
        "key": "html",
        "logo": "html_logo.png",
        "accent": "#c62828",
        "accent_light": "#ff6659",
        "data_attr": "html",
    },
    "CSS — Styling & Layout": {
        "prefix": "CSS",
        "key": "css",
        "logo": "css_logo.png",
        "accent": "#1565c0",
        "accent_light": "#5e92f3",
        "data_attr": "css",
    },
    "JavaScript — Interactivity": {
        "prefix": "JS",
        "key": "javascript",
        "logo": "js_logo.png",
        "accent": "#f9a825",
        "accent_light": "#ffd95a",
        "data_attr": "javascript",
    },
    "Python — Programming": {
        "prefix": "PY",
        "key": "python",
        "logo": "python_logo.png",
        "accent": "#2e7d32",
        "accent_light": "#60ad5e",
        "data_attr": "python",
    },
    "Advanced — Full Stack": {
        "prefix": "ADV",
        "key": "advanced",
        "logo": "js_logo.png",
        "accent": "#6a1b9a",
        "accent_light": "#9c4dcc",
        "data_attr": "advanced",
    },
    "Problem Solving — Logic": {
        "prefix": "PSL",
        "key": "problem_solving",
        "logo": "python_logo.png",
        "accent": "#e65100",
        "accent_light": "#ff833a",
        "data_attr": "problem_solving",
    },
    "Robotics — WeDo 2.0": {
        "prefix": "RWD",
        "key": "robotics-wedo",
        "logo": "wedo2.0_logo.png",
        "accent": "#7c4dff",
        "accent_light": "#b388ff",
        "data_attr": "robotics-wedo",
    },
    "Robotics — SPIKE Essential": {
        "prefix": "RSE",
        "key": "robotics-spike-essential",
        "logo": "spike-ess_logo.png",
        "accent": "#00c853",
        "accent_light": "#69f0ae",
        "data_attr": "robotics-spike-essential",
    },
    "Robotics — SPIKE Prime": {
        "prefix": "RSP",
        "key": "robotics-spike-prime",
        "logo": "spike-prime_logo.png",
        "accent": "#388e3c",
        "accent_light": "#81c784",
        "data_attr": "robotics-spike-prime",
    },
    "Robotics — EV3": {
        "prefix": "REV",
        "key": "robotics-ev3",
        "logo": "ev3_logo.png",
        "accent": "#1976d2",
        "accent_light": "#64b5f6",
        "data_attr": "robotics-ev3",
    },
    "Robotics — Arduino": {
        "prefix": "RARD",
        "key": "robotics-arduino",
        "logo": "pictoblox_logo.png",
        "accent": "#ff6d00",
        "accent_light": "#ffab40",
        "data_attr": "robotics-arduino",
    },
    "Scratch — Visual Programming": {
        "prefix": "SRC",
        "key": "scratch",
        "logo": "scratch_logo.png",
        "accent": "#ffab19",
        "accent_light": "#ffc966",
        "data_attr": "scratch",
    },
    "Scratch Jr — Early Learning": {
        "prefix": "SJR",
        "key": "scratch-jr",
        "logo": "scratch-jr_logo.png",
        "accent": "#4d97ff",
        "accent_light": "#85b8ff",
        "data_attr": "scratch-jr",
    },
}

# Lookup helpers
TRACK_KEYS: dict[str, str] = {name: data["key"] for name, data in TRACKS.items()}
TRACK_PREFIXES: dict[str, str] = {name: data["prefix"] for name, data in TRACKS.items()}
TRACK_COLORS: dict[str, tuple[str, str]] = {
    data["key"]: (data["accent"], data["accent_light"])
    for data in TRACKS.values()
}
TRACK_DATA_ATTRS: dict[str, str] = {
    name: data["data_attr"] for name, data in TRACKS.items()
}
VALID_TRACK_KEYS: frozenset[str] = frozenset(TRACK_KEYS.values())
