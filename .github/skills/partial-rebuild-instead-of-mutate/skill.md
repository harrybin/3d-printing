---
name: partial-rebuild-instead-of-mutate
description: Replace unstable local mutation with a controlled partial rebuild from frozen datums and a constrained scope.
---

# Partial Rebuild Instead Of Mutate

Use this skill when continued local edits to an existing model are no longer converging and the safer move is to **rebuild only the wrong region** while keeping the trusted rest fixed.

This skill is for cases where:

- the model has a usable correct core
- one region or subsystem is structurally wrong
- repeated mutation keeps introducing collateral damage

## Core rule

Do **not** keep deforming a bad local structure just because the overall model is mostly right.

If the geometry in one region is wrong at the construction level, cut the problem at a stable boundary and rebuild that region from measurements, references, or controlled image guidance.

## When to use

Prefer this skill when:

- one chamber, shell zone, rib field, boss cluster, clip arm, or contour family is wrong
- transforms or tiny boolean edits are starting to fight the model topology
- a photo-guided refinement keeps improving one area while degrading neighboring features
- the baseline script is still valuable, but one section should be replaced rather than tweaked

## When not to use

Skip this skill when:

- the whole model is wrong and should be rebuilt from scratch
- the mismatch is solved by one measured parameter change
- the requested change is only a transform, centering step, or print optimization
- there is no trustworthy boundary between the correct and incorrect geometry

## Workflow

### 1. Freeze the trusted remainder

Explicitly mark what stays untouched:

- mating geometry
- measured datums
- outer faces already accepted
- internal features already validated
- origin and alignment references

### 2. Cut the rebuild boundary on purpose

Choose a boundary that is:

- geometrically simple
- easy to validate after replacement
- not passing through fit-critical transitions if avoidable

Good boundaries:

- planar split
- cylindrical interface
- full perimeter ledge
- rib field start/end
- shell-to-feature transition

Bad boundaries:

- knife-edge tangencies
- half-through a countersink or snap barb
- arbitrary slices through densely coupled geometry

### 3. Re-specify only the rebuild zone

Create a local dimension table for the zone being replaced:

- measured values
- photo-derived estimates
- researched reference dimensions
- uncertainties that still need confirmation

Do not let missing local numbers silently borrow from the old wrong geometry.

### 4. Rebuild from primitives, sketches, or bounded envelopes

Use the simplest method that fits the zone:

- measured primitives for engineering features
- `photo-anchor-candidate-fit` for local candidate families
- `visual-hull-envelope-fit` when the replaced outer shell needs multi-view bounds
- `image-relief-vectorize` for a pictured motif or contour that should seed the rebuilt region

Build the replacement in parametric code, not by mutating STL triangles.

### 5. Rejoin with overlap, not knife-edge contact

When merging rebuilt and frozen geometry:

- overlap solids slightly where the design allows
- avoid tangential contacts that create non-manifold edges
- run a manifold-engine boolean union on the overlapping solids before repair/export so intersecting internal faces are removed
- re-run the standard trimesh repair/export path after the unioned rebuild

### 6. Re-validate the seam and the function

After rejoining:

- validate watertightness and normals
- probe the replaced feature volume
- compare bounds and Euler number against expectations
- confirm frozen datums did not move
- re-check the photo or silhouette match only in the intended zone

## Strategy patterns

- **Wrong internal chamber, right outer shell:** freeze shell, rebuild chamber from measured sections.
- **Wrong outer shell, right insert geometry:** freeze insert/mating core, rebuild shell around it.
- **Wrong boss/rib cluster:** rebuild the cluster from a clean sketch plane instead of boolean patching.
- **Wrong decorative face, right functional body:** rebuild only the visible face region from a traced or landmark-guided contour.

## Recommended libraries

- **build123d** for the rebuilt region and controlled interfaces
- **trimesh + manifold3d** for merge, validation, probe, and ASCII export
- **NumPy** for dimensions and transforms
- **vedo** for seam and photo verification renders
- **OpenCV** for local image-guided overlays when needed
- optional **scikit-image** for contour helpers when the rebuild zone comes from silhouettes

## Stop criteria

Stop and escalate to full rebuild when:

- the "correct" region keeps shrinking after each inspection
- the chosen seam creates unavoidable topology problems
- too many neighboring regions depend on the replaced zone
- the local rebuild requires inventing fit-critical geometry that is not actually known

## Output evidence

Report:

- frozen remainder
- rebuild zone
- chosen rebuild boundary
- source of the rebuilt dimensions
- rejoin method
- seam validation result
- proof that the untouched region stayed unchanged

## Related

- `.github/skills/photo-anchor-candidate-fit/skill.md`
- `.github/skills/visual-hull-envelope-fit/skill.md`
- `.github/skills/stl-from-image-measurements/SKILL.md`
- `.github/skills/create-ascii-stl/skill.md`

## Sources

- build123d documentation  
  https://build123d.readthedocs.io/
- trimesh documentation  
  https://trimesh.org/
