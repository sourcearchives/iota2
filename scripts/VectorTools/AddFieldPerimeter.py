#!/usr/bin/python

from osgeo import ogr
import os
import sys
import argparse

def addFieldPerimeter(filein):
	source = ogr.Open(filein, 1)
	layer = source.GetLayer()
	layer_defn = layer.GetLayerDefn()
	field_names = [layer_defn.GetFieldDefn(i).GetName() for i in range(layer_defn.GetFieldCount())]
	if 'Perimeter' in field_names or 'perimeter' in field_names:
                if 'Perimeter' in field_names:
		        i = field_names.index('Perimeter')
		        layer.DeleteField(i)
                if 'perimeter' in field_names:
		        i = field_names.index('perimeter')
		        layer.DeleteField(i)                        
	new_field1 = ogr.FieldDefn('Perimeter', ogr.OFTReal)
	layer.CreateField(new_field1)

	for feat in layer:
		if feat.GetGeometryRef():
			geom = feat.GetGeometryRef()
			perim = geom.Boundary().Length()
 		        layer.SetFeature(feat)
    		        feat.SetField("Perimeter", perim)
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
	parser = argparse.ArgumentParser(description = "Add a perimeter field " \
        "of an input shapefile")
        parser.add_argument("-s", dest="shapefile", action="store", \
                            help="Input shapefile", required = True)
	args = parser.parse_args()
        if addFieldPerimeter(args.shapefile) == 0:
                print 'Add of field perimeter succeeded!'
                sys.exit(0)
