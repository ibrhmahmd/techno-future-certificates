# Certificate Generator

Official course completion certificates for **Techno Kids, Techno Future**.

Built on the Precision Engine v3.0 design system. Light & formal, print-ready, track-accent-aware.

---

## Quick Start — Streamlit App

```bash
cd certificates
streamlit run app.py
```

The app provides:
- Form with all certificate fields
- Auto-calculated sessions (4) and hours (8) per course
- Auto-generated unique certificate ID
- Live HTML preview
- One-click PDF download (A4 landscape)

### Requirements

```
streamlit
weasyprint
```

---

## Manual Usage (HTML Template)

1. Copy `certificate_template.html` to your working directory
2. Ensure `certificate_style.css` is in the same folder
3. Set the `data-track` attribute on `.certificate-page` to your track
4. Replace all `[placeholder]` values with actual data
5. Update logo `src` paths to match your file locations
6. Print: **Ctrl + P → Landscape A4 → No margins**

---

## Course Defaults

| Setting | Value |
|---------|-------|
| Sessions per course | 4 |
| Hours per session | 2 |
| Total hours per course | 8 |

---

## Supported Tracks

Set `data-track` on the `.certificate-page` div:

| Track | `data-track` value | Accent Color |
|-------|-------------------|--------------|
| HTML | `html` | Red `#c62828` |
| CSS | `css` | Blue `#1565c0` |
| JavaScript | `javascript` | Gold `#f9a825` |
| Python | `python` | Green `#2e7d32` |
| Advanced | `advanced` | Purple `#6a1b9a` |
| Problem Solving | `problem_solving` | Orange `#e65100` |
| Robotics — WeDo | `robotics-wedo` | Purple `#7c4dff` |
| Robotics — SPIKE Essential | `robotics-spike-essential` | Green `#00c853` |
| Robotics — SPIKE Prime | `robotics-spike-prime` | Green `#388e3c` |
| Robotics — EV3 | `robotics-ev3` | Blue `#1976d2` |
| Robotics — Arduino | `robotics-arduino` | Orange `#ff6d00` |

---

## Certificate ID Format

```
TKTF-{TRACK}-{YYYYMMDD}-{RANDOM4}
```

Example: `TKTF-HTML-20260722-A3F1`

Auto-generated per certificate. Unique via UUID4 fragment.

---

## Logo Paths

| Logo | Position | Path |
|------|----------|------|
| Company (Techno Kids) | Top-left | `assests/logo.png` |
| Track-specific | Top-right | `assests/{track}_logo.png` |

The Streamlit app resolves logos automatically via base64 embedding for PDF export.

---

## Directory Structure

```
certificates/
├── app.py                      ← Streamlit certificate generator
├── certificate_template.html   ← manual HTML template
├── certificate_style.css       ← shared styles (Precision Engine v3.0)
├── README.md                   ← this file
└── examples/
    ├── html_example.html
    ├── python_example.html
    └── robotics_example.html
```

---

## Design System Reference

- **Fonts**: Space Grotesk (title) + Inter (body)
- **Palette**: Light formal with per-track accent colors
- **Border**: Accent frame with corner ornaments
- **Power Bar**: Gradient accent bar at bottom
- **System**: Precision Engine v3.0 — `doc_templates/design-system-guide.md`
