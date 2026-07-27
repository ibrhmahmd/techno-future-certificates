# Design System — Generated Documents

**Precision Engine v3.0** · Techno Kids, Techno Future

All generated documents (team timelines, student profiles) MUST follow this system. The shared CSS (`assets/shared.css`) is the single source of truth. The script (`generate_team_doc.ps1`) emits HTML using these classes and only adds CSS variable overrides + timeline-specific components inline.

---

## Core Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `--primary` | `#000000` | Headings, strong emphasis |
| `--primary-container` | `#131b2e` | Dark code blocks, table headers |
| `--secondary` | `#006a61` | Links, completed badge text |
| `--secondary-fixed` | `#89f5e7` | Highlights on dark backgrounds |
| `--secondary-container` | `#e0f5f1` | Completed badge background |
| `--on-secondary-container` | `#004d46` | Text on completed badges |
| `--tertiary` | `#7671ff` | Gradient power bar, instructor note accents |
| `--tertiary-light` | `#a5a1ff` | Lighter variant |
| `--surface` | `#f8f9ff` | Gray section backgrounds |
| `--surface-container` | `#e5eeff` | Inline code, table alternating rows, muted badges |
| `--surface-container-low` | `#eff4ff` | Arabic block backgrounds |
| `--surface-container-lowest` | `#ffffff` | White section backgrounds |
| `--on-background` | `#0b1c30` | Body text |
| `--on-surface-muted` | `#5A6070` | Secondary text, metadata |
| `--on-surface-variant` | `#7a8090` | Tertiary text, labels |
| `--error` | `#D32F2F` | Errors, warnings, in-progress badge text |
| `--error-container` | `#FFF5F5` | Warning backgrounds, in-progress badge bg |
| `--track-accent` | per-category | Primary accent (overridden per-config) |
| `--track-accent-light` | per-category | Lighter accent variant |

## Typography

| Role | Font | Weights |
|------|------|---------|
| Headings | Space Grotesk | 500, 600, 700 |
| Body | Inter | 400, 500, 600, 700 |
| Code / Mono | JetBrains Mono | 400, 500 |
| Arabic | Segoe UI / Tahoma | 400 |

Google Fonts import:
```
https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Space+Grotesk:wght@500;600;700&display=swap
```

## Spacing & Radii

| Token | Value |
|-------|-------|
| `--radius-sm` | 4px |
| `--radius-md` | 6px |
| `--radius-lg` | 8px |

## Per-Category Accent Colors

Each config overrides `--track-accent` and `--track-accent-light` via inline CSS variables. Defaults:

| Category | Accent | Hex |
|----------|--------|-----|
| Software | Teal | `#006a61` |
| Healthcare | Teal | `#0d9488` |
| Game | Teal | `#006a61` |
| Marketing | Amber | `#d97706` |

## Cover Page

Every document starts with a `.cover` section:
- Centered layout, gradient background
- Top accent bar via `::before`
- `.brand` label (mono, uppercase, accent color)
- `h1` for team/student name
- `.subtitle` for category + timeline
- `.cover-bar` accent divider
- `.cover-meta` for member/instructor details

## Section Pattern (Alternating)

All documents use alternating white/gray sections:
- **White sections** (`.sec-white`): `background: #fff`
- **Gray sections** (`.sec-gray`): `background: var(--surface)` (`#f8f9ff`)

Section headers use `.section-label` (mono, uppercase, accent) + `h2`.

## Status Badges

Use `.badge` base class with status variants:

| Status | Class | Background | Text |
|--------|-------|------------|------|
| Completed | `.badge-success` | `var(--secondary-container)` | `var(--on-secondary-container)` |
| In Progress | `.badge-error` | `var(--error-container)` | `var(--error)` |
| Upcoming | `.badge-muted` | `var(--surface-container)` | `var(--on-surface-muted)` |

## Stat Cards

Use `.stat-grid` container with `.stat-card` children:
- `.stat-num` — large number (heading font, accent color)
- `.stat-label` — small label (mono, uppercase, muted)

## Horizontal Rules

Gradient power bar — `hr.power-gradient`:
```css
background: linear-gradient(90deg, var(--track-accent), var(--tertiary));
height: 2px; border: none; margin: 20px 0;
```

## Print Rules

- `@page { size: A4 portrait; margin: 14mm 12mm; }`
- Force color: `-webkit-print-color-adjust: exact; print-color-adjust: exact;`
- Avoid page breaks: `page-break-inside: avoid;` on cards, tables, code blocks
- PDF generation: Edge headless `--print-to-pdf-no-header`

## Rules

1. **No external dependencies** — all CSS is from `assets/shared.css` + minimal inline overrides
2. **No frameworks** — vanilla HTML/CSS only
3. **One design system** — every generated doc uses these exact tokens and classes
4. **snake_case everywhere** — file names, directory names, config keys
5. **Script emits shared.css classes** — `.badge-*`, `.stat-grid`/`.stat-card`, `.cover`, `.section-label`, `h2`; only timeline components (`.tl-v-*`, `.chips`, `.skills`) are script-specific
