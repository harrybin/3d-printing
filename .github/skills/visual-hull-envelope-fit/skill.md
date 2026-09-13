---
name: visual-hull-envelope-fit
description: Use multiple silhouettes or views to constrain the outer envelope before rebuilding or refining a model.
---

# Visual Hull Envelope Fit

Use this skill when a single-view iterative approach keeps distorting the model and the real problem is that the **outer envelope is under-constrained**.

This skill derives a guarded outer shape from **multiple views** and then uses that envelope as a limit for rebuild or refinement.

## Best fit

Prefer this skill for:

- outer shells with several reference photos
- irregular parts whose broad shape is clear but local details drift under iteration
- decorative, cast, or molded bodies where silhouette agreement matters more than hidden internals
- cases where one photo angle keeps fighting another

## Do not use as sole authority

Do **not** use visual-hull or silhouette carving alone for:

- bores, threads, wall thicknesses, snap features, or mating clearances
- hidden chambers or internal ribs
- any fit-critical geometry not visible in silhouette

Those must still come from measured dimensions, specs, or explicit parametric design.

## Workflow

### 1. Assemble a calibrated multi-view set

- use at least three views when possible
- normalize orientation across the photos first
- establish scale from measured landmarks
- prefer views with low foreshortening on the region being constrained

### 2. Extract silhouettes per view

- use OpenCV masks/edges as the default path
- use `image-relief-vectorize` first when raw photo edges are contaminated by shadow or glare
- keep one accepted silhouette per view, not a blended average of uncertain masks

### 3. Build an outer envelope, not a final part

Use the silhouettes to constrain the outside only:

- intersect or carve a voxel occupancy volume from the accepted views
- or use the silhouettes as profile limits for a manual rebuild
- convert the occupancy volume to a surface only after the envelope is stable

Treat the resulting hull as a **guardrail** for rebuild, not as final engineering geometry.

### 4. Rebuild the real model against that envelope

After the envelope is accepted:

- rebuild the part in `build123d` or controlled parametric geometry
- keep measured datums and internal functional geometry separate
- use the envelope to bound outer curves, wall bulges, and non-mating surfaces

### 5. Validate with both views and mesh checks

- overlay rendered silhouettes back onto each source view
- compare candidate shells against the multi-view envelope
- validate watertightness, normals, Euler number, and feature probes after rebuild

## Decision rules

- If one silhouette disagrees strongly with the others, inspect that photo for perspective or masking error before changing geometry.
- If a part is mostly prismatic with a few ambiguous faces, use only local envelope constraints and keep the rest parametric.
- If the visual hull becomes too blobby or rounded for an engineering part, stop using it as geometry and keep it only as a maximum outer-bound reference.

## Recommended libraries

- **OpenCV** for silhouettes, masks, and calibration helpers
- **NumPy** for voxel grids and transforms
- **scikit-image** for marching cubes when a voxel envelope needs surfacing
- **trimesh** for voxel or mesh conversion, analysis, and export-side checks
- **build123d** for the final controlled rebuild
- **vedo** for view-by-view render comparison

## Stop criteria

Stop and switch back to a parametric local-fit method when:

- only one view exists
- silhouettes are too ambiguous to trust
- internal or mating geometry dominates the task
- the carved envelope is less informative than the measured dimensions already are

## Output evidence

Report:

- which views were used
- how silhouettes were obtained
- whether the envelope was used as a hard limit or a soft reference
- which features were rebuilt from measurements instead of the hull
- where the hull improved consistency across views

## Related

- `.github/skills/photo-anchor-candidate-fit/skill.md`
- `.github/skills/image-relief-vectorize/skill.md`
- `.github/skills/stl-from-image-measurements/SKILL.md`

## Sources

- scikit-image contour extraction  
  https://scikit-image.org/docs/stable/api/skimage.measure.html#skimage.measure.find_contours
- scikit-image marching cubes  
  https://scikit-image.org/docs/stable/api/skimage.measure.html#skimage.measure.marching_cubes
- trimesh voxel documentation  
  https://trimesh.org/trimesh.voxel.html
