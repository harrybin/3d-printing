---
name: stl-from-image-measurements
description: "Create or edit STL files from user-provided images and measurements. Use for identifying objects from photos, researching existing 3D models with subagents, downloading or extracting model properties when possible, recreating missing geometry, combining objects into one STL, applying requested spacing/relations/dimensions, and validating against Anycubic Kobra S1 Combo + ACE Pro print constraints before finalizing."
argument-hint: "Provide the image, target measurements, desired object relationships, and whether this is a new STL or an edit to an existing STL."
---

# STL From Image Measurements

Use this skill when the user provides an image plus measurements and wants a new STL or a modified STL that matches the pictured objects and their requested dimensions or placement.

This workflow is mandatory for tasks that involve:

- identifying real objects or parts from an image
- searching for existing 3D models that match those objects

If the image contains objects beyond what the user explicitly requested, model only the requested objects. If it is unclear which objects are in scope, list the detected objects and ask the user to confirm which to include before proceeding.

- downloading models when a permitted source is accessible
- extracting dimensions, proportions, and shape cues from research results
- recreating geometry when no suitable model is available
- combining multiple parts into one STL or one arranged build layout
- enforcing printer-safe geometry for the Anycubic Kobra S1 Combo + ACE Pro

Default policy choices for this skill:

- output packaging is chosen from: fused single solid, separate arranged bodies in one STL, or separable geometry for later assembly, based on the user's intent
- research should prefer public 3D model sites and public GitHub repositories
- fit-critical inferred dimensions require user confirmation before finalizing

## Required outcome

Produce an STL result only when all of the following are true:

- object identity or shape intent is specific enough to model
- critical dimensions are known, estimated explicitly, or confirmed by the user
- requested relations between parts are applied and reported
- the resulting mesh passes printability checks
- no known printer restriction is violated without explicit user sign-off

If any of these remain unresolved, stop, explain the blocking ambiguity precisely, and ask only for the missing information.

## Inputs to collect before modeling

Do not generate or modify STL geometry until these inputs are captured.

1. Source inputs
   - image or images of the object(s)
   - whether this is a new STL or a modification to an existing STL
   - existing STL path, if editing

2. Dimensional contract
   - at least one user-provided measurement in mm per object, or a clearly identifiable reference object in the image (e.g., a coin, ruler, or standard component) that allows scale to be calculated with less than 10% error
   - target overall size in mm
   - fit intent for any mating features: press, general, or sliding

3. Relation contract
   - how objects should relate: touching, spaced apart, nested, aligned, mirrored, stacked, centered, or mounted
   - exact requested gaps, offsets, angles, or alignments in mm/degrees

4. Manufacturing contract
   - intended material if known
   - single-color or ACE Pro multi-color intent
   - whether supports are acceptable

If a measurement is missing, ask for the minimum extra data needed to scale the object reliably. Do not pretend uncertain dimensions are exact.

## Workflow

### 1. Research before classifying

Before committing to a geometry strategy, research available models and reference data. Do not classify the job until research is complete. The classification decision is made exclusively in step 3.

### 2. Research with subagents first

Before recreating geometry from scratch, use a read-only subagent to research possible existing 3D models or reference data.

The subagent should:

- identify the likely real-world object shown in the image
- search for existing 3D models that match the object or close variants
- prefer public 3D model sites and public GitHub repositories that provide dimensions, part names, or technical drawings
- report whether downloadable models are available in accessible locations
- capture key properties: dimensions, proportions, feature layout, mounting pattern, symmetry, and likely missing measurements
- distinguish between exact matches, approximate matches, and irrelevant results

If a downloadable model is available from an accessible source, use it only when its licensing/access conditions permit use in the current task. If direct download is not possible, still use the reported dimensions and feature properties as reference evidence.

If a model's license prohibits modification or redistribution, do not use it as a base. Inform the user of the restriction, name the model and its license, and automatically fall back to recreate-from-reference using only the dimensional data as reference evidence.

### 3. Decide whether to reuse or recreate

This is the single authoritative classification point. Use this branch logic:

- `reuse-existing-model`: if an exact or near-exact model exists and can be used safely, import it and edit it.
- `hybrid-reuse-and-edit`: if a model exists but key dimensions or feature relations differ, use it as a shape reference and transform or rebuild the mismatched regions.
- `recreate-from-reference`: if no trustworthy model exists, build the geometry from measured primitives and image-derived proportions.

Choose the cheapest path that can still satisfy dimensional accuracy and printability. Do not force reuse when it would create hidden inaccuracies that are harder to fix than rebuilding.

### 4. Build the dimensional model

For each object, create a dimension table before editing geometry:

- known measurements from the user
- inferred measurements from image scaling
- borrowed measurements from researched models or technical references
- uncertainty flags for any estimated dimension

State which dimensions are exact versus inferred. If an inferred dimension controls fit or assembly, get confirmation before finalizing.

Measurement precedence and pitfalls (session-verified):

- User caliper readings always override image-derived estimates. Grid-based photo scaling (including FFT pitch estimation) routinely errs by 20-40% due to perspective and parallax; treat it as a rough prior only.
- Persist the dimension table as a markdown doc under `docs/` and keep generator parameters in sync with it. The user may edit that doc directly: re-read it before every geometry change.
- Convert user units carefully (`0,785 cm` = 7.85 mm); challenge physically implausible values (e.g., walls thinner than one extrusion line) before using them.
- Recreate the **interior structure** of cast/molded parts (chambers, ribs, bosses, pads, guide blocks), not a simplified solid. Simplified solids get rejected when compared against the original.

### 5. Apply requested relationships between objects

Translate the user's wording into explicit geometric constraints.

Examples:

- "next to" -> define XY offset and edge or center alignment
- "inside" -> define wall clearance and insertion depth
- "on top of" -> define Z offset and contact faces
- "same distance apart" -> define repeated spacing constraint
- "centered" -> define center-to-center or object-to-bed centering rule

After applying relations, report the final relative positions in mm so the user can verify intent.

### 6. Compose or edit the STL

Use the project libraries for all geometry work — never hand-write STL facets or manually computed triangle meshes for complex objects: **build123d** for engineering solids (sketches, hulls, countersinks, bosses, ribs), **trimesh + manifold3d** for simple CSG, repair, and export, **vedo** for render verification, **opencv-python-headless** for frame extraction and silhouette comparison.

Allowed operations include:

- create new solids from measured geometry
- scale, rotate, and translate imported solids
- split or merge bodies
- add alignment or mounting features
- add clearance for fit
- arrange multiple objects into one composed STL when requested

When combining objects:

    - choose packaging from the three options: fused single solid, separate arranged bodies in one STL, or separable geometry for later assembly, based on the user's intent; if wording is ambiguous, ask the user to confirm before composing

- preserve intentional separability for ACE Pro color regions or later assembly
- avoid accidental overlaps, self-intersections, or trapped unsupported regions
- keep a clear origin/placement rule and report it

### 7. Enforce Anycubic Kobra S1 Combo + ACE Pro restrictions

These checks are mandatory before final output:

- units must be millimeters
- minimum printable wall for 0.4 mm nozzle: 0.8 mm baseline
- functional wall baseline: 1.2 mm
- fit clearance baselines:
  - press fit: 0.20 mm
  - general fit: 0.30 mm
  - sliding fit: 0.40 mm
- if the user specifies a fit type and also provides an explicit clearance value, use the user-provided value and note the deviation from the baseline; if the deviation exceeds 2x the baseline, flag it and ask for confirmation before applying
- embossed/debossed text stroke minimum: 0.5 mm with depth or height >= 0.4 mm
- prefer unsupported overhangs <= 45 degrees
- flag 45-60 degree overhangs as marginal
- require redesign or supports for > 60 degree overhangs unless the user accepts that risk
- keep unsupported bridges <= 10 mm when possible; flag 10-25 mm; treat > 25 mm as requiring redesign or supports
- preserve separate solids for color regions when multi-color output is requested

If the user specifies a different nozzle size, scale wall baselines to 2x nozzle diameter minimum and 3x for functional recommendations.

### 8. Validate the final mesh

Do not finalize the STL unless all of these pass:

- watertight/manifold mesh
- no self-intersections
- no zero-area or degenerate triangles
- outward and consistent normals
- bounding box matches intended physical dimensions in mm
- object-to-object relations match the requested measurements
- placement convention is explicit or auto-detected correctly for a 250 mm x 250 mm bed

If validation fails, stop and report:

- the failing check
- the affected object or feature
- whether the issue can be corrected automatically
- the safest correction or redesign option

Never present a failing STL as complete.

### 8b. Render-and-compare loop against photos and video (mandatory for recreations)

When the goal is to match a pictured/filmed original, do not rely on mesh statistics alone. Iterate visually until the render matches the references:

1. If a video is provided, extract evenly spaced frames with OpenCV (`cv2.VideoCapture`, `CAP_PROP_POS_FRAMES`); take a denser pass over sections that show the relevant detail.
2. Render the current STL offscreen with **vedo** (`Plotter(offscreen=True)`) from at least top, bottom, front, side, and iso views. vedo/VTK works headless on Windows; matplotlib `Poly3DCollection` is only a fallback (no z-buffer, wrong occlusion).
3. Compare each render against the matching photo/frame viewpoint: outline shape, pocket/cavity contours, rib and boss layout, guide features, countersink transitions.
4. Fix one structural discrepancy at a time in the parametric script, regenerate, re-render, and repeat until no structural difference remains.
5. For quantitative checks, extract silhouettes (white-on-black render) and compare contours via OpenCV (`cv2.matchShapes`, IoU overlay).

Only report completion after the render-versus-reference loop converges and the user-visible structures match.

### 9. Show the result in the STL canvas (mandatory)

After the STL is written or updated on disk, always display it in the STL canvas. This applies to newly created STLs and to edits of existing STLs, and it must not be skipped even if the user did not ask for a preview.

- Save the STL under the workspace `models/` folder (the canvas only resolves workspace-relative paths).
- Call `open_canvas` with `canvasId: "stl-canvas"` and `input.stlPath` set to the workspace-relative path, e.g. `models/assembly.stl`.
- Use a stable `instanceId` such as `stl-preview` so repeated previews refresh the same panel; use a distinct `instanceId` per file when multiple STLs are produced.
- Optionally call the `read_stats` action and report facets and bounds alongside the preview.
- If the canvas fails to open (extension unavailable or `stl_not_found`), report the failure and the file path explicitly instead of silently continuing.

## Communication rules

- Be explicit about what came from the image, what came from research, and what was inferred.
- Prefer one or two sharply targeted follow-up questions over a broad questionnaire.
- If the image is too ambiguous to identify the object confidently, say so and ask for a clearer image or a known reference dimension.
- If research finds multiple plausible objects, present the best candidates and explain the deciding feature differences.
- If no good reusable model exists, say that directly and switch to recreation.
- If a requested relation or measurement would violate printability constraints, explain the conflict and propose the closest printable alternative.

## Completion checklist

Before finishing, provide:

- the chosen workflow path: reuse, hybrid, or recreate
- the evidence used: image cues, researched models, and user measurements
- final object dimensions and bounding box in mm
- final relation measurements between objects in mm
- printability findings and any accepted risks
- whether the mesh was centered or origin-aligned and by which convention
- confirmation that the STL was opened in the STL canvas, including the previewed path

## Recommended companion skills

When relevant, also use these workspace skills:

- `anycubic-kobra-s1-ace-pro-profile` for printer defaults and constraints
- `stl-create-edit-interview` to collect missing print-intent decisions
- `edit-stl-transform` when modifying an imported STL
- `create-ascii-stl` when building a new STL from scratch
- `validate-stl-mesh` before final delivery
