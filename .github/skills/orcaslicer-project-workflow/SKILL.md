---
name: orcaslicer-project-workflow
description: Slice and inspect this repository's STL/3MF outputs with standard OrcaSlicer through the pinned local MCP server.
---

# OrcaSlicer project workflow

Use this skill after geometry has passed `scripts/mesh_tool.py validate`.

## Repository integration

The project pins `ShreddyKrueger75/claude-orcaslicer-mcp` at commit
`b1a7cd13c853a733e09367f18d3c183f04c349d9` through
`tools/orcaslicer-mcp-requirements.txt`. It is MIT licensed and works with the
standard OrcaSlicer CLI. The alternative live-GUI server from
`MaxEllis/orcaslicer-mcp` requires a special OrcaSlicer fork and is therefore
not the default for this repository.

Run `scripts/setup_orcaslicer_mcp.ps1` once. The checked-in `.vscode/mcp.json`
then exposes the server to compatible clients.

Before the first headless slice, finish OrcaSlicer's setup wizard and save one
named machine, process and filament preset. Stop with a clear message when
`list_profiles` returns an empty category; do not invent preset names.

## Rules

- Use MCP for slicing, profile inspection and G-code analysis only.
- Prefer the OrcaSlicer CLI or the audited local MCP for all slicer work. Use
  Computer Use only to start/stop OrcaSlicer when no CLI/MCP path is available,
  or to enable/configure that MCP; once enabled, return to CLI/MCP and do not
  drive the slicer GUI for routine slicing.
- Do not configure a printer, upload G-code or start a print unless the user
  explicitly requests that separate physical action.
- Prefer the Anycubic Kobra S1 profile already configured in OrcaSlicer.
- Pin the actual bed type; never accept OrcaSlicer's implicit Cool Plate
  default.
- Validate geometry before slicing; slicer success does not prove a watertight
  mesh.
- For multi-material files, verify object-to-filament mapping and include a
  preview that shows the material regions.
- For complex assemblies, preserve the assembled presentation 3MF separately and
  create one printable OrcaSlicer project 3MF per material/spool group. A project
  may contain multiple plates when all same-material parts cannot fit the 250 mm
  bed together.
- Every printable project must embed the exact Anycubic Kobra S1 0.4 mm machine
  preset, explicit Textured PEI bed, matching filament preset, global process
  settings tuned to that material, complete BOM quantities, and per-object
  overrides for functional differences such as pins versus shells. Verify these
  values from `Metadata/project_settings.config` and
  `Metadata/model_settings.config`; a neutral 3MF with only mesh/color metadata
  is not print-ready.
- Unless a project documents a specific exception, generated OrcaSlicer 3MFs
  must set `seam_position=random`, `ironing_type=top` ("All top surfaces") and
  `enable_support=1`. Verify all three keys in
  `Metadata/project_settings.config`. Keep automatic support enabled even for
  parts expected to need none, so a zero-support slice is evidence about the
  geometry instead of a suppressed setting.
- TPU projects must state that flexible filament is fed from the external spool
  unless the installed feeder is explicitly rated for that TPU.
- Never assume a filament the user does not own. Confirm the available
  materials first and prefer a single-material (PLA) solution; a living hinge
  can be redesigned as a 0.8 mm PLA film hinge instead of requiring TPU.
- Report layer height, walls, infill, supports, estimated time and filament.
- Every generated 3MF, including neutral assembly 3MFs, must contain
  `Metadata/ghouls_grip_print_metadata.xml` with the standard print-time,
  filament-usage, printer, nozzle, layer, material, support, infill and plate
  fields. Use `unknown` and `status=not-verified` until a successful slice
  provides measured values; never invent estimates. The STL Canvas displays
  these fields.

## Ghoul's Grip defaults

- 0.20 mm layer height, 0.4 mm nozzle.
- Random seam position and ironing on all top surfaces.
- Every part is printed in PLA; only the filament colour changes between the
  four spool-group projects. Bone parts and fingers share bone-beige PLA and one
  plate. Do not reintroduce PETG or TPU without asking.
- Rigid shells and mechanism: 4-5 walls, 20-40 % Gyroid.
- PLA film-hinge fingers: 2 walls so the 0.8 mm web is exactly two perimeters,
  15 % Gyroid, 30 mm/s outer wall, reduced acceleration.
- +0.10 mm hole compensation as a starting point.
- Print one arm/pin/spacer fit coupon before committing the full job.
