---
name: image-relief-vectorize
description: Turn reference images into a relief/height-map aided vector outline before building 3D geometry.
---

# Image Relief To Vector

Use this skill when an image is the main template and the fastest reliable path is:

1. derive a **relief / height-like image**
2. extract and clean **vector-like contours**
3. only then build the 3D model

This is the repo's own workflow because no credible public Copilot skill was found that already packages the full pipeline **reference image -> relief -> vector cleanup -> 3D model**.

## Best fit

Prefer this skill for:

- glyphs, logos, symbols, stamped text
- plaques, shallow decorative reliefs, lithophane-like fronts
- cast or molded outer contours whose photo edges are noisy
- photos where direct thresholding grabs shadows or table edges

Do **not** let this skill override fit-critical measurements. User caliper values and cited specs still win.

## Default library stack

Use the lightest stack that already fits this repo:

| Stage | Preferred libraries | Purpose |
| --- | --- | --- |
| Crop / normalize / denoise | **opencv-python-headless**, **pillow**, **numpy** | grayscale, CLAHE, blur, masking, scale landmarks |
| Relief / height-like preprocessing | **opencv-python-headless**, **scikit-image** | gradient maps, edge-weighted relief, contrast flattening |
| Contour extraction | **scikit-image** (`measure.find_contours`), **OpenCV** (`findContours`) | convert relief bands or masks into polylines |
| Contour simplification | **scikit-image** (`measure.approximate_polygon`) | reduce noise before CAD import |
| Optional polygon cleanup | **Shapely** if installed | close gaps, `buffer(0)`, simplify, union nested loops |
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
3. simplify with `skimage.measure.approximate_polygon`
4. if available, clean self-touches / tiny gaps with Shapely

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

- `scikit-image` is already in this repo and is the preferred contour library here.
- `Shapely` is useful for polygon cleanup but is optional unless the repo later adopts it deliberately.
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
  https://github.com/opencv/opencv/blob/4.x/samples/python/contours.py
- scikit-image contour and polygon simplification example  
  https://github.com/scikit-image/scikit-image/blob/main/doc/examples/edges/plot_polygon.py
- build123d docs  
  https://github.com/gumyr/build123d
- trimesh docs  
  https://github.com/mikedh/trimesh
