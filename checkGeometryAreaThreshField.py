#!/usr/bin/python
#-*- coding: utf-8 -*-

import vector_functions as vf
import sys
import os
import AddFieldID
import AddField
import AddFieldArea
import DeleteField
import DeleteDuplicateGeometries
import MultiPolyToPoly
import SelectBySize
import argparse

def checkGeometryAreaThreshField(shapefile, pixelSize, pix_thresh, outshape):

    tmpfile = []
    
    pixelArea = float(pixelSize) * float(pixelSize) 
    
    # Verification de la géométrie
    vf.checkValidGeom(shapefile) 

    # suppression des doubles géométries
    shapefileNoDup = DeleteDuplicateGeometries.DeleteDupGeom(shapefile)
    tmpfile.append(shapefileNoDup)

    # Suppression des multipolygons
    shapefileNoDupspoly = shapefileNoDup[:-4] + 'spoly' + '.shp'
    MultiPolyToPoly.multipoly2poly(shapefileNoDup, shapefileNoDupspoly)
    tmpfile.append(shapefileNoDupspoly)

    # recalcul des superficies
    AddFieldArea.addFieldArea(shapefileNoDupspoly, pixelArea)

    # Attribution d'un ID
    fieldList = vf.getFields(shapefileNoDupspoly)
    if 'ID' in fieldList:
        DeleteField.deleteField(shapefileNoDupspoly, 'ID')
        AddFieldID.addFieldID(shapefileNoDupspoly)
    else:
        AddFieldID.addFieldID(shapefileNoDupspoly)

    # Selection en fonction de la surface des polygones
    SelectBySize.selectBySize(shapefileNoDupspoly, 'Area', pix_thresh, outshape)
        
    # Verification de la géométrie
    vf.checkValidGeom(outshape)

    # delete tmp file
    for fileDel in tmpfile:
        basefile = os.path.splitext(fileDel)[0]
        os.system('rm {}.*'.format(basefile))

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Manage shapefile : " \
        "1. Check geometry, "
        "2. Delete Duplicate geometries, "
        "3. Calulate Area, "
        "4. Harmonize ID field, "
        "5. Delete MultiPolygons")
        parser.add_argument("-s", dest="shapefile", action="store", \
                            help="Input shapefile", required = True)
        parser.add_argument("-p", dest="pixelSize", action="store", \
                            help="Pixel size", required = True)
        parser.add_argument("-at", dest="area", action="store", \
                            help="Area threshold in pixel unit", required = True)        
        parser.add_argument("-o", dest="outpath", action="store", \
                            help="ESRI Shapefile output filename and path", required = True)
	args = parser.parse_args()

        checkGeometryAreaThreshField(args.shapefile, args.pixelSize, args.area, args.outpath)
