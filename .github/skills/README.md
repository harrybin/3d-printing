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
| Spec sourcing | `research-part-specs` | Fit-critical dimension sourcing and measurement docs in `docs/` |
| Preflight interview | `stl-create-edit-interview` | Required intent questions before creating/editing |
| Mesh quality | `validate-stl-mesh` | Integrity checks, feature probes, stale-file checks |
| Print optimization | `optimize-stl-for-print` | Orientation and compensation decisions after geometry is correct |

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
| `pillow` | Image processing and contact sheets | Already used in this repo |

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
- Open3D: http://www.open3d.org/
- NumPy: https://numpy.org/
- SciPy: https://scipy.org/
- SymPy: https://www.sympy.org/
- Shapely: https://shapely.readthedocs.io/
- vedo: https://vedo.embl.es/
- PyVista: https://pyvista.org/
- VTK: https://vtk.org/
- OpenCV: https://opencv.org/
- Pillow: https://python-pillow.org/
