#!/usr/bin/python
#-*- coding: utf-8 -*-

import os.path
import sys
import argparse
from shutil import copyfile
from osgeo import ogr
import vector_functions as vf
import NomenclatureHarmonisation as nh
import AddFieldID
import DeleteField
import AddFieldArea
import DeleteDuplicateGeometries
import BufferOgr
import MultiPolyToPoly
import SelectBySize

def traitEchantillons(shapefile, outfile, outpath, areapix, bufferdist, tmp, fieldout, csvfile = 1, delimiter = 1, fieldin = 1):

    # copy input shapefile into the outpath folder
    basefile = os.path.splitext(os.path.basename(shapefile))[0]
    newshapefile = outpath + '/' + basefile + '.shp'
    vf.copyShapefile(shapefile, newshapefile):

    # Table to store intermediate files paths
    intermediate = []

    intermediate.append(newshapefile)

    if csvfile != 1:
        # manage nomenclature (field CODE)
        nh.harmonisationCodeIota(newshapefile, csvfile, delimiter, fieldin, fieldout)

    # manage fields of shapefile
    manageFieldShapefile(newshapefile, fieldout, areapix)

    # Geometry validation 
    shapefile = vf.checkValidGeom(newshapefile)

    # Empty geometry identification
    try:
        outShapefile = vf.checkEmptyGeom(newshapefile)
        print 'Check empty geometries succeeded'
    except Exception as e:
        print 'Check empty geometries did not work for the following error :'
        print e   

    # Duplicate geometries
    outnoDuplicatesShapefile = DeleteDuplicateGeometries.DeleteDupGeom(outShapefile)
    
    intermediate.append(outnoDuplicatesShapefile)
    
    # Apply erosion (negative buffer)
    outbuffer = os.path.splitext(outnoDuplicatesShapefile)[0] + '_buff{}'.format(bufferdist) + '.shp'
    intermediate.append(outbuffer)
    try:
        BufferOgr.bufferPoly(outnoDuplicatesShapefile, outbuffer, bufferdist)
        print 'Negative buffer of {} m succeeded'.format(bufferdist) 
    except Exception as e:
        print 'Negative buffer did not work for the following error :'
        print e    

    # Multipolygones to single polygones
    outmultisingle = os.path.splitext(outnoDuplicatesShapefile)[0] + '_buff{}'.format(bufferdist) + '_sp.shp'
    intermediate.append(outmultisingle)
    try:
        MultiPolyToPoly.multipoly2poly(outbuffer, outmultisingle)
        print 'Conversion of multipolygons shapefile to single polygons succeeded'
    except Exception as e:
        print 'Conversion of multipolygons shapefile to single polygons did not work for the following error :'
        print e

    # FID creation
    fieldList = vf.getFields(outmultisingle)
    if 'ID' not in fieldList:
        AddFieldID.addFieldID(outmultisingle)
    else:
        print 'Field ID already exists'

    # Area field refresh
    try:
        AddFieldArea.addFieldArea(outmultisingle, areapix)
    except Exception as e:
        print 'Add an Area field did not work for the following error :'
        print e

    # Filter by Area
    outShapefile =  os.path.splitext(outnoDuplicatesShapefile)[0] + '_buff{}'.format(bufferdist) + '_sp_{}m2.shp'.format(areapix)
    try:
        SelectBySize.selectBySize(outmultisingle, 'Area', 1, outShapefile)
        print 'Selection by size upper {}m2 succeeded'.format(areapix)
    except Exception as e:
        print 'Selection by size did not work for the following error :'
        print e

    # copy output file
    basefile = os.path.splitext(outfile)[0]
    for root, dirs, files in os.walk(outpath):
        for name in files:
            if os.path.splitext(name)[0] ==  os.path.splitext(os.path.basename(outShapefile))[0]:
                ext = os.path.splitext(name)[1]
                copyfile(outpath + '/' + name, folder + '/' + basefile + ext)
    
    print 'Samples vector file "{}" for classification are now ready'.format(folder + '/' + basefile + '.shp')

    if tmp:
        driver = ogr.GetDriverByName('ESRI Shapefile')
        for fileinter in intermediate:
            if os.path.exists(fileinter):
                driver.DeleteDataSource(fileinter)
                print 'Intermediate file {} deleted'.format(fileinter)
    else:
        print 'Intermediate files are preserved in folder {}'.format(os.path.dirname(os.path.realpath(intermediate[0])))

def manageFieldShapefile(shapefile, fieldout, areapix):
  
    # existing fields
    fieldList = vf.getFields(shapefile)
    fieldList.remove(fieldout)
    
    # FID creation
    if 'ID' not in fieldList:
        AddFieldID.addFieldID(shapefile)
    else:
        fieldList.remove('ID')

    # Area field creation
    if 'Area' in fieldList:
        DeleteField.deleteField(shapefile, 'Area')
        AddFieldArea.addFieldArea(shapefile, areapix)
        fieldList.remove('Area')
    else:
        AddFieldArea.addFieldArea(shapefile, areapix)        

    # Suppression des champs initiaux
    for field in fieldList:
        DeleteField.deleteField(shapefile, field)


if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "This function treats input vector file (-s)" \
                                         "to use it for training / validation samples of classification" \
                                         "proccess. Output vector file (-o) will be stored in the same folder"\
                                         "than input vector file and intermediate files in a specified folder (-tmppath)")
        parser.add_argument("-s", dest="shapefile", action="store", \
                            help="Input shapefile", required = True)
        parser.add_argument("-o", dest="output", action="store", \
                            help="Output shapefile name (store in the same folder than input shapefile)", required = True)
        parser.add_argument("-tmppath", dest="tmppath", action="store", \
                            help="path to store intermediate layers", required = True)
        parser.add_argument("-csv", dest="csv", action="store", \
                            help="CSV or recode rules")
        parser.add_argument("-d", dest="delimiter", action="store", \
                            help="CSV delimiter")
        parser.add_argument("-if", dest="ifield", action="store", \
                            help="Existing field for rules condition") 
        parser.add_argument("-of", dest="ofield", action="store", \
                            help="Field to create and populate / Field storing landcover code", required = True)
        parser.add_argument("-areapix", dest="areapix", action="store", \
                            help="Pixel area of the image used for classification", required = True)
        parser.add_argument("-buffer", dest="buffer", action="store", \
                            help="Buffer distance to erode polygon (positive value)", required = True)
        parser.add_argument("-recode", action='store_true', help="Harmonisation of nomenclature with specific classes codes" \
                            "(please provide CSV recode rules, CSV delimiter, Existing field and Field to create)", default = False)
        parser.add_argument("-notmp", action='store_true', help="No Keeping intermediate files", default = False)
	args = parser.parse_args()

        if args.recode:
            if (args.csv is None) or (args.delimiter is None) or (args.ofield is None):
                print 'Please provide CSV recode rules (-csv), CSV delimiter (-d) and Field to populate (-of)'
                sys.exit(-1)
            else:
                if int(args.buffer) >= 0:
                    print args.buffer
                    print "Buffer distance must be negative"
                    sys.exit(-1)
                else:
                    traitEchantillons(args.shapefile, args.output, args.tmppath, args.areapix, args.buffer, args.notmp, \
                                      args.ofield, args.csv, args.delimiter, args.ifield)
        else:
            traitEchantillons(args.shapefile, args.output, args.tmppath, args.areapix, args.buffer, args.notmp, args.ofield)
