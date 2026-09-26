"""Conventional wired analog sheet; preserves symbol identities and circuit nets."""
import math
from collections import Counter
import sexpdata as sx
S=sx.Symbol
def field(a,k):return next((v for v in a if isinstance(v,list) and str(v[0])==k),None)
def redraw(doc,uid):
    # Sheet layout is presentation only. The exported netlist verifies equivalence.
    field(doc,'paper')[1]='A3'
    doc[:]=[x for x in doc if not(isinstance(x,list) and str(x[0]) in ['wire','global_label','label','junction','text'])]
    symbols={}
    for a in doc:
        if isinstance(a,list) and str(a[0])=='symbol':
            ref=next(v[2] for v in a if isinstance(v,list) and str(v[0])=='property' and v[1]=='Reference')
            symbols[ref,int(field(a,'unit')[1])]=a
    locations={('J1',1):(30,80,180),('R8',1):(60,80,90),('C5',1):(90,97,0),('D1',1):(120,60,0),
      ('U2',2):(150,82.54,0),('R13',1):(165,112.5,270),('R12',1):(130,130,0),
      ('R14',1):(215,40,90),('C8',1):(240,55,0),('R15',1):(215,82.54,90),('C9',1):(240,100,0),
      ('TP3',1):(80,75,0),('TP5',1):(260,75,0),
      ('R9',1):(50,180,0),('R10',1):(50,207,0),('C6',1):(75,207,0),
      ('U2',1):(120,194.54,0),('R11',1):(165,194.54,90),('C7',1):(185,209,0),('TP4',1):(205,190,0),
      ('U2',3):(260,193,0),('C10',1):(290,193,0)}
    libs={x[1]:x for x in field(doc,'lib_symbols')[1:]};pins={}
    for key,a in symbols.items():
        x,y,angle=locations[key];field(a,'at')[1:]=[x,y,angle]
        ref,unit=key; lib=libs[field(a,'lib_id')[1]]
        for sub in lib:
            if not isinstance(sub,list) or str(sub[0])!='symbol':continue
            if int(sub[1].split('_')[-2]) not in [0,unit]:continue
            for pin in sub:
                if not isinstance(pin,list) or str(pin[0])!='pin':continue
                num=field(pin,'number')[1];px,py=map(float,field(pin,'at')[1:3]);r=math.radians(angle)
                pins[ref,num]=(round(x+px*math.cos(r)-py*math.sin(r),4),round(y-px*math.sin(r)-py*math.cos(r),4))
        for prop in [v for v in a if isinstance(v,list) and str(v[0])=='property']:
            if prop[1] not in ['Reference','Value']:continue
            n=0 if prop[1]=='Reference' else 1
            if ref.startswith(('R','C')) and angle in [90,270]:at=(x,y-5+2.6*n)
            elif ref.startswith(('R','C')):at=(x+8,y-1.3+2.6*n)
            elif ref=='U2' and unit<3:at=(x+2,y-10+2.6*n)
            elif ref=='U2':at=(x+8,y-1.3+2.6*n)
            elif ref=='J1':at=(x,y+8+2.6*n)
            else:at=(x+5,y-6+2.6*n)
            field(prop,'at')[1:]=[*at,90 if angle in [90,270] else 0]
    def pin(ref,n):return pins[ref,str(n)]
    segments=[];labels=[]
    def wire(*pts):segments.extend(zip(pts,pts[1:]))
    def label(net,point,angle=0):
        labels.append(point);doc.append([S('global_label'),net,[S('shape'),S('bidirectional')],[S('at'),*point,angle],[S('effects'),[S('font'),[S('size'),1,1]]],[S('uuid'),uid('analog-label/'+net+str(point))]])
    def stub(ref,num,net,point):wire(pin(ref,num),point);label(net,point)
    def note(t,x,y,size=1.4):doc.append([S('text'),t,[S('at'),x,y,0],[S('effects'),[S('font'),[S('size'),size,size]]],[S('uuid'),uid('analog-note/'+t)]])
    wire(pin('J1',1),(45,80),pin('R8',1));label('CT_P',(45,80));stub('J1',2,'VMID',(40,77.46))
    wire(pin('R8',2),(80,80),(90,80),(100,80),(120,80),pin('U2',5));wire((80,80),pin('TP3',1));label('SENSE',(80,80))
    wire((90,80),pin('C5',1));stub('C5',2,'VMID',(90,108))
    wire((120,80),pin('D1',3));stub('D1',1,'GND',(107,60));stub('D1',2,'VDD_A',(138,60))
    wire((100,80),(100,40),pin('R14',1));wire(pin('R14',2),(240,40),(265,40));label('ADC_LOW',(265,40),180)
    wire((240,40),pin('C8',1));stub('C8',2,'VMID',(240,65))
    wire(pin('U2',7),(185,82.54),pin('R15',1));label('HIGH_OUT',(185,82.54),180)
    wire(pin('R15',2),(240,82.54),(260,82.54),(265,82.54));wire((260,82.54),pin('TP5',1));label('ADC_HIGH',(265,82.54),180)
    wire((240,82.54),pin('C9',1));stub('C9',2,'VMID',(240,112))
    wire((185,82.54),(185,112.5),pin('R13',1));wire(pin('R13',2),(130,112.5),pin('R12',1))
    wire((130,112.5),(130,85.08),pin('U2',6));wire((130,112.5),(122,112.5));label('GAIN_FB',(122,112.5))
    stub('R12',2,'VMID',(130,140))
    stub('R9',1,'VDD_A',(50,167));wire(pin('R9',2),(50,192),pin('R10',1));stub('R10',2,'GND',(50,218))
    wire((50,192),(75,192),(95,192),pin('U2',3));wire((75,192),pin('C6',1));stub('C6',2,'GND',(75,218))
    wire((95,192),(95,184));label('VMID_DIV',(95,184))
    wire(pin('U2',1),(140,194.54),(147,194.54),pin('R11',1))
    wire(pin('U2',2),(100,197.08),(100,215),(140,215),(140,194.54))
    wire((147,194.54),(147,185));label('VMID_BUF',(147,185),180)
    wire(pin('R11',2),(185,194.54),(205,194.54),(220,194.54));label('VMID',(220,194.54),180)
    wire((185,194.54),pin('C7',1));stub('C7',2,'GND',(185,218));wire((205,194.54),pin('TP4',1))
    stub('U2',8,'VDD_A',(257.46,175));stub('U2',4,'GND',(257.46,211))
    stub('C10',1,'VDD_A',(290,175));stub('C10',2,'GND',(290,211))
    note('NAMI / ANALOG FRONT END',190,18,2.5)
    note('CURRENT SIGNAL / NON-INVERTING GAIN = 1 + 309k / 10k = 31.9',160,29,1.4)
    note('MIDPOINT REFERENCE / UNITY-GAIN BUFFER',120,157,1.6)
    note('SUPPLY DECOUPLING',277,160,1.4)
    note('Permanent 5-ohm burden stays at the CT head. J1 return is VMID, not GND.',160,239,1.3)
    note('Both ADC paths measure differentially against VMID. Nominal supply 3.0 V; midpoint 1.5 V.',160,247,1.3)
    # Split at every branch endpoint and add explicit junction dots.
    vertices=set(labels)|{a for a,z in segments}|{z for a,z in segments};edges=set()
    for a,z in segments:
        dx,dy=z[0]-a[0],z[1]-a[1];den=dx*dx+dy*dy
        if not den:continue
        pts=[q for q in vertices if abs((q[0]-a[0])*dy-(q[1]-a[1])*dx)<1e-5 and -1e-6<=((q[0]-a[0])*dx+(q[1]-a[1])*dy)/den<=1+1e-6]
        pts.sort(key=lambda q:((q[0]-a[0])*dx+(q[1]-a[1])*dy)/den)
        for f,t in zip(pts,pts[1:]):edges.add(tuple(sorted([f,t])))
    degree=Counter()
    for a,z in sorted(edges):
        degree[a]+=1;degree[z]+=1
        doc.append([S('wire'),[S('pts'),[S('xy'),*a],[S('xy'),*z]],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('uuid'),uid('analog-wire/'+str(a)+str(z))]])
    for point,n in degree.items():
        if n>=3:doc.append([S('junction'),[S('at'),*point],[S('diameter'),0],[S('color'),0,0,0,0],[S('uuid'),uid('analog-junction/'+str(point))]])
    # KiCad's standard 50-mil connection grid. Symbol pin offsets are integral
    # grid units, so snapping origins and explicit wire endpoints preserves nets.
    def snap_tree(a):
        if not isinstance(a,list):return
        if a and str(a[0]) in ['at','xy']:
            a[1]=round(round(float(a[1])/1.27)*1.27,4)
            a[2]=round(round(float(a[2])/1.27)*1.27,4)
        for child in a:snap_tree(child)
    for a in doc:
        if isinstance(a,list) and str(a[0])!='lib_symbols':snap_tree(a)
    return doc
