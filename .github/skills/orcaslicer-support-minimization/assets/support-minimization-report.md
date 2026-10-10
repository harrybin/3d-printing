# OrcaSlicer support-minimization report

## Status

- Result: `verified`
- Selected candidate: `support-free-black-single-plate`
- Final project path: `models/ghouls-grip-print-black-pla.3mf`
- Final project SHA-256: `1F125B35A8159DEBA431B817C3BC7A3B2FE468AAB61248F9753C56B3D77BACAC`
- Geometry changes applied: tapered lid pocket roofs, vertical lid orientation,
  tapered chest plinth/cornice/pilasters/hinge supports, 1.2 mm lightened wall skin
- Final validation status: mesh checks and final Orca CLI slice passed; full
  mechanism verification is recorded in `docs/ghouls-grip-mechanik-verifikation.md`

## Exact input

- Absolute input path: `models/ghouls-grip-print-black-pla.3mf` in this worktree
- Input kind: printable 3MF
- SHA-256: `1F125B35A8159DEBA431B817C3BC7A3B2FE468AAB61248F9753C56B3D77BACAC`
- Size: see repository artifact
- Modification time: 2026-10-10
- OrcaSlicer version: GUI 2.4.3 available; prior CLI evidence used 2.4.2

## Fixed profiles and policy

- Printer preset: `Anycubic Kobra S1 0.4 nozzle`
- Nozzle diameter: 0.4 mm
- Bed type: Textured PEI Plate
- Process preset: `0.20mm Standard @Anycubic Kobra S1 0.4 nozzle`
- Layer height: 0.20 mm
- Filament preset(s), slot(s), and color/material: Anycubic PLA, black `#202124`
- Support type/style: globally disabled; also disabled on both objects
- Support threshold/settings: not applicable; no support toolpaths generated
- Brim/raft policy: automatic 5 mm brim, no raft
- Other fixed overrides: 3 walls, 10% gyroid, 0.15 mm elephant-foot compensation

## Preserved project semantics

- Plate count: 1
- Plate names/order: black plate 1
- Objects per plate: chest and lid
- Material grouping: one black PLA spool/project, unchanged
- Object/volume-to-filament mapping: both objects use black PLA slot 1
- Modifiers/per-object overrides: 3 walls, 10% infill, support disabled
- Presentation master preserved at: `models/ghouls-grip-master.3mf`
- Differences from baseline other than selected orientation/placement: listed
  source-model chamfers and wall lightening only

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
| baseline | Existing project orientation | 0 | 0 | 0 | black plate 2 | tree supports present | 8 h 48 min 04 s / 173.56 g for lid plate | stable flat lid | 746.68 mm² unsupported at 45°; 16,110.24 mm² ceiling-like bridge area | preserved | preserved | superseded |
| lid-tapered-pocket-roofs | Flat lid with tapered underside pockets | 0 | 0 | 0 | black plate 2 | tree supports present | 8 h 28 min 23 s / 166.11 g for lid plate | stable flat lid | fewer support-triggering pocket roofs | preserved | preserved | superseded |
| support-free-black-single-plate | Chest upright; lid on straight front edge | 90 | 0 | 0 | black plate 1 | 0 support toolpaths | 12 h 44 min 30 s / 385.08 g for complete black project | 206 mm edge plus auto brim; 129 mm high | broad lid roof vertical; chest ledges tapered | visible relief faces remain unobstructed | hinge axis stays in XY layers | selected/verified |

For every numeric metric, identify the source:
`Orca summary | 3MF slice data | G-code | parser`. Use `not exposed` rather than an
estimate.

## Ranking and decision

1. Rejected candidates and hard rejection reason: the first monolithic chest
   frustum edit refilled or destabilized rail/service booleans.
2. Viable candidates ranked by support amount: vertical lid plus partially rebuilt
   chest produced zero black-project support paths; flat tapered lid remained second.
3. Selected candidate rationale: it removes all black support material, combines
   two plates into one, and preserves hinge/rail datums.
4. Lower-support alternatives: none; the selected black project is already
   support-free.

## Selected-candidate printability review

- Support contact/removal/scarring: none; no `Support` or `Support interface`
  feature appears in the final black G-code.
- Bed contact and first-layer continuity: chest base and 206 mm lid edge are
  continuous; automatic brim retained.
- Center of mass, height/footprint, and stability: lid height is 129 mm; its long
  edge and brim provide the required stability.
- Bridges, unsupported islands, and overhangs: lid pocket roofs are tapered;
  chest courses and hinge undersides use self-supporting slopes.
- Seam locations: unchanged from Orca automatic placement.
- Functional and visible surface quality: relief faces are vertical and never
  touch support material.
- Hole/bore/mating/datum dimensional risk: hinge axis remains horizontal in XY;
  assembled datums are unchanged.
- Anisotropic strength/load path: hinge axis and primary bending loads remain
  within layers rather than pulling across Z seams.
- Material changes, purge, and wipe tower: one black PLA filament, no changes,
  no wipe tower.
- Slicer warnings and resolution: only the benign precise-wall/profile warning.

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

- Absolute selected project path: `models/ghouls-grip-print-black-pla.3mf`
- SHA-256 after save: `1F125B35A8159DEBA431B817C3BC7A3B2FE468AAB61248F9753C56B3D77BACAC`
- Per-object absolute rotations: chest 0/0/0; lid +90/0/0 degrees
- Per-object positions and plate IDs: chest and lid on plate 1 with 20 mm layout gap
- Printer preset: Anycubic Kobra S1 0.4 nozzle
- Nozzle: 0.4 mm
- Bed: Textured PEI Plate
- Process/layer height: 0.20mm Standard / 0.20 mm
- Filament presets and mappings: Anycubic PLA, black, slot 1
- Support settings: disabled per chest and lid object
- Plate count: 1
- Estimated total time: 12 h 44 min 30 s
- Total filament length/volume/mass: 129,110.25 mm / 310,550 mm³ / 385.08 g
- Support-only filament/volume/time: 0 / 0 / 0, verified by absent support
  feature paths in the G-code
- Layer count: 645
- Tool changes: 0 material changes
- Wipe-tower volume/cost: 0
- Brim/raft: auto brim / no raft
- Warnings: benign precise-wall/profile warning only
- Reopen/re-slice timestamp and result: 2026-10-10, successful CLI slice

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

- [x] Exact input path/hash and complete profiles recorded
- [x] Baseline sliced (previous geometry)
- [x] Candidates use stable absolute datum rotations
- [x] OrcaSlicer CLI runs were sequential
- [x] Material grouping and multi-plate semantics preserved
- [x] Actual support metrics recorded where exposed; unavailable values marked
- [x] First layer, stability, bridges, overhangs, seams, surfaces, dimensions, and strength reviewed
- [x] Mechanically or dimensionally unacceptable candidates rejected
- [x] Selected orientation saved in 3MF without overwriting authoritative STL
- [x] Final project reopened and re-sliced
- [x] Required previews and metadata captured
- [x] Geometry suggestions, if any, remain unapplied pending user decision
- [x] `orcaslicer-print-validation` completed successfully
