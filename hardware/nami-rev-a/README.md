# Nami Rev A0 — bench hardware

An editable KiCad 10 design for evaluating the SCT006 sensing chain and Thread/BLE operation. **This is an unreleased bench prototype, not an outlet-installation or fabrication release.** The board is 95 × 75 mm, deliberately larger than the eventual device. No physical hardware, firmware, battery-life test or enclosure validation has been completed.

Open **`nami.kicad_pro`** in KiCad. The five-sheet schematic is `nami.kicad_sch`; the routed two-layer PCB is `nami.kicad_pcb`. The parts are native editable KiCad symbols and footprints, not an image imported into the editor.

## Files

| File | Purpose |
|---|---|
| `power.kicad_sch` | Battery/bench input, TPS63900 3.0 V regulator and removable current links |
| `analog.kicad_sch` | Bias buffer, gain stage, protection, filters and test points |
| `digital.kicad_sch` | Thread/BLE module, clock, flash, SWD and controls |
| `harness.kicad_sch` | Permanently burdened off-board CT assembly |
| `exports/nami-schematic.pdf` | Five-sheet review copy |
| `exports/nami-board.png` | Rendered board overview |
| `exports/bom.csv` | Board BOM; generic passives specify values/packages, not procurement-approved MPNs |
| `exports/nami-netlist.xml` | Netlist exported by KiCad, checked independently |
| `verification/erc.rpt` | KiCad electrical-rule results |
| `verification/drc.rpt` | PCB rules, unrouted-net and schematic-parity results |
| `verification/connectivity-and-calculations.json` | Critical pin checks and approximate signal calculations |
| `nami.ses` | Local autorouter session, retained for reproducibility |

The clamp, two harness resistors, wiring, battery/holder, programmer and hub are external assemblies; see the table below. Test-point BOM rows are bare PCB pads, not purchased components.

## Architecture and selected evaluation parts

- SCT006 **20 A : 25 mA** split-core CT, fitted with a **permanent 5.00 Ω burden at the sensing head**. The main board must not carry a second parallel burden.
- TPS63900DSKR regulator, 3.0 V output with SEL grounded and CFG3 = 13.3 kΩ. CFG2 = 1.87 kΩ selects 25 mA input current limit. CFG1 = 0 Ω selects an unused 1.8 V alternate output; SEL is not software-controlled. Verify startup with the intended battery and effective capacitance.
- OPA2333AID dual op amp: midpoint buffer and gain 31.9 stage. This is a characterization choice; its approximately 34 µA typical combined quiescent draw already uses much of the one-year coin-cell budget.
- Raytac MDBT50Q-1MV2 **nRF52840** module. It supports the intended Thread/BLE firmware, but is not preprogrammed for Nami. This documented module is used instead of a bare nRF54L15 on Rev A; a later power-optimized revision may change it.
- W25Q128JVSIQ, 128 Mbit / 16 MiB SPI flash. The 3.0 V regulated rail satisfies its 2.7 V minimum; firmware must stop writes before the rail leaves specification. No one-year flash energy budget is claimed.
- External 32.768 kHz, CL=7 pF crystal. The initial 9 pF load capacitors assume about 2.5 pF stray capacitance; verify clock startup and frequency on the real layout.

The module normal-voltage reference configuration ties VDD, VDDH and DCCH together. USB is unused: VBUS is grounded and D+/D− are no-connects. The KiCad symbol types DCCH as a power output; no redundant power flag is added on that rail. REG0 must remain disabled and REG1 DC/DC should be enabled in firmware. The module already contains its high-frequency crystal and REG1 inductor.

## Signal ranges and limitations

With an ideal 800:1 CT and 5 Ω burden:

`Vsecondary = 0.00625 × Iprimary` and `Vhigh − Vmid = 31.9 × (Vsense − Vmid)`.

| Condition | Calculated signal, before losses/filtering |
|---|---:|
| 0.1 A RMS at burden | 0.625 mV RMS |
| 0.1 A RMS at high-gain output | 19.94 mV RMS |
| 20 A RMS at burden | 125 mV RMS |
| 20 A, crest factor 3 | 375 mV peak at burden |
| 0.8 A, crest factor 3, high gain | 478.5 mV peak |

Both ADC channels are differential against VMID with a nominal ±0.6 V range. Use the high path only for complete windows that remain within a characterized range; initially aim below 0.8 A at crest factor 3. At higher currents the high path deliberately saturates. Use the low path and allow measured amplifier recovery time before returning to high gain. Software must inspect both raw clipping and analog overload behavior.

Start at **32,768 samples/s per range**, 12-bit differential, 10 µs acquisition, hardware triggering and DMA. This rate is for characterization, not an optimized production power setting. The two ADC conversions occur sequentially; calculate each path's RMS independently rather than splicing mismatched samples.

R8/C5 and the two output RC networks provide input filtering. R8 also loads the low-path RC, so the low filter is not simply `R14 × C8`. The verification script calculates the coupled small-signal response. It is only an approximate RC/single-pole-amplifier calculation, not SPICE validation. CT harmonic response, alias rejection, noise, offset, nonlinearity, gain error and saturation remain bench measurements. There is **no demonstrated ±10% accuracy or one-year battery life** yet.

## Connectors and firmware assignment

| Connection | Pins / mapping |
|---|---|
| J1 CT | 1 = CT positive/signal; 2 = VMID/CT return. Return is not ground. |
| J2 power | 1 = battery positive; 2 = GND. One source only, 2.0–3.3 V, correct polarity. No charger or reverse-polarity protection is fitted. |
| J3 SWD | Standard 10-pin 1.27 mm: 1 VTref, 2 SWDIO, 3/5/9 ground, 4 SWCLK, 10 reset; 6/7/8 unused. Debugger must sense VTref, not supply it. |
| J4 analog debug | 1 low ADC, 2 high ADC, 3 VMID, 4 ground |
| P0.02 / AIN0 | ADC_LOW |
| P0.03 / AIN1 | ADC_HIGH |
| P0.04 / AIN2 | VMID, negative input for both differential channels |
| P0.05 / AIN3 | Battery monitor: VBAT/3, separate single-ended ADC configuration |
| P0.00 / P0.01 | External low-frequency crystal |
| P0.13 / P0.14 | Flash clock / chip select |
| P0.15 / P0.16 | Flash MOSI / MISO |
| P0.17 | Pair button, active low |
| P0.18 | Reset: configure the nRF52840 UICR reset function |
| P0.19 | LED, active high; normally off |

R1 permits whole-system current measurement. R5, R6 and R7 isolate module, analog and flash rails for measurement. Removing a link is a diagnostic action: other signal pins can back-power an unpowered subsystem. Do not infer its leakage by removing its supply while other pins are driven. SWD/debugger connection also changes the power measurement.

The battery divider is 2 MΩ / 1 MΩ with a 100 nF reservoir. Its high source resistance requires deliberate ADC acquisition timing and verification. Battery checks and offset calibration must not silently create missing current samples. The initial divider alone draws about 1 µA at 3 V.

## External assembly BOM

| Item | Quantity | Specification |
|---|---:|---|
| CT | 1 | SCT006, explicitly 20 A : 25 mA; not another SCT006 variant |
| R101, R102 | 2 | 10 Ω, 0.1%, suitable low-tempco resistor; parallel to make 5 Ω |
| CT harness | 1 | Short twisted pair, insulated solder joints and strain relief; burden stays with clamp |
| Battery and holder | 1 | CR2450 candidate; external holder for bench characterization |
| Power lead | 1 | Polarized/clearly marked lead to J2 |
| Debug probe | 1 | 3 V compatible SWD, external target-power sense |
| Hub | 1 | Powered host plus Thread radio/border router and eventual Nami service |

`J101` on the harness drawing represents permanent solder joints. Solder both burden resistors directly at the sensing-head secondary connection, upstream of any detachable lead. Verify the ordered CT's internal secondary protection rather than assuming it from a product-family photo. Bench-check burden resistance before clamping a current-carrying test wire.

## Bring-up sequence

1. Inspect assembly orientation and power-to-ground resistance. Verify the two parallel burden resistors measure approximately 5 Ω **before attaching the CT winding**. After attachment the winding's DC resistance is in parallel, so an ordinary ohmmeter across the completed assembly will not necessarily read 5 Ω. Check continuity and the permanent solder connections separately.
2. Start with a current-limited 3.0 V bench source at J2. No coin cell and no primary current initially. Check VREG approximately 3.0 V and VMID approximately 1.5 V; check regulator startup, ripple and heating.
3. Connect SWD with external target-power sensing. Read the MCU ID, program minimal diagnostics, verify reset and low-frequency crystal. Then read flash JEDEC ID and exercise erase/program/read.
4. On an **isolated low-voltage AC test loop**, compare the burden and amplifier waveforms with a calibrated reference. Sweep current, especially 0.1 A, and verify the high path's overload recovery. An oscilloscope ground lead connects to board GND, not VMID.
5. Exercise complete one-second acquisition during flash activity and radio transmissions. Verify alias/noise sensitivity, clipping flags and absence of unnoticed gaps.
6. Measure subsystem and total energy with the debugger disconnected. Test radio/flash pulses on the intended battery at low voltage and temperature, including 25 mA regulator input limiting. Do not equate regulator input-current limit with acceptable coin-cell pulse behavior.
7. Validate Thread connection, commissioning, lost-hub backoff and backfill once firmware/hub software exists. Repeat RF testing in the eventual enclosure; this open bench board cannot establish in-box range.

## Review status and remaining work

- Native schematics, board, BOM, exported netlist and render are provided.
- KiCad ERC and PCB DRC including schematic parity are recorded in `verification/`.
- Independent checks compare the exported pin connectivity against the intended CT, amplifier, supply, module, flash and debug connections.
- Routing used a local Freerouting 2.0.1 session, then explicit module ground connections and copper pours. No cloud autorouting service was used. Autorouting and a clean DRC do not validate switching-loop EMI, RF performance or analog noise.
- Final analog/power layout review, actual passive sourcing/ratings, footprint-to-ordered-part audit, firmware, calibration, cell endurance, enclosure and installation review remain required before a fabrication/field release. No Gerbers are issued as a manufacturing release.

## Sources and reproducibility

- [SCT006 specifications](https://www.poweruc.pl/products/split-core-current-transformer-sct006-rated-input-20a): ratio and 5 Ω burden, dimensions and frequency envelope.
- [TPS63900](https://www.ti.com/lit/ds/symlink/tps63900.pdf): resistor configuration, layout and supply requirements.
- [OPA2333](https://www.ti.com/product/OPA2333): amplifier operating envelope.
- [Raytac module specification](https://www.raytac.com/tw/download/index.php?index_id=24): normal-voltage and USB-disabled wiring; also reviewed manufacturer version K distributed by SparkFun.
- [Winbond W25Q128JV](https://www.winbond.com/hq/support/documentation/?__locale=en&category=%2F.categories%2Fresources%2Fdatasheet%2F&family=%2Fproduct%2Fcode-storage-flash%2Fserial-nor-flash%2Findex.html&pno=W25Q128JV): memory family documentation.

The committed CAD is authoritative for this revision. The scripts under `../tools/` reproduce it; rerunning `generate.py` overwrites the schematic and project settings, and `place_board.py` overwrites the PCB with an unrouted board. Do not rerun them over manual edits without committing/backing up first.

`generate.py` requires Python plus `sexpdata`; the board scripts require KiCad's bundled Python with `pcbnew` and `wx`. Set `KICAD_SYMBOL_DIR` and `KICAD_FOOTPRINT_DIR` on other systems. Sequence: generate schematic, export XML netlist with KiCad CLI, place board, route DSN locally (or reuse the matching committed `nami.ses`), finish board, synchronize metadata, run ERC/DRC and `verify.py`. Changing placement invalidates the old routing session. `finish_board.py` expects a fresh unrouted board and imports the session itself.
