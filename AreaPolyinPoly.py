#!/usr/bin/python

import os
import glob
import sys
from sys import argv
import vector_functions as vf
from osgeo import ogr


def AreaPoly(shp1,shp2):
	ds = vf.openToWrite(shp1)
	lyr = ds.GetLayer()
	ds2 = vf.openToRead(shp2)
	lyr2 = ds2.GetLayer()
	lyr_defn = lyr.GetLayerDefn()
	field_names = [lyr_defn.GetFieldDefn(i).GetName() for i in range(lyr_defn.GetFieldCount())]
	field = 'AreaP'
	if field in field_names:
		i = field_names.index(field)
		lyr.DeleteField(i)

	field_c = ogr.FieldDefn(field, ogr.OFTReal)
	field_c.SetWidth(8)
	lyr.CreateField(field_c)

	for feat in lyr:
		geom = feat.GetGeometryRef()
		area1 = geom.GetArea()
		lyr2.SetSpatialFilter(geom)
		area2 = 0
		print feat.GetFID()
		for feat2 in lyr2:
			geom2 = feat2.GetGeometryRef()
			area2 = area2 + geom2.GetArea()
		areaP = (area2/area1)*100
		lyr.SetFeature(feat)
		feat.SetField(field, areaP)
		lyr.SetFeature(feat)

if __name__=='__main__':
    usage='usage: <shpfile1> <shpfile2>'
    if len(sys.argv) == 3:
        if AreaPoly(sys.argv[1],sys.argv[2]):
            print 'Succeeded!'
            sys.exit(0)
        else:
            print 'Failed!'
            sys.exit(1)
    else:
        print usage
        sys.exit(1)

