#!/usr/bin/env python3
"""Create compact C0 placement and critical routes with KiCad's bundled Python.
Overwrites only hardware/nami-compact/nami.kicad_pcb and routing input.
"""
import json, os
from pathlib import Path
import pcbnew as p
import wx
app=wx.App(False)
OUT=Path(__file__).resolve().parents[1]/'nami-compact'
LIB=Path(os.environ.get('KICAD_FOOTPRINT_DIR','/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'))
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def mm(q):return (p.ToMM(q.x),p.ToMM(q.y))
# Local connector land patterns: bare pads, no connector body, no paste openings.
for name,points,size in [
 ('WirePads_2_P2.5',[(1,-1.25,0),(2,1.25,0)],(1.5,2.5)),
 ('Pogo_2x05_P1.27',[(2*j+i+1,(i-.5)*1.27,(j-2)*1.27) for j in range(5) for i in range(2)],(.8,.8)),
 ('Pogo_1x04_P1.27',[(i+1,(i-1.5)*1.27,0) for i in range(4)],(.8,.8))]:
 f=p.FOOTPRINT(None);f.SetReference('REF**');f.SetValue(name);f.SetAttributes(p.FP_SMD)
 f.SetLibDescription('Nami bare PCB contact pads; external fixture or strain relief required')
 for num,x,y in points:
  pad=p.PAD(f);pad.SetNumber(str(num));pad.SetAttribute(p.PAD_ATTRIB_SMD);pad.SetShape(p.PAD_SHAPE_ROUNDRECT);pad.SetRoundRectRadiusRatio(.25)
  layers=p.LSET();layers.AddLayer(p.F_Cu);layers.AddLayer(p.F_Mask);pad.SetLayerSet(layers);pad.SetSize(v(*size));pad.SetPosition(v(x,y));f.Add(pad)
 xmin=min(x for _,x,y in points)-size[0]/2-.25;xmax=max(x for _,x,y in points)+size[0]/2+.25
 ymin=min(y for _,x,y in points)-size[1]/2-.25;ymax=max(y for _,x,y in points)+size[1]/2+.25
 for a,z in [((xmin,ymin),(xmax,ymin)),((xmax,ymin),(xmax,ymax)),((xmax,ymax),(xmin,ymax)),((xmin,ymax),(xmin,ymin))]:
  s=p.PCB_SHAPE(f);s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(v(*a));s.SetEnd(v(*z));s.SetLayer(p.F_CrtYd);s.SetWidth(p.FromMM(.05));f.Add(s)
 f.SetFPID(p.LIB_ID('Nami',name));p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(OUT/'Nami.pretty'),f)
(OUT/'fp-lib-table').write_text('(fp_lib_table\n (version 7)\n (lib (name "Nami")(type "KiCad")(uri "${KIPRJMOD}/Nami.pretty")(options "")(descr "Nami PCB contact pads"))\n)\n')
b=p.BOARD();b.GetDesignSettings().SetCopperLayerCount(4);b.GetDesignSettings().SetBoardThickness(p.FromMM(1.0))
ds=b.GetDesignSettings();ds.m_MinClearance=p.FromMM(.15);ds.m_TrackMinWidth=p.FromMM(.15);ds.m_MinThroughDrill=p.FromMM(.25);ds.m_ViasMinSize=p.FromMM(.5)
nc=b.GetDesignSettings().m_NetSettings.GetDefaultNetclass()
nc.SetClearance(p.FromMM(.15));nc.SetTrackWidth(p.FromMM(.18));nc.SetViaDiameter(p.FromMM(.5));nc.SetViaDrill(p.FromMM(.25))
data=json.loads((OUT/'connectivity.json').read_text());nets={}
for name in sorted({n for c in data.values() for n in c['nets'].values()}):
 net=p.NETINFO_ITEM(b,name);b.Add(net);nets[name]=net
# (x, y, rotation, side) in mm. Antenna at north edge. Quiet analog southwest;
# switcher southeast. Flash and service contacts on reverse side.
pos={
 'U3':(32,28,0,'F'),'C11':(32,37,0,'B'),'C12':(32,35,0,'B'),
 'Y1':(24,33,90,'F'),'C13':(22,32,90,'F'),'C14':(22,35,90,'F'),
 'U4':(32,29.5,0,'B'),'C15':(37.8,27.6,90,'B'),'C16':(40.3,29.3,90,'B'),
 'R16':(25.8,27.5,90,'B'),'R17':(25.8,30.5,90,'B'),'R18':(37.8,31.5,90,'B'),
 'J1':(23,49.5,0,'F'),'R8':(22,45,90,'F'),'C5':(28,45.5,90,'F'),'D1':(25,45,0,'F'),
 'U2':(26,41,0,'F'),'R9':(25,37.5,0,'F'),'R10':(25,35.8,0,'B'),'C6':(25,37.5,0,'B'),
 'R11':(22,41,90,'F'),'C7':(22,38,90,'F'),'R12':(30.5,43,90,'F'),'R13':(30.5,39.7,90,'F'),
 'R14':(28.5,49.5,0,'F'),'C8':(33.5,49.5,0,'F'),'R15':(30.5,45.4,0,'F'),'C9':(31.8,47.3,0,'F'),
 'C10':(29,37.4,0,'F'),'TP3':(22,44,0,'B'),'TP4':(24,44,0,'B'),'TP5':(26,44,0,'B'),
 'J2':(40.5,49.8,0,'B'),'R1':(36.8,49.8,90,'B'),'C1':(39.5,46,0,'B'),
 'U1':(37,43.4,90,'F'),'L1':(37,38.85,0,'F'),'C2':(33.3,42.6,180,'F'),
 'C3':(41.3,42,90,'F'),'C4':(41.5,37,90,'F'),
 'R2':(34.5,46.8,90,'F'),'R3':(37,46.8,90,'F'),'R4':(39.5,46.8,90,'F'),
 'R5':(35,37.5,90,'B'),'R6':(32.5,38.5,90,'F'),'R7':(41,33,0,'B'),
 'TP1':(41.5,38,0,'B'),'TP2':(41.5,40,0,'B'),
 'J3':(38.5,37,0,'B'),'J4':(25.5,40.5,0,'B'),
 'SW1':(24,47.7,0,'B'),'R19':(22,30,90,'B'),'SW2':(30,47.7,0,'B'),'R20':(41,34,0,'F'),
 'R21':(22,28,90,'F'),'D2':(24,27,90,'F'),
 'R22':(30,41,90,'B'),'R23':(32,41,90,'B'),'C17':(34,41,90,'B'),
}
assert set(pos)==set(data),(set(data)-set(pos),set(pos)-set(data))
fps={}
for ref,c in data.items():
 lib,name=c['fp'].split(':');base=OUT/'Nami.pretty' if lib=='Nami' else LIB/(lib+'.pretty')
 f=p.FootprintLoad(str(base),name);assert f,c['fp'];f.SetReference(ref);f.SetValue(c['value']);f.SetFPID(p.LIB_ID(lib,name));f.SetPath(p.KIID_PATH(c['sheet_path']+'/'+c['uuid']))
 x,y,ang,side=pos[ref];f.SetPosition(v(x,y));b.Add(f)
 if side=='B':f.Flip(v(x,y),False)
 f.SetOrientationDegrees(ang)
 for pad in f.Pads():
  if pad.GetNumber() in c['nets']:pad.SetNet(nets[c['nets'][pad.GetNumber()]])
 f.Reference().SetVisible(False);f.Value().SetVisible(False)
 # Assembly references remain available in editor and fabrication views.
 fps[ref]=f
for a,z in [((20,20),(44,20)),((44,20),(44,52)),((44,52),(20,52)),((20,52),(20,20))]:
 s=p.PCB_SHAPE();s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(v(*a));s.SetEnd(v(*z));s.SetLayer(p.Edge_Cuts);s.SetWidth(p.FromMM(.05));b.Add(s)
# All-layer keepout across entire top strip, beyond manufacturer 3.8mm region.
z=p.ZONE(b);z.SetIsRuleArea(True);ls=p.LSET()
for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:ls.AddLayer(l)
z.SetLayerSet(ls);z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True)
poly=z.Outline();poly.NewOutline()
for x,y in [(20,20),(44,20),(44,24),(20,24)]:poly.Append(p.FromMM(x),p.FromMM(y))
b.Add(z)
# Board-only assembly fiducials, not components.
for i,(x,y,side) in enumerate([(21,25,'F'),(43,50,'F'),(43,25,'B'),(21,50.5,'B')],1):
 f=p.FootprintLoad(str(LIB/'Fiducial.pretty'),'Fiducial_0.5mm_Mask1mm');f.SetReference('FID'+str(i));f.SetPosition(v(x,y));f.Reference().SetVisible(False);f.Value().SetVisible(False)
 b.Add(f)
 if side=='B':f.Flip(v(x,y),False)
 f.SetAttributes(f.GetAttributes()|p.FP_BOARD_ONLY|p.FP_EXCLUDE_FROM_BOM)
# Text in assembly and free silkscreen regions; antenna marking has no copper.
for text,x,y,size,layer in [('NAMI C0',32,21.5,.9,p.B_SilkS),('24 x 32',32,22.7,.8,p.B_SilkS),('CT',28,51.3,.8,p.F_SilkS),('BAT',34,51,.8,p.B_SilkS)]:
 t=p.PCB_TEXT(b);t.SetText(text);t.SetPosition(v(x,y));t.SetTextSize(v(size,size));t.SetTextThickness(p.FromMM(.12));t.SetLayer(layer);t.SetMirrored(layer==p.B_SilkS);b.Add(t)
# Hand-routed switching loops. These remain fixed in the routing exchange.
def route(net,points,width=.25,layer=p.F_Cu):
 for a,z in zip(points,points[1:]):
  t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*z));t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNet(nets[net]);t.SetLocked(True);b.Add(t)
def via(net,x,y):
 t=p.PCB_VIA(b);t.SetPosition(v(x,y));t.SetWidth(p.FromMM(.5));t.SetDrill(p.FromMM(.25));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(nets[net]);t.SetLocked(True);b.Add(t)
route('LX1',[(36.5,42.1875),(36.5,41.7),(35.815,41.015),(35.815,38.85)],.3)
route('LX2',[(37.5,42.1875),(37.5,41.7),(38.185,41.015),(38.185,38.85)],.3)
route('VBAT',[(34.25,42.6),(35.3,42.6),(35.7125,42.1875),(36,42.1875)],.3)
route('VBAT',[(34.25,42.6),(34.25,43.95),(35.2,44.9),(36,44.9),(36,44.6125)],.3)
route('VREG',[(38,42.1875),(38.5,42.6875),(39.2875,43.475),(41.3,43.475)],.3)
route('GND',[(37,42.1875),(37,43.4),(35.5,43.4)],.3);via('GND',35.5,43.4)
route('GND',[(36.5,44.6125),(36.5,43.4)],.25)
route('GND',[(32.35,42.6),(32.35,43.7)],.3);via('GND',32.35,43.7)
route('GND',[(41.3,40.525),(42.9,40.525)],.3);via('GND',42.9,40.525)
route('GND',[(27.35,24.25),(27.35,25.35)],.18)
route('GND',[(36.65,24.25),(37.65,24.25),(38,24.6)],.18);via('GND',38,24.6)
# L2 is a ground plane, never a general signal-routing layer.
z=p.ZONE(b);z.SetLayer(p.In1_Cu);z.SetNet(nets['GND']);z.SetLocalClearance(p.FromMM(.15));z.SetMinThickness(p.FromMM(.15));z.SetPadConnection(p.ZONE_CONNECTION_FULL)
poly=z.Outline();poly.NewOutline()
for x,y in [(20.25,24),(43.75,24),(43.75,51.75),(20.25,51.75)]:poly.Append(p.FromMM(x),p.FromMM(y))
b.Add(z)
p.ZONE_FILLER(b).Fill(b.Zones())
# Pad-coordinate listing supports explicit short critical routes below.
(OUT/'verification/pads.json').write_text(json.dumps({r:{pad.GetNumber():[round(z,4) for z in mm(pad.GetPosition())]+[pad.GetNetname()] for pad in f.Pads()} for r,f in fps.items()},indent=2)+'\n')
p.SaveBoard(str(OUT/'nami.kicad_pcb'),b)
assert p.ExportSpecctraDSN(b,str(OUT/'nami.dsn'))
dsn=OUT/'nami.dsn'
dsn.write_text(dsn.read_text().replace('(layer In1.Cu\n      (type signal)', '(layer In1.Cu\n      (type power)'))
print('Placed compact board: 24 x 32 mm, 4 layers, double-sided assembly')
