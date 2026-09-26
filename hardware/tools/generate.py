#!/usr/bin/env python3
"""Generate editable KiCad bench schematics and a connectivity manifest.

Requires sexpdata and installed KiCad libraries. Does not overwrite a routed PCB.
"""
import copy, csv, json, math, os, uuid
from pathlib import Path
import sexpdata as sx

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'nami-rev-a'
LIB = Path(os.environ.get('KICAD_SYMBOL_DIR', '/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols'))
S = sx.Symbol
def uid(key): return str(uuid.uuid5(uuid.NAMESPACE_URL, 'nami-reva/' + key))
def field(a,k): return next((x for x in a if isinstance(x,list) and str(x[0])==k),None)
def children(a,k): return [x for x in a if isinstance(x,list) and str(x[0])==k]
cache={}
def library(lib):
    if lib not in cache:
        cache[lib]={x[1]:x for x in sx.loads((LIB/(lib+'.kicad_sym')).read_text()) if isinstance(x,list) and str(x[0])=='symbol'}
    return cache[lib]
def resolve(lib,name):
    a=copy.deepcopy(library(lib)[name]); ext=field(a,'extends')
    if ext:
        parent=resolve(lib,ext[1]); old=parent[1]
        props={p[1]:p for p in children(parent,'property')}
        props.update({p[1]:p for p in children(a,'property')})
        a=[S('symbol'), name]+[p for p in parent[2:] if not (isinstance(p,list) and str(p[0])=='property')]+list(props.values())
        for b in children(a,'symbol'): b[1]=name+b[1][len(old):]
    return a
def eff(size=1.0,hide=False):
    a=[S('effects'),[S('font'),[S('size'),size,size]]]
    if hide:a.append([S('hide'),S('yes')])
    return a
def prop(name,value,x,y,hide=False):return [S('property'),name,value,[S('at'),x,y,0],eff(1.0,hide)]
parts=[]
def add(sheet,ref,lib,value,nets,at,fp=None,unit=1,mpn='',note='',dnp=False,board=True):
    l,n=lib.split(':'); sym=resolve(l,n)
    properties={p[1]:p[2] for p in children(sym,'property')}
    pins=[]
    for sub in children(sym,'symbol'):
        u=int(sub[1].split('_')[-2]); style=int(sub[1].split('_')[-1])
        if u in [0,unit] and style in [0,1]:pins+=children(sub,'pin')
    nets={str(k):v for k,v in nets.items()}
    obj=dict(sheet=sheet,ref=ref,lib=lib,value=value,nets=nets,at=at,fp=fp or properties.get('Footprint',''),unit=unit,mpn=mpn or (value if lib.split(':')[0] in ['Amplifier_Operational','RF_Module','Memory_Flash','Regulator_Switching'] else ''),note=note,dnp=dnp,board=board,pins=pins)
    parts.append(obj);return obj
RFP='Resistor_SMD:R_0805_2012Metric'
CFP='Capacitor_SMD:C_0805_2012Metric'
def r(sh,ref,val,a,b,xy,**kw):return add(sh,ref,'Device:R',val,{1:a,2:b},xy,RFP,**kw)
def c(sh,ref,val,a,b,xy,**kw):return add(sh,ref,'Device:C',val,{1:a,2:b},xy,CFP,**kw)
def conn(sh,ref,n,val,nets,xy):return add(sh,ref,'Connector_Generic:Conn_01x%02d'%n,val,nets,xy,'Connector_PinHeader_2.54mm:PinHeader_1x%02d_P2.54mm_Vertical'%n)
def flag(sh,ref,net,xy):return add(sh,ref,'power:PWR_FLAG','PWR_FLAG',{1:net},xy,board=False)
def tp(sh,ref,net,xy):return add(sh,ref,'Connector:TestPoint',net,{1:net},xy,'TestPoint:TestPoint_Pad_D1.5mm')

# Power: one external battery OR bench source; no on-board charger.
conn('power','J2',2,'BATTERY / BENCH 2.0-3.3V',{1:'BAT_IN',2:'GND'},(25.4,40.64))
r('power','R1','0R / AMMETER','BAT_IN','VBAT',(50.8,40.64),note='Remove to insert current meter; never attach two supplies')
flag('power','#FLG01','VBAT',(63.5,25.4));flag('power','#FLG02','GND',(76.2,25.4))
add('power','C1','Device:C','100u 6.3V X5R',{1:'VBAT',2:'GND'},(76.2,48.26),'Capacitor_SMD:C_1210_3225Metric',mpn='GRM32ER60J107ME20L',note='Verify effective capacitance and cold-cell startup')
c('power','C2','10u 10V X7R','VBAT','GND',(99.06,48.26))
add('power','U1','Regulator_Switching:TPS63900','TPS63900DSKR',{1:'VBAT',2:'GND',3:'CFG1',4:'CFG2',5:'CFG3',6:'VREG',7:'LX2',8:'GND',9:'LX1',10:'VBAT',11:'GND'},(144.78,55.88),'Package_SON:WSON-10-1EP_2.5x2.5mm_P0.5mm_EP1.2x2mm',mpn='TPS63900DSKR')
add('power','L1','Device:L','2.2uH >=2A',{1:'LX1',2:'LX2'},(109.22,83.82),'Inductor_SMD:L_Coilcraft_XAL4020-XXX',mpn='XAL4020-222MEC',note='Verify land pattern before procurement')
r('power','R2','0R','CFG1','GND',(187.96,40.64))
r('power','R3','1.87k 1%','CFG2','GND',(210.82,40.64),note='25mA input-current limit; measure startup and flash load')
r('power','R4','13.3k 1%','CFG3','GND',(233.68,40.64),note='SEL=0 selects 3.0V')
add('power','C3','Device:C','47u 6.3V X5R',{1:'VREG',2:'GND'},(187.96,81.28),'Capacitor_SMD:C_1210_3225Metric')
c('power','C4','100n 10V X7R','VREG','GND',(213.36,81.28))
for i,net,x in [(5,'VDD_M',45.72),(6,'VDD_A',111.76),(7,'VDD_F',177.8)]:
    r('power','R'+str(i),'0R / CURRENT LINK','VREG',net,(x,121.92))
    if net != 'VDD_M': flag('power','#FLG'+str(i+2),net,(x+20.32,116.84))
tp('power','TP1','VREG',(238.76,116.84));tp('power','TP2','GND',(261.62,116.84))

# Analog. Burden is in a permanent CT harness, not across removable board connector.
conn('analog','J1',2,'CT HARNESS',{1:'CT_P',2:'VMID'},(25.4,38.1))
r('analog','R8','1k','CT_P','SENSE',(55.88,38.1))
c('analog','C5','1n C0G','SENSE','VMID',(81.28,38.1))
add('analog','D1','Diode:BAV99','BAV199',{1:'GND',2:'VDD_A',3:'SENSE'},(111.76,38.1),mpn='BAV199,215',note='Low-leakage series diode pinout compatible with BAV99; not a mains barrier')
r('analog','R9','1M 0.1%','VDD_A','VMID_DIV',(35.56,88.9))
r('analog','R10','1M 0.1%','VMID_DIV','GND',(60.96,88.9))
c('analog','C6','1u X7R','VMID_DIV','GND',(86.36,88.9))
opa='Amplifier_Operational:OPA2333xxD';opfp='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'
add('analog','U2',opa,'OPA2333AID',{1:'VMID_BUF',2:'VMID_BUF',3:'VMID_DIV'},(121.92,88.9),opfp,unit=1)
r('analog','R11','100R','VMID_BUF','VMID',(154.94,88.9))
c('analog','C7','1u X7R','VMID','GND',(180.34,88.9))
add('analog','U2',opa,'OPA2333AID',{5:'SENSE',6:'GAIN_FB',7:'HIGH_OUT'},(172.72,38.1),opfp,unit=2)
r('analog','R12','10k 0.1%','GAIN_FB','VMID',(210.82,35.56))
r('analog','R13','309k 0.1%','HIGH_OUT','GAIN_FB',(241.3,35.56),note='Gain 31.9 relative to VMID')
r('analog','R14','1k','SENSE','ADC_LOW',(38.1,137.16))
c('analog','C8','22n C0G','ADC_LOW','VMID',(68.58,137.16))
r('analog','R15','1k','HIGH_OUT','ADC_HIGH',(106.68,137.16))
c('analog','C9','47n C0G','ADC_HIGH','VMID',(139.7,137.16))
add('analog','U2',opa,'OPA2333AID',{4:'GND',8:'VDD_A'},(215.9,93.98),opfp,unit=3)
c('analog','C10','100n X7R','VDD_A','GND',(246.38,93.98))
tp('analog','TP3','SENSE',(177.8,137.16));tp('analog','TP4','VMID',(208.28,137.16));tp('analog','TP5','ADC_HIGH',(241.3,137.16))

# Radio/digital, A3 landscape.
radio={1:'GND',2:'GND',15:'GND',28:'VDD_M',30:'VDD_M',31:'VDD_M',32:'GND',33:'GND',55:'GND',11:'ADC_LOW',9:'ADC_HIGH',20:'VMID',17:'XL1',18:'XL2',51:'SWDIO',53:'SWDCLK',40:'RESET_N',36:'FLASH_CS_N',37:'FLASH_CLK',38:'FLASH_MISO',39:'FLASH_MOSI',41:'PAIR_N',42:'LED_DRIVE',21:'BAT_MON'}
add('digital','U3','RF_Module:MDBT50Q-1MV2','MDBT50Q-1MV2',radio,(68.58,91.44))
c('digital','C11','10u 10V X7R','VDD_M','GND',(127,38.1));c('digital','C12','100n X7R','VDD_M','GND',(152.4,38.1))
add('digital','Y1','Device:Crystal','32.768kHz CL=7pF',{1:'XL1',2:'XL2'},(134.62,73.66),'Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm',mpn='ABS07-32.768KHZ-7-T',note='9pF capacitors assume approximately 2.5pF stray; characterize')
c('digital','C13','9p C0G','XL1','GND',(116.84,101.6));c('digital','C14','9p C0G','XL2','GND',(152.4,101.6))
add('digital','U4','Memory_Flash:W25Q128JVS','W25Q128JVSIQ',{1:'FLASH_CS_N',2:'FLASH_MISO',3:'FLASH_WP_N',4:'GND',5:'FLASH_MOSI',6:'FLASH_CLK',7:'FLASH_HOLD_N',8:'VDD_F'},(233.68,66.04),mpn='W25Q128JVSIQ')
r('digital','R16','100k','VDD_F','FLASH_CS_N',(203.2,111.76));r('digital','R17','100k','VDD_F','FLASH_WP_N',(236.22,111.76));r('digital','R18','100k','VDD_F','FLASH_HOLD_N',(269.24,111.76))
c('digital','C15','100n X7R','VDD_F','GND',(279.4,55.88));c('digital','C16','10u 10V X7R','VDD_F','GND',(307.34,55.88))
add('digital','J3','Connector:Conn_ARM_JTAG_SWD_10','SWD 1.27mm',{1:'VDD_M',2:'SWDIO',3:'GND',4:'SWDCLK',5:'GND',9:'GND',10:'RESET_N'},(350.52,68.58),'Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical',note='VTref is sense only; debugger must not power board')
add('digital','SW1','Switch:SW_Push','PAIR',{1:'PAIR_N',2:'GND'},(76.2,172.72),'Button_Switch_THT:SW_PUSH_6mm')
r('digital','R19','100k','VDD_M','PAIR_N',(40.64,172.72))
add('digital','SW2','Switch:SW_Push','RESET',{1:'RESET_N',2:'GND'},(152.4,172.72),'Button_Switch_THT:SW_PUSH_6mm')
r('digital','R20','100k','VDD_M','RESET_N',(116.84,172.72))
r('digital','R21','4.7k','LED_DRIVE','LED_A',(210.82,172.72))
add('digital','D2','Device:LED','GREEN',{1:'GND',2:'LED_A'},(243.84,172.72),'LED_SMD:LED_0805_2012Metric',note='Normally off')
r('digital','R22','2M 1%','VBAT','BAT_MON',(294.64,157.48));r('digital','R23','1M 1%','BAT_MON','GND',(327.66,157.48));c('digital','C17','100n X7R','BAT_MON','GND',(358.14,157.48))
conn('digital','J4',4,'ANALOG DEBUG',{1:'ADC_LOW',2:'ADC_HIGH',3:'VMID',4:'GND'},(299.72,210.82))

def pins_for(p):
    seen=set()
    for pin in p['pins']:
        n=field(pin,'number')[1];at=field(pin,'at')
        key=tuple(at[1:3])
        if key in seen:continue
        seen.add(key)
        yield n,at,pin

def text(t,x,y,size=1.27):return [S('text'),t,[S('at'),x,y,0],eff(size),[S('uuid'),uid('text/'+t+'/'+str(x)+str(y))]]
notes={
'power':[("POWER / 3.0 V regulated / battery or bench supply",139.7,20.32,2),("U1: SEL grounded; CFG3=13.3k selects 3.0V. CFG2=1.87k limits input to 25mA.",139.7,144.78,1.2),("Single external source only. R1/R5/R6/R7 permit subsystem current measurements.",139.7,152.4,1.2),("Battery chemistry: primary 3V cell, no charging. Validate pulse sag, startup and brownout.",139.7,160.02,1.2)],
'analog':[("CURRENT SENSING / external permanent 5-ohm burden",139.7,20.32,2),("J1 requires the separately documented SCT006 harness. Never remove its burden under current.",139.7,153,1.1),("20A:25mA CT gives 6.25mV/A. High gain=31.9. ADC differential against VMID.",139.7,159,1.1),("RC values are bench defaults; characterize CT/filter response, low-current noise and high-path recovery.",139.7,165,1.1)],
'digital':[("THREAD / BLE / STORAGE / SERVICE",205.74,20.32,2),("U3: normal-voltage mode; VDD, VDDH and DCCH tied together. VBUS grounded; D+/D- unused.",205.74,241.3,1.2),("P0.02/03/04 = low/high/midpoint. Differential SAADC at +/-0.6V; start at 32768 samples/s per range.",205.74,248.92,1.2),("Configure P0.18 as RESET in UICR. Enable REG1 DC/DC. Keep radio antenna copper-free on all layers.",205.74,256.54,1.2)]}

# The CT harness is an off-board assembly, included as a fifth schematic page.
conn('harness','J101',2,'SCT006 SECONDARY / SOLDER',{1:'HEAD_P',2:'HEAD_N'},(40.64,66.04))
r('harness','R101','10R 0.1%','HEAD_P','HEAD_N',(91.44,66.04),note='Permanently solder directly across CT secondary at sensing head')
r('harness','R102','10R 0.1%','HEAD_P','HEAD_N',(129.54,66.04),note='Parallel with R101: total 5.00 ohms')
conn('harness','J102',2,'TO MAIN J1 / PIGTAIL',{1:'HEAD_P',2:'HEAD_N'},(195.58,66.04))
for part in parts:
    if part['sheet']=='harness':part['board']=False
notes['harness']=[('PERMANENT CT HARNESS / OFF-BOARD ASSEMBLY',139.7,20.32,2),('SCT006 20A:25mA. R101 and R102 form a permanent 5.00-ohm burden.',139.7,109.22,1.3),('J101 represents solder joints, NOT a removable connector. Insulate and strain-relieve the assembly.',139.7,119.38,1.1),('J102 pin 1 -> board J1 pin 1; J102 pin 2 -> board J1 pin 2 (VMID).',139.7,129.54,1.1),('Do not add a second burden on the main PCB. Verify factory secondary protection on the ordered CT.',139.7,139.7,1.1),('This assembly never connects electrically to the monitored primary conductor.',139.7,149.86,1.1)]

rootid=uid('root')
sheetids={k:uid('sheet/'+k) for k in notes}
def write_sheet(sh):
    selected=[p for p in parts if p['sheet']==sh]
    libs={}
    for p in selected:
        if p['lib'] not in libs:
            lib,name=p['lib'].split(':'); a=resolve(lib,name);a[1]=p['lib'];libs[p['lib']]=a
    sid=uid('schematic/'+sh)
    doc=[S('kicad_sch'),[S('version'),20250114],[S('generator'),'eeschema'],[S('uuid'),sid],[S('paper'),'A3' if sh=='digital' else 'A4'],[S('title_block'),[S('title'),'Nami Rev A - '+sh],[S('date'),'2026-09-26'],[S('rev'),'A0 BENCH']],[S('lib_symbols')]+list(libs.values())]
    for n in notes[sh]:doc.append(text(*n))
    for p in selected:
        x,y=p['at'];pts=list(pins_for(p));maxy=max(float(a[2]) for _,a,_ in pts)
        if p['ref']=='U1': maxy += 5.08
        symid=uid('part/'+p['ref']+'/unit'+str(p['unit']))
        a=[S('symbol'),[S('lib_id'),p['lib']],[S('at'),x,y,0],[S('unit'),p['unit']],[S('in_bom'),S('no' if p['ref'].startswith('#') else 'yes')],[S('on_board'),S('yes' if p['board'] else 'no')],[S('dnp'),S('yes' if p['dnp'] else 'no')],[S('uuid'),symid],prop('Reference',p['ref'],x+6.35,y-maxy-5.08,p['ref'].startswith('#')),prop('Value',p['value'],x+6.35,y-maxy-2.54,p['ref'].startswith('#')),prop('Footprint',p['fp'],x,y,True),prop('Datasheet','',x,y,True),prop('MPN',p['mpn'],x,y,True),prop('DesignNote',p['note'],x,y,True)]
        for pin in p['pins']:a.append([S('pin'),field(pin,'number')[1],[S('uuid'),uid(symid+'/pin/'+field(pin,'number')[1])]])
        a.append([S('instances'),[S('project'),'nami',[S('path'),'/'+rootid+'/'+sheetids[sh],[S('reference'),p['ref']],[S('unit'),p['unit']]]]])
        doc.append(a)
        for num,at,pin in pts:
            px,py=round(x+float(at[1]),4),round(y-float(at[2]),4);angle=int(at[3]);net=p['nets'].get(num)
            if net is None:
                doc.append([S('no_connect'),[S('at'),px,py],[S('uuid'),uid(symid+'/nc/'+num)]])
                continue
            dx,dy=-math.cos(math.radians(angle)),math.sin(math.radians(angle))
            ex,ey=round(px+dx*5.08,4),round(py+dy*5.08,4)
            doc.append([S('wire'),[S('pts'),[S('xy'),px,py],[S('xy'),ex,ey]],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('uuid'),uid(symid+'/wire/'+num)]])
            doc.append([S('global_label'),net,[S('shape'),S('bidirectional')],[S('at'),ex,ey,angle],eff(.9),[S('uuid'),uid(symid+'/label/'+num)]])
    doc.append([S('embedded_fonts'),S('no')]);(OUT/(sh+'.kicad_sch')).write_text(sx.dumps(doc)+'\n')
for sh in notes:write_sheet(sh)
doc=[S('kicad_sch'),[S('version'),20250114],[S('generator'),'eeschema'],[S('uuid'),rootid],[S('paper'),'A3'],[S('title_block'),[S('title'),'Nami - Rev A bench prototype'],[S('date'),'2026-09-26'],[S('rev'),'A0']],[S('lib_symbols')]]
doc+=[text('NAMI / AC CURRENT MONITOR',205.74,25,3),text('Thread + BLE | SCT006 | 16 MiB local history',205.74,36,1.8),text('ENGINEERING PROTOTYPE - ISOLATED LOW-VOLTAGE BENCH USE',205.74,49,1.5)]
for i,sh in enumerate(notes):
    x=25.4+i*88.9;y=71.12
    doc.append([S('sheet'),[S('at'),x,y],[S('size'),71.12,38.1],[S('stroke'),[S('width'),.1524],[S('type'),S('default')]],[S('fill'),[S('color'),0,0,0,0]],[S('uuid'),sheetids[sh]],prop('Sheetname',sh.upper(),x+35.56,y-2.54),prop('Sheetfile',sh+'.kicad_sch',x+35.56,y+40.64),[S('instances'),[S('project'),'nami',[S('path'),'/'+rootid,[S('page'),str(i+2)]]]]])
doc+=[text('External sensor harness: SCT006 20A:25mA + permanent 5.00-ohm burden at the clamp.',205.74,132,1.2),text('No mains conductors terminate on this board. Battery/bench source connects at J2.',205.74,140,1.2),text('Schematic and routed PCB are review artifacts. See README for verification and release status.',205.74,148,1.2),[S('sheet_instances'),[S('path'),'/',[S('page'),'1']]],[S('embedded_fonts'),S('no')]]
(OUT/'nami.kicad_sch').write_text(sx.dumps(doc)+'\n')
# Manifest ties physical pins directly to schematic connections for independent netlist checks.
physical={}
for p in parts:
    if not p['board']:continue
    if p['ref'] not in physical:
        physical[p['ref']]={k:v for k,v in p.items() if k not in ['pins','at','unit','nets']}
        physical[p['ref']]['uuid']=uid('part/'+p['ref']+'/unit1');physical[p['ref']]['nets']={};physical[p['ref']]['sheet_path']='/'+rootid+'/'+sheetids[p['sheet']]
    physical[p['ref']]['nets'].update(p['nets'])
(OUT/'connectivity.json').write_text(json.dumps(physical,indent=2)+'\n')
with (OUT/'exports/bom.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['Reference','Value','MPN','Footprint','DNP','Note'])
    for ref,p in physical.items():w.writerow([ref,p['value'],p['mpn'],p['fp'],p['dnp'],p['note']])
# Minimal project; KiCad fills editor preferences when opened.
project={'meta':{'filename':'nami.kicad_pro','version':1},'net_settings':{'classes':[{'name':'Default','clearance':0.2,'track_width':0.25,'via_diameter':0.6,'via_drill':0.3}],'version':3},'board':{'design_settings':{'rules':{'min_clearance':0.15,'min_track_width':0.15,'min_via_diameter':0.5,'min_through_hole_diameter':0.3},'rule_severities':{'silk_over_copper':'warning'}}}}
(OUT/'nami.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')
print('Generated',len(physical),'physical components and five schematic sheets')
