#!/usr/bin/python

from osgeo import ogr
import sys

def addFieldID(filein):
	source = ogr.Open(filein, 1)
	layer = source.GetLayer()
	layer_defn = layer.GetLayerDefn()
	field_names = [layer_defn.GetFieldDefn(i).GetName() for i in range(layer_defn.GetFieldCount())]
	new_field1 = ogr.FieldDefn('ID', ogr.OFTInteger)
	layer.CreateField(new_field1)
	i = 1
	for feat in layer:
 		layer.SetFeature(feat)
    		feat.SetField("ID", i )
    		layer.SetFeature(feat)
		i+=1
	return 0

if __name__=='__main__':
    usage='usage: <infile>'
    if len(sys.argv) == 2:
        if addFieldID(sys.argv[1]) == 0:
            print 'Add of field succeeded!'
            sys.exit(0)
    else:
        print usage
        sys.exit(1)
