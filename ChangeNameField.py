#!/usr/bin/python

from osgeo import ogr
import sys

def changeName(filein, fieldin, fieldout):
	source = ogr.Open(filein, 1)
	layer = source.GetLayer()
	layer_defn = layer.GetLayerDefn()
	i = layer_defn.GetFieldIndex(fieldin)
	#field_names = [layer_defn.GetFieldDefn(i).GetName() for i in range(layer_defn.GetFieldCount())]
	print layer_defn.GetFieldDefn(2)
	new_field1 = ogr.FieldDefn(fieldout, ogr.OFTString)
	layer.CreateField(new_field1)
	i = 1
	for feat in layer:
		val =  feat.GetField(fieldin)
 		layer.SetFeature(feat)
    		feat.SetField(fieldout, val )
    		layer.SetFeature(feat)
		i+=1

	return 0

if __name__=='__main__':
    usage='usage: <infile> <fieldin> <fieldout>'
    if len(sys.argv) == 4:
        if changeName(sys.argv[1], sys.argv[2], sys.argv[3]) == 0:
            print 'Add of field succeeded!'
            sys.exit(0)
    else:
        print usage
        sys.exit(1)
