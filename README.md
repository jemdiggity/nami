# Nami 波

An internal prototype that senses the changing magnetic field around an insulated outlet wire to measure AC current without an electrical connection to the conductor.

Nami records one RMS current value each second, retains local history, and sends measurements over Thread to a powered local hub. BLE provides commissioning. The name means “wave”: we are picking up the waves from the wire and measuring them.

- [Product requirements and system diagrams](docs/PRD.md) — authoritative prototype specification.
- [Earlier design explorations](docs/research/) — rationale and candidate circuits; superseded where they conflict with the PRD.

Status: specification and feasibility stage. Hardware performance, battery life, packaging, and installation suitability have not been validated. This repository does not yet contain firmware, a fabrication-ready schematic, or a PCB.

The repository is this `nami/` directory, not its parent. No remote repository is configured.
