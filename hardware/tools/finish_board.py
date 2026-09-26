#!/usr/bin/env python3
"""Import local autorouter session; finish ground connections and pours."""
from pathlib import Path
import pcbnew as p
import wx
app=wx.App(False)
out=Path(__file__).resolve().parents[1]/'nami-rev-a'
b=p.LoadBoard(str(out/'nami.kicad_pcb'))
assert p.ImportSpecctraSES(b,str(out/'nami.ses'))
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
g=b.FindNet('GND')
def track(a,c):
    t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*c));t.SetWidth(p.FromMM(.2));t.SetLayer(p.F_Cu);t.SetNet(g);b.Add(t)
track((83.35,27.25),(83.35,28.35))
track((92.65,27.25),(94.7,27.25))
via=p.PCB_VIA(b);via.SetPosition(v(94.7,27.25));via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(g);b.Add(via)
for layer in [p.F_Cu,p.B_Cu]:
    z=p.ZONE(b);z.SetLayer(layer);z.SetNet(g);z.SetLocalClearance(p.FromMM(.2));z.SetThermalReliefGap(p.FromMM(.25));z.SetThermalReliefSpokeWidth(p.FromMM(.25));z.SetMinThickness(p.FromMM(.2))
    poly=z.Outline();poly.NewOutline()
    for x,y in [(20.5,20.5),(114.5,20.5),(114.5,94.5),(20.5,94.5)]:poly.Append(p.FromMM(x),p.FromMM(y))
    b.Add(z)
f=p.ZONE_FILLER(b);f.Fill(b.Zones())
p.SaveBoard(str(out/'nami.kicad_pcb'),b)
print('Added two ground pours and module ground connections')
