---
name: photo-anchor-candidate-fit
description: Refine a model toward image references with frozen datums, landmark alignment, and candidate sweeps to avoid iterative drift.
---

# Photo Anchor Candidate Fit

Use this skill when an existing model should be brought **closer to a pictured original** and naive tweak-render-tweak cycles are starting to drift away from the real part.

This skill is for **reconstruction of a pictured object**, not for free designs, imagined parts, or replacements driven only by function.

## Problem this skill prevents

Repeatedly editing the latest mesh based on one screenshot tends to:

- move fit-critical features that were already correct
- mix several uncertain changes into one step
- overfit to one photo angle while degrading another
- make the model smoother or stranger without becoming more faithful

## Core rule

Do **not** chain uncontrolled edits from the latest STL.

Instead:

1. freeze trusted geometry
2. calibrate image landmarks
3. branch several controlled candidates from the same baseline script
4. score or compare the candidates against the reference
5. keep only the winner and discard the rest

## When to use

Prefer this skill when:

- the object already has a usable parametric script or a stable editable baseline
- some dimensions are measured, but the outer shell or feature placement still differs from photos
- multiple photos exist, but single-view tweaking keeps producing regressions
- the task is an engineering replacement part and the mating geometry must stay fixed

## When not to use

Skip this skill when:

- the task is a new design inspired by a photo
- there is no meaningful baseline model to branch from
- the mismatch is purely dimensional and can be fixed directly from caliper values
- the part never existed in the shown form

## Workflow

### 1. Freeze the trusted datums first

Create an explicit frozen set before changing geometry:

- bores, shafts, slots, inserts, and mounting patterns with measured values
- wall thicknesses or clearances already confirmed by test fit
- coordinate references and alignment faces
- any internal feature the user did **not** ask to change

Do not let photo-driven edits move frozen geometry.

### 2. Define the uncertain zone separately

Limit the image-fitting work to one or more uncertain regions:

- outer silhouette
- one rib or boss cluster
- one contour family
- one decorative or visible face

If more than one region is wrong, fix them in separate rounds.

### 3. Calibrate a landmark frame

Use the repo's existing landmark-calibrate-and-overlay approach:

- choose 2+ trustworthy landmarks visible in the photo
- derive scale and orientation from known dimensions
- if available, use more landmarks and solve pose instead of guessing perspective
- normalize several photos into one orientation before comparing left/right features

For stronger perspective effects, use OpenCV pose estimation (`solvePnP`) from 3D model points to 2D image points.

### 4. Branch candidates from the same source script

Do **not** edit candidate B on top of candidate A.

Generate several parameterized candidates from the same baseline:

- radius sweep
- offset sweep
- contour family A/B/C
- feature on left vs right
- shallow vs deep pocket

Name and preserve them as separate candidate outputs until one wins.

### 5. Compare by overlay and metrics

Judge candidates against the same calibrated view set:

- overlayed contours at trusted landmarks
- reprojection error for landmark points
- directed Hausdorff distance for contour mismatch
- Procrustes disparity for normalized landmark/outline shape mismatch
- SSIM only as a secondary image-structure check, never as the sole authority

Weight the least foreshortened, best-lit views highest.

### 6. Accept only a single controlled delta

After choosing the best candidate:

- copy only its governing parameters back into the source script
- regenerate from script
- re-run mesh validation and feature probes
- re-check all frozen datums remain unchanged

If the candidate improves one view but breaks frozen geometry or another critical view, reject it.

## Strategy by part type

- **Engineering replacement part:** freeze mating geometry, fit only outer shell and visible non-mating features.
- **Cast/molded shell:** fit silhouette families and rib locations in isolated rounds.
- **Glyph/logo/decorative shape:** larger candidate sweeps are acceptable because fewer mechanical datums are frozen.

## Recommended libraries

Use current repo-compatible tools first:

- **OpenCV** for landmarks, pose estimation, overlays
- **NumPy** for coordinate transforms
- **SciPy** for Procrustes and Hausdorff metrics
- **vedo** for offscreen render candidates
- **build123d** for controlled parametric rebuilds
- **trimesh + manifold3d** for validation and probes
- optional **scikit-image** for contour extraction or SSIM support

## Stop criteria

Stop and switch strategy when:

- every candidate that improves the photo worsens a frozen fit-critical feature
- the same feature needs contradictory changes across views
- the baseline model is structurally wrong rather than locally wrong
- silhouette mismatch is too large for parameter tweaking and needs multi-view envelope reconstruction instead
- the local structure itself is wrong and should be replaced from a clean boundary instead of kept alive through further mutation

In those cases, move to `visual-hull-envelope-fit` or `partial-rebuild-instead-of-mutate`.

## Output evidence

Report:

- frozen geometry list
- uncertain region in scope
- candidate parameters explored
- comparison method used
- winning candidate and why
- proof that frozen features stayed unchanged

## Related

- `.github/skills/stl-from-image-measurements/SKILL.md`
- `.github/skills/image-relief-vectorize/skill.md`
- `.github/skills/validate-stl-mesh/skill.md`

## Sources

- OpenCV pose estimation (`solvePnP`)  
  https://docs.opencv.org/4.x/d5/d1f/calib3d_solvePnP.html
- SciPy Procrustes  
  https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.procrustes.html
- SciPy directed Hausdorff distance  
  https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.distance.directed_hausdorff.html
- scikit-image structural similarity  
  https://scikit-image.org/docs/stable/api/skimage.metrics.html#skimage.metrics.structural_similarity
