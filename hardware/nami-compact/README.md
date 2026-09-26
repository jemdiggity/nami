# Nami Compact C0 — production layout candidate

**24 × 32 mm, four copper layers, 1.0 mm nominal PCB thickness, components on both sides.** This reduces board area from the Rev A bench board's 7,125 mm² to 768 mm²: **89.22% smaller**. Open [nami.kicad_pro](nami.kicad_pro) in KiCad 10.

This is a routed, checked candidate for the product's electronics, not a qualified production release. The dimensions describe the PCB alone. Battery/holder, CT, burden assembly, wiring, strain relief and enclosure are separate. Accuracy, endurance and installed RF performance remain unmeasured.

| Review artifact | Contents |
|---|---|
| [Front render](exports/nami-top.png) / [back render](exports/nami-bottom.png) | Actual KiCad board geometry and library component models |
| [Size comparison](exports/size-comparison.svg) | Board outlines to scale |
| [Schematic PDF](exports/nami-schematic.pdf) | Five sheets, including the off-board CT burden |
| [STEP model](exports/nami-compact.step) | Board and available library models for initial enclosure work; not a certified component tolerance model |
| [BOM](exports/bom.csv) | Package changes and preliminary parts; PCB contacts/test pads are not purchased components |
| [Routing review: before / after](exports/routing-review.pdf) | Ten close-ups covering the flagged routing details; ground fills hidden for clarity |
| [Layout verification](verification/compact-layout.json) | Dimensions, circuit equivalence, layer use and critical route lengths |
| [ERC](verification/erc.rpt) / [DRC](verification/drc.rpt) | Electrical, clearance, connectivity and schematic parity checks |

## What changed

The circuit and pin assignments are electrically equivalent to [Rev A](../nami-rev-a/README.md). It still uses the SCT006 20 A : 25 mA clamp, a permanent 5 Ω burden at the head, two ADC ranges, Thread/BLE, 16 MiB flash, and a 3 V regulated supply. No sensing range or battery-life claim has been changed to achieve the smaller outline.

- Most resistors and small capacitors use 0603 packages. The bulk capacitors, larger capacitance values and 22/47 nF C0G filters retain larger packages. Their effective capacitance and exact sourcing still need confirmation.
- U2 is **OPA2333AIDGKR in VSSOP-8**, with the same pinout and amplifier function as the bench SOIC part. [TI package information](https://www.ti.com/lit/gpn/OPA2333).
- SW1 and SW2 use **B3U-1000P** surface-mount buttons. [Manufacturer information](https://components.omron.com/us-en/products/switches/B3U).
- CT and battery headers become two solder pads each. Programming uses a custom ten-pad pogo fixture with the original ARM SWD pin numbering; analog debug uses four pogo pads. These are not sockets or a standard Tag-Connect footprint.
- The radio and analog/power circuits are on the front. Flash, bulk input storage, service contacts and buttons occupy the back. The PCB needs an enclosure cradle and local support under the buttons; there are no mounting holes.
- The same module and flash remain to limit electrical changes. A bare radio SoC or smaller flash package could reduce area further, at the cost of new RF/package engineering and additional validation. C0 is a practical compact layout, not a proven global minimum.

## Copper and assembly plan

| Layer | Role |
|---|---|
| L1 / F.Cu | Radio, analog and power components; short critical routes; ground fill |
| L2 / In1.Cu | Ground reference plane; **no routed signal tracks** |
| L3 / In2.Cu | Limited signal routing |
| L4 / B.Cu | Flash, service and battery-side components; signal routing; ground fill |

The nominal 1.0 mm construction is a mechanical target. Laminate, copper weights and dielectric thicknesses must be agreed with the fabricator before release; no controlled-impedance external RF feed is routed on this carrier. The module contains its antenna/feed. Use a conventional four-layer process, 0.15 mm minimum clearance/track constraint, 0.18 mm default signal tracks, and 0.50/0.25 mm through vias. No blind or buried vias are used. Inspect and agree solder-mask registration/tenting with the fabricator. Assembly requires two-sided reflow and a custom programming/test fixture.

The TPS63900 input/output and switch-node connections were placed and routed explicitly before the remaining local autorouting. LX1 and LX2 each have about 3.62 mm total routed length and **zero vias**. Ground pours are stitched to L2; the input/output capacitor returns and exposed pad have local ground connections. This follows TI's emphasis on short power loops, but does not replace oscilloscope/EMI testing. [TPS63900 layout guidance](https://www.ti.com/lit/ds/symlink/tps63900.pdf).

RF placement uses the north board edge and a **24 × 4 mm copper exclusion on all four layers**, plus the module footprint's local restrictions. The module maker requires no ground beneath the antenna on any layer and recommends placing it at the PCB edge. [Raytac layout guidance, section 2.3](https://www.raytac.com/tw/download/index.php?index_id=24). Metal from a battery, mounting hardware or an outlet box must not occupy the antenna's surrounding volume. The carrier ground area is much smaller than the bench board; range and antenna tuning need measurement in the intended enclosure.

## Connections and packaging

The [Rev A pin table and bring-up sequence](../nami-rev-a/README.md#connectors-and-firmware-assignment) remain applicable, except that J1–J4 now use bare contact pads and U2 has a different package.

| Interface | Compact implementation |
|---|---|
| J1, front southwest | 1 = CT signal, 2 = VMID. Permanent 5 Ω burden stays at the clamp, before the detachable harness. VMID is not GND. |
| J2, back southeast in front-view coordinates | 1 = battery positive, 2 = GND. Single 2.0–3.3 V source; no charger or reverse-polarity protection. |
| J3, back | Ten pads on 1.27 mm pitch, ARM SWD numbering. VTref senses the target rail; do not power through the debug fixture. |
| J4, back | 1 low ADC, 2 high ADC, 3 VMID, 4 GND, 1.27 mm pitch. |
| SW1 / SW2, back | Pair / reset; enclosure must provide access and mechanical support. |

Use the native footprint pad numbers to build the jig. The bottom render is viewed from below and therefore mirrors the front coordinate system. Wire pads require external strain relief and insulated joints; they cannot support the clamp or battery mechanically. Keep fixture contacts accessible before final enclosure assembly. A board-specific fixture can locate against the PCB edges; its tooling is not designed here.

The **CR2450 remains an external candidate**, approximately 24.5 mm diameter by 5 mm thick before its holder. It is already slightly wider than the PCB, and cannot simply be stacked behind the antenna. No integrated 24 × 32 mm device envelope is claimed. The SCT006 is also a separate, roughly 29 × 16.5 × 19 mm clamp. Prefer faceplate-side electronics and a remote clamp in the box; the final antenna location, battery service access and conductor/insulation clearances require enclosure design. [Battery dimensions](https://energy.panasonic.com/dam/master/pdf/en/datasheet/lithium/CR2450_Datasheet_EN.pdf), [CT dimensions](https://www.poweruc.pl/products/split-core-current-transformer-sct006-rated-input-20a).

## Verification and remaining release work

Recorded checks pass with zero ERC violations, zero DRC violations, zero unconnected items and zero schematic/PCB mismatches. Independent checks verify all 59 electrical footprint entries against the schematic manifest, 51 critical pin connections, and identical electrical nets to Rev A. Compact-specific checks verify the outline, substrate target, all-layer antenna exclusion, ground-plane layer and via-free switching paths. These checks establish CAD consistency, not measured product performance.

Before ordering a production run:

1. Audit exact ordered parts against footprints, capacitor derating and assembly tolerances. Finalize the fabricator stackup, panel/rail strategy and fixture. Validate small contact pads and button access against the enclosure.
2. Validate low-current noise, clipping recovery and ±10% RMS performance with the radio and flash active. Repeat the isolated low-voltage bring-up from Rev A.
3. Close the energy budget. Continuous ADC acquisition, the amplifier's roughly 34 µA typical total quiescent current and flash activity still make the one-year coin-cell target uncertain. Verify startup and flash/radio bursts against the regulator's 25 mA input limit and actual battery impedance.
4. Measure RF range in the proposed faceplate/box installation, with the battery and mounting hardware in place. Confirm mechanical insulation, thermal behavior and applicable installation/product requirements before field use.

Firmware, hub software, calibration, enclosure, battery endurance and qualification remain outstanding. No manufacturing release or claim of mains-installation suitability accompanies this layout.

## Reproduce

The committed native CAD is the review result. The scripts overwrite generated files: preserve manual edits before using them. Run commands from the repository root. Use ordinary Python with `sexpdata` for generation and KiCad's bundled Python for `pcbnew` scripts.

1. `NAMI_VARIANT=compact python hardware/tools/generate.py`
2. Run `hardware/tools/compact_board.py` with KiCad Python. This creates local contact footprints, a fresh board, hand-routed power paths and `nami.dsn`.
3. Reuse the matching committed `nami.ses`, or run Freerouting 2.0.1 locally against that DSN. L2 is marked as a power layer in the routing exchange. Changed placement or critical routes require a new session.
4. Run `hardware/tools/compact_finish.py` with KiCad Python to import the session, fill ground, stitch ground regions, and apply `refine_routes.py`. The refinement moves the crystal/load capacitors and selected vias, and replaces the reviewed routing details. Do not apply it a second time to a finished board.
5. Export KiCad XML netlist to `exports/nami-netlist.xml`; run `NAMI_VARIANT=compact ... hardware/tools/sync_board.py` with KiCad Python.
6. Run KiCad ERC and PCB DRC with `--schematic-parity --exit-code-violations`; run `NAMI_VARIANT=compact python hardware/tools/verify.py` and `hardware/tools/compact_verify.py` with KiCad Python. Regenerate review PDF, renders and STEP after changes.

Local connector footprints live in `Nami.pretty` and `fp-lib-table`. Other symbols/footprints use the installed KiCad libraries. `NAMI_VARIANT` defaults to the original bench design; selecting compact does not overwrite it.

### Layout review, 2026-09-26

The analog sheet now draws the midpoint voltage follower, input network, non-inverting gain stage, feedback resistors and ADC filters with direct wires. Decoupling remains separate. This presentation is shared with the bench design and preserves the original electrical nets.

The reviewed routing changes align C13/C14 with Y1, remove the module supply loop/spur, straighten the CT return pad exits, replace pair/MOSI jogs, improve rear supply and flash pad exits, and move the battery split into C1 instead of an external right-angle T. The clock via and two ground stitching vias move to maintain clearance. The 24 × 32 mm outline, power-loop routes, four-layer construction and component values remain unchanged. See the before/after PDF above.
