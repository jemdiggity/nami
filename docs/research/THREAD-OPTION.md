# Nami Thread option — recommended for a hub-based product

> Historical design exploration. The [PRD](../PRD.md) is authoritative where decisions differ.

2026-09-26. This is an architectural recommendation under discussion, not a committed replacement of the BLE baseline. It follows the [user-story review](USER-STORIES.md).

## Recommendation

For permanent installation, remote activity monitoring and several outlets, prefer a Thread Sleepy End Device with a powered hub. Retain BLE for commissioning and optionally local diagnostics. For a single monitor used only near a phone, BLE remains simpler. Do not assume Thread is inherently lower-power than BLE: measure complete acquisition, polling, reporting, reattachment and update behavior.

The hub has two separate responsibilities that may share a physical enclosure:

1. Thread border router: routes traffic between the Thread mesh and the home IP network.
2. Application service/controller: understands measurements, stores history, runs rules, serves the UI, and provides any remote access.

A generic border router does not automatically provide the second function. Thread transports application traffic; it does not define the current-monitoring application. [OpenThread roles](https://openthread.io/guides/thread-primer/node-roles-and-types)

```text
CT → measurement/logging MCU → Thread sleepy end device
                                  ↕
                       Powered Thread parent/router
                                  ↕
                           Thread border router
                                  ↕
                     Local history / rules / application
                                  ↕
                           Phone / remote access
```

The parent and border router can be the same unit. Battery monitors do not relay each other's packets; coverage expansion needs powered Thread routers. Mesh does not remove the need to test an antenna near/in a metal outlet box. [Nordic device roles](https://nrfconnectdocs.nordicsemi.com/ncs/latest/nrf/protocols/thread/device_types.html)

## Defaults to test

- Acquire and store every full second, unchanged.
- Upload all readings in 30-second batches in normal operation, with timestamps and sequence numbers. Batch size is not a promise of a single radio packet.
- Send an application event promptly after detecting a meaningful state change, with hysteresis and rate limiting. A locally generated event need not wait for the next inbound poll.
- Use a bounded live-view session to report once per second, then automatically return to batching.
- Test a roughly 5-second idle inbound poll interval for a custom Thread application; this trades command latency for power. Matter configurations need their own supported timing and controller-compatibility review.
- Retain the proposed 30-day local log initially. The hub supplies long-term history; the local log covers hub outages. Backfill with rate limiting and acknowledgments when it returns.
- Back off discovery/rejoin attempts during a hub outage; avoid turning a missing hub into a battery-drain loop.
- Show separately: appliance inactive, sensor unreachable, and hub offline. Remote notifications require a working remote-access path, not merely Thread connectivity.

Polling, retransmissions, active windows and application exchanges materially affect energy; network branding alone cannot establish battery life. [Nordic power guidance](https://docs.nordicsemi.com/r/bundle/nwp_049)

## Hardware impact

Replace the nRF52832 radio candidate with an IEEE 802.15.4-capable MCU. Prefer evaluating nRF54L15 for a new low-power design; nRF52840 is an alternative prototype platform. The nRF54L15 supports Thread and BLE; exact module, SDK configuration, memory budget and acquisition power remain to be validated. The old nRF52832 analog/ADC register configuration cannot simply be assumed to transfer unchanged. [nRF54L15](https://www.nordicsemi.com/Products/nRF54L15), [nRF52840](https://www.nordicsemi.com/Products/nRF52840/Development-Tools)

The sensor still needs battery-backed operation at zero load. Switching to Thread does not solve the measurement front end's power budget or the maintenance problem. Account for firmware updates and weak-signal operation in the runtime tests.

## Thread application versus Matter over Thread

For a hub we control, a small authenticated application protocol over Thread gives control over bulk logs, commissioning, sequence acknowledgments and reporting. Network security alone is not a substitute for application authorization; specify endpoint authentication and encryption. This requires our own hub service/integration and is not automatically compatible with consumer smart-home UIs.

For broad consumer ecosystem integration, investigate Matter over Thread. Matter supports current reporting through its electrical measurement functionality, but the exact current-only device model, mandatory attributes and target controllers must be verified. Do not invent voltage or watts just to populate attributes. Standard live measurements do not establish support for our one-second historical archive. Expect a separate history service or integration unless validated otherwise. [CSA electrical measurement overview](https://csa-iot.org/newsroom/matter-1-3-specification-released/)

BLE can remain the setup transport even when normal operation uses Thread. Nordic documents BLE commissioning for its Matter devices. [Commissioning and low-power configuration](https://nrfconnectdocs.nordicsemi.com/addons/ncs-matter/latest/matter/getting_started/low_power_configuration.html)

## Next decision

Choose the intended hub experience before freezing the application protocol: a hub/service we control favors a focused Thread application; compatibility with existing smart-home controllers favors investigating Matter. In either case, test the same stories: unattended reporting, zero-load availability, hub loss/recovery, full history backfill, weak coverage, setup after installation, and battery service.
