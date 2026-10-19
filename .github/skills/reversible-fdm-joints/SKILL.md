---
name: reversible-fdm-joints
description: Select, design, and validate strong glue-free FDM assembly joints, preferring serviceable removable connections and checking load paths and insertion sweeps.
---

# Reversible FDM joints

Use this skill when a printed design contains multiple parts, replaceable
components, pivots, shafts, covers, mechanisms, or any installation step.
Prefer reversible, glue-free assembly unless the user explicitly accepts a
permanent connection and permanence has a clear mechanical benefit.

Use `scripts/fdm_joints.py` for standard joint geometry. Treat its dimensions as
starting values: print fit coupons on the target printer/material before
committing a large assembly.

## Workflow

1. **Write the assembly contract**
   - List every joined part, assembly order, expected service access, tools,
     insertion direction, available hand/tool clearance, and whether the joint
     must be removable.
   - Record the load modes at each interface: torque, bending, tension,
     compression, shear, shock, vibration, and cyclic/fatigue loading.
   - Record temperature, moisture, material, print orientation, expected life,
     and whether sustained preload could cause creep.

2. **Choose a reversible joint first**
   - Alignment/light shear: printed headed pin with an R-clip/cotter retainer,
     filament cross-pin, or removable stop.
   - Repeated screw service: machine screw into a captive nut, cross-dowel, or
     heat-set insert. Use the hardware manufacturer's hole dimensions, then
     calibrate them with a coupon.
   - Torque transmission: D, hex, or square shaft with adequate engagement
     length; add a removable axial retainer. Do not ask a round friction fit to
     carry meaningful torque.
   - Fast quarter-turn service: bayonet/twist-lock with a positive end stop and
     a separate anti-rotation detent or screw when vibration can unlock it.
   - Long guided interfaces: dovetail or tongue-and-groove with a removable end
     stop, screw, pin, or clip. The slide locates and carries transverse load;
     the stop provides axial retention.
   - Clips: use compliant clips only when the material, print orientation, and
     required cycle life allow them. Prefer a screw/pin backup for critical
     retention.

3. **Route the load through the right feature**
   - Torque: use opposed flats/splines/keys with broad bearing area. Increase
     engagement length before tightening fit. Avoid sharp keyway roots.
   - Bending: separate bearing planes, shorten unsupported spans, add root
     fillets/gussets, and keep bending stress in the stronger XY layer plane.
   - Tension: use shoulders, through-bolts, washers, cross-pins, or captured
     hardware so load does not peel layers apart in Z.
   - Compression: provide hard stops and broad faces; do not make a flexible
     latch carry continuous compressive preload.
   - Shear: prefer double shear for pins and screws. Keep holes away from edges
     and provide enough material around the bore.
   - Fatigue/shock: reduce notches, avoid abrupt section changes, lower working
     strain, remove sustained snap-arm deflection, and use ductile material.
   - Creep: do not rely on permanent plastic spring force for long-duration
     clamp load, especially near heat. Transfer preload into screws, metal
     inserts, stops, or shoulders.

4. **Account for FDM anisotropy and process limits**
   - Orient primary tension and snap-arm bending in XY where practical; avoid
     opening a joint by peeling adjacent layers apart.
   - Prefer commercial metal pins for critical pins below 5 mm. If a printed
     pin is acceptable, use a root fillet, generous diameter, and replaceable
     geometry.
   - Printed holes often finish undersize. Use named clearance constants from
     `scripts/fdm_joints.py`, but verify with the actual printer, filament,
     nozzle, layer height, and hole orientation.
   - Add lead-in chamfers and elephant-foot relief where first-layer flare can
     block insertion. Avoid unsupported internal roofs in nut traps and slots.
   - Place more walls/material around inserts, nut traps, pin bores, and shaft
     flats than the nominal minimum; the local load path matters more than
     global infill percentage.

5. **Model retention separately from location**
   - A shaft profile or sliding rail locates and transmits load; it does not
     automatically retain axially.
   - Add an explicit retainer: cross-pin, screw and washer, nut, removable stop,
     collar, circlip/R-clip feature, or accessible service clip.
   - Captive nuts and cross-dowels must be mechanically trapped after assembly
     but remain replaceable. Provide an insertion path and tool access.
   - Heat-set inserts are acceptable glue-free hardware, but the insert itself
     is not normally intended for repeated removal from the plastic. Design the
     screw joint to be serviced, not the insert-to-plastic interface.

6. **Prove assembly access and insertion**
   - Create a swept volume for every inserted part and tool along the complete
     insertion/removal path, including rotations for bayonets and tilted
     hardware.
   - Boolean/interference-check each sweep against already installed parts.
   - Verify the final retainer can be reached and removed without bending,
     cutting, or destroying another part.
   - Stop if the assembly only works by passing through occupied geometry,
     relies on an inaccessible fastener, or traps a service part behind a
     permanent joint.

7. **Prototype and validate**
   - Print a coupon containing the exact hole, shaft, nut trap, dovetail, or
     clip orientation before the full build.
   - Check free insertion, backlash, retention, tool access, and disassembly.
   - Apply representative torque, bending, pull, compression, and side load.
     For cyclic joints, test repeated cycles beyond the expected service count
     or downgrade the joint to replaceable/limited-life.
   - Validate every exported body as watertight and single-body. Run:
     `.\.venv\Scripts\python.exe -m unittest tests.test_fdm_joints`

## Joint selection rules

| Need | Preferred joint | Required checks |
| --- | --- | --- |
| Pivot or hinge | Metal/printed pin with removable retainer; filament pin for light duty | Double shear, bearing area, pin bending, axial retention, insertion access |
| Repeated cover removal | Machine screws plus captive nuts or heat-set inserts | Pull-out direction, boss splitting, tool access, compression stops |
| High torque | Keyed D/hex/square shaft or separate key | Flat bearing pressure, engagement length, torsional layer path, axial retainer |
| Guided removable panel | Dovetail or tongue-and-groove plus removable stop | Full insertion sweep, end breakout, wear, debris clearance |
| Quick quarter-turn | Bayonet/twist-lock | Ramp load, stop strength, accidental reverse rotation, wear |
| Light service latch | Releasable compliant clip | Neutral state after engagement, root fillet, strain, fatigue, release access |
| Permanent low-service retention | One-way snap, calibrated press fit, or staking | Explicit user acceptance, no trapped service item, documented destruction/removal method |

## Permanent joints: limited exceptions

Only propose these after reversible options have been considered and rejected:

- **One-way snap fits:** allowed for tamper evidence, disposable modules, or
  parts never expected to be serviced. Mark them as destructive removal.
- **Interference/press fits:** allowed for low-cycle locating or permanent
  retention after a printed tolerance coupon. Do not use as the sole critical
  torque connection or where creep/temperature can relax the fit.
- **Thermal/mechanical staking:** allowed for factory-style permanent capture
  of a non-service item. Provide enough head material and backing support, and
  document that disassembly destroys the stake.
- Adhesive is not a default fallback. Use it only when the user specifically
  accepts it or when sealing/bonding—not mechanical retention—is the governing
  requirement.

## Validation checklist

- Reversible glue-free joint selected wherever service is plausible.
- All load modes and load directions documented.
- Strongest print orientation aligned with the governing load.
- No critical joint depends only on friction, infill, or Z-layer adhesion.
- Location and axial/rotational retention are both explicit.
- Hardware, hands, and tools have collision-free insertion/removal sweeps.
- Nut/insert/pin cannot escape into the mechanism.
- Sustained loads do not leave a compliant arm continuously deflected.
- Fit-critical dimensions are calibrated with coupons.
- Every generated helper mesh is watertight, winding-consistent, positive
  volume, and one connected body.

## Mechanism and assembly audit (mandatory for multi-part mechanisms)

Run this audit whenever a design contains moving parts, pins, gears, racks,
cams, sliders, snap features, or more than one printed body that must be put
together. A whitelist check of "expected contacts" is not enough: earlier
projects passed such a verifier while the slider could not be inserted, arms
collided and pins had no retention. Automate the audit as a script (example:
`scripts/audit_ghouls_grip_assembly.py`) and write a PASS/FAIL report under
`docs/`. Never declare a mechanism done from renders alone.

1. **Completeness and BOM**
   - Derive the BOM from the assembled scene, not from memory. Every scene body
     must map to exactly one printable part name, and every print quantity must
     equal the number of scene instances (no missing parts, no extras).
   - Every pivot, shaft, follower and gear has a named retainer part in the BOM
     (pin, cross-pin, snap nose, clip). Removed features must also leave the
     print project, docs and tests.
   - **Non-printed fasteners** (filament cross-pins, hinge filament, dowels,
     screws) belong in the BOM with length and bore. Model each as a
     proxy cylinder in the audit: it must not collide with any part and must
     engage every host it is meant to pass through. A proxy hit is how a
     knuckle bore that a later union silently refilled was found — drill
     shared axes once, after every union of the host body.
   - The assembled scene must place each part by the **same datum the real
     joint uses** (pin axis, shoulder, seat). Apply every seat offset to all
     bodies located through that joint; an offset applied to only one side
     (forearm shifted 4 mm, hand not) hides a misaligned cross pin.
   - Every gear or wheel needs a defined axial stop on **both** sides (hub
     shoulder, collar, pin head, wall) with 0.2–0.5 mm total play; free axial
     float larger than about 1 mm can walk a narrow gear off its mate.

2. **Function across the full motion range**
   - Solve every pivot/linkage analytically and sample the full range (ends,
     dwell boundaries and at least five interior poses).
   - Cache every unique part's base mesh once per process (`@lru_cache`) and
     transform copies via `4x4` matrices for each pose rather than rebuilding
     CAD/boolean solids inside the pose loop. Pre-filter every pair by bounding
     box (`bounds`) overlap before running `manifold` boolean intersections,
     parallelize independent finger builds, pose sweeps, and insertion sweeps
     with `concurrent.futures.ThreadPoolExecutor` (sharing `@lru_cache` meshes
     in-memory while `manifold3d` releases the GIL), and use a `--quick` subset
     (7 key poses, 5 insertion steps) during iterative tuning before running the
     final full-density verification suites in parallel at the end.
   - Run an **all-pairs** boolean intersection of every body at every pose.
     Any intersection above about 0.5 mm³ is a failure unless it is a
     documented intended contact (pin in bore, tooth flank); fix geometry, do
     not whitelist collisions.
   - Check drive signs and phase: input rotation direction, rack/pinion
     direction, cam law and output timing must match the intended motion (for
     example, the lid must start opening when planned, not after a dwell).
   - Check flexible members under expected load (cantilever racks, long
     arms): estimate deflection; add webs, skids or second supports when a
     deflection can disengage teeth or jam a slide.

3. **Fits with print inaccuracy** (start values, then confirm with a coupon on
   the Kobra S1 / 0.4 mm nozzle)
   - Rotating pin in printed bore: ≥ 0.5–0.6 mm diametral clearance for
     printed pins (for example Ø4.0 pin in Ø4.6 bore); horizontal bores print
     oval and undersized, so test the worst orientation.
   - Sliding guides and rails: ≥ 0.4–0.5 mm per side; plug-in keys and
     D-shafts: 0.3–0.4 mm diametral (`CLEARANCE_SERVICE`).
   - Axial stack-ups (lugs, arms, washers, gears on one pin): ≥ 0.2 mm axial
     play per moving interface; sum the stack and verify the pin grip length.
   - Gears and racks: keep module ≥ 1 for printed teeth where possible, give
     0.15–0.35 mm backlash per flank and ≥ 0.25 mm tip-to-root clearance;
     measure backlash and tip clearance numerically at several mesh phases.
   - Account for elephant foot (chamfer the first 0.4 mm of mating edges) and
     for support-contact surfaces, which are rough and need extra clearance.

4. **Pins, Splinte and latching**
   - Every pin needs a positive axial lock: head plus snap barb (split shank
     with a flat catch face and a lead-in cone), a cross-pin, an R-clip or a
     captured position. A plain friction pin is a failure; defined crush ribs
     (0.1–0.2 mm interference) are acceptable only where a split is
     impossible and the pin carries no axial load — document the exception.
   - Snap barbs: verify the split slot gives enough deflection space
     (barb overlap < slot width), estimate bending strain
     ε ≈ 3·δ·c/L² (δ = closure per half, c = half-section fibre distance,
     L = split root to barb; ≤ about 2 % for PETG/PLA one-time, ≤ 1 % for
     repeated use; a stiff head at the root does not lengthen L) and sink the
     barb in a counterbore so it neither rubs moving parts nor protrudes into
     a sweep.
   - Prove the closed-state envelope numerically: shift each split half by
     the available closure and check the barb against the bore radius. A
     revolved (round) barb on a split pin never passes its bore, because
     closing only narrows the flex direction while the slot-plane width
     stays oversize; use per-half barb arcs offset outward by the closure.
   - Avoid running a split section as a journal in a slot or bearing: each
     load then bends a single cantilever half and the slot gap makes the
     journal non-round. Keep the split in the retained zone or use a solid pin.
   - Snap noses on sliders/covers: flat catch face, 30–45° lead-in, deflection
     room behind the spring arm along the whole insertion path, and a release
     path for service.
   - Print pins lying flat (layers along the shank) with a small flat; never
     print a load-carrying pin upright. Offer a metal dowel alternative below
     Ø5 mm.

5. **Assembly order and insertion sweeps**
   - Write the full assembly order. For each step, sweep the inserted part
     (and the finger/tool path for pins) against everything already installed.
   - Check that guides have an entry (a slider wider than the cavity cannot be
     inserted into closed full-length grooves), that pins can be pushed in from
     a reachable side, and that the barb exit side has free space.
   - Verify the final installed state and disassembly path as well.
   - Gear meshing: insert a gear along the **line of centres** of its mating
     gear. When that line is not parallel to the insertion direction (for
     example a platform dropped vertically onto a gear whose line of centres
     is 64° from vertical), approach offset away from the mesh, then slide
     into mesh; sweep both segments and install the driven gear before the
     sub-assembly that would block it.
   - Enclosed retainers (spacers, washers, keys trapped between two shells):
     prove they can still be placed after both shells are joined. If not,
     sub-assemble them on the loose part first and sweep the whole unit,
     including any offset-then-slide path into mesh.
   - Packaging: after adding or removing objects, re-check the 3MF
     `model_settings.config` `<assemble>` section and plate lists. OrcaSlicer
     aborts loading ("parsing aborted") when an assemble item references a
     missing object ID; a stale section is a delivery defect, not a cosmetic
     one.

6. **Printability per part**
   - Each part is watertight, one body, and has a stated print orientation that
     puts the governing bending/tension in XY.
   - Spring arms and snap noses print with layers along the arm; slots and
     bore roofs either bridge cleanly or are listed as supported.
   - Minimum wall/stroke ≥ 2 perimeters (0.8–1.2 mm) around every bore.

Record each check with numbers (clearance, volume, strain, backlash) in the
PASS/FAIL report and keep the audit script runnable by tests.

## Edge cases

- If no removal path exists, change the part split or assembly order before
  making the joint permanent.
- If a screw axis is inaccessible, use a cross-dowel, side-loaded captive nut,
  bayonet, or relocate the fastener; do not hide an unserviceable screw.
- If torque reverses, eliminate backlash-sensitive one-sided keys and verify
  both flanks.
- If a sliding joint carries bending, lengthen bearing engagement or add a
  second rail; do not tighten clearance until it binds.
- If material data, load magnitude, or service cycles are unknown, state the
  uncertainty, choose a conservative replaceable joint, and require a physical
  load test.

See `references/joint-design-sources.md` for the research basis and source
limitations.
