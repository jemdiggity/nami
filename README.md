# Nami 波

An internal prototype that senses the changing magnetic field around an insulated outlet wire to measure AC current without an electrical connection to the conductor.

Nami records one RMS current value each second, retains local history, and sends measurements over Thread to a powered local hub. BLE provides commissioning. The name means “wave”: we are picking up the waves from the wire and measuring them.

- [Product requirements and system diagrams](docs/PRD.md) — authoritative prototype specification.
- [Compact C0 hardware](hardware/nami-compact/README.md) — 24 × 32 mm, four-layer production layout candidate, renders and STEP model.
- [Rev A bench hardware](hardware/nami-rev-a/README.md) — KiCad schematics, routed PCB, BOM, verification and bring-up guide.
- [Earlier design explorations](docs/research/) — rationale and candidate circuits; superseded where they conflict with the PRD.

Status: bench and compact hardware design; feasibility validation remains. Native KiCad schematics and a routed prototype PCB are included; firmware and physical validation are not yet complete. Accuracy, battery life, packaging, and installation suitability remain unverified. The board is not a manufacturing or mains-installation release.

The repository is this `nami/` directory, not its parent. No remote repository is configured.
