#!/usr/bin/env python3
"""Independent checks on KiCad-exported connectivity and analog calculations."""
import cmath, json, math
import os
from pathlib import Path
import xml.etree.ElementTree as ET
out=Path(__file__).resolve().parents[1]/('nami-compact' if os.environ.get('NAMI_VARIANT')=='compact' else 'nami-rev-a')
doc=ET.parse(out/'exports/nami-netlist.xml')
pin_net={}
for net in doc.findall('./nets/net'):
    for n in net.findall('node'):pin_net[n.attrib['ref'],n.attrib['pin']]=net.attrib['name']
expected={
 ('J1','1'):'CT_P',('J1','2'):'VMID',('J2','1'):'BAT_IN',('J2','2'):'GND',
 ('U1','1'):'VBAT',('U1','2'):'GND',('U1','5'):'CFG3',('U1','6'):'VREG',('U1','7'):'LX2',('U1','9'):'LX1',('U1','10'):'VBAT',('U1','11'):'GND',
 ('U2','1'):'VMID_BUF',('U2','2'):'VMID_BUF',('U2','3'):'VMID_DIV',('U2','4'):'GND',('U2','5'):'SENSE',('U2','6'):'GAIN_FB',('U2','7'):'HIGH_OUT',('U2','8'):'VDD_A',
 ('D1','1'):'GND',('D1','2'):'VDD_A',('D1','3'):'SENSE',
 ('U3','28'):'VDD_M',('U3','30'):'VDD_M',('U3','31'):'VDD_M',('U3','32'):'GND',('U3','11'):'ADC_LOW',('U3','9'):'ADC_HIGH',('U3','20'):'VMID',
 ('U3','17'):'XL1',('U3','18'):'XL2',('U3','40'):'RESET_N',('U3','51'):'SWDIO',('U3','53'):'SWDCLK',
 ('U3','37'):'FLASH_CLK',('U3','36'):'FLASH_CS_N',('U3','39'):'FLASH_MOSI',('U3','38'):'FLASH_MISO',
 ('U4','1'):'FLASH_CS_N',('U4','2'):'FLASH_MISO',('U4','3'):'FLASH_WP_N',('U4','4'):'GND',('U4','5'):'FLASH_MOSI',('U4','6'):'FLASH_CLK',('U4','7'):'FLASH_HOLD_N',('U4','8'):'VDD_F',
 ('R101','1'):'HEAD_P',('R101','2'):'HEAD_N',('R102','1'):'HEAD_P',('R102','2'):'HEAD_N'
}
for pin,net in expected.items():assert pin_net.get(pin)==net,(pin,pin_net.get(pin),net)
manifest=json.loads((out/'connectivity.json').read_text())
for ref,c in manifest.items():
    for num,net in c['nets'].items():assert pin_net.get((ref,num))==net,(ref,num,net)
for num in ['1','2','15','33','55']:assert pin_net['U3',num]=='GND'
for num in ['34','35']:assert pin_net['U3',num].startswith('unconnected-')
# 5-ohm CT burden, unloaded transformer approximation.
gain=1+309000/10000
v_per_a=5/800
assert math.isclose(v_per_a*20*3,.375)
assert v_per_a*20*3 < .6
assert v_per_a*.8*gain*3 < .5
assert 2*(10+2) < 1e6/32768 # two 10us acquisitions + nominal 2us conversions
assert 30*86400*4 < 16*1024*1024
rows=[]
for hz in [60,1000,16384]:
    s=2j*math.pi*hz
    z8=1/(s*22e-9)
    ys=s*1e-9+1/(1000+z8)
    sense=1/(1+1005*ys) # R8 + approximate burden source resistance
    lo=sense*z8/(1000+z8)
    hi=sense/(1+s/(2*math.pi*350000/gain))/(1+s*1000*47e-9)
    rows.append({'frequency_hz':hz,'low_magnitude_relative_to_dc':abs(lo),'high_magnitude_relative_to_dc_gain':abs(hi)})
result={'critical_pin_assertions':len(expected),'manifest_components_verified':len(manifest),'ct_volts_per_ampere':v_per_a,'high_gain':gain,'low_at_20A_rms_V':v_per_a*20,'high_at_0_1A_rms_V':v_per_a*.1*gain,'low_at_20A_CF3_peak_V':.375,'high_at_0_8A_CF3_peak_V':v_per_a*.8*gain*3,'high_rms_counts_at_0_1A_12bit_differential_range_0_6V':v_per_a*.1*gain/(1.2/4096),'filter_estimates':rows,'limitations':'Linear approximate RC + single-pole op-amp calculation only. No CT magnetizing model, op-amp macro-model, parasitics, noise, saturation, regulator simulation or measured hardware.'}
(out/'verification/connectivity-and-calculations.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
