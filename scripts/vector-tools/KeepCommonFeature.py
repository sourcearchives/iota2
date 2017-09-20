#!/usr/bin/python


import sys,os
from osgeo import ogr
import vector_functions as vf

#This script looks at two different files and compare if the same geometry exists in both files. If yes, keep this geometry in a new file.

def CheckDoubleGeomTwofilesCopy(shp1, shp2, field1, field2):

   """Priority to file No. 1 """

   ds1 = vf.openToRead(shp1)
   lyr1 = ds1.GetLayer()
   ds2 = vf.openToRead(shp2)
   lyr2 = ds2.GetLayer()
   newshp = vf.copyShp(shp1, "commonshape")
   dict1 = dict()
   dict2 = dict()
   dict3 = dict()
   for feat in lyr1:
	values= []
	ge = feat.GetGeometryRef()
	f =  feat.GetFID()
	code = feat.GetField(field1)
	values.append(ge.ExportToWkt())
	values.append(code)
	dict1[f] = values
   for feat in lyr2:
	values= []
	ge = feat.GetGeometryRef()
	f =  feat.GetFID()
	code = feat.GetField(field2)
	values.append(ge.ExportToWkt())
	values.append(code)
	dict2[f] = values
   for k1,v1 in dict1.items():
	for k2, v2 in dict2.items():
		if v1 == v2:
			new_feat = lyr1.GetFeature(k1)
			vf.copyFeatInShp2(new_feat, newshp)


if __name__=='__main__':
	usage='usage: <file1.shp> <file2.shp> <field_shp1> <field_shp2>'
	listfiles = []
	if len(sys.argv) == 5:
		CheckDoubleGeomTwofilesCopy(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
        	sys.exit(0)
	else:
	        print usage
	        sys.exit(1)

