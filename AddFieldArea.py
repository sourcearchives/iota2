#!/usr/bin/python

from osgeo import ogr
import sys
import argparse
import os

def addFieldArea(filein, sizepix, precision='', width=''):
	source = ogr.Open(filein, 1)
	layer = source.GetLayer()
	layer_defn = layer.GetLayerDefn()
	field_names = [layer_defn.GetFieldDefn(i).GetName() for i in range(layer_defn.GetFieldCount())]
	if 'Area' in field_names:
                resp = True
                while [i for i, elem in enumerate(field_names) if 'Area' in elem] != [] and resp :
                        fieldsperim = [i for i, elem in enumerate(field_names) if 'Area' in elem]
                        response = raw_input('Do you want to delete field "%s" ? (yes (y) or no (n))'%(field_names[fieldsperim[0]]))
                        if response in ['yes','y']:
                                layer.DeleteField(fieldsperim[0])
                        else:
                                resp = False

                        field_names = [layer_defn.GetFieldDefn(i).GetName() for i in range(layer_defn.GetFieldCount())]

	if 'AREA' in field_names:
                resp = True
                while [i for i, elem in enumerate(field_names) if 'AREA' in elem] != [] and resp :
                        fieldsperim = [i for i, elem in enumerate(field_names) if 'AREA' in elem]
                        response = raw_input('Do you want to delete field "%s" ? (yes (y) or no (n))'%(field_names[fieldsperim[0]]))
                        if response in ['yes','y']:
                                layer.DeleteField(fieldsperim[0])
                        else:
                                resp = False
                        field_names = [layer_defn.GetFieldDefn(i).GetName() for i in range(layer_defn.GetFieldCount())]
	if 'Perimeter' in field_names:
                resp = True
                while [i for i, elem in enumerate(field_names) if 'Perimet' in elem] != [] and resp:
                        fieldsperim = [i for i, elem in enumerate(field_names) if 'Perimet' in elem]
                        response = raw_input('Do you want to delete field "%s" ? (yes (y) or no (n))'%(field_names[fieldsperim[0]]))
                        if response in ['yes','y']:
                                layer.DeleteField(fieldsperim[0])
                        else:
                                resp = False

                        field_names = [layer_defn.GetFieldDefn(i).GetName() for i in range(layer_defn.GetFieldCount())]

	new_field1 = ogr.FieldDefn('Area', ogr.OFTReal)
        if width is not None:
                new_field1.SetWidth(int(width))
        if precision is not None:
                new_field1.SetPrecision(int(precision))
	layer.CreateField(new_field1)

	new_field2 = ogr.FieldDefn('Perimeter', ogr.OFTReal)
        if width is not None:
                new_field2.SetWidth(int(width))
        if precision is not None:
                new_field2.SetPrecision(int(precision))
	layer.CreateField(new_field2)

	for feat in layer:
		if feat.GetGeometryRef():
			geom = feat.GetGeometryRef()
			area = geom.GetArea()
                        perimeter = feat.GetGeometryRef().Boundary().Length()
			size = (area/int(sizepix))
		else: 
			print "not geom"
			print feat.GetFID()			
			size = 0
 		layer.SetFeature(feat)
    		feat.SetField( "Area", size )
    		feat.SetField( "Perimeter", perimeter )
    		layer.SetFeature(feat)
	return 0


if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Add area and perimeter fields " \
        "of an input shapefile")
        parser.add_argument("-s", dest="shapefile", action="store", \
                            help="Input shapefile", required = True)
        parser.add_argument("-spix", dest="spix", action="store", \
                            help="Pixel size in m2", required = True)
        parser.add_argument("-precision", dest="precision", action="store", \
                            help="Geometry fields precision", required = False)
        parser.add_argument("-width", dest="width", action="store", \
                            help="Geometry fields width", required = False)
	args = parser.parse_args()
        if addFieldArea(args.shapefile, args.spix, args.precision, args.width) == 0:
                print 'Add of field succeeded!'
                sys.exit(0)
