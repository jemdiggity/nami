#!/usr/bin/env python3
"""Run with KiCad's bundled Python (pcbnew). Creates an unrouted review board."""
import json, os
from pathlib import Path
import pcbnew as p
import wx
app=wx.App(False)
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'nami-rev-a'
LIB=Path(os.environ.get('KICAD_FOOTPRINT_DIR','/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'))
data=json.loads((OUT/'connectivity.json').read_text());b=p.BOARD()
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
nets={}
for name in sorted({n for c in data.values() for n in c['nets'].values()}):
    n=p.NETINFO_ITEM(b,name);b.Add(n);nets[name]=n
pos={
 'J1':(24,35,0),'R8':(30,35,0),'C5':(35,38,90),'D1':(35,33,0),
 'U2':(47,43,0),'R9':(32,47,90),'R10':(32,53,90),'C6':(37,49,90),
 'R11':(43,53,0),'C7':(48,53,90),'R12':(54,47,90),'R13':(54,41,90),
 'R14':(39,30,0),'C8':(45,30,90),'R15':(59,36,0),'C9':(63,40,90),
 'C10':(47,37,0),'TP3':(30,29,0),'TP4':(56,54,0),'TP5':(64,32,0),
 'J2':(24,78,0),'R1':(29,68,0),'C1':(31,72,90),'C2':(42,71,0),
 'U1':(42,75,0),'L1':(47,75,270),'R2':(36.5,73,0),'R3':(36.5,76,0),'R4':(36.5,79,0),
 'C3':(44,81,0),'C4':(49,81,90),'R5':(60,66,0),'R6':(37,61,0),'R7':(69,66,0),
 'TP1':(54,84,0),'TP2':(28,84,0),
 'U3':(88,31,0),'C11':(84,43,0),'C12':(88,41,0),'Y1':(79,40,90),
 'C13':(75,39,0),'C14':(75,43,0),'U4':(90,55,0),'C15':(96,51,90),'C16':(100,55,90),
 'R16':(83,51,90),'R17':(83,57,90),'R18':(96,59,0),'J3':(105,71,0),
 'SW1':(65,81,0),'R19':(65,76,0),'SW2':(82,81,0),'R20':(82,76,0),
 'R21':(72,55,0),'D2':(72,59,0),'R22':(60,59,0),'R23':(60,63,0),'C17':(65,59,90),
 'J4':(108,44,0),
}
assert set(pos)==set(data),(set(data)-set(pos),set(pos)-set(data))
for ref,c in data.items():
    lib,name=c['fp'].split(':');f=p.FootprintLoad(str(LIB/(lib+'.pretty')),name)
    if not f:raise RuntimeError('Missing '+c['fp'])
    f.SetReference(ref);f.SetValue(c['value']);f.SetFPID(p.LIB_ID(lib,name))
    f.SetPath(p.KIID_PATH(c['sheet_path']+'/'+c['uuid']))
    x,y,a=pos[ref];f.SetPosition(v(x,y));f.SetOrientationDegrees(a)
    for pad in f.Pads():
        if pad.GetNumber() in c['nets']:pad.SetNet(nets[c['nets'][pad.GetNumber()]])
    f.Reference().SetTextSize(v(.8,.8));f.Reference().SetTextThickness(p.FromMM(.12))
    f.Value().SetVisible(False)
    b.Add(f)
for a,z in [((20,20),(115,20)),((115,20),(115,95)),((115,95),(20,95)),((20,95),(20,20))]:
    s=p.PCB_SHAPE();s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(v(*a));s.SetEnd(v(*z));s.SetLayer(p.Edge_Cuts);s.SetWidth(p.FromMM(.05));b.Add(s)
for i,(x,y) in enumerate([(24,24),(111,24),(24,91),(111,91)],1):
    f=p.FootprintLoad(str(LIB/'MountingHole.pretty'),'MountingHole_2.7mm_M2.5');f.SetReference('H'+str(i));f.SetPosition(v(x,y));f.Value().SetVisible(False);f.Reference().SetVisible(False);b.Add(f)
for t,x,y,size in [('NAMI / REV A0',49,24,1.3),('BENCH PROTOTYPE',48,89,1),('CT + 5R HARNESS',37,56.5,.8),('2.0-3.3V ONLY',33,87,.8),('PAIR',68,89,.8),('RESET',85,89,.8)]:
    a=p.PCB_TEXT(b);a.SetText(t);a.SetPosition(v(x,y));a.SetTextSize(v(size,size));a.SetTextThickness(p.FromMM(.15));a.SetLayer(p.F_SilkS);b.Add(a)
# Extra keepout extends module antenna region to board edge on BOTH copper layers.
z=p.ZONE(b);z.SetIsRuleArea(True);layers=p.LSET();layers.AddLayer(p.F_Cu);layers.AddLayer(p.B_Cu);z.SetLayerSet(layers)
z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True)
poly=z.Outline();poly.NewOutline()
for x,y in [(72,20),(104,20),(104,25.8),(72,25.8)]:poly.Append(p.FromMM(x),p.FromMM(y))
b.Add(z)
b.GetDesignSettings().SetCopperLayerCount(2)
p.SaveBoard(str(OUT/'nami.kicad_pcb'),b)
print('Placed',len(data),'components on 95 x 75 mm bench PCB')
if not p.ExportSpecctraDSN(b,str(OUT/'nami.dsn')):raise RuntimeError('DSN export failed')
