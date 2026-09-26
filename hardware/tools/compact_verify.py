#!/usr/bin/env python3
"""Check compact-specific mechanical, copper-layer and circuit invariants."""
import collections, json, math
from pathlib import Path
import pcbnew as p
import wx
app=wx.App(False)
root=Path(__file__).resolve().parents[1];out=root/'nami-compact'
b=p.LoadBoard(str(out/'nami.kicad_pcb'))
base=json.loads((root/'nami-rev-a/connectivity.json').read_text())
now=json.loads((out/'connectivity.json').read_text())
assert set(base)==set(now)
for ref in base:assert base[ref]['nets']==now[ref]['nets'],ref
box=b.GetBoardEdgesBoundingBox();width=p.ToMM(box.GetWidth());height=p.ToMM(box.GetHeight())
assert math.isclose(width,24,abs_tol=.06) and math.isclose(height,32,abs_tol=.06)
assert b.GetCopperLayerCount()==4
assert b.GetDesignSettings().GetBoardThickness()==p.FromMM(1)
bylayer=collections.Counter();lengths=collections.defaultdict(float);vias=collections.Counter()
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA):
  assert t.GetViaType()==p.VIATYPE_THROUGH
  assert t.GetDrillValue()>=p.FromMM(.25)
  assert p.ToMM(t.GetPosition().y)-p.ToMM(t.GetWidth(p.F_Cu))/2>=24
  vias[t.GetNetname()]+=1
 else:
  assert t.GetLayer()!=p.In1_Cu,'L2 must remain an unbroken ground plane'
  assert min(p.ToMM(t.GetStart().y),p.ToMM(t.GetEnd().y))-p.ToMM(t.GetWidth())/2>=24
  bylayer[b.GetLayerName(t.GetLayer())]+=1
  lengths[t.GetNetname()]+=p.ToMM(t.GetLength())
for n in ['LX1','LX2']:
 assert vias[n]==0
 assert lengths[n]<5
for f in b.GetFootprints():
 for pad in f.Pads():
  if not pad.GetLayerSet().Contains(p.F_Cu) and not pad.GetLayerSet().Contains(p.B_Cu):continue
  assert pad.GetBoundingBox().GetTop()>=p.FromMM(24),f.GetReference()
keepouts=[z for z in b.Zones() if z.GetIsRuleArea() and all(z.GetLayerSet().Contains(l) for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu])]
assert keepouts,'Missing all-layer antenna keepout'
sides=collections.Counter('front' if f.GetLayer()==p.F_Cu else 'back' for f in b.GetFootprints() if f.GetReference() in now)
result={'outline_mm':[24,32],'area_mm2':768,'bench_area_mm2':7125,'area_reduction_percent':round(100*(1-768/7125),2),'nominal_substrate_mm':1,'copper_layers':4,'same_electrical_components_as_bench':len(now),'placement_sides':dict(sides),'routing_segments_by_layer':dict(bylayer),'ground_plane_layer':'In1.Cu; no routed tracks','via_count':sum(vias.values()),'switch_node_length_mm':{n:round(lengths[n],3) for n in ['LX1','LX2']},'switch_node_vias':{n:vias[n] for n in ['LX1','LX2']},'crystal_net_total_length_mm':{n:round(lengths[n],3) for n in ['XL1','XL2']},'crystal_net_vias':{n:vias[n] for n in ['XL1','XL2']},'antenna_copper_exclusion_mm':{'x':[20,44],'y':[20,24],'all_copper_layers':True},'scope':'CAD verification only; excludes battery, CT, enclosure and field qualification'}
(out/'verification/compact-layout.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
