# Nami — user stories and revised design decisions

> Historical design exploration. The [PRD](../PRD.md) is authoritative where decisions differ.

2026-09-26. These are inferred stories and proposed defaults, not findings from user interviews. The original requirements remain: no electrical connection to the monitored conductor, 10% current accuracy over a declared range, one stored measurement each second, and BLE. This review supersedes v0.1 product defaults where stated; its circuit remains a bench experiment.

## Product purpose

Help someone understand when an appliance runs, how much current it draws, and what happened while they were away, without replacing the outlet or inserting a plug-through adapter. Default to a long-lived installed monitor with phone access. Reliable remote alerts are an optional gateway use case. Revenue metering, power-cost reporting, protection, and millisecond fault diagnosis are outside the first version.

## Stories, choices and acceptance criteria

| Story | Consequence for the design | Proposed acceptance criterion |
|---|---|---|
| As an installer, I want to know exactly what this sensor measures. | Verify the load-specific conductor; name the monitored scope in setup. A feed-through outlet may require wiring changes to isolate its load, conflicting with a clamp-only retrofit. | With a known test load, verify both intended receptacle positions and downstream outlets. Reject unsupported arrangements or explicitly label combined loads. Never silently call branch current outlet current. |
| As an owner, I want the outlet to look normal and accept my existing plugs. | Compare enclosure fit with plug clearance, rather than minimizing PCB area alone. Prefer a modest faceplate enclosure with only the insulated CT and lead inside the box. | Representative plugs and wall adapters fit; battery compartment is accessible without exposing mains terminals; installed RF and electrical enclosure design pass review. |
| As an owner, I do not want routine maintenance to require opening an electrical box. | Accessible battery becomes the preferred architecture. Target at least 12 months between replacements; six months is only a prototype benchmark. | Demonstrate runtime from measured duty-cycle energy and discharge tests; change a battery without removing the receptacle or opening the mains compartment. If geometry cannot support this, revisit packaging. |
| As a user, I want to see whether an appliance is running right now. | One-second live values, last-update time, and optional threshold/hysteresis-based activity state. Preserve numeric measurements. | After connection, a new valid value arrives within two seconds. Stale, below-range and invalid measurements are visibly different from zero. Threshold state has no universal appliance classification claim. |
| As a user, I want to distinguish running from standby. | Accuracy and state detection are different requirements. Keep 0.1–20 A at ±10%; characterize lower currents separately. | Publish the verified detection floor and false-transition behavior. Below 0.1 A show below-range/estimate, not an asserted accurate zero. Measuring small standby current to ±10% would require a new range decision. |
| As a user, I want to review what happened while my phone was absent. | Logging is autonomous, and does not rely on a background phone connection. Increase local retention to 30 days. | All one-second records remain retrievable after 30 days without BLE. The app identifies overwritten history and actual measurement gaps. |
| As a user investigating a failure, I want the last moments before it stopped. | The old two-minute RAM-only tail is too large. Target at most 10 seconds of uncommitted data and preserve reset/brownout events. | Random power cuts during flash activity produce no fabricated records; the lost valid tail is no more than 10 seconds. This changes flash energy and format requirements. |
| As a user, I want an alert when something stops while I am away. | A nearby, powered BLE-to-network gateway is required for dependable remote operation. The phone-only product offers nearby access and retrospective history. | With a gateway, distinguish inactivity from sensor unreachable and gateway/network offline. Alert latency and availability are separate service specifications; do not market this as a safety alarm. |
| As an owner, I want the device to remain reachable when the appliance is off. | Retain battery-backed operation. Harvesting may extend life but must not determine basic availability. | Measure and communicate during extended zero-current periods. Harvesting claims include the required load/duty cycle and zero-load endurance. |
| As an owner of several monitors, I want to identify, pair and transfer the right one. | Visible device identifier/QR, accessible pairing control, short identification indication and an ownership-reset flow. | Setup works after the cover is installed; private history requires authenticated access; ownership reset removes bonds and old history. |

## Reconsidered tradeoffs

### Packaging before miniaturization

Prefer a serviceable faceplate enclosure containing the radio and battery, with a small split-core CT in the electrical box. This is an architectural proposal requiring mechanical and electrical validation, not an assumption that a loose cable can be routed through an arbitrary faceplate. Provide a designed insulated passage and separate battery access from mains wiring. Antenna placement must be tested with the metal box and receptacle installed.

The concession is visible bulk and a replacement cover. A fully hidden unit remains an alternative when aesthetics dominate, but it needs much longer maintenance intervals and verified RF performance. Do not select a six-month hidden battery merely because the PCB fits. A plug-through meter would simplify installation but conflicts with the intended existing-outlet form and is not the selected approach.

### Availability before batteryless operation

A stopped appliance can be the most interesting event. Making communication depend on its current would undermine that story. Select battery operation as the baseline and pursue harvesting only if net lifetime benefit outweighs a larger clamp, additional circuitry and installation effort. TI's [CT harvesting reference design](https://www.ti.com/tool/TIDA-01385) also uses backup power; its performance is not evidence for this smaller sensor's threshold.

Set a 12-month service target for the accessible battery. At 70% assumed usable capacity from a nominal 620 mAh CR2450, this requires average draw no greater than approximately 49.5 µA. The old 36 µA analog allocation alone consumes most of that budget. Therefore the OPA2333 + continuously sampled nRF52832 arrangement is a characterization platform, not a selected production architecture. Evaluate a lower-power acquisition path and a larger battery within the chosen enclosure in parallel as design alternatives, without weakening full-second coverage. The capacity assumption is a planning calculation, not a validated derating model. [Panasonic battery specification](https://energy.panasonic.com/dam/master/pdf/en/datasheet/lithium/CR2450_Datasheet_EN.pdf)

If hidden installation becomes a priority, use a multi-year maintenance target. For context, three years from the same assumed capacity permits only about 16.5 µA average draw. That would require a substantial redesign or dependable harvested energy plus enough reserve for the defined idle period.

### Faithful records before frequent radio traffic

Keep continuous measurement and one-second RMS records. Do not introduce short sampling snapshots as an invisible power optimization: an intermittent load may be exactly what the owner wants to investigate. BLE can sleep between advertisements and transfer records in batches. Logging cadence and radio cadence need not match.

Thirty days replaces seven days because it supports travel and occasional use without mandatory weekly synchronization. Budget 16 MiB of low-power nonvolatile storage: four bytes/second is 10.37 MB over 30 days, with room for timestamps, integrity metadata and spare sectors. This is a capacity budget, not a finalized record layout or selected part. Re-select the flash and characterize its energy. Use sequence-indexed resumable transfers and retrieve recent summaries before requesting a full month. Summaries supplement one-second records; they do not replace them during the retention period.

Reduce the uncommitted tail to 10 seconds. Choose between supported partial-page writes, a journal or a nonvolatile staging buffer after evaluating power and flash constraints. A 256-byte page written for every second wastes capacity and energy. The exact persistence format must demonstrate the retention and power-cut criteria together.

### Trustworthy meaning before extra precision

Keep 0.1–20 A and ±10% of reading as the proposed accurate range. At 120 V, 0.1 A represents about 12 VA; this is not a 12 W threshold, and many standby loads are below it. Do not widen the specification to 0.01 A just to support a UI label until core accuracy, interference and power have been measured.

Report RMS current, not watts, energy cost or power factor. No voltage/phase measurement exists in this architecture. Distinguish a one-second RMS window from the average of cycle-RMS magnitudes; the former remains the default. One-second data can describe cycles and activity but does not diagnose millisecond inrush events. Overrange flags are useful; waveform capture would be a separate feature with its own storage and bandwidth budget.

Preserve honest status: valid, below accurate range, overrange/clipped, incomplete window, sensor unreachable, clock unsynchronized and history overwritten. A zero-current CT reading alone cannot prove the clamp is installed or connected. Commission with a known load; do not invent sensor-health certainty from silence.

## Revised baseline

| Decision | Baseline after review |
|---|---|
| Primary story | Installed appliance activity/current history, accessed nearby by phone |
| Installation | Qualified installation, supported load-specific conductor required |
| Enclosure | Serviceable faceplate electronics preferred; CT inside box |
| Sensing | Split-core CT; exact part remains unqualified |
| Measurement | Full-second RMS, ±10% target from 0.1–20 A |
| Persistence | 30 days, target at most 10 seconds lost on abrupt battery removal |
| Storage | 16 MiB capacity budget, component/format to be selected |
| Power | Battery-backed; 12-month accessible service target |
| Battery | CR2450 candidate, larger cell allowed if packaging warrants it |
| Harvesting | Optional lifetime extension, no dependence for zero-load operation |
| BLE | Nearby live view and resumable history; gateway for remote alerts |
| Calibration | Device calibration during manufacture/prototype characterization; user only verifies installation with a known load |

## What to validate first

1. Installation and enclosure mockups: can a clamp-only retrofit isolate the intended load, and can a serviceable cover fit representative outlets/plugs? A precise sensor in an unusable package does not satisfy the story.
2. Core behavior: low-current accuracy, repeated closure, nearby conductors and distorted appliance loads, with no user calibration required after installation.
3. Power architecture: full-window acquisition, normal advertising and 10-second persistence at the 12-month energy target. Compare a different front end and larger accessible battery before adding harvesting complexity.
4. Complete user journey: commission with known load, disconnect phone, reconnect after missing days, resume interrupted download, remove battery unexpectedly, and distinguish missing data from actual zero current.
5. Harvesting: add only after the baseline works, and assess net benefit against representative appliance duty cycles.

No physical validation has occurred. This revision changes product priorities and acceptance criteria; it does not claim the new runtime, enclosure, storage implementation or accuracy has been achieved.
