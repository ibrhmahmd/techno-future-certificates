"""
Central configuration — paths, track maps, color tokens.
Pure Python, zero Streamlit imports.
"""

from pathlib import Path

# ─── Paths ───
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = (BASE_DIR / "certificates.db").resolve()
COMPANY_LOGO = (BASE_DIR / "assests" / "logo.png").resolve()
CSS_PATH = (BASE_DIR / "certificate_style.css").resolve()
FONTS_DIR = (BASE_DIR / "assests" / "fonts").resolve()
TEMPLATE_PATH = (BASE_DIR / "certificate_template.html").resolve()

# ─── Track Metadata ───
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
    "html":                     ("#c62828", "#ff6659"),
    "css":                      ("#1565c0", "#5e92f3"),
    "javascript":               ("#f9a825", "#ffd95a"),
    "python":                   ("#2e7d32", "#60ad5e"),
    "advanced":                 ("#6a1b9a", "#9c4dcc"),
    "problem_solving":          ("#e65100", "#ff833a"),
    "robotics-wedo":            ("#7c4dff", "#b388ff"),
    "robotics-spike-essential": ("#00c853", "#69f0ae"),
    "robotics-spike-prime":     ("#388e3c", "#81c784"),
    "robotics-ev3":             ("#1976d2", "#64b5f6"),
    "robotics-arduino":         ("#ff6d00", "#ffab40"),
    "scratch":                  ("#ffab19", "#ffc966"),
    "scratch-jr":               ("#4d97ff", "#85b8ff"),
}

LEVEL_LABELS = {
    "Level 1 — Junior": "Level 1 — Junior",
    "Level 2 — Intermediate": "Level 2 — Intermediate",
    "Level 3 — Advanced": "Level 3 — Advanced",
}
