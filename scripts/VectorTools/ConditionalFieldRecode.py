#!/usr/bin/python
#-*- coding: utf-8 -*-

import sys
import os
import argparse
import ogr
import vector_functions as vf

def conFieldRecode(shapefile, fieldin, fieldout, valin, valout):

    # open
    ds = ogr.Open(shapefile, 1)
    lyr = ds.GetLayer()
    
    # fields list
    fieldList = vf.getFields(lyr)
    try:
        indfield = fieldList.index(fieldin)
    except:
        raise Exception("The field {} does not exist in the input shapefile".format(fieldin), "You must choose one of these existing fields : {}".format(' / '.join(fieldList)))
        sys.exit(-1)

    # Field type
    inLayerDefn = lyr.GetLayerDefn()
    fieldTypeCode = inLayerDefn.GetFieldDefn(indfield).GetType()
    fieldType = inLayerDefn.GetFieldDefn(indfield).GetFieldTypeName(fieldTypeCode)
    if fieldout.lower() in [x.lower() for x in fieldList]:
        print "Field '{}' already exists. Existing value of {} field will be changed !!!".format(fieldout, fieldout)
    else:
        try:
            new_field = ogr.FieldDefn(fieldout, ogr.OFTInteger)
            lyr.CreateField(new_field)
            print "Field '{}' created".format(fieldout)
        except:
            print("Error while creating field '{}'".format(fieldout))
            sys.exit(-1)

    if fieldType != "String":
        lyr.SetAttributeFilter(fieldin + "=" + str(valin))
        if lyr.GetFeatureCount() != 0:
            try:
                changeValueField(lyr, fieldout, valout)
                print "Field '{}' populated with {} value".format(fieldout, valout)
            except:
                print "Error while populate field '{}'".format(fieldout)
                sys.exit(-1)
        else:
            print "The value '{}' does not exist for the field '{}'".format(valin, fieldin)
    else:
        lyr.SetAttributeFilter(fieldin + "=\'" + str(valin) + "\'")
        if lyr.GetFeatureCount() != 0:
            try:
                changeValueField(lyr, fieldout, valout)
                print "Field '{}' populated with {} value".format(fieldout, valout)
            except:
                print "Error while populate field '{}'".format(fieldout)
                sys.exit(-1)
        else:
            print "The value '{}' does not exist for the field '{}'".format(valin, fieldin)            
    
    ds.Destroy()

def changeValueField(layer, field, value):
    for feat in layer:
        layer.SetFeature(feat)
        feat.SetField(field, value)
        layer.SetFeature(feat)


if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Add a field of a shapefile " \
        "and populate it with a user defined value based on another field value condition")
        parser.add_argument("-s", dest="shapefile", action="store", \
                            help="Input shapefile", required = True)
        parser.add_argument("-if", dest="ifield", action="store", \
                            help="Existing field for value condition", required = True)
        parser.add_argument("-of", dest="ofield", action="store", \
                            help="Field to create and populate", required = True)
        parser.add_argument("-vc", dest="cvalue", action="store", \
                            help="Value condition on the input field", required = True) 
        parser.add_argument("-vp", dest="pvalue", action="store", \
                            help="Value to populate in the new field", required = True) 
	args = parser.parse_args()
        conFieldRecode(args.shapefile, args.ifield, args.ofield, args.cvalue, args.pvalue)

# python ConditionalFieldRecode.py -s /home/thierion/Documents/OSO/iota2/Echantillons/references_2016/preparation/OSO_2016_dynafor.shp -if ros2016 -of CODE -vc FF -vp 666
