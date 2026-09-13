---
name: image-relief-vectorize
description: Turn reference images into a relief/height-map aided vector outline before building 3D geometry.
---

# Image Relief To Vector

Use this skill when an image is the main template and the fastest reliable path is:

1. derive a **relief / height-like image**
2. extract and clean **vector-like contours**
3. only then build the 3D model

Use it when a direct photo trace is too noisy, but a cleaned relief/height-like intermediate can still produce a reliable 2D basis for later CAD work.

## Best fit

Prefer this skill for:

- glyphs, logos, symbols, stamped text
- plaques, shallow decorative reliefs, lithophane-like fronts
- cast or molded outer contours whose photo edges are noisy
- photos where direct thresholding grabs shadows or table edges

Do **not** let this skill override fit-critical measurements. User caliper values and cited specs still win.

## Core stack plus optional helpers

Use the lightest stack that fits the task:

| Stage | Preferred libraries | Purpose |
| --- | --- | --- |
| Crop / normalize / denoise | **opencv-python-headless**, **pillow**, **numpy** | grayscale, CLAHE, blur, masking, scale landmarks |
| Relief / height-like preprocessing | **opencv-python-headless** | gradient maps, edge-weighted relief, contrast flattening |
| Contour extraction | **OpenCV** (`findContours`) | convert relief bands or masks into polylines |
| Default contour simplification | **OpenCV**, **numpy** | contour filtering, decimation, area/perimeter cleanup |
| Default contour cleanup | **OpenCV** | morphological cleanup, contour filtering, polygon simplification |
| Optional contour extraction / simplification | **scikit-image** (`measure.find_contours`, `measure.approximate_polygon`) | cleaner marching-squares style contour extraction when available |
| Out-of-repo optional polygon cleanup | **Shapely** if deliberately installed | close gaps, `buffer(0)`, simplify, union nested loops |
| 3D build / extrusion | **build123d**, **trimesh** | import cleaned outline, extrude, add exact engineering features |
| Visual verification | **vedo**, **opencv-python-headless** | overlay render vs reference photo |

Avoid making heavy ML depth models the default branch here. For this repo they are optional research tools, not the primary workflow, because they can hallucinate depth on shiny technical parts.

## Workflow

### 1. Calibrate first

- Build the contact sheet first when several images exist.
- Pick one or two tiles that show the target feature clearly.
- Establish scale from a user measurement or a known landmark in the same plane.
- Crop tightly to the feature before any contour work.

### 2. Build a relief-like image before vectorization

Do not jump straight from RGB photo to binary contour.

Create one or more relief candidates:

- normalized grayscale
- CLAHE-equalized grayscale
- gradient magnitude (`Sobel`/`Scharr`) blended onto grayscale
- optionally inverted relief when the feature is embossed vs recessed

Goal: separate structural edges from lighting and background noise.

### 3. Vectorize the relief, not the raw photo

Preferred order:

1. threshold one relief candidate or a narrow band of it
2. extract contours with `skimage.measure.find_contours` or `cv2.findContours`
3. simplify with OpenCV contour filtering, and optionally `skimage.measure.approximate_polygon` when available
4. clean noise with morphology, contour-area filtering, and polygon simplification; only use Shapely if the repo explicitly adopts it later

Keep multiple candidate outlines when needed. Do not assume the first trace is correct.

### 4. Accept or reject the vector by overlay

Project the cleaned contour back onto the calibrated photo and inspect the well-lit edges:

- if the vector hugs the real edge at known landmarks, keep it
- if it drifts into shadow, glare, or a neighboring object, reject it
- if several candidates are plausible, keep the one that best matches the calibrated overlay, not the smoothest one

### 5. Only then build the 3D model

After the 2D basis is accepted:

- import the outline into **build123d** or reconstruct it as arcs/lines
- extrude or loft the base form
- add fit-critical bores, ribs, clearances, and mating features from measured or sourced dimensions
- validate and compare renders back to the reference images

## Decision rules

- For **glyph-or-logo** jobs, this relief-first vector branch is usually the default.
- For **organic-or-mixed** silhouettes, use it as a candidate-outline generator before manual correction.
- For **recognizable-part-family** engineering parts, use it only for the outer silhouette or decorative zones; do not derive critical bores, wall thicknesses, or mating geometry from the relief trace alone.
- If the relief/vector result disagrees with the landmark-calibrated overlay or user measurements, discard it and fall back to the manual overlay method from `stl-from-image-measurements`.

## Library notes

- `scikit-image` is a useful optional helper for this workflow, especially for marching-squares contour extraction and polygon simplification.
- `Shapely` is useful for polygon cleanup but is **not** part of the supported default repo stack today.
- Potrace-style tracers can work for logos, but do not make them the default dependency path here; license and over-tracing risk must be checked first.

## Output evidence

Report:

- which relief candidate won
- which library path was used for contour extraction
- whether optional cleanup was needed
- which dimensions came from measurement/specs vs the vector trace
- one overlay artifact or description proving the contour was accepted before 3D modeling

## Related

- `.github/skills/stl-from-image-measurements/SKILL.md`
- `.github/skills/create-ascii-stl/skill.md`
- `.github/skills/research-part-specs/skill.md`

## Sources

- OpenCV contour sample  
  https://github.com/opencv/opencv/blob/3d3fe5545559c918afed2590fdc8168c8d34e9b9/samples/python/snippets/contours.py
- scikit-image contour and polygon simplification example  
  https://github.com/scikit-image/scikit-image/blob/v0.26.0/doc/examples/edges/plot_polygon.py
- build123d docs  
  https://github.com/gumyr/build123d
- trimesh docs  
  https://github.com/mikedh/trimesh
