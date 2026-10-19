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
- For a complex assembly, preserve one assembled `-view.3mf` separately from one
  consolidated, printable `-print.3mf`. Put all parts and spool groups in the
  print project; same-material/color parts should share plates when safe. Use
  additional plates inside that same file for bed limits, orientation, support
  clearance or print-risk isolation, rather than creating per-material projects.
  If it has a mechanism, the view file should show meaningful states on separate
  plates.
- The single printable project must embed the exact Anycubic Kobra S1 0.4 mm
  machine preset, explicit Textured PEI bed, each matching filament preset,
  per-object filament mapping, complete BOM quantities, material/process
  settings, and per-object overrides for functional differences such as pins
  versus shells. Verify these values from `Metadata/project_settings.config`
  and `Metadata/model_settings.config`; a neutral 3MF with only mesh/color
  metadata is not print-ready.
- Unless a project documents a specific exception, all generated OrcaSlicer 3MFs
  must set `layer_height <= 0.16` (`layer_height=0.16` default),
  `seam_position=random` (mandatory), `ironing_type=top` ("All top surfaces"),
  `enable_support=1`, `support_type=tree(auto)`, and a 1-layer Z contact
  distance (`support_top_z_distance=0.16`, `support_bottom_z_distance=0.16`,
  matching `layer_height`) for easy support tree removal after printing. Verify
  all of these keys in `Metadata/project_settings.config`. Keep automatic tree
  support enabled even for parts expected to need none, so a zero-support slice
  is evidence about the geometry instead of a suppressed setting.
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
- Render a complete-project preview for every 3MF as
  `docs/images/<3mf-stem>-preview.png`; multi-material project previews must
  preserve visible material/color regions.
- For every plate actually sliced, render a support-path image named
  `docs/images/<3mf-stem>-plate-<n>-supports.png` from that plate's G-code.
  Show an explicit no-support result when the G-code has no support extrusion;
  never synthesize support paths for an unsliced plate.
- The shared STL Canvas and Web viewer expose project-preview and per-plate
  support-preview buttons, including within expandable per-plate print
  details. Missing image assets must hide the action or disable it with an
  explanation; the web build copies these sidecars from `docs/images/`.

## Ghoul's Grip defaults

- `<= 0.16 mm` layer height (`0.16 mm` default), 0.4 mm nozzle.
- Random seam position (`seam_position=random`) and ironing on all top surfaces (`ironing_type=top`).
- Automatic tree supports (`enable_support=1`, `support_type=tree(auto)`) with 1-layer Z contact distance (`support_top_z_distance=0.16`, `support_bottom_z_distance=0.16`).
- Every part is printed in PLA using four color/spool assignments in the single
  project. Bone parts and fingers share bone-beige PLA and one plate. Do not
  reintroduce PETG or TPU without asking.
- Rigid shells and mechanism: 4-5 walls, 20-40 % Gyroid.
- PLA film-hinge fingers: 2 walls so the 0.8 mm web is exactly two perimeters,
  15 % Gyroid, 30 mm/s outer wall, reduced acceleration.
- +0.10 mm hole compensation as a starting point.
- Print one arm/pin/spacer fit coupon before committing the full job.
