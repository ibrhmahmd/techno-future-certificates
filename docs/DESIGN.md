# Design System Document: The Precision Engine

## 1. Overview & Creative North Star
The "Precision Engine" is the creative North Star for this design system. We are moving away from the "generic SaaS dashboard" look toward a sophisticated, high-density environment that feels like a high-end flight deck or a professional laboratory. 

This design system rejects the "boxed-in" layout of traditional CRMs. Instead, it utilizes **Organic Command Control**—a layout strategy that relies on tonal layering, intentional asymmetry, and extreme typographic precision. We favor "breathing room" over borders and "depth" over dividers. For a robotics center, the UI should feel as engineered as the machines the students build: sleek, efficient, and undeniably powerful.

---

## 2. Colors: Tonal Architecture
We define space through color, not lines. This system utilizes a sophisticated Material-based palette where depth is created through shifting background values.

### Core Palette
- **Primary Architecture:** `#000000` (Primary) paired with `#131b2e` (Primary Container). This deep slate/navy creates an authoritative, tech-forward anchor.
- **Action Secondary:** `#006a61` (Secondary) and `#89f5e7` (Secondary Fixed). This vibrant teal is the heartbeat of the system, reserved for high-value actions and progress.
- **Tertiary Accents:** `#000000` (Tertiary) and `#7671ff` (Tertiary Container). Use this for data visualization or secondary highlights to break the monotony of the navy/teal.

### The "No-Line" Rule
**Explicit Instruction:** Traditional 1px solid borders are strictly prohibited for sectioning. 
- Use **Background Shifts:** Place a component using `surface_container_lowest` (#ffffff) on a `surface_container` (#e5eeff) background.
- Use **Nesting:** Tiered information should "step down" in surface color. An admin panel might sit on `surface_dim`, while individual student cards sit on `surface_container_lowest`.

### Signature Textures
- **The Power Gradient:** For primary buttons or hero data points, use a subtle linear gradient from `primary` to `primary_container`.
- **Glassmorphism:** For floating modals or "sticky" navigation, use a background of `surface` at 80% opacity with a `20px` backdrop-blur. This keeps the data-heavy environment feeling light and breathable.

---

## 3. Typography: Editorial Utility
We pair **Space Grotesk** (Display/Headline) with **Inter** (Body/Label) to create a "Technical-Editorial" aesthetic.

- **Display & Headlines (Space Grotesk):** These are the "Command" fonts. Use `display-lg` (3.5rem) for high-level metrics and `headline-sm` (1.5rem) for section titles. The wider apertures of Space Grotesk feel futuristic and robotics-adjacent.
- **Body & Labels (Inter):** Inter is our "Utility" font. For the data-heavy tables of a CRM, use `body-md` (0.875rem) with a tight letter-spacing (-0.01em) to maximize information density without sacrificing legibility.
- **Hierarchy through Scale:** Instead of bolding everything, use the contrast between `title-lg` and `label-sm` to create clear visual entry points.

---

## 4. Elevation & Depth: The Layering Principle
Forget "drop shadows." We build hierarchy through **Tonal Layering**.

- **Surface Stacking:** 
    1. Base: `surface` (#f8f9ff)
    2. Section: `surface_container_low` (#eff4ff)
    3. Card/Active Element: `surface_container_lowest` (#ffffff)
- **Ambient Shadows:** When a "lift" is required (e.g., a student profile modal), use an extra-diffused shadow: `box-shadow: 0 12px 40px rgba(11, 28, 48, 0.06)`. Note the shadow color—it is a tinted `on_surface` color, not neutral grey.
- **The "Ghost Border" Fallback:** If accessibility requirements demand a container edge, use `outline_variant` (#c6c6cd) at **15% opacity**. It should be felt, not seen.

---

## 5. Components: High-Density Primitives

### Buttons & Inputs
- **Primary Action:** Solid `secondary` (#006a61) with `on_secondary` text. `0.375rem` (md) corner radius. 
- **Ghost Input:** Inputs should not have a background. Use a `surface_container_high` bottom-border only (2px) to keep the layout feeling "Terminal-like."
- **Status Chips:** 
    - *Active/Paid:* `secondary_container` background with `on_secondary_container` text.
    - *Debt/Inactive:* `error_container` background with `on_error_container` text.

### High-Density Tables
- **Forbid Dividers:** Use `surface_container_low` for the header row and alternating `surface` and `surface_container_lowest` for rows.
- **Vertical Spacing:** Use `spacing-3` (0.6rem) for row padding to keep density high for admin efficiency.

### Relevant Robotics Context Components
- **The "Logic Node" Card:** A specialized card component for robotics curriculum tracking. Use a `tertiary_container` left-accent bar (4px) to distinguish educational modules from administrative tasks.
- **Availability Matrix:** A high-density grid for classroom scheduling using `surface_container_highest` for occupied blocks and `surface_variant` for empty ones.

---

## 6. Do's and Don'ts

### Do
- **Do** use `space-10` and `space-12` for large-scale layout margins to create an "expensive" feel.
- **Do** use `on_surface_variant` for secondary data in tables to create clear visual hierarchy.
- **Do** allow content to overlap slightly in "Advanced" views to emphasize the layered, glass-like UI.

### Don't
- **Don't** use 100% black text. Use `on_background` (#0b1c30) for better optical comfort during long admin shifts.
- **Don't** use standard "Blue" for links. Use the Teal `secondary` palette for all interactive intent.
- **Don't** use `radius-xl` on small components. Keep roundedness to `sm` or `md` for a more "precision tool" feel. Large radii are reserved only for main app containers.