# Skills Library

This file is the reusable knowledge index for STL workflows in this repository.
If a procedure is needed more than once, it belongs in a skill file.

## Goal

- Keep repeatable workflows in one place instead of isolated PR notes.
- Enforce consistent decisions for geometry, printability, validation, and sourcing.
- Make future sessions productive without rediscovering the same process steps.

## Library structure

| Area | Skill | Scope |
| --- | --- | --- |
| Printer profile | `anycubic-kobra-s1-ace-pro-profile` | Wall/clearance/overhang/bridge baselines and nozzle scaling |
| New modeling | `create-ascii-stl` | Parametric modeling, CSG/repair workflow, export rules |
| STL edits | `edit-stl-transform` | Transform/boolean rules and output/orientation policy |
| Image to model | `stl-from-image-measurements` | Contact-sheet flow, research branch, render-compare loop |
| Image preprocessing | `image-relief-vectorize` | Conditional relief-first image cleanup and contour vectorization when reconstructing a pictured object before 3D modeling |
| Photo-guided refinement | `photo-anchor-candidate-fit` | Freeze trusted geometry, branch candidates from one baseline, and compare them against calibrated image landmarks |
| Multi-view envelope | `visual-hull-envelope-fit` | Constrain an outer shell from several silhouettes before rebuilding or refining the model |
| Partial rebuild | `partial-rebuild-instead-of-mutate` | Rebuild only the wrong local region from a stable boundary instead of continuing to mutate a drifting model |
| Spec sourcing | `research-part-specs` | Fit-critical dimension sourcing and measurement docs in `docs/` |
| Preflight interview | `stl-create-edit-interview` | Required intent questions before creating/editing |
| Mesh quality | `validate-stl-mesh` | Integrity checks, feature probes, stale-file checks |
| Print optimization | `optimize-stl-for-print` | Orientation and compensation decisions after geometry is correct |

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
| Coordinate convention | mesh coordinates and user intent | `validate-stl-mesh` | `edit-stl-transform`, `optimize-stl-for-print` | Auto-detect center-origin vs corner-origin unless the user specifies it. |
| Mesh proof and feature existence | `scripts/mesh_tool.py` checks | `validate-stl-mesh` | `stl-from-image-measurements`, `photo-anchor-candidate-fit` | Prove ambiguous internal features with probes/slices, not screenshots alone. |
| STL canvas preview | written output path under `models/` | `create-ascii-stl` | `edit-stl-transform`, `stl-from-image-measurements`, `validate-stl-mesh`, `optimize-stl-for-print` | Preview any written STL immediately; for 3MF-first outputs, report the 3MF path and preview an STL counterpart when available. |
| Optional helper libraries | repo support status | `.github/skills/README.md` | all skills | Mark non-default helpers such as `scikit-image` or `shapely` explicitly as optional where applicable. |

## What belongs in the library

Keep only durable, reusable content:

- stable decision rules (for example STL vs 3MF, coordinate-convention detection)
- reproducible checklists (validation, print optimization, photo workflow)
- recurring failure patterns and mitigations
- proven repo command paths (`scripts/mesh_tool.py`, `scripts/make_contact_sheet.py`)

Do not store as a formal library rule:

- one-off task details with no reuse value
- volatile numeric values without policy relevance
- PR-specific discussions or temporary workarounds

## Maintenance rules

1. **Single source of truth:** Keep reusable procedures in the owning skill file.
2. **Resolve conflicts by specificity:** Prefer the more specific skill when rules differ.
3. **Keep sources visible:** Maintain external references in each skill’s `Sources` section.
4. **Update together:** When scripts or policies change, update affected skills in the same change.
5. **Keep it actionable:** Write concise but complete rules.

## Template for adding new reusable findings

When new reusable guidance emerges from research or bug-fix cycles, add to the matching skill:

1. **Rule name**
2. **When to apply**
3. **Required steps**
4. **Stop/warning criteria**
5. **Output evidence** (what metrics/artifacts must be reported)

## Python library catalog for future 3D workflows (online researched)

This is a candidate catalog for future capabilities in 3D generation, geometry
calculation, mesh repair/analysis, and visualization. It complements currently
used repo libraries (`build123d`, `trimesh`, `manifold3d`, `vedo`).

### A) Parametric CAD / solid modeling

| Library | Typical use | Notes |
| --- | --- | --- |
| `build123d` | Parametric BREP modeling on OCCT | Already used in this repo |
| `cadquery` | Scriptable parametric CAD on OCCT | Strong alternative/complement to build123d |
| `pythonocc-core` | Low-level OpenCascade access | Useful for deep OCCT operations |
| `solidpython2` | Python frontend for OpenSCAD CSG | Useful for CSG-heavy designs |

### B) Mesh processing, booleans, repair, STL I/O

| Library | Typical use | Notes |
| --- | --- | --- |
| `trimesh` | Mesh I/O, analysis, repair, conversion | Already used in this repo |
| `manifold3d` | Robust mesh booleans | Already used in this repo |
| `numpy-stl` | Lightweight STL read/write/transform tasks | Useful for simple batch jobs |
| `pymeshlab` | MeshLab filter/repair pipeline | ⚠ Avoid aggressive cleanup filters on thin multi-chamber parts; same risk class as the repo `pymeshfix` prohibition |
| `open3d` | Mesh + point-cloud processing | Useful for reconstruction/registration tasks |

### C) Geometry/math engine (indirect modeling support)

| Library | Typical use | Notes |
| --- | --- | --- |
| `numpy` | Numeric vector/matrix operations | Already used in this repo |
| `scipy` | Optimization, spatial/distance algorithms | Useful for fitting and solver tasks |
| `sympy` | Symbolic geometry/algebra | Useful for exact formulas/derivations |
| `shapely` | 2D computational geometry | ⚠ Not installed in this repo venv; together with missing `rtree` this breaks `mesh.contains()` and `section().to_planar()` in current workflows |

### D) Visualization, rendering, verification

| Library | Typical use | Notes |
| --- | --- | --- |
| `vedo` | Offscreen rendering and visual comparison | Already used in this repo |
| `pyvista` | High-level VTK visualization | Useful for interactive analysis pipelines |
| `vtk` | Low-level visualization/filter pipeline | Powerful but more complex |
| `open3d` | Interactive viewers + geometry inspection | Useful for mesh/point-cloud review |

### E) Image/measurement workflow (indirect but critical)

| Library | Typical use | Notes |
| --- | --- | --- |
| `opencv-python-headless` | Frame extraction, contour comparison, overlay checks | Already used in this repo |
| `scikit-image` | Relief-style preprocessing, contour extraction, polygon simplification | Useful optional helper for the relief/vector workflow when available |
| `pillow` | Image processing and contact sheets | Already used in this repo |

### F) 2D vector cleanup / tracing

| Library | Typical use | Notes |
| --- | --- | --- |
| `shapely` | Polygon cleanup, boolean cleanup, simplification after contour extraction | Useful only as an out-of-repo optional companion for experiments; not installed in this repo venv today and should not be relied on in committed default workflows |
| Potrace-style Python wrappers | Bitmap-to-vector tracing for glyph/logo style inputs | Treat as optional only; check license before adoption and do not make it the default path |

## Rule for introducing new libraries

Before adopting a new library into the permanent repo workflow:

1. Confirm current repo libraries cannot already solve the use case.
2. Add only when there is clear capability or quality gain.
3. Document in the owning skill: when to use, when not to use, and required validation.
4. Keep `requirements.txt`, README, and skill docs aligned.

## References (official entry points)

- build123d: https://pypi.org/project/build123d/
- CadQuery: https://github.com/CadQuery/cadquery
- pythonocc-core: https://github.com/tpaviot/pythonocc-core
- SolidPython2: https://pypi.org/project/solidpython2/
- trimesh: https://github.com/mikedh/trimesh
- manifold3d: https://pypi.org/project/manifold3d/
- numpy-stl: https://pypi.org/project/numpy-stl/
- pymeshlab: https://pypi.org/project/pymeshlab/
- Open3D: https://www.open3d.org/
- NumPy: https://numpy.org/
- SciPy: https://scipy.org/
- SymPy: https://www.sympy.org/
- Shapely: https://shapely.readthedocs.io/
- vedo: https://vedo.embl.es/
- PyVista: https://pyvista.org/
- VTK: https://vtk.org/
- OpenCV: https://opencv.org/
- Pillow: https://python-pillow.org/
