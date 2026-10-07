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
- Do not configure a printer, upload G-code or start a print unless the user
  explicitly requests that separate physical action.
- Prefer the Anycubic Kobra S1 profile already configured in OrcaSlicer.
- Pin the actual bed type; never accept OrcaSlicer's implicit Cool Plate
  default.
- Validate geometry before slicing; slicer success does not prove a watertight
  mesh.
- For multi-material files, verify object-to-filament mapping and include a
  preview that shows the material regions.
- Report layer height, walls, infill, supports, estimated time and filament.

## Ghoul's Grip defaults

- 0.20 mm layer height, 0.4 mm nozzle.
- PLA/PETG hard parts: 4-5 walls, 20-40 % Gyroid.
- TPU fingers: 3 walls, 15 % Gyroid, low acceleration.
- +0.10 mm hole compensation as a starting point.
- Print one arm/pin/spacer fit coupon before committing the full job.
