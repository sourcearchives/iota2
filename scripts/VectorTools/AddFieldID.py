#!/usr/bin/python

from osgeo import ogr
import sys, os
import argparse


def addFieldID(filein):
	source = ogr.Open(filein, 1)
	layer = source.GetLayer()
	layer_defn = layer.GetLayerDefn()
	field_names = [layer_defn.GetFieldDefn(i).GetName() for i in range(layer_defn.GetFieldCount())]
	if 'ID' in field_names or 'id' in field_names or 'Id' in field_names:
                if 'ID' in field_names:
                        i = field_names.index('ID')
		        layer.DeleteField(i)
                if 'id' in field_names:
                        i = field_names.index('id')
		        layer.DeleteField(i)
                if 'Id' in field_names:
                        i = field_names.index('Id')
		        layer.DeleteField(i)                        
	new_field1 = ogr.FieldDefn('ID', ogr.OFTInteger)
	layer.CreateField(new_field1)
	i = 1
	for feat in layer:
 		layer.SetFeature(feat)
    		feat.SetField("ID", i )
    		layer.SetFeature(feat)
		i+=1
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
	parser = argparse.ArgumentParser(description = "Create a FID field" \
        "for the given shapefile")
        parser.add_argument("-s", dest="shapefile", action="store", \
                            help="Input shapefile", required = True)
	args = parser.parse_args()
        addFieldID(args.shapefile)

        
