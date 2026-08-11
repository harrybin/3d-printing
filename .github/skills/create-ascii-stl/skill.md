---
name: create-ascii-stl
description: Create ASCII STL files using print-safe defaults for Anycubic Kobra S1 Combo + ACE Pro.
---

# Create ASCII STL

Use this skill to generate new STL files for FDM printing.

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
