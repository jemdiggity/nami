#!/usr/bin/env python3
"""Export the compact PCB as GLB with web-preview material finishes (stdlib only).

Requires KiCad 10 kicad-cli. Geometry and source board are not modified.
"""
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CLI = os.environ.get('KICAD_CLI') or shutil.which('kicad-cli') or '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
OUTPUT = ROOT / 'docs/viewer/nami.glb'
with tempfile.TemporaryDirectory() as tmp:
    raw = Path(tmp) / 'nami.glb'
    subprocess.run([CLI, 'pcb', 'export', 'glb', '--subst-models', '--include-pads',
                    '--include-silkscreen', '--include-soldermask', '--user-origin', '32x36mm',
                    '--output', str(raw), str(ROOT / 'hardware/nami-compact/nami.kicad_pcb')], check=True)
    data = raw.read_bytes()
length, kind = struct.unpack_from('<II', data, 12)
assert kind == 0x4E4F534A
scene = json.loads(data[20:20 + length])
# STEP colors have no PBR finish. Give plastics/ceramics a matte finish and
# light neutral component surfaces a satin metal finish. Preserve source colors.
for material in scene['materials']:
    pbr = material.setdefault('pbrMetallicRoughness', {})
    rgb = pbr.get('baseColorFactor', [1, 1, 1, 1])[:3]
    if 'metallicFactor' not in pbr:
        metal = min(rgb) > 0.45 and max(rgb) - min(rgb) < 0.2 and min(rgb) < 0.95
        pbr['metallicFactor'] = 0.8 if metal else 0.0
        pbr['roughnessFactor'] = 0.3 if metal else 0.65
    # Opaque soldermask/FR4 avoids glTF transparency sorting artifacts.
    if material.get('alphaMode') == 'BLEND' and rgb[1] > rgb[0]:
        pbr['baseColorFactor'][3] = 1.0
        material.pop('alphaMode', None)
        material['doubleSided'] = False
payload = json.dumps(scene, separators=(',', ':')).encode()
payload += b' ' * (-len(payload) % 4)
rest = data[20 + length:]
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_bytes(struct.pack('<III', 0x46546C67, 2, 20 + len(payload) + len(rest)) + struct.pack('<II', len(payload), kind) + payload + rest)
print(f'{OUTPUT}: {len(scene["meshes"])} meshes, {len(scene["materials"])} materials')
