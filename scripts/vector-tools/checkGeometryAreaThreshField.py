#!/usr/bin/python
#-*- coding: utf-8 -*-

import vector_functions as vf
import sys
import os
import AddFieldID
import AddField
import AddFieldArea
import DeleteField
import DeleteDuplicateGeometriesSqlite
import MultiPolyToPoly
import SelectBySize
import SimplifyPoly
import argparse

def checkGeometryAreaThreshField(shapefile, pixelArea, pix_thresh, outshape):

    tmpfile = []

    # Empty geometry identification
    try:
        outShapefileGeom = vf.checkEmptyGeom(shapefile)
        tmpfile.append(outShapefileGeom)        
        print 'Check empty geometries succeeded'
    except Exception as e:
        print 'Check empty geometries did not work for the following error :'
        print e  

    # suppression des doubles géométries
    DeleteDuplicateGeometriesSqlite.deleteDuplicateGeometriesSqlite(outShapefileGeom)

    # Suppression des multipolygons
    shapefileNoDupspoly = outShapefileGeom[:-4] + 'spoly' + '.shp'
    tmpfile.append(shapefileNoDupspoly)
    try:
        MultiPolyToPoly.multipoly2poly(outShapefileGeom, shapefileNoDupspoly)
        print 'Conversion of multipolygons shapefile to single polygons succeeded'
    except Exception as e:
        print 'Conversion of multipolygons shapefile to single polygons did not work for the following error :'
        print e

    # recalcul des superficies
    try:
        AddFieldArea.addFieldArea(shapefileNoDupspoly, pixelArea)       
    except Exception as e:
        print 'Add an Area field did not work for the following error :'
        print e

    # Attribution d'un ID
    fieldList = vf.getFields(shapefileNoDupspoly)
    if 'ID' in fieldList:
        DeleteField.deleteField(shapefileNoDupspoly, 'ID')
        AddFieldID.addFieldID(shapefileNoDupspoly)
    else:
        AddFieldID.addFieldID(shapefileNoDupspoly)


    # Filter by Area
    try:
        SelectBySize.selectBySize(shapefileNoDupspoly, 'Area', pix_thresh, outshape)
        print 'Selection by size upper {} pixel(s) succeeded'.format(pix_thresh)
    except Exception as e:
        print 'Selection by size did not work for the following error :'
        print e
            
    # Check geometry
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
