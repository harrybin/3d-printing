# 3D Printing Models

A collection of ASCII STL models for the Anycubic Kobra S1 Combo + ACE Pro (250 × 250 mm build plate).

## Models

| File | Description |
|------|-------------|
| `models/cube_30mm_ascii.stl` | 30 mm cube |
| `models/cone_30mm_ascii.stl` | 30 mm cone |

## Agent Skills

| Skill | Description |
|-------|-------------|
| `anycubic-kobra-s1-ace-pro-profile` | Printer defaults and constraints (bed size, nozzle, temperatures, wall minimums) for the Anycubic Kobra S1 Combo + ACE Pro. Referenced by other skills when authoring or editing STL files. |
| `create-ascii-stl` | Generates new ASCII STL files using print-safe defaults. Collects dimensions, material, use case, and multi-color requirements before producing any geometry. |
| `edit-stl-transform` | Edits existing STL geometry: scale, rotate, translate, merge, split, and origin alignment — while preserving manifold/watertight topology. |
| `stl-create-edit-interview` | Guided interview run before creating or editing STLs. Determines wall strategy, mesh pattern, infill strategy, and fit intent one question at a time. |
| `validate-stl-mesh` | Validates an STL for manifold correctness and FDM printability: syntax, triangle count, watertight topology, normal consistency, and bed-fit. |

## Coordinate Convention

Models support both placement conventions on the 250 × 250 mm bed:

- **Center-origin** — XY target `(0, 0)`
- **Corner-origin** — XY target `(125, 125)`

Convention is auto-detected from coordinates: negative XY implies center-origin, otherwise corner-origin. When ambiguous, corner-origin is used to match common slicer build-plate coordinates.
