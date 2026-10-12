# Sources

Accessed 2026-10-10.

## OrcaSlicer official documentation

- [CLI mode](https://www.orcaslicer.com/wiki/cli/cli_mode) — headless loading,
  transformation, slicing, setting overrides, hyphenated option names, and the
  requirement to treat vector settings carefully.
- [CLI actions](https://www.orcaslicer.com/wiki/cli/cli_actions) — `--slice`,
  `--export-3mf`, `--export-slicedata`, `--export-settings`, `--info`, and
  normative checking.
- [CLI transform](https://www.orcaslicer.com/wiki/cli/cli_transform) — arrangement,
  orientation, X/Y/Z rotation, on-bed placement, transform ordering, and assembly
  behavior.
- [CLI misc](https://www.orcaslicer.com/wiki/cli/cli_misc) — profile/filament
  loading, object-to-filament IDs, output directories, material-aware arrangement,
  and metadata.
- [Auto Orientation](https://www.orcaslicer.com/wiki/print_prepare/prepare_auto_orient)
  — OrcaSlicer generates and scores orientation candidates using overhang area,
  bottom contact, support interface, and contour complexity, but requires manual
  review for complex models and layer-adhesion strength.
- [Auto Arrange](https://www.orcaslicer.com/wiki/print_prepare/prepare_auto_arrange)
  — spacing, arrangement rotation, material grouping, and printer-motion-aware
  alignment.
- [Support](https://www.orcaslicer.com/wiki/print_settings/support/support_settings_support)
  — support types/styles, threshold behavior, build-plate-only support, critical
  regions, and small-overhang filtering.
- [Placeholder variables](https://www.orcaslicer.com/wiki/developer_reference/built_in_placeholders_variables)
  — sliced-job statistics including print time, filament length, extrusion volume,
  weight, cost, tool changes, wipe-tower metrics, first-layer bounds, and active
  preset names.
- [Publishing 3MF files for creators](https://www.orcaslicer.com/wiki/publishing_3mf/publish_3mf_creators)
  — project settings and full filament presets can be embedded; geometry-only
  publication is possible; receiving a project does not modify the recipient's
  preset library; not every setting necessarily survives a round trip.

## FDM design and orientation guidance

- [Prusa Knowledge Base: Modeling with 3D printing in mind](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135)
  — support/overhang limits vary with nozzle and settings; short bridges can print
  without support; splitting can improve orientation; supported undersides have
  worse finish; FFF strength depends on orientation; and downward-facing fillets
  may create severe overhangs while chamfers are often preferable.

## Interpretation limits

- OrcaSlicer's documented global statistics expose whole-job time and material
  values. Support-only time/volume is recorded only when the installed version,
  project slice data, G-code, or a deterministic parser explicitly exposes a
  support breakdown.
- Auto-orient's unprintability score is advisory. It does not replace functional
  load, fit, seam, stability, or surface-quality review.
