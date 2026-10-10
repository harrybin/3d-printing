---
name: orcaslicer-support-minimization
description: Minimize supports in delivered STL/3MF print projects by comparing controlled OrcaSlicer orientation candidates while preserving project semantics; use when a final print project needs support-focused orientation and placement review without source-geometry edits.
---

# OrcaSlicer support minimization

Use this skill when the user wants a delivered STL or OrcaSlicer 3MF inspected
and re-oriented to reduce support. This workflow may change orientation and
placement inside the print project. It must not edit source geometry or replace an
authoritative generator STL with a rotated mesh.

## Required input contract

Do not start candidate slicing until all of these are known:

1. Exact final input path. Resolve it to an absolute path and record file size,
   modification time, and SHA-256.
2. Exact Anycubic Kobra S1 machine preset and nozzle diameter.
3. Exact process preset, including layer height and support policy.
4. Exact filament preset for every material/color slot.
5. Intended material grouping, object-to-filament mapping, plate membership, and
   whether the input is a presentation 3MF or a printable project.
6. Functional load direction, fit-critical surfaces, show surfaces, seam-sensitive
   surfaces, and any orientation the user has forbidden.

Stop rather than inventing profile names or using an implicit bed/profile default.
Hold machine, nozzle, process, filament, bed type, support settings, and object
count constant across candidates.

## Safety and scope

- Run `validate-stl-mesh` before slicing. Slicer success does not prove mesh
  correctness.
- Work from the exact delivered input, never an earlier export or another
  worktree.
- Preserve object identity, scale, material assignment, modifiers, per-object
  settings, assembly relations, plate membership, and multi-plate ordering.
- Do not merge, split, clone, reassign materials, or move objects between plates
  merely to improve the score.
- Do not use `--assemble` for an existing multi-object or multi-material project.
- Do not enable arrangement options that mix material groups or collapse
  multi-plate semantics.
- Never run two OrcaSlicer CLI processes concurrently. Slice candidates and plates
  sequentially because OrcaSlicer may share profile/cache state.
- Verify every intended CLI option against the installed executable's `--help`;
  behavior varies by version.
- CLI transform flags are order-dependent. Record their exact order.
- Do not use `--no-check`.
- Never upload G-code or start a physical print under this skill.

## Workflow

### 1. Freeze the baseline

1. Record OrcaSlicer version and the required input/profile metadata.
2. Inspect the input with `--info` and, for 3MF, inspect project settings, object
   transforms, plate assignments, and filament mappings.
3. Slice the unchanged baseline first.
4. Save baseline metrics and previews before testing any orientation.
5. Create candidate projects in a temporary/output workspace. Do not mutate the
   sole copy of the input.

### 2. Define stable orientation candidates

Define rotations from the same frozen baseline coordinate system. Never obtain
candidate C by rotating candidate B.

Use a bounded candidate set based on named datums:

- `baseline`: existing project orientation
- `datum-bottom`: intended manufactured base face down
- `datum-back`: stable back/reference face down
- `x+90`, `x-90`, `x180`
- `y+90`, `y-90`, `y180`
- a deliberately justified 45-degree candidate only when a real datum, bridge,
  load path, or support interface makes it meaningful
- OrcaSlicer auto-orient as an advisory candidate, not an automatic winner

Record each candidate as absolute X/Y/Z rotations from baseline plus its datum
description. Deduplicate geometrically equivalent candidates. Keep the set small
enough to explain and reproduce.

For multi-object projects, preserve assembly-relative transforms unless the project
already defines independently printable loose parts. If independent objects may be
oriented separately, record each object's absolute rotation and keep it on its
original plate and filament group.

### 3. Position without changing semantics

Place each candidate fully on the intended bed and retain safe spacing, purge/wipe
structures, calibration regions, and sequential-print clearance where applicable.
Check that a support-saving rotation has not created a narrow or point-like first
layer, a tall unstable lever arm, or an unfavorable center of mass.

Auto-arrange may be used only after locking orientation behavior and material/plate
constraints. Confirm the resulting project still has the same plates, objects, and
filament assignments.

### 4. Slice candidates sequentially

For each candidate, in a separate sequential OrcaSlicer invocation:

1. Load the same machine, nozzle, process, filament, bed, and support settings.
2. Apply the recorded absolute datum rotation and placement.
3. Slice every affected plate.
4. Export or save a candidate 3MF and G-code/slice data when supported.
5. Capture the required prepare and sliced-preview evidence.
6. Record warnings and metrics before starting the next candidate.

Prefer explicit rotations such as `--rotate-x`, `--rotate-y`, and `--rotate` over
unrecorded manual drift. Use `--ensure-on-bed` only after confirming it does not
hide an incorrect datum or unintended below-bed geometry.

### 5. Inspect printability, not support alone

Inspect every candidate for:

- support footprint, interface area, support contact locations, removal access,
  and risk of scarring
- bed-contact area, first-layer continuity, small islands, brim need, and
  elephant-foot exposure on fit surfaces
- center of mass, height-to-footprint ratio, collision/wobble risk, and tall
  cantilevers
- bridge direction and span, unsupported islands, overhang severity, and cooling
  exposure
- seam placement and whether seams land on fit, cosmetic, sealing, or sliding
  surfaces
- downward-facing and support-facing functional surface quality
- holes, bores, pins, mating faces, datum faces, and dimensional accuracy
- anisotropic strength: reject orientations that put critical tension, bending,
  snap, hinge, hook, or fastener loads mainly across weak Z-layer bonds
- multi-material transitions, purge/wipe impact, and preservation of mappings

Rounded edges are not universally better. A downward-facing fillet can create a
progressively steeper overhang and worsen support demand or underside quality.
Chamfers and self-supporting arches are usually more support-friendly, subject to
the proven printer/profile overhang capability.

### 6. Measure support and job metrics

Use actual data from the successful slice:

- total print time
- total filament length, volume, and mass
- support filament length, volume, mass, and support-attributable time when
  OrcaSlicer, embedded slice data, or generated G-code explicitly exposes them
- support/interface material by filament slot when dedicated support material is
  used
- layer count, tool changes, wipe-tower volume/cost, brim/raft, and warnings

Do not estimate a support-only value by subtracting unrelated totals or by visual
guessing. If OrcaSlicer exposes only whole-job values, record support-specific
filament/volume/time as `not exposed` and keep the visual support evidence.
Record the extraction source for every metric: OrcaSlicer summary, 3MF slice data,
G-code comment/statistic, or deterministic parser output.

### 7. Rank and select

Rank viable candidates by:

1. least actual support material/volume first
2. least support contact on functional or visible surfaces
3. lower total time/material and easier support removal
4. better bed contact and stability
5. better bridges, seams, functional surface quality, dimensional behavior, and
   load-path strength

Support amount is the primary optimization target, but it is not a permission to
accept a mechanically weak, unstable, out-of-tolerance, or visibly damaged
orientation. Mark those candidates `rejected` before ranking the survivors.

When support-specific quantity is not exposed, rank using the slicer's support
preview and contact/interface evidence, clearly labeling the metric limitation.

### 8. Write only the selected project orientation

Write the winning transforms and positions into the delivered OrcaSlicer print
project or a clearly named successor 3MF. Preserve the untouched authoritative STL
or source-generated mesh. Never export a rotated STL over that source file.

Reopen and re-slice the selected saved project, then verify that its hashes,
profiles, plates, mappings, transforms, metrics, and previews match the selected
candidate. Run `orcaslicer-print-validation` as the final printability gate.

## High-support outcome: suggestions only

If substantial support remains after viable orientation candidates, do not edit
geometry. Add a bounded suggestion table with no more than the few changes most
likely to help:

| Candidate source-model change | Target feature | Likely support effect | Functional/visual risk | Verification needed |
| --- | --- | --- | --- | --- |
| 45-degree chamfer | Downward horizontal edge | Replaces an abrupt overhang with a self-supporting ramp | Alters edge shape or mating envelope | Clearance and surface review |
| Teardrop/diamond hole | Horizontal circular bore | Reduces support inside the bore | Changes bore profile and fit assumptions | Pin/fastener fit test |
| Self-supporting arch | Opening/bridge | Shortens unsupported spans | Alters silhouette and stress distribution | Load and dimension check |
| Split part | Complex undercut | Allows each part to use a favorable orientation | Adds seam, joint, and assembly tolerance | Joint/load validation |
| Sacrificial bridge | Internal gap | Gives the slicer a removable printable span | Requires cleanup and access | Removal/access test |
| Rounded/angled local transition | Abrupt local underside | May smooth load transfer or remove a local cliff | A downward fillet can worsen support | Section and overhang review |
| Removable support tab | Narrow unstable feature | Adds controlled bed/support contact | Leaves cleanup witness | Removal and finish test |
| Relocate interface | Support-sensitive mating/show face | Moves support damage away from critical surface | Changes assembly or datum scheme | Assembly and tolerance review |

State explicitly: these are proposals, not approved edits. Do not apply them until
the user makes a subsequent decision and the authoritative source model is edited
and regenerated.

## Acceptance and reporting

Use `assets/support-minimization-report.md` for every run.

Acceptance requires:

- exact input and profile contract recorded
- baseline plus bounded stable-datum candidates evaluated from one frozen baseline
- OrcaSlicer CLI runs performed sequentially
- material grouping and multi-plate semantics unchanged
- candidate metrics and required preview evidence captured
- weak, unstable, dimensionally bad, or surface-damaging candidates rejected
- selected transforms saved in a 3MF print project, not baked over a source STL
- selected project reopened and re-sliced successfully
- remaining high-support geometry changes listed only as unperformed suggestions
- final validation handed to `orcaslicer-print-validation`

## Edge cases

- **Input is STL:** create a settings-bearing OrcaSlicer 3MF for orientation and
  slicing; keep the STL unchanged.
- **Presentation/master 3MF:** do not overwrite it. Create or update the appropriate
  printable project while preserving the master assembly.
- **Multiple plates:** baseline and selected evidence are required per plate; do not
  flatten plates.
- **Multiple materials:** preserve object/volume-to-filament assignments and capture
  a material-colored preview.
- **Auto-orient disagrees with function:** function, strength, fit, and surface
  requirements override the automated score.
- **Metrics unavailable:** report `not exposed`; never invent values.
- **Slicer repairs geometry:** stop and return to the source-model/mesh workflow
  instead of treating repair as support optimization.

## References

See `references/sources.md` for authoritative OrcaSlicer CLI/project behavior and
FDM orientation/support guidance.
