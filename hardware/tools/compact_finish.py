#!/usr/bin/env python3
"""Import compact routing into a fresh compact_board.py board, then fill pours."""
import math, json
from pathlib import Path
import pcbnew as p
import wx
app=wx.App(False)
out=Path(__file__).resolve().parents[1]/'nami-compact'
b=p.LoadBoard(str(out/'nami.kicad_pcb'))
assert p.ImportSpecctraSES(b,str(out/'nami.ses'))
g=b.FindNet('GND')
# Ground fills on exterior layers. L2 ground was present during routing.
for layer in [p.F_Cu,p.B_Cu]:
 z=p.ZONE(b);z.SetLayer(layer);z.SetNet(g);z.SetLocalClearance(p.FromMM(.15));z.SetThermalReliefGap(p.FromMM(.2));z.SetThermalReliefSpokeWidth(p.FromMM(.2));z.SetMinThickness(p.FromMM(.15));z.SetPadConnection(p.ZONE_CONNECTION_FULL)
 poly=z.Outline();poly.NewOutline()
 for x,y in [(20.25,24),(43.75,24),(43.75,51.75),(20.25,51.75)]:poly.Append(p.FromMM(x),p.FromMM(y))
 b.Add(z)
for z in b.Zones():
 if not z.GetIsRuleArea():z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
p.ZONE_FILLER(b).Fill(b.Zones())
# Stitch exterior ground regions to L2. Reject positions near any component pad,
# any non-ground conductor, and every existing drill. No via-in-pad is used.
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
pads=[a for f in sorted(b.GetFootprints(),key=lambda f:f.GetReference()) for a in sorted(f.Pads(),key=lambda a:a.GetNumber())]
tracks=list(b.GetTracks());vias=[a for a in tracks if isinstance(a,p.PCB_VIA)]
outer=[z for z in b.Zones() if not z.GetIsRuleArea() and z.GetLayer() in [p.F_Cu,p.B_Cu]]
def allowed(x,y):
 q=v(x,y)
 if 29.3<x<31.7 and y<25.65:return False # module's local top-side keepout
 if not (20.8<x<43.2 and 24.55<y<51.2):return False
 if any(a.GetEffectiveShape(a.GetLayer()).Collide(q,p.FromMM(.30 if a.GetNetname()=='GND' else .42)) for a in pads):return False
 if any(a.GetNetname()!='GND' and a.GetEffectiveShape(a.GetLayer()).Collide(q,p.FromMM(.41)) for a in tracks):return False
 if any(math.hypot(p.ToMM(a.GetPosition().x)-x,p.ToMM(a.GetPosition().y)-y)<.65 for a in vias):return False
 return any(z.HitTestFilledArea(z.GetLayer(),q) for z in outer)
candidates=[]
for pad in pads:
 if pad.GetNetname()!='GND':continue
 x,y=p.ToMM(pad.GetPosition().x),p.ToMM(pad.GetPosition().y)
 for radius in [.8,1.1,1.5]:
  for angle in range(0,360,45):candidates.append((x+radius*math.cos(math.radians(angle)),y+radius*math.sin(math.radians(angle))))
candidates += [(x/2,y/2) for x in range(42,87,4) for y in range(50,103,4)]
added=[]
for x,y in candidates:
 if any(math.hypot(x-a,y-c)<1.5 for a,c in added):continue
 if not allowed(x,y):continue
 t=p.PCB_VIA(b);t.SetPosition(v(x,y));t.SetWidth(p.FromMM(.5));t.SetDrill(p.FromMM(.25));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(g);b.Add(t);vias.append(t);added.append((x,y))
for z in b.Zones():
 if not z.GetIsRuleArea():z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
p.ZONE_FILLER(b).Fill(b.Zones())
# Resolve small ground islands with a finer via search, rather than leaving
# apparently poured but electrically isolated ground pads.
for z in outer:
 polys=z.GetFilledPolysList(z.GetLayer())
 for i in range(polys.OutlineCount()):
  if any(polys.Contains(t.GetPosition(),i) for t in vias if t.GetNetname()=='GND'):continue
  bb=polys.COutline(i).BBox();found=False
  for xi in range(math.ceil(p.ToMM(bb.GetX())*10),math.floor(p.ToMM(bb.GetRight())*10)+1):
   if found:break
   for yi in range(math.ceil(p.ToMM(bb.GetY())*10),math.floor(p.ToMM(bb.GetBottom())*10)+1):
    x,y=xi/10,yi/10
    if not polys.Contains(v(x,y),i) or not allowed(x,y):continue
    t=p.PCB_VIA(b);t.SetPosition(v(x,y));t.SetWidth(p.FromMM(.5));t.SetDrill(p.FromMM(.25));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(g);b.Add(t);vias.append(t);added.append((x,y));found=True;break
p.ZONE_FILLER(b).Fill(b.Zones())
# Assembly/service markings in reserved spaces.
for label,x,y,layer in [('+',21.75,47.4,p.F_SilkS),('+',39.25,48,p.B_SilkS),('PAIR',24,45.6,p.B_SilkS),('RST',30,45.6,p.B_SilkS)]:
 t=p.PCB_TEXT(b);t.SetText(label);t.SetPosition(v(x,y));t.SetTextSize(v(.8,.8));t.SetTextThickness(p.FromMM(.12));t.SetLayer(layer);t.SetMirrored(layer==p.B_SilkS);b.Add(t)
# Apply the explicit layout-review corrections after importing the original
# routing session and stitching; keep the same edits in every regeneration.
from refine_routes import refine
refine(b)
p.ZONE_FILLER(b).Fill(b.Zones())
(out/'verification/pads.json').write_text(json.dumps({f.GetReference():{pad.GetNumber():[round(p.ToMM(pad.GetPosition().x),4),round(p.ToMM(pad.GetPosition().y),4),pad.GetNetname()] for pad in f.Pads()} for f in b.GetFootprints() if not f.GetReference().startswith('FID')},indent=2)+'\n')
p.SaveBoard(str(out/'nami.kicad_pcb'),b)
print('Added',len(added),'ground stitching vias')
print('Imported compact routes and filled ground planes')
