#!/usr/bin/python


import sys,os
from osgeo import ogr
import vector_functions as vf

"""
For a attribute field list the values
"""

def ListValues(shp):
	fields = vf.getFields(shp)
	print "The name of the fields are: "+' - '.join(fields)
	field = raw_input("Field to list values: ")
	if not field in fields:
		print 'This field does not exist. Verify!'
		sys.exit(1)
  	ds = vf.openToRead(shp)
	layer = ds.GetLayer()
	values = []
	for feat in layer:
		if not feat.GetField(field) in values:
			values.append(feat.GetField(field))
	return values


if __name__=='__main__':
    usage='usage: <shapefile>'
    if len(sys.argv) != 2:
	print usage
	sys.exit(1)
    else:
	print ListValues(sys.argv[1])
	
	


