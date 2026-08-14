# AGENTS

This repository contains parametric STL generation workflows for FDM printing on the Anycubic Kobra S1 Combo + ACE Pro.

## First Steps

1. Read [README.md](README.md) for project context and the image-to-STL workflow.
2. Use Python in the local virtual environment under `.venv`.
3. Treat scripts in `scripts/` as source of truth; regenerate STL files in `models/` instead of hand-editing mesh files.

## Build And Validation Commands

- Create environment:
  - `python -m venv .venv`
  - `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`
- Regenerate clip model:
  - `.\.venv\Scripts\python.exe scripts\lineal_clip_kappe.py`
- The generator already prints validation stats (facets, bounds, extents, watertight, winding consistency, Euler number, degenerate faces).

There is no separate test suite in this repo at the moment.

## Architecture Boundaries

- `scripts/`: parametric geometry definitions and boolean operations.
- `models/`: generated STL outputs (ASCII STL expected).
- `.github/skills/`: task-specialized behavior used by agents for STL creation, editing, and validation.

If behavior around print constraints, validation policy, or coordinate targeting changes, update both script logic and the relevant skill file so they stay aligned.

## Project Conventions

- Units are millimeters.
- Printer bed target is 250 mm x 250 mm.
- Coordinate convention supports both:
  - center-origin target `(0, 0)`
  - corner-origin target `(125, 125)`
- When convention is not explicitly provided, prefer auto-detection (negative XY implies center-origin; otherwise corner-origin).
- For fit-critical features, keep clearances explicit and parameterized (example: `PRESS_CLEAR` in `scripts/lineal_clip_kappe.py`).
- For mesh booleans, use the manifold engine and keep output watertight.
- Never hand-write STL facets or manual vertex/triangle lists for complex objects: always generate geometry through the Python libraries in `requirements.txt` (build123d for engineering solids, trimesh + manifold3d for CSG/repair/export, vedo for render checks, opencv for reference comparison).
- For engineering shapes (countersinks, bosses, ribs, hulled contours), prefer **build123d** for the solid and re-export through trimesh (round vertices to 0.001 mm, merge, dedupe faces) to guarantee a watertight ASCII STL.
- When recreating parts from photos/videos, run the render-and-compare loop (vedo offscreen renders vs. reference frames) before declaring the model done; see `.github/skills/stl-from-image-measurements/SKILL.md`.

## Common Pitfalls

- `manifold3d` must be installed, or boolean operations fail.
- OCCT exports (build123d) are often not watertight until the trimesh repair re-export runs; tangential knife-edge contours cause non-manifold edges and must be fixed by overlapping solids in the source geometry.
- `pymeshfix` deletes geometry on thin-walled multi-chamber parts; do not use it.
- Editing `models/*.stl` directly can desync files from their parametric source script.
- Fit tweaks should be made in script parameters, then regenerated and revalidated.
- User-edited measurement docs under `docs/` are authoritative; re-read them before every geometry change.

## Key References

- Project overview and workflow: [README.md](README.md)
- Clip generator implementation: [scripts/lineal_clip_kappe.py](scripts/lineal_clip_kappe.py)
- Printer/profile constraints: [.github/skills/anycubic-kobra-s1-ace-pro-profile/skill.md](.github/skills/anycubic-kobra-s1-ace-pro-profile/skill.md)
- STL validation policy: [.github/skills/validate-stl-mesh/skill.md](.github/skills/validate-stl-mesh/skill.md)
- Image-to-STL workflow: [.github/skills/stl-from-image-measurements/SKILL.md](.github/skills/stl-from-image-measurements/SKILL.md)

## Session-Learned Friction To Avoid

Recent sessions in this repo skew heavily toward mesh-quality issues. Default behavior should be:

1. Regenerate from script, do not patch triangles manually.
2. Confirm watertight/manifold status and degenerate-face count after each geometry change.
3. Re-check XY centering convention whenever moving or merging meshes.
