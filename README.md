# Drill Hole 3D Concept Model (Offline-capable)

This project builds a **fully offline** interactive 3D conceptual model from the provided drill collars and assay intervals.

## Why the old version failed
The earlier HTML relied on external CDN JavaScript (Three.js). If your browser/network blocked those URLs, you saw text only and no model.

This version embeds all logic directly in the generated HTML and requires **no internet**.

## Run (Windows PowerShell)
```powershell
cd path\to\Drill-hole-checker
python model_drillholes.py
```
(If `python` fails, run `py model_drillholes.py`.)

Then double-click `drillhole_model_3d.html` to open it.

## Outputs
- `drillhole_model_3d.html`
  - offline 3D canvas renderer
  - mouse rotate, zoom, pan
  - auto-rotate animation
  - toggle terrain / intervals
  - drill traces, mineralized intervals, strike extension vector
- `contained_sb_estimate.json`
  - assumptions + per-interval conceptual contained antimony calculation + total

## Math used
For each interval:
- `length = to_m - from_m`
- `true_width = length * TRUE_WIDTH_FACTOR` (default `0.7`)
- `volume = STRIKE_EXTENSION_M * true_width^2` (default `120 m`)
- `rock_tonnes = volume * density` (default `3.6 t/m³`)
- `contained_sb_tonnes = rock_tonnes * grade_pct / 100`

## Important
This is a **conceptual targeting visualization and scenario estimate**, not NI 43-101 / JORC compliant resource estimation.
