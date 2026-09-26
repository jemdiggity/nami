# Nami outlet current monitor — prototype design v0.2

> Historical design exploration. The [PRD](../PRD.md) is authoritative where decisions differ.

Status: engineering proposal, 2026-09-26. Component candidates and calculated circuit values are provided for a bench prototype. No schematic capture, simulation, PCB layout, physical testing, or installation approval has been completed.

Product priorities were reconsidered against inferred user stories in [USER-STORIES.md](USER-STORIES.md). That review is the current product baseline. The analog circuit below remains a characterization experiment, not a selected production implementation. The key changes are serviceable faceplate packaging, a 12-month battery-service target, 30-day retention and a maximum 10-second uncommitted tail.

## Defaults

| Requirement | Default |
|---|---|
| Application | One 120 V, 60 Hz, 15/20 A receptacle load |
| Coupling | Split-core current transformer around one insulated conductor; no galvanic connection |
| Measurement | True RMS over every complete, consecutive second |
| Accurate range | 0.1–20 A RMS; target ±10% of reading after calibration |
| Below 0.1 A | Report estimate with below-range flag; do not claim ±10% |
| Waveform envelope | AC, crest factor up to 3; distorted-load accuracy requires validation |
| DC | Not measured; asymmetric currents that bias/saturate the core must be tested |
| Storage | At least 30 days of one-second readings, circular overwrite; 16 MiB capacity budget |
| Wireless | BLE, connectable advertising every 2 seconds; authenticated history download |
| Power | Accessible replaceable battery; CR2450 candidate, larger cell permitted by enclosure |
| Battery goal | 12 months, subject to measured consumption; old six-month allocation below is a bench comparison only |
| Environment | Indoor, 0–50 °C design target |
| Physical arrangement | CT inside box; serviceable faceplate electronics preferred, subject to mechanical/electrical validation |

An incoming hot/neutral feed may also serve downstream outlets. Installation must identify a conductor carrying only the intended receptacle load. Both hot and neutral through the same CT cancel. A shared neutral is unsuitable for isolating one load. A CT cannot distinguish an unplugged sensor from a truly idle outlet.

## Architecture and candidate parts

```text
Insulated load conductor
        │ magnetic coupling only
Split-core CT + permanently attached burden and secondary clamp
        │ twisted pair
Input protection → low-range / high-range analog paths → nRF52832 SAADC
                                                         ├─ BLE
                                                         ├─ SPI flash
                                                         └─ 32.768 kHz crystal
CR2450 → pulse reservoir → battery rail → electronics
```

| Function | Prototype selection | Qualification needed |
|---|---|---|
| CT | SCT006, 20 A / 25 mA variant, candidate | Confirm exact ordered ratio, allowed burden, closure repeatability, low-current error, bandwidth, insulation, dimensions |
| MCU/radio | nRF52832 module with exposed analog pins and antenna | Select exact module after fit check; use its antenna keepout and reference power circuit |
| Analog | OPA2333 dual op amp | One midpoint buffer and one gain stage; check settling, noise and overload recovery |
| Memory | 16 MiB low-power flash, exact part to be selected | Replaces the 2 MiB MX25R1635F candidate; verify voltage, write energy and partial-page limits |
| Battery | Panasonic CR2450, holder with retained cell | Pulse sag, contact reliability and safe battery access |
| Timebase | 32.768 kHz crystal, nominal 20 ppm target | Load capacitance and temperature drift |

The SCT006 supplier lists a 50 Hz–1 kHz frequency range, but that is not a flatness guarantee or evidence of ±10% at 0.1 A. Treat this inexpensive part as an experiment; replace it if validation fails. Its published dielectric tests do not establish suitability for permanent installation in a North American outlet box. [CT source](https://www.poweruc.pl/products/split-core-current-transformer-sct006-rated-input-20a)

The MCU supports differential ADC inputs, programmable gain and DMA. Use it first to establish waveform accuracy. Continuous ADC operation and clocks may exceed the battery budget; a low-power external ADC or metering front end remains a possible revision. [Nordic SAADC documentation](https://docs.nordicsemi.com/r/bundle/ps_nrf52832/page/saadc.html)

The OPA2333 operates from 1.8 V and is specified at typically 17 µA per amplifier. [TI](https://www.ti.com/product/OPA2333) The original MX25R family candidate supports a wide supply range appropriate to a declining coin-cell voltage, but the replacement storage device must be verified independently. [Macronix](https://www.macronix.com/en-us/products/NOR-Flash/Pages/Ultra-Low-Power-Flash.aspx)

## Analog circuit starting values

For the candidate 20 A : 25 mA CT, the nominal turns ratio is 800:1. Fit an 8.2 Ω, 0.1%, low-temperature-coefficient burden permanently across its secondary, physically at the sensing head so unplugging the cable does not remove the burden. Fit secondary overvoltage protection there too. Protection voltage, pulse rating and leakage require final circuit review.

Calculated transfer, before magnetizing-current and winding errors:

`Vburden = Iprimary × 8.2 / 800 = 10.25 mV per ampere`

| Primary RMS current | Burden RMS voltage |
|---|---:|
| 0.1 A | 1.025 mV |
| 1 A | 10.25 mV |
| 20 A | 205 mV |

At 20 A RMS and crest factor 3 the expected peak burden voltage is 615 mV. Burden dissipation at 20 A is approximately 5.1 mW. These calculations do not prove the CT will avoid saturation; winding resistance and core characteristics also matter.

Generate Vmid = Vbattery/2 using two 1 MΩ resistors, a bypass capacitor and one op amp as a buffer. Reference one CT secondary terminal to Vmid. At a 2.0 V battery rail the full-load waveform nominally spans 0.385–1.615 V, leaving useful input headroom.

Use two independently calibrated signal paths:

- Wide range: burden signal measured differentially against Vmid, nominal ADC gain 1/2, ±1.2 V differential range.
- Sensitive range: second op amp, non-inverting gain 16 relative to Vmid, using Rf = 150 kΩ and Rg = 10 kΩ (0.1%); measure against Vmid. At 0.1 A this produces 16.4 mV RMS. Select this path only when the whole window is unclipped and in the characterized overlap region.

Start with 12-bit conversions and internal ADC reference. Sample both channels at 8,192 samples/second each, using hardware triggering and DMA. At this resolution the sensitive channel has roughly 56 RMS counts at 0.1 A with ±0.6 V range: useful resolution, but accuracy still depends on CT error, noise, ADC linearity and calibration. Log from the wide path when the sensitive path saturates, and allow characterized recovery time before reusing the sensitive path.

Provide footprints for analog anti-alias filtering and input protection on both paths. Final filter topology and values are deliberately not frozen: select and simulate against the measured CT response and ADC acquisition loading. The full chain must preserve sufficient harmonic energy for representative charger/dimmer waveforms. Increasing sample rate cannot recover harmonics lost in the CT. Do not claim unrestricted true-RMS accuracy from a 1 kHz sensor.

Calibration: electronic zero/offset plus gain checks at 0.1, 0.5, 2, 10 and 20 A. Use a characterized reference with uncertainty comfortably below the 10% requirement. Repeat after opening/reclosing the clamp and over temperature. Store separate gain coefficients for each path. Do not simply subtract each one-second mean if doing so would hide clipping or asymmetric-load problems.

## Firmware, persistence and BLE

Compute the RMS of calibrated instantaneous samples over full one-second windows. Maintain sampling during radio and flash activity; double-buffer DMA. Any incomplete or clipped window receives an invalid/overrange flag. Never silently substitute zero or duplicate the last reading. ADC calibration interruptions must be flagged if they create a sampling gap.

Store current as unsigned milliamperes in 16 bits; reserve codes above the operating range for invalid, below-range and overrange conditions. A 1 mA storage step is 1% at the bottom of the accurate range, not a claim of 1 mA measurement accuracy.

Budget 16 MiB for at least 30 days: four bytes per second uses 10,368,000 bytes, leaving space for metadata and spare sectors. Exact record format is open. Preserve per-reading validity and chronological ordering. Support summaries for quick browsing while retaining all one-second records during the retention interval.

Commit at least every 10 seconds; abrupt battery removal may lose at most that uncommitted tail. The old 120-second RAM-only page format is superseded. Select a journal, supported partial-page writes or a nonvolatile staging buffer after validating write constraints and energy. Recover with sequence numbers and integrity checks. Rotate metadata with data; do not erase a fixed sector every second. Pre-erase spare sectors without interrupting sampling, and stop writes safely at low battery. A CRC identifies damaged records but does not make an interrupted write atomic.

Keep monotonic time on the low-frequency crystal. BLE supplies UTC; retain a time-valid flag and a new session identifier after reset. A nominal 20 ppm oscillator corresponds to approximately 1.7 seconds/day before temperature effects. Preserve time-adjustment information rather than changing historical ordering.

BLE services: current/status, battery, device information, time sync, and resumable history retrieval by sequence number. Default advertising interval 2 seconds; current notifications 1/second only while subscribed. Transfer history in batches. Initial physical pairing action, bonding and encrypted access; do not broadcast detailed current history in advertisements. No cloud dependency.

## Power and mechanics

Use the battery directly for the first prototype, with local decoupling and a pulse reservoir. All selected components must operate through the chosen approximately 2.0–3.2 V battery envelope; verify the exact module supply limits. Begin reservoir sizing around 100 µF effective capacitance, then measure radio/program/erase sag and leakage. For illustration, 6 mA for 3 ms discharges 100 µF by 0.18 V if the capacitor supplies the entire pulse. Longer flash operations require separate checking. Avoid a continuously lit LED.

The CR2450 has nominal 620 mAh capacity; that capacity is conditional on load, temperature and cutoff. [Panasonic datasheet](https://energy.panasonic.com/dam/master/pdf/en/datasheet/lithium/CR2450_Datasheet_EN.pdf)

Previous engineering allocation for a six-month bench target, expressed as average battery current. This does not meet the revised 12-month product target:

| Subsystem | Target allocation, not measured |
|---|---:|
| Analog amplifiers and bias | 36 µA |
| ADC, clocks and RMS processing | 30 µA |
| BLE advertising and occasional download | 15 µA |
| Flash, timekeeping, leakage and margin | 19 µA |
| Total | 100 µA |

Assuming only 70% of nominal capacity is usable gives 434 mAh: about 181 days at 100 µA, 90 days at 200 µA, or 36 days at 500 µA. This is a sensitivity calculation, not a prediction. The MCU ADC/clock allocation is particularly aggressive and must be measured early. If it fails, change the acquisition architecture or battery; do not shorten the measurement window without explicitly changing the requirement.

At the same 70% capacity assumption, 12 months requires about 49.5 µA average battery draw. The analog allocation consumes most of it. Reconsider the front end and battery size before committing to a production MCU or amplifier. See the user-story review for the revised decision order.

Use a short twisted pair, initially about 50–100 mm, between sensing head and electronics. The original electronics PCB target of 30 × 25 mm excluding the CT is subordinate to battery access, plug clearance and antenna placement. The CR2450 alone is 24.5 mm across and 5 mm thick before its holder. Allow more space for an insulated enclosure and antenna keepout.

Prefer a faceplate-integrated enclosure for battery and radio, with a designed insulated sensor-lead passage and battery access separated from mains wiring. Test with the outlet and cover installed. Entirely hidden electronics are an alternative requiring separate maintenance and RF justification. Default RF acceptance: reliable connection and history download at 3 m in the representative installed geometry. No claim of universal fit in existing boxes.

## Energy-harvesting experiment

Keep the measurement CT burden fixed. Evaluate a separate harvesting CT into a protected rectifier, storage capacitor and power manager. TI's [TIDA-01385](https://www.ti.com/tool/TIDA-01385) demonstrates the architecture; it does not establish a usable threshold for this miniature device.

Measure net delivered power and cold-start time at 0.1, 0.5, 1, 2, 5, 10 and 20 A, plus shutdown at zero current. Compare harvested daily energy with measured consumption and realistic outlet duty cycle. Retain the battery at zero/low current; block all charging into the primary coin cell. Revisit a shared-core design only after measurement/harvesting interactions are quantified. There is no batteryless promise or minimum operating-current claim at this stage.

## Validation and next build gate

1. Bench sensing: isolated low-voltage 60 Hz source, controlled load and reference instrument. Multiple primary turns can generate equivalent ampere-turns for initial characterization; confirm final behavior with one conductor pass.
2. Accuracy: current points above, repeated clamp closure, nearby loaded conductors, temperature and battery extremes. Include resistive, motor, charger, dimmer and intermittent loads; document crest factor and harmonic limitations. Pass: every supported test within ±10% of reference, with no missed windows.
3. Power: measure complete hardware with debugger disconnected, including advertising, history download, erase/program, ADC calibration, and worst-case pulse sag. Exercise applicable MCU errata workarounds; Nordic documents an [SAADC residual-current anomaly](https://docs.nordicsemi.com/r/bundle/errata_nrf52832_rev3/page/err/nrf52832/rev3/latest/anomaly_832_241.html).
4. Persistence: fill/wrap 30 days; remove power during writes and erase; recover without misordered or fabricated records. Verify the revised 10-second maximum uncommitted tail and resumable history transfer.
5. Mechanical/RF: representative plastic and metal boxes, standard and bulky GFCI receptacles, cover installed, antenna orientations and battery servicing.
6. Installation design: qualified review of insulation, enclosure, CT protection, fault behavior, thermal limits and wiring space before any permanent mains installation. Early prototypes stay on an isolated low-voltage bench; mains installation is de-energized work for a qualified person.

First validate installation scope and serviceable enclosure geometry, then candidate CT performance and full-system acquisition/persistence energy. Proceed to production schematic capture after those checks support the user stories and revised runtime. The bench circuit can be assembled to characterize sensing, but a fabrication-ready product PCB would freeze unresolved packaging and power choices.
