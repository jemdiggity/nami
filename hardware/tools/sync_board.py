#!/usr/bin/env python3
"""Synchronize schematic metadata and explicit NC nets without changing routing."""
from pathlib import Path
import xml.etree.ElementTree as ET
import pcbnew as p
import wx
app=wx.App(False)
out=Path(__file__).resolve().parents[1]/'nami-rev-a'
b=p.LoadBoard(str(out/'nami.kicad_pcb'));doc=ET.parse(out/'exports/nami-netlist.xml')
components={c.attrib['ref']:c for c in doc.findall('./components/comp')}
nc={}
for n in doc.findall('./nets/net'):
    name=n.attrib['name'].replace('/', '{slash}')
    if name.startswith('unconnected-'):
        net=b.FindNet(name)
        if not net:
            net=p.NETINFO_ITEM(b,name);b.Add(net)
        for node in n.findall('node'):nc[(node.attrib['ref'],node.attrib['pin'])]=net
for fp in b.GetFootprints():
    ref=fp.GetReference()
    if ref not in components:
        fp.SetAttributes(fp.GetAttributes() | p.FP_BOARD_ONLY | p.FP_EXCLUDE_FROM_BOM)
        continue
    c=components[ref];fp.SetValue(c.findtext('value'))
    fp.SetAttributes(fp.GetAttributes() & ~p.FP_EXCLUDE_FROM_BOM)
    for f in c.findall('./fields/field'):
        if f.attrib['name'] in ['MPN','DesignNote']:
            fp.SetField(f.attrib['name'],f.text or '')
            fp.GetField(f.attrib['name']).SetVisible(False)
    for pad in fp.Pads():
        if (ref,pad.GetNumber()) in nc:pad.SetNet(nc[(ref,pad.GetNumber())])
p.SaveBoard(str(out/'nami.kicad_pcb'),b)
print('Synchronized metadata and explicit no-connect nets')
