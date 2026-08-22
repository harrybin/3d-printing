---
name: stl-create-edit-interview
description: Guided question flow for STL authoring/editing choices (wall strategy, mesh pattern, infill strategy, and fit intent).
---

# STL Create/Edit Interview

Use this skill before creating or editing STL files. It forces key printability decisions up front.

## Step-by-step user interview (ask one question at a time)

1. What is the part purpose?
   - Visual prototype
   - Fit/assembly test
   - Functional load-bearing

2. Wall strategy?
   - Solid/perimeter walls
   - Mesh/lattice style walls

3. If mesh/lattice is selected, choose pattern intent:
   - Gyroid-like (balanced isotropic behavior)
   - Honeycomb (stiff but more material/time)
   - Rectilinear/Grid (fast and simple)

- Record this mesh/lattice wall pattern in `wall_pattern`.

4. Internal volume strategy?
   - Hollow (shell only)
   - Sparse infill
   - Dense/near-solid infill

5. If sparse infill is selected, choose pattern:
   - Gyroid (recommended default)
   - Cubic / Adaptive cubic
   - Rectilinear
   - Concentric (special cases/flex parts)

   If hollow, set infill_pattern = none and infill_density_percent = 0.
   If dense/near-solid, set infill_pattern = rectilinear (default) and infill_density_percent = 40-60%.

6. Target fit behavior?
   - Press fit (0.20 mm baseline)
   - General fit (0.30 mm baseline)
   - Sliding fit (0.40 mm baseline)

7. Multi-color with ACE Pro?
   - No
   - Yes: separate bodies per color + seam hiding boundaries

8. If multiple materials/colors are visible in the real object: should those regions stay distinct in the model?
   - No: merge into one printable body/material intent
   - Yes: preserve as distinct solids/regions

9. Output format decision?
   - STL (only if single-material/single-region intent)
   - 3MF (required when distinct material/color regions must be preserved)

   If answer 8 is "Yes", force output_format = 3mf.

10. Does the part have overhangs greater than 45°?

- Yes (set `support_likelihood` = high)
- No (set `support_likelihood` = low)
- Unsure (set `support_likelihood` = medium)

## Recreating an existing part (session-verified)

When the job is a replacement for a real part rather than a fresh design, most of the interview above is already decided by the original. Ask these instead, one at a time:

1. Which geometry is **frozen**? On replacement parts users typically approve the current walls, chamber layout and outer envelope and only want one feature changed. Record the frozen set explicitly and do not touch it, even when a neighbouring feature looks wrong.
2. Which single feature is in scope for this iteration? Fix one structural discrepancy per round and re-verify before starting the next; users get lost when several features change at once.
3. Which measurements are caliper-verified versus photo-derived? Caliper values win, and photo-derived values must stay flagged as estimates in the measurement doc.

Then reuse the fit, wall and infill defaults below only for the parts of the geometry that are genuinely new.

## Best-practice defaults to apply

- Nozzle profile baseline: 0.4 mm
- Min wall: 0.8 mm, functional wall: 1.2 mm+
- Derive wall_thickness_mm from part purpose: visual prototype → 0.8 mm, general functional → 1.2 mm, load-bearing → 1.6 mm+. Record this value in wall_thickness_mm.
- Infill defaults:
  - visual: 10-15%
  - general functional: 20-35%
  - high load: 40-60% with thicker walls

## Picture references to show during choices

When asking infill/wall pattern choices, show these images to the user. If images cannot be displayed, describe the pattern visually in one sentence (e.g., Gyroid: a continuous S-curve lattice with no flat surfaces):

- Gyroid pattern:  
  https://help.prusa3d.com/wp-content/uploads/2021/01/gyroidfinal.jpg
- Cubic pattern:  
  https://help.prusa3d.com/wp-content/uploads/2021/01/cubicfinal.jpg
- Rectilinear pattern:  
  https://help.prusa3d.com/wp-content/uploads/2021/01/rectilinear_final.jpg
- Honeycomb pattern:  
  https://help.prusa3d.com/wp-content/uploads/2021/01/plastevfinal.jpg
- Concentric pattern:  
  https://help.prusa3d.com/wp-content/uploads/2021/01/concentricfinal-1.jpg

## Interview outcome

Produce a concise parameter set:

- wall_mode
- wall_pattern
- wall_thickness_mm
- infill_mode
- infill_pattern
- infill_density_percent
- fit_clearance_mm
- support_likelihood
- multi_color_plan
- material_semantics_plan
- output_format

Record mesh/lattice wall pattern in `wall_pattern` and internal infill pattern in `infill_pattern` separately.

Use this parameter set as the input contract for STL generation/editing tasks.

## Sources

- Prusa infill pattern properties  
  https://help.prusa3d.com/article/infill-patterns_177130
- Prusa modeling best practices  
  https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135
