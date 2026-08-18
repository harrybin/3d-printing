---
name: optimize-stl-for-print
description: Optimize an existing STL for FDM printing on the Anycubic Kobra S1 - orientation, overhangs, wall and hole compensation, elephant foot, bed layout and material estimate.
---

# Optimize STL for print

Use this skill after the geometry is correct and before slicing, or when a printed
part failed for a reason that is not a mesh defect (weak in the wrong direction,
sagging overhangs, a hole that came out too tight, a lid that does not close).

Correctness first: run `.github/skills/validate-stl-mesh` for manifold and feature
checks. This skill assumes a watertight mesh and only changes how it prints.

All numbers below assume the **0.4 mm** stock nozzle from
`.github/skills/anycubic-kobra-s1-ace-pro-profile`. For another nozzle, scale
wall values with the nozzle diameter and re-check clearances manually.

## Tooling

`scripts/mesh_tool.py` answers most of these questions without opening a slicer:

```powershell
python scripts\mesh_tool.py overhang models\part.stl            # unsupported area
python scripts\mesh_tool.py overhang models\part.stl --limit 50 # PLA limit
python scripts\mesh_tool.py measure  models\part.stl --infill 20
python scripts\mesh_tool.py transform models\part.stl -o models\part_rot.stl --rotate x,90
python scripts\mesh_tool.py center   models\part.stl --drop
python scripts\mesh_tool.py arrange  models\a.stl models\b.stl -o models\plate.stl --gap 5
```

Orientation changes are print-setup decisions, so write them to a **new** file or
do them in the slicer. Never overwrite the parametric output of a generator
script with a rotated copy - that desyncs `models/` from `scripts/`.

## Step 1 - orientation

FDM parts are anisotropic: strong within a layer (XY), weak across layer bonds (Z).

- Orient so the main load runs **along** layers, never as tension across a layer seam.
- Clips and springs: put the flexing direction in XY so the flexure is not a stack
  of layer bonds. `scripts/lineal_clip_kappe.py` already follows this - plate flat,
  pegs up.
- Holes and bores: a bore printed vertically is round and accurate; printed
  horizontally it needs a teardrop top or comes out oval.
- Prefer the orientation with the largest flat face on the bed for adhesion, unless
  it costs strength or forces supports into an enclosed cavity.

Compare candidates numerically instead of guessing:

```powershell
python scripts\mesh_tool.py overhang models\part.stl
python scripts\mesh_tool.py transform models\part.stl -o models\_try.stl --rotate y,90
python scripts\mesh_tool.py overhang models\_try.stl
```

Pick the orientation with the smallest unsupported area that still satisfies the
load direction. Delete the throwaway `_try` files afterwards.

## Step 2 - remove the need for supports

Support inside an enclosed cavity cannot be removed - treat it as a design error.

| Problem | Model-level fix |
| --- | --- |
| 90 degree horizontal lip | replace with a 45 degree chamfer |
| horizontal through-bore | teardrop profile, 45 degree point on top |
| flat ceiling over a pocket | arch or chamfered transition |
| tall thin part with a heavy top | split into two parts with a keyed joint |

Repo limits (from the printer profile): unsupported overhang <= 45 degrees,
bridges <= 10 mm free, 10-25 mm only with ribs or chamfers, > 25 mm needs supports.

## Step 3 - walls, features and text

- Minimum wall: **0.8 mm** (2 lines). Functional wall: **1.2 mm** (3 lines).
  Load bearing: **1.6-2.4 mm**.
- Snap-fit and press-fit bosses: at least **2.0 mm** of surrounding material.
- Minimum through-hole diameter **1.5 mm**, minimum pin diameter **1.0 mm**,
  minimum slot **0.4 mm**.
- Text: stroke >= **0.5 mm**, depth/height >= **0.4 mm**, cap height >= **3 mm**.
- Keep the facet count reasonable. Above roughly 500k triangles slicing gets slow
  without adding accuracy at 0.4 mm extrusion width; lower `SEGMENTS` in the
  generator instead of decimating the mesh.

## Step 4 - fit compensation

Clearances stay the repo defaults, and they belong in a **named parameter** in the
generator script (see `PRESS_CLEAR` in `scripts/lineal_clip_kappe.py`), never as a
magic number inside geometry code.

| Fit | Clearance |
| --- | --- |
| Press / tight | 0.20 mm |
| General | 0.30 mm |
| Sliding | 0.40 mm |

Hole shrinkage: FDM bores print undersized because the extrusion path cuts the
corner on every arc.

- Bore <= 5 mm: add **+0.2 mm** to the diameter
- Bore > 5 mm: add **+0.1 mm** to the diameter
- For a fit that must work first try, print a small test coupon of just the mating
  feature before printing the full part.

## Step 5 - elephant foot

The first layers bulge outward by roughly 0.2-0.5 mm per side because the first
layer is squished for adhesion. That breaks exactly the parts that matter: press
fits, lids and mating faces that start at z = 0.

- Any mating surface at z = 0 gets a **0.4 mm chamfer** in the model.
- Additionally enable elephant-foot compensation of about 0.2 mm in the slicer.
- Purely decorative or non-mating bottoms can skip the chamfer.

## Step 6 - bed layout and material

```powershell
python scripts\mesh_tool.py center  models\part.stl --drop
python scripts\mesh_tool.py measure models\part.stl --infill 20
python scripts\mesh_tool.py arrange models\a.stl models\b.stl -o models\plate.stl
```

- Bed is **250 x 250 mm**; `validate` fails a footprint that does not fit.
- Keep the model on the bed: lowest z must be 0.
- Centering follows the repo convention rule - `center-origin` targets (0, 0),
  `corner-origin` targets (125, 125); auto-detect when the user does not say.
- `measure` reports a 100 % infill upper bound and an infill-scaled lower bound.
  Real usage lands between the two because perimeters are always solid.

## ACE Pro multi-color

- Model each color region as its own solid and export separate STLs, then combine
  in the slicer - a single mesh cannot carry color regions.
- Put color boundaries on a chamfer, fillet or step so the seam is not on a flat face.
- Avoid tiny isolated islands of a second color: each one costs a full tool change
  plus purge.

## Output format

Report:

- chosen orientation and why (load direction, unsupported area before/after)
- unsupported area and bridge spans that still need supports
- wall, hole and text features below the limits, with their location
- clearance and hole compensation applied, and the parameter name that carries it
- elephant-foot decision
- footprint, placement convention, centered yes/no
- volume plus estimated mass and filament length

## Sources

- Prusa, modeling with 3D printing in mind:
  https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135
- Anycubic Kobra S1 Combo product page:
  https://store.anycubic.com/products/kobra-s1-combo
