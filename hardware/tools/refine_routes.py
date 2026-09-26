#!/usr/bin/env python3
"""Explicit post-routing cleanup for the ten C0 review details.
Run once on the original routed C0 board; electrical nets do not change.
Moves Y1/C13/C14 and selected vias to make room for clean pad exits.
Also called by compact_finish.py before its final save.
"""
import pcbnew as p

def refine(b):
    def xy(q):return (round(p.ToMM(q.x),4),round(p.ToMM(q.y),4))
    def v(q):return p.VECTOR2I(p.FromMM(q[0]),p.FromMM(q[1]))
    def remove(net,layer,edges=None):
        keys={tuple(sorted(e)) for e in edges} if edges is not None else None
        count=0
        for t in list(b.GetTracks()):
            if isinstance(t,p.PCB_VIA) or t.GetNetname()!=net or t.GetLayer()!=layer:continue
            if keys is not None and tuple(sorted([xy(t.GetStart()),xy(t.GetEnd())])) not in keys:continue
            b.RemoveNative(t);count+=1
        if keys is not None:assert count==len(keys),(net,count,len(keys))
    def route(net,layer,*points,width=.18):
        for a,z in zip(points,points[1:]):
            t=p.PCB_TRACK(b);t.SetStart(v(a));t.SetEnd(v(z));t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNet(b.FindNet(net));b.Add(t)
    F,B=p.F_Cu,p.B_Cu
    # Align both load capacitors with the crystal terminals. This replaces
    # the cramped routed forks with direct, normal pad-to-pad connections.
    fps={f.GetReference():f for f in b.GetFootprints()}
    fps['Y1'].SetPosition(v((24.5,33)))
    for ref,y in [('C13',31.75),('C14',34.25)]:
        fps[ref].SetPosition(v((21.8,y)));fps[ref].SetOrientationDegrees(180)
    for t in b.GetTracks():
        if isinstance(t,p.PCB_VIA) and t.GetNetname()=='GND':
            q=xy(t.GetPosition())
            if abs(q[0]-22.7778)<.01 and abs(q[1]-33.4472)<.01:t.SetPosition(v((22,33)))
            if abs(q[0]-24.2)<.01 and abs(q[1]-47.7)<.01:t.SetPosition(v((23.6,47.7)))
    # 1/2: the load capacitors and oscillator traces leave separate pad faces.
    # Branching is within the crystal pad, not an acute fork below it.
    remove('XL1',F)
    route('XL1',F,(24.5,31.75),(24.5,32.5),(26.6083,34.6083),(28.65,34.6083),(28.8,34.7583),(28.8,35.15))
    route('XL1',F,(24.5,31.75),(22.575,31.75))
    remove('XL2',F)
    route('XL2',F,(24.5,34.25),(24.5,35.05),(25.1417,35.6917),(29.45,35.6917),(29.6,35.5417),(29.6,35.15))
    route('XL2',F,(24.5,34.25),(22.575,34.25))
    # 3: direct pad-centre supply links replace the upper loop and spur.
    remove('VDD_M',F)
    route('VDD_M',F,(33.6,35.15),(34.4,35.15),(35.2,35.15))
    route('VDD_M',F,(35.2,35.15),(35.2,35.5512),(34.8891,35.8621))
    route('VDD_M',F,(35.2,35.15),(35.2,34.7918),(35.4,34.5918),(39.5832,34.5918),(40.175,34))
    # 4: straight top/bottom exits on the large CT-return solder pad.
    remove('VMID',F,[((24.25,49.5),(22.7482,51.0018)),((22.7482,51.0018),(21.087,51.0018)),((21.087,51.0018),(20.7354,50.6502)),((24.25,49.5),(24.7569,48.9931)),((24.7569,48.9931),(24.7569,47.0689))])
    route('VMID',F,(24.25,49.5),(24.25,51),(24.1,51.15),(21.2352,51.15),(20.7354,50.6502))
    route('VMID',F,(24.25,49.5),(24.25,47.9),(24.7569,47.3931),(24.7569,47.0689))
    # 5: chamfer the pair exit; eliminate the tiny MOSI right-angle jog.
    remove('PAIR_N',F)
    route('PAIR_N',F,(36.65,30.95),(37.05,30.95),(37.1917,30.8083),(37.1917,29.0777),(38.7034,27.566))
    remove('FLASH_MOSI',F)
    route('FLASH_MOSI',F,(36.65,31.75),(37.1917,31.75),(39.2181,29.7236),(39.2181,27.3764),(38.6797,26.838),(36.9009,26.838))
    # 6: join the rear supply branches at the pad, not at a notch above it.
    remove('VDD_M',B,[((25.6265,34.4515),(31.225,34.4515)),((31.4149,34.2616),(31.225,34.4515)),((31.225,34.4515),(31.225,35)),((33.2886,34.2616),(31.4149,34.2616))])
    route('VDD_M',B,(25.6265,34.4515),(29.9515,34.4515),(30.5,35),(31.225,35))
    route('VDD_M',B,(33.2886,34.2616),(31.3634,34.2616),(31.225,34.4),(31.225,35))
    # 7/9: flash signals leave the right face normally before bending.
    remove('FLASH_MOSI',B)
    route('FLASH_MOSI',B,(35.5875,27.595),(36.6,27.595),(36.9009,27.2941),(36.9009,26.838))
    # Move the clock via slightly outward to leave a clean MOSI diagonal.
    for t in b.GetTracks():
        if isinstance(t,p.PCB_VIA) and t.GetNetname()=='FLASH_CLK':t.SetPosition(v((39.1,30.6417)))
    remove('FLASH_CLK',F)
    route('FLASH_CLK',F,(36.65,32.55),(37.1917,32.55),(39.1,30.6417))
    remove('FLASH_CLK',B)
    route('FLASH_CLK',B,(35.5875,28.865),(36.55,28.865),(37.2527,29.5677),(38.026,29.5677),(39.1,30.6417))
    # 8: normal exits at both rear VREG current links.
    remove('VREG',B,[((35,38.325),(36.888,40.213)),((36.888,40.213),(39.5276,40.213)),((40.4463,33),(40.175,33)),((42.2998,34.8535),(40.4463,33)),((42.2998,36.7876),(42.2998,34.8535))])
    route('VREG',B,(35,38.325),(35,39.1),(36.113,40.213),(39.5276,40.213))
    route('VREG',B,(40.175,33),(40.175,33.65),(40.625,34.1),(41.77,34.1),(42.2998,34.6298),(42.2998,36.7876))
    # 10: split the battery feed at the capacitor pad, removing the external T.
    remove('VBAT',B)
    route('VBAT',B,(38.025,46),(35.6484,46),(35.3812,45.7328),(33.6359,45.7328),(30,42.0969),(30,41.825))
    route('VBAT',B,(38.025,46),(38.025,48.3),(37.35,48.975),(36.8,48.975))

if __name__=='__main__':
    import wx
    from pathlib import Path
    app=wx.App(False)
    out=Path(__file__).resolve().parents[1]/'nami-compact'
    b=p.LoadBoard(str(out/'nami.kicad_pcb'))
    refine(b)
    p.ZONE_FILLER(b).Fill(b.Zones())
    p.SaveBoard(str(out/'nami.kicad_pcb'),b)
    print('Applied explicit C0 routing review edits')
