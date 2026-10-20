# Engine / catalog split

## Ownership

`harrybin/3d-printing` owns shared tools, Python distribution
`harrybin-printforge`, skills, viewer code and engine setup docs.
`harrybin/3d-printing-models` owns model generators and their supporting
modules, model tests, measurements, source attribution, reference assets,
STL/3MF output and presentation/support images.

For example, `mechanism.py`, `skeleton_hand.py`, `skull.py`, the Ghoul's Grip
export/slice/audit scripts and their tests are model-owned, not engine APIs.
`mesh_kit.py`, `fdm_joints.py`, `sdf_blend.py`, `sdf_bones.py`, the mesh CLI,
generic renderers, contact-sheet and GenAI tooling are engine-owned.

## Migration guarantees

The initial catalog history is filtered from engine commit
`4243f0e` (the full source SHA is recorded in `catalog.json`). The source
repository history is not rewritten. Model paths remain unchanged to preserve
links, measurement references, Blender sources and generator datums.
`catalog.json` records 13 model entries, 29 STL/3MF outputs and the SHA-256
baseline for 141 migrated model assets/docs. Its generator field is explicitly
null when no existing source is known. No generator is invented during transfer.

The catalog contains no versioned copy of shared engine tools/skills/viewer.
It installs the pinned engine and runs `printforge bootstrap .`. Generated
resources are ignored by Git, and tracked model sources continue to use their
original sibling-import/CLI paths. Engine resources remain reproducible from
the selected package. Bootstrap records owned resource hashes and refuses
unmanaged changes instead of clobbering them.

The repository MIT license, per-model source licenses and provenance remain
unchanged. Visibility remains public. Binary assets use normal Git, as explicitly
chosen for this migration; there is no LFS billing or pointer-download change.
No geometry is regenerated or sliced, and existing print-profile exceptions and
physical test-print risks are preserved, not reported as newly validated.
The original 81-test baseline already had one error in
`test_ghouls_grip_bone_plate_layout`: the ring finger's proposed layout crosses
the plate edge (X maximum 271.07479884546865 mm). That model test/project remains
unchanged in the catalog; its CI reports the failure rather than hiding it.
The independent post-migration 60-test model suite reproduced that one error
without any additional failures. Engine 1.0.1 stores its agent resources in one
ZIP inside the wheel, avoiding Windows temporary-build `MAX_PATH` errors in
the initial 1.0.0 Git-pinned installation.

## Catalog contract

`catalog.json` schema version 1 declares the repository, engine version/source,
and a `models` array. Every entry has a unique slug, optional catalog-relative
generator, output paths, doc paths and source/license status. Every STL/3MF in
`models/` must be listed exactly once. `printforge verify-catalog` checks this
inventory and path existence. Use `--migration` only to verify the frozen
historical hashes; deliberate later asset changes need not match that baseline.
Printability, mechanism checks and slice evidence remain separate model gates.

## CI and publishing

Engine PRs run the independent engine/viewer suites and build the wheel.
The catalog installs its engine version for model tests and checks out the same
version for the Pages viewer. The web build sets `CATALOG_ROOT` to the catalog,
copies models plus preview/support sidecars, and targets catalog repository/issue
links. The previous engine Pages URL remains supported through a second build
against the external catalog.

New model requests and the optional Copilot model-agent workflow belong to the
catalog. Configure `COPILOT_GITHUB_TOKEN` and `PAGES_RUNNER_ALLOWLIST` there only
if that runner is needed; GitHub secrets are neither copied nor recoverable from
the engine. No secrets are required for the public Pages/validation workflows.

For engine upgrades, update package version declarations, release a tested tag,
then update the catalog `requirements.txt` pin and Pages engine ref together.
Review the catalog model suite before accepting the new version.

## Rollback

Do not force-push or rewrite the engine's existing main history. Until the split
PR is merged, main still contains the original combined layout. The new catalog
is independently available and pins the published engine tag.
After merge, revert the split commit if the original combined layout is needed.
Retain the catalog and released engine tag for reproducibility; do not delete
either as part of a rollback. An engine upgrade can instead be rolled back by
restoring the catalog's previous engine dependency and viewer ref together.
