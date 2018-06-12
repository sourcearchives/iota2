#!/usr/bin/python

from osgeo import ogr
import os
import sys
import argparse
import DeleteField
import vector_functions as vf

def changeName(filein, fieldin, fieldout):

        fieldList = vf.getFields(filein)
        if fieldout in fieldList:
                print "Field name {} already exists".format(fieldout)
                sys.exit(1)
        
        # Get input file and field characteritics 
	source = ogr.Open(filein, 1)
	layer = source.GetLayer()
	layer_defn = layer.GetLayerDefn()
        i = layer_defn.GetFieldIndex(fieldin)
        
        # Create the out field with in field characteristics 
        try:
                fieldTypeCode = layer_defn.GetFieldDefn(i).GetType()
                fieldWidth = layer_defn.GetFieldDefn(i).GetWidth()
                fieldPrecision = layer_defn.GetFieldDefn(i).GetPrecision()
        except:
                print "Field {} not exists in the input shapefile".format(fieldin)
                sys.exit(0)
        
        newField = ogr.FieldDefn(fieldout, fieldTypeCode)
        newField.SetWidth(fieldWidth)
        newField.SetPrecision(fieldPrecision)
        layer.CreateField(newField)

	for feat in layer:
		val =  feat.GetField(fieldin)
                layer.SetFeature(feat)
                feat.SetField(fieldout, val)
                layer.SetFeature(feat)

        layer = feat = newfield = source = None

        DeleteField.deleteField(filein, fieldin)

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Change exsiting field name " \
        "of an input shapefile")
        parser.add_argument("-s", dest="shapefile", action="store", \
                            help="Input shapefile", required = True)
        parser.add_argument("-fi", dest="fieldi", action="store", \
                            help="Field to rename", required = True)
        parser.add_argument("-fo", dest="fieldo", action="store", \
                            help="New field name", required = True)
	args = parser.parse_args()
        try:
                changeName(args.shapefile, args.fieldi, args.fieldo)
                print 'Field has been changed successfully'
        except Exception, err:
                print 'Problem occured in the process'
                sys.stderr.write('ERROR: %sn' % str(err))
                sys.exit(0)
