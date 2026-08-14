---
name: validate-stl-mesh
description: Validate STL meshes for manifold correctness and FDM printability readiness.
---

# Validate STL Mesh

Use this skill to evaluate whether an STL is ready for slicing and printing.

## Input

Accept one of the following: (1) a file path to an STL file, (2) raw ASCII STL text pasted inline, or (3) a JSON representation of mesh data with fields: triangles[], normals[], vertices[]. If input format is unrecognized, respond with an error explaining accepted formats.
If the provided input cannot be parsed or validated (e.g., binary data is not accessible, file is corrupted, or triangle data is missing), return a critical error in the output with the message: "Input could not be parsed - provide ASCII STL text or structured mesh data."

## Geometry integrity checks

- Valid STL syntax - detect format (ASCII vs binary) by header inspection and validate accordingly.
- Triangle count > 0
- No NaN/invalid vertices
- Watertight/manifold mesh
- No self-intersections
- No zero-area or degenerate triangles
- Consistent outward normals
- Single connected component unless separate bodies are intentional (check `mesh.split(only_watertight=False)`)

## Repair recipe for CAD-kernel exports (session-verified)

OCCT-based exporters (build123d, CadQuery) frequently produce STLs that are not watertight even though the solid is valid. Apply this lossless repair before failing the mesh:

1. `vertices = np.round(vertices, 3)` (0.001 mm grid, print-neutral)
2. `merge_vertices()`, then `unique_faces()` and `nondegenerate_faces()`
3. Re-check watertightness and re-export as ASCII STL if it passes.

Diagnosis guidance when repair does not converge:

- Open edges = 0 but not watertight -> non-manifold edges. Count edge occurrences (`edges_sorted`); edges used by more than 2 faces usually come from **tangential knife-edge contact** between design contours. Fix in the source geometry by overlapping the solids, not in the mesh.
- Never use pymeshfix on thin-walled or multi-chamber parts: its smallest-component removal deletes valid geometry.
- Coarser rounding than 0.01 mm collapses thin features and creates new open edges; do not exceed it.

## Feature-presence checks (session-verified)

Mesh statistics say nothing about whether a requested feature was actually built in the right place. When a change adds or moves an internal feature, prove it:

- **Volume probe:** intersect the mesh with a box covering the expected feature volume and compare volumes.

  ```python
  b = trimesh.creation.box(extents=np.subtract(hi, lo))
  b.apply_translation(np.add(lo, hi) / 2)
  ratio = trimesh.boolean.intersection([mesh, b], engine="manifold").volume / b.volume
  ```

  Report three numbers: the feature volume (expect ~100%), the space directly above/beside it (expect low), and the mirrored position on the opposite side (expect low). Equal values on both sides mean the feature is missing or symmetric by accident.

- `mesh.contains()` and `mesh.section(...).to_planar()` require `shapely` and `rtree`, which are **not** in the project `.venv`. Use the boolean-intersection probe above instead of installing them.

- The **Euler number** encodes topology and is a cheap regression guard: a solid with two through-holes must report `-2`. A change in Euler number after a geometry edit means a hole or handle appeared or vanished.

- Re-run the same probes after every subsequent geometry change and after merges, so an unrelated edit cannot silently remove the feature.

## Manufacturing checks (FDM)

If no nozzle size is specified by the user, assume 0.4 mm as the default. If a different nozzle diameter is provided, scale minimum wall thickness to 2x nozzle diameter and functional recommendation to 3x nozzle diameter.
For placement, a created object should always be placed at the center of a 25 cm x 25 cm build plate (250 mm x 250 mm).

Placement validation rule:

- Compute XY bounds and XY center from mesh vertices.
- Support two coordinate conventions for a 250 mm x 250 mm bed:
  - `center-origin` convention: centered means XY center at (0, 0)
  - `corner-origin` convention: centered means XY center at (125, 125)
- If the user specifies a convention, use it.
- If the user does not specify convention, auto-detect from coordinates:
  - if any XY vertex is negative, prefer `center-origin`
  - otherwise prefer `corner-origin`
- If detection is ambiguous, default to `corner-origin` to match common slicer build-plate coordinates.
- A model is considered centered when its XY center is within +/-0.01 mm of the convention target.

Automatic correction rule:

- If the user asks to "correct", "fix", "adjust", or "make it valid", and the mesh is otherwise valid but not centered, apply a translation to all vertices so that the model XY center matches the active convention target, preserving Z values and orientation.
- Report the applied translation vector (dx, dy, dz) and updated bounds in the output.
- If input is inline STL text (not a file path), return corrected ASCII STL text in full.
- If input is a file path, update that STL file in place.

- Wall thickness against nozzle profile:
  - 0.4 nozzle minimum: 0.8 mm practical baseline
  - functional recommendation: 1.2 mm+
- Overhang analysis:
  - <=45 degrees safe baseline
  - 45-60 degrees conditionally printable
  - > 60 degrees likely support needed
- Bridges and unsupported spans flagged
- Feature-size and text legibility checks

## Fit and tolerance checks

- Press fit recommendation: ~0.20 mm
- General fit recommendation: ~0.30 mm
- Sliding fit recommendation: ~0.40 mm

## Output format

Return:

- pass/fail
- critical errors
- warnings
- recommended fixes
- mesh stats (bounds, facets, unique vertices)
- placement status (centered/not centered), including convention (`center-origin` or `corner-origin`)
- applied transform (if auto-correction was requested and performed)

## Mandatory canvas preview after auto-correction

If this validation writes or rewrites an STL file (e.g., the centering auto-correction updates a file in place), the corrected file must be shown in the STL canvas right afterwards.

- Call `open_canvas` with `canvasId: "stl-canvas"` and `input.stlPath` set to the workspace-relative path under `models/`.
- Use a stable `instanceId` such as `stl-preview` so the panel refreshes instead of stacking.
- If the canvas fails to open (extension unavailable or `stl_not_found`), report the failure and the file path explicitly.
- Pure read-only validation without file changes does not require opening the canvas, but it is still recommended.

## Source

- Prusa modeling for 3D printing in mind  
  https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135
