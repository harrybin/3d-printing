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

When updating geometry in a saved multi-plate project, preserve unaffected mesh
payloads, settings, plate membership and build transforms. Align each changed
mesh to its original transformed bed-contact plane; bounds-centering alone can
put a taller replacement below Z=0. OrcaSlicer 2.4.2 crashed during plate loading
for the below-bed crank, but sliced all five plates after correcting this source
export datum. Do not hide this by rearranging or resetting user settings.
Require one successful G-code per original plate and retain its diagnostics.

CLI profile loading (verified with OrcaSlicer 2.4.2): pass the system profile JSON
files from `C:\Program Files\OrcaSlicer\resources\profiles\Anycubic\{machine,process,filament}`
directly to `--load-settings "<machine>;<process>"` and `--load-filaments <filament>`.
Hand-flattened copies of those profiles fail with exit code `-17`
(`CLI_PROCESS_NOT_COMPATIBLE`), even with emptied compatibility lists.

Computer Use is a fallback only: use it to start or stop OrcaSlicer when no
usable CLI/MCP path exists, or to enable/configure the local MCP. Once a CLI or
MCP path is available, perform slicing and inspection through that path rather
than driving the GUI.

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

Do not infer `support-free` from a project whose support setting is `none`.
Generated projects keep `enable_support=1` by default for exactly this reason.
Validate that claim with automatic support enabled at the intended threshold,
then confirm the generated G-code contains neither support nor support-interface
paths. Also record the analytical maximum ceiling/bridge span; zero generated
support does not override a span beyond the repository limit.

## Required report

Write `docs/<model>-druckvalidierung.md` or update the model's existing validation
document with:

- OrcaSlicer version
- source file hash or unambiguous path and modification time
- printer, nozzle, process, and filament profile names
- plate number and included objects
- orientation and arrangement
- layer height and layer count
- seam position and ironing type
- estimated print time
- filament length, mass, and cost when configured
- support material mass, length and volume whenever supports are generated;
  recover the share from the G-code by summing positive extruder deltas under
  `;TYPE:Support` and `;TYPE:Support interface` and scaling it with the
  slicer's own mm-to-mass ratio per plate. Respect `M82`/`M83` extrusion modes
  and `G92` resets; exclude extruder-only retraction/unretraction movements.
  State `none` only for a slice that produced
  no support path at all.
- supports, brim/raft, bridges, and notable overhangs
- material/color changes and purge impact when available
- slicer warnings and their resolution
- status: `verified`, `failed`, or `not verified`

Capture a slicer preview for every delivered print plate. For multi-color output,
the preview must make the assigned regions visible.

Also render a complete-project preview for every delivered 3MF at
`docs/images/<3mf-stem>-preview.png`. For every successfully sliced plate,
render `docs/images/<3mf-stem>-plate-<n>-supports.png` from that plate's actual
G-code, including a clearly labeled result when no support extrusion was
generated. Do not create support screenshots for an unsliced plate or infer
support paths from the mesh alone. These sidecars are exposed as buttons in the
STL Canvas extension and Web viewer, including each plate's expandable print
details; if an image is unavailable, hide or disable its button with an
explanation.

## 3MF metadata contract

Every generated project 3MF must include a slicer-neutral metadata part named
`Metadata/ghouls_grip_print_metadata.xml`. It must expose, at minimum:

- `estimatedPrintTimeSeconds`
- `filamentUsageGrams`
- `filamentUsageMillimeters`
- `filamentUsageCubicMillimeters`
- `supportFilamentGrams`
- `supportFilamentMillimeters`
- `supportFilamentCubicMillimeters`
- printer, nozzle, process/layer height, filament/material, bed, supports,
  infill, wall loops, and plate count
- `plateDetails`: an ordered JSON array containing each plate's name, status,
  print time, filament usage and support usage using the same field names as
  the project totals

Values that are not backed by a successful slice must be `unknown`, with
`status=not-verified`; never invent estimates. The STL Canvas reads and displays
these fields alongside mesh and plate information. Its top summary always shows
project totals, independent of the selected plate; the bottom collapsible details
also show the per-plate breakdown. Missing support data is not a zero-support proof.
After a successful slice,
patch the same metadata entry with the exact slicer-reported values and set
`status=verified`.

## Acceptance

`verified` requires:

- successful slicing with the intended profiles
- no unresolved collision, out-of-bed, empty-layer, or invalid-toolpath warning
- removable supports where supports are used
- acceptable bridges, first layer, seams, and color/material transitions
- random seam placement, ironing on all top surfaces and enabled automatic
  support are present unless a documented project-specific exception overrides
  the repository default
- recorded print time and material estimate from that successful slice

Do not call a model print-ready when OrcaSlicer validation failed or was skipped.

## Sources

- OrcaSlicer CLI actions:
  https://www.orcaslicer.com/wiki/cli/cli_actions
- OrcaSlicer project:
  https://github.com/SoftFever/OrcaSlicer
