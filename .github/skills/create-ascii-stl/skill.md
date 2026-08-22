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
- If multiple materials/colors are visible in the target object: whether these regions must remain distinct in the final model
- Final output format intent (STL vs 3MF) based on that material/color decision
- Do not generate any final output until all required inputs are confirmed. If any input is missing, ask for it explicitly before proceeding.

## Hard constraints

- Use **millimeters**.
- Output valid ASCII STL (`solid ... endsolid`) for single-material/single-region outputs.
- If the user requires distinct material/color regions, use **3MF** as the final deliverable format instead of STL.
- Triangles only, with outward normals and manifold mesh.
- Keep the model centered or explicitly origin-aligned as requested.

## Proven toolchain (session-verified)

- For engineering shapes (countersinks, bosses, ribs, hulled contours, fillets), build the solid with **build123d** (OCCT kernel) instead of hand-assembled trimesh primitives. Conical countersinks must blend directly into their bores (`Cone` from sink diameter to bore diameter) so no ledge or material gap remains.
- Model teardrop/egg outlines as a **three-arc construction**, never as `make_hull` of two circles. A convex hull joins the two circles with **straight tangent lines** (for a 19 mm head, a 10.85 mm tip and 12.55 mm centre distance that is a ~9.5 mm long flat), which is immediately visible on the part and gets rejected in photo comparison. Instead add flank arcs of radius `Rf` that are *internally* tangent to both end circles (the flank circle contains both), giving a continuously curved, G1-smooth outline:

  ```
  D  = distance between head centre C1 and tip centre C2   (tip along +t)
  oy = (D**2 + (r - R) * (2*Rf - R - r)) / (2*D)
  ox = -sqrt((Rf - R)**2 - oy**2)          # negative for the +x flank
  P1 = C1 + R * unit(C1 - O)               # tangent point on the head arc
  P2 = C2 + r * unit(C2 - O)               # tangent point on the tip arc
  ```

  Walk head arc -> flank arc around `O` -> tip arc, then mirror for the -x half, and feed the point list to build123d `Polygon(*pts, align=None)`. Larger `Rf` approaches the straight hull; smaller `Rf` bulges more. Pick `Rf` by overlaying candidates on a reference photo.

- **Offset property of the three-arc egg:** shrinking all three radii by the same wall thickness `t` leaves every arc centre unchanged. So one `egg_outline(head_r, tip_r, flank_r)` helper serves both the outer body and the inner pocket (`egg_outline(R - t, r - t, Rf - t)`), and the wall is automatically constant everywhere.
- Avoid tangential (knife-edge) contact between contours: it creates a non-manifold edge in the tessellation. Overlap solids by >= 1 mm instead. For a ledge that hugs a wall, extend it ~0.5 mm *into* that wall for the same reason.
- Sketch internal ledges, shelves and floor ribs on the plane they **sit on** (`Plane.XY.offset(floor_z)`) and extrude upwards. Sketching them in a side plane (`Plane.YZ`) and extruding across the cavity silently places a slab in mid-air where it is hidden behind bosses and ribs - a defect that looks like "the feature is missing" in the viewer.
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
- If color/material regions must be preserved in the output file, finalize as 3MF, not STL.

## Output checklist

- Output format is correct for intent (STL for merged single-region output, 3MF for preserved material/color regions).
- ASCII STL is syntactically correct when STL is the selected output format.
- Triangle count and bounding box are reported.
- Printability risks are reported (thin walls, steep overhangs, tiny details).
- If the requested geometry cannot be made printable within the stated constraints without fundamental redesign, explain the specific conflict and propose an alternative geometry before generating the output.
- For STL outputs: the finished STL was opened in the STL canvas and the previewed path is reported.
- For 3MF outputs: the written 3MF path is reported, and an STL counterpart preview is shown when available.

## Mandatory canvas preview after writing the output

Every newly created output file must be previewed immediately after it is written to disk. This step is not optional and must not be skipped, even if the user did not ask for a preview.

- Write the output into the workspace `models/` folder first (the canvas only resolves workspace-relative paths).
- For STL outputs, call `open_canvas` with `canvasId: "stl-canvas"` and `input.stlPath` set to the workspace-relative path, e.g. `models/bracket.stl`.
- For 3MF outputs, report the written 3MF path explicitly and preview an STL counterpart if one was also produced for inspection.
- Use a stable `instanceId` such as `stl-preview`, so repeated previews refresh the same panel instead of opening new ones.
- Optionally call the `read_stats` action on that instance and report facets and bounds together with the preview.
- If the canvas fails to open (extension unavailable or `stl_not_found`), report the failure and the file path explicitly instead of silently continuing.

## Sources

- Anycubic store: Kobra S1 Combo nozzle support and hotend data  
  https://store.anycubic.com/products/kobra-s1-combo
- Prusa best practices (overhangs, wall width, tolerances, manifold checks)  
  https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135
