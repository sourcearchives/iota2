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
import checkGeometryAreaThreshField


def traitEchantillons(shapefile, outfile, outpath, areapix, pix_thresh, bufferdist, tmp, fieldout, csvfile = 1, delimiter = 1, fieldin = 1):

    # copy input shapefile into the outpath folder
    basefile = os.path.splitext(os.path.basename(shapefile))[0]
    newshapefile = outpath + '/' + basefile + '.shp'
    vf.copyShapefile(shapefile, newshapefile)

    # Table to store intermediate files paths
    intermediate = []

    intermediate.append(newshapefile)

    if csvfile != 1:
        # manage nomenclature (field CODE)
        nh.harmonisationCodeIota(newshapefile, csvfile, delimiter, fieldin, fieldout)

    # Refresh Id and Area fields, keep landcover field and delete other ones
    manageFieldShapefile(newshapefile, fieldout, areapix)

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

    outfile = os.path.dirname(shapefile) + '/' + outfile
    checkGeometryAreaThreshField.checkGeometryAreaThreshField(outbuffer, areapix, pix_thresh, outfile)
    
    print 'Samples vector file "{}" for classification are now ready'.format(outfile)

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
    fieldList = [x.lower() for x in fieldList]
    fieldList.remove(fieldout.lower())
    
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
        parser.add_argument("-areat", dest="pixthresh", action="store", \
                            help="Area threshold to select available polygons (in pixel)", required = True)
        parser.add_argument("-buffer", dest="buffer", action="store", \
                            help="Buffer distance to erode polygon (negative value)", required = True)
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
                    traitEchantillons(args.shapefile, args.output, args.tmppath, args.areapix, args.pixthresh, args.buffer, args.notmp, \
                                      args.ofield, args.csv, args.delimiter, args.ifield)
        else:
            traitEchantillons(args.shapefile, args.output, args.tmppath, args.areapix, args.pixthresh, args.buffer, args.notmp, args.ofield)
