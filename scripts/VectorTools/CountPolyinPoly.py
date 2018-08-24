#!/usr/bin/python

import os
import glob
import sys
from sys import argv
import vector_functions as vf
from osgeo import ogr


def count(shp1,shp2):
	ds = vf.openToWrite(shp1)
	lyr = ds.GetLayer()
	ds2 = vf.openToRead(shp2)
	lyr2 = ds2.GetLayer()
	lyr_defn = lyr.GetLayerDefn()
	field_names = [lyr_defn.GetFieldDefn(i).GetName() for i in range(lyr_defn.GetFieldCount())]
	field = 'Count'
	if field in field_names:
		i = field_names.index(field)
		lyr.DeleteField(i)

	field_c = ogr.FieldDefn(field, ogr.OFTInteger)
	field_c.SetWidth(8)
	lyr.CreateField(field_c)

	for feat in lyr:
		geom = feat.GetGeometryRef()
		lyr2.SetSpatialFilter(geom)
		count = lyr2.GetFeatureCount()
		lyr.SetFeature(feat)
		feat.SetField("Count", count)
		lyr.SetFeature(feat)



 
if __name__=='__main__':
    usage='usage: count <shpfile1> <shpfile2>'
    if len(sys.argv) == 3:
        if count(sys.argv[1],sys.argv[2]):
            print 'Counting succeeded!'
            sys.exit(0)
        else:
            print 'Counting failed!'
            sys.exit(1)
    else:
        print usage
        sys.exit(1)
