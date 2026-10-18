# AGENTS

This repository contains parametric STL generation workflows for FDM printing on the Anycubic Kobra S1 Combo + ACE Pro.

## First Steps

1. Read [README.md](README.md) for project context and the image-to-STL workflow.
2. Use Python in the local virtual environment under `.venv`.
3. Treat scripts in `scripts/` as source of truth; regenerate STL files in `models/` instead of hand-editing mesh files.
4. Before building any new nontrivial object from scratch, run the reusable-asset
   and license search from `research-reusable-3d-assets`, including searches for
   similar functional or stylistic templates when no exact model is expected.
5. Route technical/fit geometry to Python, organic/visual geometry to the controlled
   Blender workflow, and every final print job through OrcaSlicer when available.

## Build And Validation Commands

### Bounded tool output

Use `scripts\compact_output.py` for verbose commands and log inspection. Keep
complete logs under `build\`; return only bounded summaries to the agent:

- Run tests/builds: `.\.venv\Scripts\python.exe scripts\compact_output.py run --log build\tests.log -- .\.venv\Scripts\python.exe -m unittest discover -s tests`
- Inspect logs: `.\.venv\Scripts\python.exe scripts\compact_output.py log build\tests.log`
- Inspect Orca projects: `.\.venv\Scripts\python.exe scripts\compact_output.py project models\ghouls-grip-print.3mf`

The runner preserves the command exit code. Summaries are heuristic, not proof
of success; read targeted full-log ranges for failures, unknown warnings or
omitted diagnostic kinds. Never replace error evidence with a success-shaped
summary. Do not pipe output to an arbitrary first-N-lines cutoff.
For source/docs, use targeted searches and line ranges instead of full reads or
overlapping rereads. Use `git diff --stat` first, then only relevant hunks.
Do not print whole 3MF XML, G-code, environment dumps or archive member lists.
These helpers need no additional packages and do not change model geometry.

### Batch model changes before the final quality phase

When several requested tasks change model geometry or assembly objects, complete
all related source changes first. Then optimize the combined result and run the
final mesh/mechanism validation, slicing, metadata updates and presentation
renders as one consolidated quality phase, rather than repeating this expensive
pipeline after each task. During construction, use only targeted, inexpensive
checks needed to catch defects or choose the next geometry change. Re-run final
checks only when subsequent changes invalidate their evidence; never deliver
stale slices or previews.

- Create environment:
  - `python -m venv .venv`
  - `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`
- Regenerate clip model:
  - `.\.venv\Scripts\python.exe scripts\lineal_clip_kappe.py`
- Build a reference image index:
  - `.\.venv\Scripts\python.exe scripts\make_contact_sheet.py model-sources`
- Inspect, validate or edit an existing STL:
  - `.\.venv\Scripts\python.exe scripts\mesh_tool.py validate models\<part>.stl`
  - `.\.venv\Scripts\python.exe scripts\mesh_tool.py overhang models\<part>.stl`
- The generator already prints validation stats (facets, bounds, extents, watertight, winding consistency, Euler number, degenerate faces).

There is no separate test suite in this repo at the moment.

## Pull Request Output

- For work that starts from `.github/ISSUE_TEMPLATE/model-request.yml`, fill out `.github/pull_request_template.md`.
- PRs for 3D-model work must list the exact script/model/doc paths changed, the validation commands/results, and any remaining fit-risk.
- Include the source/license decision, Blender roundtrip evidence when used, and the
  OrcaSlicer version, profiles, print time, material estimate, warnings, and status.
- When geometry or delivered outputs change, attach rendered preview images for the final STL/3MF (or slicer previews for multi-material 3MF output) and reference them in the PR description.

## Final model image in chat (mandatory)

- Whenever a model is created or its delivered geometry changes, render the exact final STL/3MF and show that image inline in the final chat response. Do not stop at opening the STL canvas, describing the model, or reporting a file path: a canvas preview is not a chat image.
- For multi-material or multi-color 3MF, show a rendered or slicer preview that makes the final color/material regions visible. For multiple delivered parts, include a view that shows their final arrangement.
- Keep the final presentation render separate from temporary analysis/reference renders. Do not delete it before it has been displayed in chat; temporary renders may be cleaned up afterward.
- Use the platform's image attachment/inline-image mechanism. If the current interface cannot embed the image, state that limitation explicitly and provide the rendered image path as a fallback rather than implying that the canvas preview was posted in chat.

## 3MF project and support screenshots

- For every delivered `models/<stem>.3mf`, render a complete-project preview at
  `docs/images/<stem>-preview.png`. The preview must show the full project and
  preserve visible material/color regions for multi-material projects.
- After a successful OrcaSlicer slice, render one support-path screenshot for
  every sliced plate at `docs/images/<stem>-plate-<n>-supports.png`. Derive
  these images from that plate's actual G-code; show an explicit no-support
  result when the slice contains no support extrusion. Never fabricate support
  paths or screenshots when the plate was not sliced.
- Keep the screenshot names beside the project stem so both the STL Canvas
  extension and Web viewer can resolve the same images. The viewers expose a
  project-preview button and per-plate support-preview buttons, including in
  the expandable per-plate print details. Missing images must hide the action
  or leave it disabled with an explanation.
- `web/scripts/sync-models.mjs` must copy the preview/support sidecars into the
  static web build. Keep the final screenshots in `docs/images/` as committed
  deliverables.

## Architecture Boundaries

- `scripts/`: parametric geometry definitions, boolean operations, reference-image tooling (`make_contact_sheet.py`) and the shared mesh CLI (`mesh_tool.py`).
- `models/`: generated STL outputs (ASCII STL expected).
- `.github/skills/`: task-specialized behavior used by agents for STL creation, editing, and validation.
- `.blend` files may preserve organic modeling sources, but Python scripts and
  measurement docs remain authoritative for fit-critical geometry.

If behavior around print constraints, validation policy, or coordinate targeting changes, update both script logic and the relevant skill file so they stay aligned.

## Project Conventions

- Units are millimeters.
- Printer bed target is 250 mm x 250 mm.
- Coordinate convention supports both:
  - center-origin target `(0, 0)`
  - corner-origin target `(125, 125)`
- When convention is not explicitly provided, prefer auto-detection (negative XY implies center-origin; otherwise corner-origin).
- For fit-critical features, keep clearances explicit and parameterized (example: `PRESS_CLEAR` in `scripts/lineal_clip_kappe.py`).
- For mesh booleans, use the manifold engine and keep output watertight.
- Never hand-write STL facets or manual vertex/triangle lists for complex objects.
  Generate technical geometry through the Python libraries in `requirements.txt`
  (build123d for engineering solids, trimesh + manifold3d for CSG/repair/export,
  vedo for render checks, opencv for reference comparison); route approved organic
  geometry through `blender-assisted-modeling`.
- Blender is allowed for organic, sculptural, relief, and visually complex regions.
  It must not freely alter measured datums, bores, fits, interfaces, or keyed joints.
  Validate every Blender export independently with the repo tools.
- Whenever a region should read as realistic, photorealistic, organic or sculptural
  (ornaments, creatures, skulls, foliage, drapery), do not keep stacking Python
  primitives. Switch to Blender for that region and first search online for a
  license-compatible motif, scan or asset that comes close to the target, then adapt
  it instead of approximating it from scratch. Record source, author and license per
  `research-reusable-3d-assets`.
- Ornaments do not have to be purely raised. Recessed/engraved relief is allowed
  wherever the remaining wall thickness and stability still satisfy the part's
  structural requirement. Whichever direction is used, the decorated part must be
  sliced against a matched undecorated control with automatic support enabled, and
  it must not increase support paths or support extrusion.
- Prefer the official Blender Lab MCP integration, bind it only to localhost, save a
  `.blend` checkpoint before agent-controlled changes, and treat arbitrary Blender
  Python execution as trusted local code execution.
- Use the versioned `.vscode/mcp.json` template and `docs/mcp-setup.md`; keep
  executable paths, downloaded servers, add-ons, secrets, and personal profiles out
  of Git.
- Before original modeling, always search for exact or similar adaptable 3D assets
  with a clear license. Record source, author, license,
  modification/redistribution rights, and attribution. Never use unclear or
  no-derivatives assets as an editable base.
- Never invent a fit-critical dimension. Every such number is user-measured, taken from a cited published spec, or explicitly flagged as an estimate needing a test print; record origin, source and confidence in the `docs/` measurement doc (see `research-part-specs`).
- Print-orientation rotations go into a new file or the slicer. Never overwrite a generator's `models/` output with a rotated copy - that desyncs the mesh from its parametric source.
- Every delivered print plate must be sliced in OrcaSlicer with the intended Kobra
  S1/nozzle/process/filament profiles when OrcaSlicer is available. Record print
  time and material only from a successful slice.
- Generated OrcaSlicer 3MF projects default to random seam placement, ironing on
  all top surfaces and enabled automatic support (`seam_position=random`,
  `ironing_type=top`, `enable_support=1`) unless a documented part-specific reason
  requires an exception. Support stays on so that a zero-support slice is proven
  geometry, never a disabled setting.
- New complex assemblies use exactly two 3MF deliverables:
  `models/<name>-view.3mf` contains the fully assembled object, with separate
  plates for other meaningful mechanism states; `models/<name>-print.3mf`
  contains the complete print BOM. Group parts of each material/color together
  and use multiple plates as needed instead of splitting the project into
  per-material files. Optional part STLs do not replace these files.
- Prefer separately printed, keyed color bodies over purge-heavy in-place
  multicolor when assembly, strength, and appearance remain acceptable.
- Material-separated parts must be physically assemblable after printing. Define
  and verify an insertion direction, assembly order, reachable retaining feature
  and collision-free insertion sweep for every cross-material joint. A static
  master render is not proof: reject any part that reaches its final pose only by
  passing through another solid, and split integral cross-material shafts/gears
  into keyed couplings where necessary.
- Detect Blender, Blender MCP, and OrcaSlicer before relying on them. If a tool is
  missing, ask whether the user wants it installed or enabled. If declined,
  continue with repo-native tools and label unavailable validation explicitly.
- OrcaSlicer has an official CLI but no project-approved first-party MCP entry. Keep
  the repository's OrcaSlicer MCP template disabled unless a specific third-party
  server has been audited and explicitly enabled.
- For engineering shapes (countersinks, bosses, ribs, hulled contours), prefer **build123d** for the solid and re-export through trimesh (round vertices to 0.001 mm, merge, dedupe faces) to guarantee a watertight ASCII STL.
- When recreating parts from photos/videos, run the render-and-compare loop (vedo offscreen renders vs. reference frames) before declaring the model done; see `.github/skills/stl-from-image-measurements/SKILL.md`.
- Before reading reference photos, build a numbered contact sheet with `python scripts/make_contact_sheet.py <image folder>` and open only the tiles that show the feature in question. Commit the sheet as `<image folder>/_index.png` and cite tile numbers in the measurement doc.
- When a model is finished, delete its raw reference photos and temporary analysis renderings after the final presentation render has been shown in chat. Keep the final presentation render as needed for the deliverable/PR, and keep only the contact sheet(s), renamed after the model, in `model-sources/archiv/` (e.g. `duschscharnier_ersatz-referenzfotos-index.png`); record the tile-to-file legend in `model-sources/archiv/README.md`.

## Realism And Mechanism Proof

- For anatomical, skeletal, creature, historical-artifact or other complex organic forms, search for a license-compatible scan or reference mesh before approximating the shape with primitives. Preserve attribution and license metadata in `docs/`; cache only the smallest reproducible derivative needed by the generator.
- Treat a reference mesh as shape evidence, not as a finished printable mechanism. Re-rig, segment, thicken, fuse and add sockets/flexures parametrically while preserving the recognizable source anatomy.
- Separate visual and mechanical reconstruction: organic parts may reuse researched meshes, while pivots, rails, latches, stops and clearances must come from explicit dimensions and equations.
- A moving assembly is not complete after static mesh validation. Sample the full motion range, solve every pivot analytically, and run manifold intersection-volume checks against fixed parts and adjacent moving parts. Record a PASS/FAIL report under `docs/`.
- For every multi-part mechanism, run the "Mechanism and assembly audit" from `reversible-fdm-joints`: BOM-vs-scene completeness, all-pairs collision sweep (not a whitelist), fit clearances including print inaccuracy, gear backlash, positive pin/snap retention, and insertion sweeps for the full assembly order.
- Verify both end states: the deployed state must clear the enclosure and lid; the retracted state must fit wholly inside the usable cavity with explicit minimum margins. Render both states.
- Replace any solid tray, bridge or decorative body that crosses the swept volume with an open yoke/frame or another structurally bounded rebuild; never hide a collision in the closed render.
- Put hinges on the physically correct edge and verify their rotation axis against the reference image before detailing the shell.
- Keep assembly and manufacturing separate: the `-view.3mf` is the assembled
  presentation model, never a print layout. For mechanisms, include a plate for
  each meaningful assembly state in the view project.
- The single complex-project `-print.3mf` must contain the complete BOM, the
  Anycubic Kobra S1 0.4 mm machine profile, explicit Textured PEI bed selection,
  each matching filament/spool profile and object-to-filament mapping, plus
  object-specific overrides for walls, infill, supports, speeds or brim where
  function differs. Neutral geometry-only 3MF files do not satisfy this
  requirement.
- Do not split a complex project's print BOM into separate material/color
  projects. Group parts with the same material and color on shared plates when
  they fit safely; use additional internal plates for bed size, orientation,
  supports or print-risk isolation.
- For ornate reference designs, use real raised/recessed geometry (scrolls, tracery, leaves, ribs, cartouches), not a few generic arches or a texture. Validate minimum stroke and relief depth for the nozzle. Raised and engraved relief may be mixed; engraving requires enough remaining wall thickness to stay structurally sound.

## Common Pitfalls

- `manifold3d` must be installed, or boolean operations fail.
- `shapely` and `rtree` are **not** installed, so `mesh.contains()` and `section().to_planar()` raise. Verify feature placement with a boolean volume probe against a small box instead.
- OCCT exports (build123d) are often not watertight until the trimesh repair re-export runs; tangential knife-edge contours cause non-manifold edges and must be fixed by overlapping solids in the source geometry.
- `make_hull` of two circles produces straight tangent segments and is the wrong way to build teardrop/egg contours; use tangent flank arcs (see `create-ascii-stl`).
- Internal ledges must be sketched on the plane they sit on and extruded upwards; sketching them in a side plane hides them mid-cavity and looks like a missing feature.
- `pymeshfix` deletes geometry on thin-walled multi-chamber parts; do not use it.
- Slicer auto-repair is not a source fix. Return to Python or Blender, repair the
  source geometry, re-export, and revalidate.
- PATH absence alone does not prove Blender or OrcaSlicer is uninstalled; inspect
  common install locations or ask for the executable path.
- Editing `models/*.stl` directly can desync files from their parametric source script.
- Fit tweaks should be made in script parameters, then regenerated and revalidated.
- User-edited measurement docs under `docs/` are authoritative; re-read them before every geometry change.
- When the user reports a defect that the mesh probes contradict, check **which file they are actually looking at**. This repo is used through git worktrees, so `D:\harrybin\3d-printing\models\*.stl` (the main checkout) can hold a stale working copy while the session worktree is current. Compare `mtime`, facet count, bounds and `euler_number` of both paths before changing any geometry.
- `euler_number` is a cheap hole detector: a closed part with N through-bores has `2 - 2*N`. An unexpectedly lower value means an extra through-hole, for example a missing floor.

## Key References

- Project overview and workflow: [README.md](README.md)
- Clip generator implementation: [scripts/lineal_clip_kappe.py](scripts/lineal_clip_kappe.py)
- Shared mesh CLI: [scripts/mesh_tool.py](scripts/mesh_tool.py)
- Printer/profile constraints: [.github/skills/anycubic-kobra-s1-ace-pro-profile/skill.md](.github/skills/anycubic-kobra-s1-ace-pro-profile/skill.md)
- STL validation policy: [.github/skills/validate-stl-mesh/skill.md](.github/skills/validate-stl-mesh/skill.md)
- Print optimization policy: [.github/skills/optimize-stl-for-print/skill.md](.github/skills/optimize-stl-for-print/skill.md)
- Dimension sourcing policy: [.github/skills/research-part-specs/skill.md](.github/skills/research-part-specs/skill.md)
- Image-to-STL workflow: [.github/skills/stl-from-image-measurements/SKILL.md](.github/skills/stl-from-image-measurements/SKILL.md)
- Reusable asset/license research: [.github/skills/research-reusable-3d-assets/skill.md](.github/skills/research-reusable-3d-assets/skill.md)
- Blender-assisted modeling: [.github/skills/blender-assisted-modeling/skill.md](.github/skills/blender-assisted-modeling/skill.md)
- OrcaSlicer support minimization: [.github/skills/orcaslicer-support-minimization/SKILL.md](.github/skills/orcaslicer-support-minimization/SKILL.md)
- OrcaSlicer validation: [.github/skills/orcaslicer-print-validation/skill.md](.github/skills/orcaslicer-print-validation/skill.md)
- Multimaterial packaging: [.github/skills/multimaterial-assembly-packaging/skill.md](.github/skills/multimaterial-assembly-packaging/skill.md)
- Local MCP setup: [docs/mcp-setup.md](docs/mcp-setup.md)

## Central consistency matrix

| Concern | Source of truth | Primary skill | Secondary skills | Non-negotiable rule |
| --- | --- | --- | --- | --- |
| Fit-critical dimensions | user measurements or cited specs in `docs/` | `research-part-specs` | `stl-from-image-measurements`, `photo-anchor-candidate-fit`, `create-ascii-stl` | Never invent a fit-critical dimension. |
| Image-based reconstruction gate | task intent | `stl-from-image-measurements` | `image-relief-vectorize`, `photo-anchor-candidate-fit`, `visual-hull-envelope-fit` | Photo-driven skills apply only when reconstructing a pictured object or motif. |
| Free-design / no-original parts | functional constraints and measurements | `create-ascii-stl` | `stl-create-edit-interview`, `research-part-specs` | Do not force photo-tracing workflows onto invented or function-first parts. |
| Relief-first contour extraction | accepted calibrated overlay | `image-relief-vectorize` | `stl-from-image-measurements` | Treat traced contours as candidate outlines, not authority for fit-critical geometry. |
| Refining an existing model toward photos | frozen datums plus branched candidates from one baseline | `photo-anchor-candidate-fit` | `stl-from-image-measurements`, `validate-stl-mesh` | Do not chain uncontrolled edits from the latest STL; branch candidates from the same baseline script. |
| Multi-view outer-envelope recovery | accepted silhouettes from several views | `visual-hull-envelope-fit` | `image-relief-vectorize`, `photo-anchor-candidate-fit` | Use visual hulls only for outer-envelope guidance, not hidden or mating geometry. |
| Rebuild-vs-mutate decision | stable local boundary plus frozen trusted geometry | `partial-rebuild-instead-of-mutate` | `photo-anchor-candidate-fit`, `visual-hull-envelope-fit`, `create-ascii-stl` | If a local region is structurally wrong, rebuild that region from the script instead of continuing STL mutation. |
| Source of geometry edits | parametric scripts in `scripts/` | `create-ascii-stl` | `edit-stl-transform`, `photo-anchor-candidate-fit` | Regenerate from script instead of hand-editing STL facets. |
| STL vs 3MF decision | confirmed material/color semantics | `stl-create-edit-interview` | `create-ascii-stl`, `stl-from-image-measurements`, `optimize-stl-for-print`, `anycubic-kobra-s1-ace-pro-profile` | Distinct material/color regions require a 3MF deliverable; STL is only for merged single-region output. |
| Complex-project print handoff | complete BOM plus material/object process intent | `orcaslicer-project-workflow` | `multimaterial-assembly-packaging`, `anycubic-kobra-s1-ace-pro-profile` | Deliver an assembled `-view.3mf` and one Kobra-S1 settings-bearing `-print.3mf` with all filament mappings; group same-color parts on shared plates and use multiple plates as needed. |
| Coordinate convention | mesh coordinates and user intent | `validate-stl-mesh` | `edit-stl-transform`, `optimize-stl-for-print` | Auto-detect center-origin vs corner-origin unless the user specifies it. |
| Mesh proof and feature existence | `scripts/mesh_tool.py` checks | `validate-stl-mesh` | `stl-from-image-measurements`, `photo-anchor-candidate-fit` | Prove ambiguous internal features with probes/slices, not screenshots alone. |
| Final model image in chat | exact final STL/3MF output | `create-ascii-stl` | `edit-stl-transform`, `stl-from-image-measurements`, `optimize-stl-for-print` | Post an inline rendered image in the final chat response; a canvas preview or path alone is not enough. |
| STL canvas preview | written output path under `models/` | `create-ascii-stl` | `edit-stl-transform`, `stl-from-image-measurements`, `validate-stl-mesh`, `optimize-stl-for-print` | Also preview written STL outputs in the canvas; for 3MF-first outputs, report the 3MF path and preview an STL counterpart when available. |
| Optional helper libraries | repo support status | `.github/skills/README.md` | all skills | Mark non-default helpers such as `scikit-image` or `shapely` explicitly as optional where applicable. |
| Reusable online assets | original source and explicit license | `research-reusable-3d-assets` | `research-part-specs`, `stl-from-image-measurements` | Search before original modeling; unclear or incompatible licenses are reference-only. |
| Python vs Blender routing | feature type and frozen datums | `blender-assisted-modeling` | `create-ascii-stl`, `stl-from-image-measurements`, `research-reusable-3d-assets` | Python owns fit geometry; Blender owns approved organic/visual regions, and realistic or sculptural requests move to Blender with a prior license-compatible asset search instead of more primitives. |
| Delivered-project support minimization | exact final STL/3MF plus fixed Kobra S1 profiles | `orcaslicer-support-minimization` | `orcaslicer-project-workflow`, `optimize-stl-for-print`, `orcaslicer-print-validation` | Compare bounded absolute datum rotations sequentially, preserve material/plate semantics, save orientation in 3MF, and leave geometry changes as suggestions until separately approved at the source model. |
| Final slice evidence | successful OrcaSlicer project slice | `orcaslicer-print-validation` | `optimize-stl-for-print`, `anycubic-kobra-s1-ace-pro-profile` | Never claim print time or final print readiness without a successful slice. |
| Complex 3MF packaging | assembled view plus complete print BOM | `multimaterial-assembly-packaging` | `stl-create-edit-interview`, `optimize-stl-for-print` | Deliver exactly one multi-state `-view.3mf` and one settings-bearing `-print.3mf`; group same-color parts on shared plates and add plates as needed. |
| Mechanism and assembly audit | scripted all-pairs sweep plus PASS/FAIL report in `docs/` | `reversible-fdm-joints` | `validate-stl-mesh`, `multimaterial-assembly-packaging` | No unintended collision at any pose, no missing/extra BOM part, every pin positively retained, every fit and gear backlash sized for print inaccuracy, every assembly step has a free insertion path. |

## Session-Learned Friction To Avoid

Recent sessions in this repo skew heavily toward mesh-quality issues. Default behavior should be:

1. Regenerate from script, do not patch triangles manually.
2. Confirm watertight/manifold status and degenerate-face count after each geometry change.
3. Re-check XY centering convention whenever moving or merging meshes.
4. Prove new internal features with a volume probe, not just mesh stats, and confirm which file the STL canvas actually rendered before believing "the feature is missing".
5. Determine feature sides by normalising several photos to one orientation; a single photo is not enough and has already caused a mirrored feature.
6. Pick contour parameters by projecting candidate outlines onto a landmark-calibrated photo, not by automatic silhouette extraction, which bleeds into shadows.
7. When refining a model toward photos, freeze measured datums and compare branched candidates from the same baseline instead of chaining edits on the last STL.
8. If local tweaking keeps fighting across views, constrain the outer shell from multiple silhouettes first and then rebuild against that envelope.
9. If one local region is structurally wrong, cut at a stable boundary and partially rebuild it instead of continuing mutation across the whole model.
