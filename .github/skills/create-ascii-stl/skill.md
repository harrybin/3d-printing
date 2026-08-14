---
name: create-ascii-stl
description: Create ASCII STL files using print-safe defaults for Anycubic Kobra S1 Combo + ACE Pro.
---

# Create ASCII STL

Use this skill to generate new STL files for FDM printing.

## Mandatory library usage

Never write STL facets or triangle lists by hand and never assemble complex geometry from manually computed vertices. Always generate geometry through a parametric Python script (in `scripts/`, run with the project venv `.venv`) using these libraries from `requirements.txt`:

| Task                                                                                 | Library                                |
| ------------------------------------------------------------------------------------ | -------------------------------------- |
| Engineering solids: sketches, extrusions, countersinks, bosses, ribs, hulls, fillets | **build123d** (OCCT kernel)            |
| Simple prismatic CSG, mesh loading, repair, validation, ASCII export                 | **trimesh** + **manifold3d**           |
| Numeric parameters and vertex post-processing                                        | **numpy**                              |
| Offscreen rendering for visual verification                                          | **vedo**                               |
| Photo/video frame analysis for reference comparison                                  | **opencv-python-headless**, **pillow** |

Hand-written meshes (raw `Trimesh(vertices, faces)` constructions, manual `solid ... endsolid` text) are only acceptable for trivial primitives that the libraries cannot express more simply — and even then a library primitive (`trimesh.creation.box`, `Cylinder`, `convex_hull`) is preferred.

## Inputs to collect first

- Target dimensions (mm)
- Material (PLA/PETG/ABS/ASA/TPU)
- Use case (display, fit-test, functional load-bearing)
- Multi-color requirement (ACE Pro): yes/no
- Do not generate any STL output until all four inputs are confirmed. If any input is missing, ask for it explicitly before proceeding.

## Hard constraints

- Use **millimeters**.
- Output valid ASCII STL (`solid ... endsolid`) unless binary is explicitly requested.
- Triangles only, with outward normals and manifold mesh.
- Keep the model centered or explicitly origin-aligned as requested.

## Proven toolchain (session-verified)

- For engineering shapes (countersinks, bosses, ribs, hulled contours, fillets), build the solid with **build123d** (OCCT kernel) instead of hand-assembled trimesh primitives. Conical countersinks must blend directly into their bores (`Cone` from sink diameter to bore diameter) so no ledge or material gap remains.
- Model teardrop/egg outlines as the **hull of two intersecting circles** (`make_hull`), not as ellipse unions.
- Avoid tangential (knife-edge) contact between contours: it creates a non-manifold edge in the tessellation. Overlap solids by >= 1 mm instead.
- OCCT STL exports are often not watertight. Always re-export through trimesh: `vertices = round(vertices, 3)` -> `merge_vertices()` -> `unique_faces()` -> `nondegenerate_faces()` -> verify `is_watertight` -> `export(file_type="stl_ascii")`.
- Do **not** use pymeshfix on thin-walled or multi-chamber parts: it deletes geometry (`remove_smallest_components`).
- Keep trimesh + manifold3d for simple prismatic CSG and as the validation layer.
- Every generator script must print: facets, bounds, extents, watertight, winding consistency, volume, degenerate-face count.

## Anycubic Kobra S1 Combo defaults

- Stock nozzle: **0.4 mm** (supports 0.25/0.6/0.8 mm).
- Model minimum wall target for 0.4 nozzle:
  - visual/light duty: **0.8 mm**
  - functional baseline: **1.2 mm**
- Clearance defaults:
  - tight fit: **0.20 mm**
  - general fit: **0.30 mm**
  - easy/sliding fit: **0.40 mm**

## Best-practice geometry rules (research-backed)

- Prefer overhang angles <= **45 degrees** without support; angles between 45-60 degrees are marginal and must be flagged as a printability risk.
- Prefer chamfers over downward fillets when print-side finish matters.
- Split models into parts when it improves orientation and reduces support.
- Ensure tiny features are not thinner than one extrusion line.

## ACE Pro multi-color guidance

- Prefer separate solids/bodies for color regions.
- Put color boundaries on natural geometry breaks.
- Avoid tiny isolated color islands (reduces purge waste and print time).

## Output checklist

- ASCII STL is syntactically correct.
- Triangle count and bounding box are reported.
- Printability risks are reported (thin walls, steep overhangs, tiny details).
- If the requested geometry cannot be made printable within the stated constraints without fundamental redesign, explain the specific conflict and propose an alternative geometry before generating the STL.
- The finished STL was opened in the STL canvas and the previewed path is reported.

## Mandatory canvas preview after writing the STL

Every newly created STL file must be shown in the STL canvas immediately after it is written to disk. This step is not optional and must not be skipped, even if the user did not ask for a preview.

- Write the STL into the workspace `models/` folder first (the canvas only resolves workspace-relative paths).
- Then call `open_canvas` with `canvasId: "stl-canvas"` and `input.stlPath` set to the workspace-relative path, e.g. `models/bracket.stl`.
- Use a stable `instanceId` such as `stl-preview`, so repeated previews refresh the same panel instead of opening new ones.
- Optionally call the `read_stats` action on that instance and report facets and bounds together with the preview.
- If the canvas fails to open (extension unavailable or `stl_not_found`), report the failure and the file path explicitly instead of silently continuing.

## Sources

- Anycubic store: Kobra S1 Combo nozzle support and hotend data  
  https://store.anycubic.com/products/kobra-s1-combo
- Prusa best practices (overhangs, wall width, tolerances, manifold checks)  
  https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135
