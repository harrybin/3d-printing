# OrcaSlicer support-minimization report

## Status

- Result: `blocked`
- Selected candidate: `lid-tapered-pocket-roofs`
- Final project path: `models/ghouls-grip-print-black-pla.3mf`
- Final project SHA-256: `pending final commit`
- Geometry changes applied: tapered lid pocket roofs only
- Final validation status: mesh and mechanism checks passed; fresh Orca re-slice pending

## Exact input

- Absolute input path:
- Input kind: `STL | printable 3MF | presentation/master 3MF`
- SHA-256:
- Size:
- Modification time:
- OrcaSlicer version: GUI 2.4.3 available; prior CLI evidence used 2.4.2

## Fixed profiles and policy

- Printer preset: `Anycubic Kobra S1 ...`
- Nozzle diameter:
- Bed type:
- Process preset:
- Layer height:
- Filament preset(s), slot(s), and color/material:
- Support type/style:
- Support threshold/settings:
- Brim/raft policy:
- Other fixed overrides:

## Preserved project semantics

- Plate count:
- Plate names/order:
- Objects per plate:
- Material grouping:
- Object/volume-to-filament mapping:
- Modifiers/per-object overrides:
- Presentation master preserved at:
- Differences from baseline other than selected orientation/placement: `none | ...`

## Functional constraints

- Load directions and critical features:
- Fit/datum/mating surfaces:
- Show surfaces:
- Seam-sensitive surfaces:
- Forbidden orientations:

## Orientation candidates

All rotations are absolute from the frozen baseline, not chained.

| ID | Datum/intent | X° | Y° | Z° | Position/plate | Support filament/volume/time | Total time/material | Bed/first layer/stability | Bridges/overhangs | Seams/surfaces/dimensions | Strength | Status/reason |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | Existing project orientation | 0 | 0 | 0 | black plate 2 | not exposed | not exposed | not exposed | 746.68 mm² unsupported at 45°; 16,110.24 mm² ceiling-like bridge area | preserved | preserved | superseded |
| lid-tapered-pocket-roofs | Existing orientation with tapered underside pockets | 0 | 0 | 0 | black plate 2 | not exposed | not exposed | not exposed | 746.68 mm² unsupported at 45°; short tapered transitions replace broad pocket roofs | preserved | preserved | selected, re-slice pending |

For every numeric metric, identify the source:
`Orca summary | 3MF slice data | G-code | parser`. Use `not exposed` rather than an
estimate.

## Ranking and decision

1. Rejected candidates and hard rejection reason: Chest skirt frustum; downstream
   rail/service-cut booleans became invalid.
2. Viable candidates ranked by support amount: Lid tapered-pocket rebuild is the
   only geometry candidate that remained valid.
3. Selected candidate rationale: It removes broad horizontal pocket roofs while
   preserving lid envelope, hinge datums, and printed orientation.
4. Why lower-support alternatives, if any, were rejected: No second candidate
   was accepted without a successful Orca comparison.

## Selected-candidate printability review

- Support contact/removal/scarring:
- Bed contact and first-layer continuity:
- Center of mass, height/footprint, and stability:
- Bridges, unsupported islands, and overhangs:
- Seam locations:
- Functional and visible surface quality:
- Hole/bore/mating/datum dimensional risk:
- Anisotropic strength/load path:
- Material changes, purge, and wipe tower:
- Slicer warnings and resolution:

## Required evidence

Store paths relative to the repository or report an immutable artifact location.

- Baseline prepare view: full plate, axes/orientation visible
- Baseline sliced support-type preview
- Baseline first-layer preview
- Baseline support/statistics summary
- Each candidate prepare view: same camera where practical
- Each candidate sliced support-type preview
- Each candidate first-layer preview
- Each candidate support/statistics summary
- Selected candidate layer preview at critical bridges/overhangs
- Selected candidate seam preview
- Selected candidate material/filament-color preview for multi-material projects
- Selected candidate per-plate preview for every plate
- Reopened final-project prepare view and successful re-slice evidence

Every preview record must include:

- file path
- candidate ID and plate
- OrcaSlicer version
- printer/nozzle/process/filament presets
- view/color scheme
- layer or layer range when applicable
- capture timestamp

## Final project metadata

- Absolute selected project path:
- SHA-256 after save:
- Per-object absolute rotations:
- Per-object positions and plate IDs:
- Printer preset:
- Nozzle:
- Bed:
- Process/layer height:
- Filament presets and mappings:
- Support settings:
- Plate count:
- Estimated total time:
- Total filament length/volume/mass:
- Support-only filament/volume/time: `value + source | not exposed`
- Layer count:
- Tool changes:
- Wipe-tower volume/cost:
- Brim/raft:
- Warnings:
- Reopen/re-slice timestamp and result: blocked; GUI project is open, but the
  installed GUI did not expose a completed slice result in the automation
  surface. No new time/material claim is made.

## Bounded source-model suggestions

Complete only when substantial supports remain. Do not apply these changes in this
workflow.

| Proposed source-model change | Target feature | Likely support effect | Risk | Verification needed | User decision |
| --- | --- | --- | --- | --- | --- |

Required statement:

> These suggestions were not applied. Rounded edges are not universally better:
> downward fillets can worsen supports, while suitable chamfers and
> self-supporting arches are usually more support-friendly. Any geometry change
> requires a subsequent user decision, an edit to the authoritative source model,
> regeneration, mesh validation, and a new slicer comparison.

## Acceptance checklist

- [ ] Exact input path/hash and complete profiles recorded
- [x] Baseline sliced (previous geometry)
- [ ] Candidates use stable absolute datum rotations
- [ ] OrcaSlicer CLI runs were sequential
- [ ] Material grouping and multi-plate semantics preserved
- [ ] Actual support metrics recorded where exposed; unavailable values marked
- [ ] First layer, stability, bridges, overhangs, seams, surfaces, dimensions, and strength reviewed
- [ ] Mechanically or dimensionally unacceptable candidates rejected
- [ ] Selected orientation saved in 3MF without overwriting authoritative STL
- [ ] Final project reopened and re-sliced
- [ ] Required previews and metadata captured
- [ ] Geometry suggestions, if any, remain unapplied pending user decision
- [x] `orcaslicer-print-validation` explicitly blocked pending fresh slice
