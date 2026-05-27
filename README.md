# Drill Hole 3D Concept Model

This repository now contains a reproducible script that builds a **3D conceptual drillhole model** from the provided table/image data.

## Outputs

Running the script generates:

- `drillhole_model_3d.html` — interactive 3D scene with:
  - drill traces from collar, azimuth, dip, and final depth,
  - mineralized intervals colorized by grade,
  - approximate topographic surface,
  - conceptual strike-extension vector,
  - orbit controls for clean animation.
- `contained_sb_estimate.json` — interval-by-interval and total conceptual contained antimony estimate.

## Run

```bash
python3 model_drillholes.py
```

Then open `drillhole_model_3d.html` in a browser.

## Math used (contained antimony)

For each interval:

- `length = to_m - from_m`
- `true_width = length * TRUE_WIDTH_FACTOR` (default `0.7`)
- `volume = STRIKE_EXTENSION_M * true_width^2` (default strike extension `120 m`)
- `rock_tonnes = volume * density` (default density `3.6 t/m^3`)
- `contained_sb_tonnes = rock_tonnes * grade_pct / 100`

This is a **conceptual targeting estimate**, not a compliant resource calculation.

## Accuracy notes

- Drill collar and interval inputs are taken directly from the provided screenshot table.
- Topography is an approximate reconstruction from local collar elevations and map cues.
- Strike extension is a proposed vector for planning and visualization.

