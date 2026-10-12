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
