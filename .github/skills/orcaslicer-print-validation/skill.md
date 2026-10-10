---
name: orcaslicer-print-validation
description: Perform the final OrcaSlicer printability gate and record the exact profile, print time, material use, supports, warnings, and preview evidence.
---

# OrcaSlicer print validation

Use this skill after geometry passes `validate-stl-mesh` and design-level
optimization passes `optimize-stl-for-print`. OrcaSlicer is the final authority for
the selected printer/process/filament combination, not for source mesh correctness.

## Availability

Detect OrcaSlicer from PATH, common install locations, registered applications, or a
user-provided executable. If it is missing, ask whether the user wants to install it.
Installation requires explicit approval.

If installation is declined or unavailable:

- continue repo mesh and analytical printability checks
- mark slicer validation as `not verified`
- do not invent print time, filament use, support volume, or purge values
- state that the model still requires a real slicer pass before printing

## Version and automation

Record the installed OrcaSlicer version. Verify supported CLI options against the
local executable's help before using them; CLI behavior can change between versions.
Use the GUI when the installed CLI cannot expose the required project, plate, or
preview information.

CLI profile loading (verified with OrcaSlicer 2.4.2): pass the system profile JSON
files from `C:\Program Files\OrcaSlicer\resources\profiles\Anycubic\{machine,process,filament}`
directly to `--load-settings "<machine>;<process>"` and `--load-filaments <filament>`.
Hand-flattened copies of those profiles fail with exit code `-17`
(`CLI_PROCESS_NOT_COMPATIBLE`), even with emptied compatibility lists.

The repository MCP template is `.vscode/mcp.json`, but the OrcaSlicer entry is
disabled by default because OrcaSlicer officially documents a CLI, not a first-party
MCP server. Only enable a third-party OrcaSlicer MCP after auditing its source,
license, local binding, and data handling. Otherwise use the official CLI and the
setup guidance in `docs/mcp-setup.md`.

## Required input contract

- exact final STL or 3MF path
- Anycubic Kobra S1 printer profile and nozzle diameter
- process/layer-height profile
- filament profile per material/color
- intended plate and part arrangement
- support policy

Do not report comparable print estimates unless these settings are held constant.

## Slice gate

1. Load the exact delivered model, not an earlier export or another worktree copy.
2. Confirm units, bounds, object count, plate assignment, and bed fit.
3. Assign the intended printer, nozzle, process, and filament profiles.
4. Slice every print plate.
5. Inspect layer preview, first layer, seams, bridges, supports, thin walls,
   unsupported islands, collisions, and color/material transitions.
6. Treat unexpected slicer repair as a source defect. Fix and re-export rather than
   silently accepting changed geometry.
7. Re-slice after every geometry, orientation, support, or profile change.

## Required report

Write `docs/<model>-druckvalidierung.md` or update the model's existing validation
document with:

- OrcaSlicer version
- source file hash or unambiguous path and modification time
- printer, nozzle, process, and filament profile names
- plate number and included objects
- orientation and arrangement
- layer height and layer count
- estimated print time
- filament length, mass, and cost when configured
- supports, brim/raft, bridges, and notable overhangs
- material/color changes and purge impact when available
- slicer warnings and their resolution
- status: `verified`, `failed`, or `not verified`

Capture a slicer preview for every delivered print plate. For multi-color output,
the preview must make the assigned regions visible.

## Acceptance

`verified` requires:

- successful slicing with the intended profiles
- no unresolved collision, out-of-bed, empty-layer, or invalid-toolpath warning
- removable supports where supports are used
- acceptable bridges, first layer, seams, and color/material transitions
- recorded print time and material estimate from that successful slice

Do not call a model print-ready when OrcaSlicer validation failed or was skipped.

## Sources

- OrcaSlicer CLI actions:
  https://www.orcaslicer.com/wiki/cli/cli_actions
- OrcaSlicer project:
  https://github.com/SoftFever/OrcaSlicer
