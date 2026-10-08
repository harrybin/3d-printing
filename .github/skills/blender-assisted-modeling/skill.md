---
name: blender-assisted-modeling
description: Use local Blender through a controlled MCP workflow for organic or visual geometry while preserving measured datums and validating every exported mesh.
---

# Blender-assisted modeling

Use Blender for organic, sculptural, relief, character, cloth-like, or visually
complex geometry that is inefficient to express as parametric engineering solids.
Do not use it merely because Blender is available.

Python remains the source of truth for dimensions, mating surfaces, bores, fasteners,
clearances, keyed joints, and other fit-critical geometry.

## Tool routing

| Feature | Owner |
| --- | --- |
| Measured envelope, datums, fit surfaces, holes, joints | Python/build123d |
| Organic shell, sculpted detail, visual surface transitions | Blender |
| Simple transforms, arrangement, centering | `mesh_tool.py` |
| Mesh integrity and feature proof | `validate-stl-mesh` |
| Final print settings and time | `orcaslicer-print-validation` |

For mixed objects, export the technical geometry as frozen reference bodies. Lock or
otherwise protect them in Blender. Sculpt only the explicitly allowed region.

## Availability and installation

Detect Blender from the current PATH, common platform install locations, registered
applications, or an explicit user path. PATH absence alone does not prove Blender is
not installed.

If Blender or the selected MCP integration is unavailable, ask whether the user
wants to install or enable it. Installing software or an add-on requires explicit
approval. If declined, continue with the repo's Python, photo, relief, visual-hull,
and render-compare workflows and state the quality limitation.

Prefer the official Blender Lab MCP Server and current official installation
instructions. Re-check version requirements before setup; do not copy stale commands
from this skill.

The repository template is `.vscode/mcp.json`; set `BLENDER_MCP_DIR` locally rather
than committing a machine-specific path. Setup details and the security checklist
are in `docs/mcp-setup.md`.

## MCP safety

Blender MCP can execute Python with the permissions of the Blender process.

- Bind only to localhost. Never expose the server port publicly.
- Do not process secrets or unrelated sensitive files in the Blender session.
- Prefer a virtual machine or a system without access to sensitive data, as
  recommended by the official Blender MCP security warning.
- Save a checkpoint `.blend` before agent-controlled changes.
- Prefer bounded structured tools over arbitrary Python execution.
- Review generated Python before execution when arbitrary code is necessary.
- Execute small operations, inspect the result, and keep recoverable checkpoints.
- Never install or enable an add-on without user approval.

## Scene contract

Before editing:

1. Set scene units to millimeters and verify imported scale with a known dimension.
2. Name objects by role: `frozen_*`, `organic_*`, `color_*`, `cutting_*`.
3. Record which objects and datums are frozen.
4. Keep each intended color, material, or separately printed body as a distinct
   object.
5. Preserve origin and coordinate conventions needed by the repo and slicer.

## Modeling workflow

1. Run `research-reusable-3d-assets` before original modeling.
2. Import the licensed asset or Python-generated technical reference.
3. Validate scale and compare bounds with the measurement document.
4. Perform only the planned Blender operations: sculpt, retopology, modifiers,
   boolean refinement, relief, material/object separation, or render comparison.
5. Apply modifiers deliberately; do not hide unresolved non-manifold geometry behind
   the viewport result.
6. Compare renders with accepted photo landmarks when the work is reference-driven.
7. Export each printable object separately using millimeter scale, plus an assembly
   export when needed.

Avoid destructive decimation of fit surfaces. Keep detail no finer than the target
nozzle and layer height can reproduce.

## Roundtrip validation

After every important export:

- validate each body with `scripts/mesh_tool.py validate`
- compare bounds, scale, component count, and frozen datum positions with the
  pre-Blender source
- prove critical features with probes or slices
- check for self-intersections, open edges, inverted normals, zero-area faces, and
  unintended internal shells
- render the exported file, not merely the live Blender scene

If a fit-critical datum moved, the component count changed unexpectedly, or repair
would alter intended geometry, reject the export and return to the last checkpoint.
Do not rely on slicer auto-repair as the source fix.

## Deliverables

Keep:

- the `.blend` source for reproducible organic edits
- exported per-body meshes
- the source/licensing document
- render-compare evidence when photos drove the shape

Then hand off to `multimaterial-assembly-packaging`,
`optimize-stl-for-print`, and `orcaslicer-print-validation`.

## Sources

- Official Blender Lab MCP Server:
  https://www.blender.org/lab/mcp-server/
- Blender Lab MCP source:
  https://projects.blender.org/lab/blender_mcp
- Blender unit settings:
  https://docs.blender.org/manual/en/latest/scene_layout/scene/properties.html#units
