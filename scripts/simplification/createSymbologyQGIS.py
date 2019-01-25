#!/usr/bin/env python
# encoding: utf-8

#!/usr/bin/python
#-*- coding: utf-8 -*-

# =========================================================================
#   Program:   iota2
#
#   Copyright (c) CESBIO. All rights reserved.
#
#   See LICENSE for details.
#
#   This software is distributed WITHOUT ANY WARRANTY; without even
#   the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the above copyright notices for more information.
#
# =========================================================================

from xml.etree import cElementTree as ET
from string import *


def getClassesFromQML(qml):
    
    tree = ET.parse(qml).getroot()

    classes = []
    nomenclature = []
    for item in tree.findall("renderer-v2"):
        for subitem in item.findall("categories"):
            for category in subitem :
                classes.append([category.attrib["symbol"], category.attrib["value"], category.attrib["label"]])

    for classe in classes:
        for item in tree.findall("renderer-v2"):        
            for subitem in item.findall("symbols"):
                for symbol in subitem:
                    if int(symbol.attrib["name"]) == int(classe[0]):
                        for layer in symbol.findall("layer"):
                            for prop in layer.findall("prop"):
                                if prop.attrib["k"] == "color":
                                    nomenclature.append([classe[2].encode("utf-8"), classe[1], [int(x) for x in prop.attrib["v"].split(",")[0:3]]])
                                    
    return nomenclature        
                
def createVectorQML(classeslist, outpath, codefield, outlinestyle = "SolidLine"):    

    intro = ET.Element("qgis")
    transp = ET.SubElement(intro,"transparencyLevelInt")
    transp.text = '255'
    classatr = ET.SubElement(intro, "classificationattribute")
    classatr.text = codefield
    typec = ET.SubElement(intro,"uniquevalue")
    classif = ET.SubElement(typec,"classificationfield")
    classif.text = codefield
    
    for elem in classeslist:
        symb = symbol(typec, codefield, elem)
        symb.creation(codefield, outlinestyle)
        
    # écriture du ficher style final
    fich_style = ET.ElementTree(intro)
    fich_style.write(outpath)

def createRasterQML(classeslist, outpath, classfield, nodata="0"):

    intro = ET.Element("qgis")
    pipe = ET.SubElement(intro,"pipe")
    rasterrenderer = ET.SubElement(pipe,"rasterrenderer", opacity="1", alphaBand="0", classificationMax="211", classificationMinMaxOrigin="CumulativeCutFullExtentEstimated", band="1", classificationMin="0", type="singlebandpseudocolor")
    rastershader = ET.SubElement(rasterrenderer,"rastershader")
    colorrampshader = ET.SubElement(rastershader,"colorrampshader", colorRampType="INTERPOLATED", clip="0")

    for elem in classeslist:
        symb = symbolraster(colorrampshader, classfield, elem)
        symb.creation(classfield)
        
    itemnd = ET.SubElement(colorrampshader,"item", alpha="0", value="%s"%(nodata), label="", color="#0000ff")
    brightnesscontrast = ET.SubElement(pipe,"brightnesscontrast", brightness="0", contrast="0")
    huesaturation = ET.SubElement(pipe,"huesaturation", colorizeGreen="128", colorizeOn="0", colorizeRed="255", colorizeBlue="128", grayscaleMode="0", saturation="0", colorizeStrength="100")
    rasterresampler = ET.SubElement(pipe,"rasterresampler", maxOversampling="2")
    tree = ET.ElementTree(intro)
    tree.write(outpath, xml_declaration=True, encoding='utf-8', method='xml')
        

class symbolraster:
    def __init__(self, colorrampshader, codefield, valeurs=[]):
        self.valeurs = valeurs
        self.cle = [codefield, 'classname', 'R', 'G', 'B', 'HEX']
        self.donnees = dict(zip(self.cle, self.valeurs))
        self.item = ET.SubElement(colorrampshader, "item")
        
    def creation(self, codefield):
        self.item.set("alpha", "255")
        self.item.set("value", str(self.donnees[codefield]))        
        self.item.set("label", self.donnees[self.cle[1]])        
        self.item.set("color", self.donnees['HEX'])        
        
class symbol:
    def __init__(self, typec, codefield, valeurs=[]):
        self.typec = typec
        self.valeurs = valeurs
        self.cle = [codefield, 'classname', 'R', 'G', 'B', 'HEX']
        self.donnees = dict(zip(self.cle, self.valeurs))
        self.symb = ET.SubElement(typec, "symbol")
        self.lower = ET.SubElement(self.symb, "lowervalue")
        self.upper = ET.SubElement(self.symb, "uppervalue")
        self.label = ET.SubElement(self.symb, "label")
        self.outline = ET.SubElement(self.symb, "outlinecolor")
        self.outsty = ET.SubElement(self.symb, "outlinestyle")
        self.outtail = ET.SubElement(self.symb, "outlinewidth")
        self.fillc = ET.SubElement(self.symb, "fillcolor")
        self.fillp = ET.SubElement(self.symb, "fillpattern")
        
    def creation(self, codefield, outlinestyle):
        self.lower.text = str(self.donnees[codefield])
        self.upper.text = str(self.donnees[codefield])
        self.label.text = self.donnees[self.cle[1]]
        self.outsty.text = outlinestyle
        self.outtail.text = "0.26"
        self.outline.set("red",self.donnees['R'])
        self.outline.set("green",self.donnees['G'])
        self.outline.set("blue",self.donnees['B'])
        self.fillc.set("red",self.donnees['R'])
        self.fillc.set("green",self.donnees['G'])
        self.fillc.set("blue",self.donnees['B'])
        self.fillp.text = "SolidPattern"

getClassesFromQML("/home/qt/thierionv/testvector.qml")
