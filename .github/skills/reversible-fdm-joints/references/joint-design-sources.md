# FDM joint design sources

Consulted 2026-10-10. Numeric fit values are starting points, not universal
truths; printer, material, orientation, and hardware-specific coupons remain
mandatory.

## Authoritative and engineering sources

1. **Stratasys, _Fused Deposition Modeling (FDM) Design Guidelines_**
   - https://www.stratasys.com/siteassets/sdm/resources/design-guidelines/fdm/fdm_design_guidelines_2017-1.pdf
   - Manufacturer guidance for FDM feature sizing, build orientation, and the
     directional nature of printed properties.

2. **Protolabs Network, _How to design parts for FDM 3D printing_**
   - https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/
   - Documents undersized vertical holes, first-layer flare, bridging and
     overhang limits, and recommends inserted commercial pins for critical
     pins below 5 mm.

3. **Protolabs Network, _How do you design snap-fit joints for 3D printing?_**
   - https://www.hubs.com/knowledge-base/how-design-snap-fit-joints-3d-printing/
   - Covers cantilever and annular snaps, fatigue, creep, stress
     concentrations, material choice, and a nominal 0.5 mm FDM clearance.

4. **Formlabs, _How to Design and 3D Print Snap-Fit Joints_**
   - https://formlabs.com/global/blog/designing-3d-printed-snap-fit-enclosures/
   - Useful cross-process engineering discussion of assembly tolerances,
     orientation, snap engagement, and enclosure access. Its SLA/SLS numeric
     values must not be copied directly to FDM.

5. **Protolabs, _Threading in 3D Printing: Heat Set and Press Fit Inserts,
   Tapping_**
   - https://www.protolabs.com/resources/blog/threading-and-inserts-for-3d-printing/
   - Recommends post-installed hardware rather than relying on fine
     as-printed threads and emphasizes machining/installation access.

6. **CNC Kitchen, _Tips & Tricks for Heat-Set Inserts used in 3D printing_**
   - https://www.cnckitchen.com/blog/tips-and-tricks-for-heat-set-inserts
   - Test-backed installation guidance, supplier-dimensioned hole/wall tables,
     blind-hole depth guidance, straight installation, and calibration coupons.

## How these sources are applied

- Source dimensions are not silently generalized across printers or insert
  brands.
- FDM anisotropy is treated as a load-path constraint, not just an orientation
  preference.
- Snap fits are not the default for repeatedly serviced or continuously
  preloaded joints because creep and fatigue are explicit failure modes.
- Metal fasteners, captive hardware, and removable retainers are preferred when
  loads or service cycles exceed what a printed compliant feature can reliably
  carry.
- Every assembly requires a collision-free insertion and tool sweep even when
  the individual joint geometry is printable.
