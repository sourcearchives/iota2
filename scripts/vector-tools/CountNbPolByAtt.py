#!/usr/bin/python

import sys
from osgeo import ogr
import vector_functions as vf

classes = []
def countByAtt(shpfile, field):
	ds = vf.openToRead(shpfile)
	fields = vf.getFields(shpfile)	
	layer = ds.GetLayer()
	for feature in layer:
    		cl =  feature.GetField(field)
		if cl not in classes:
	 		classes.append(cl)
	layerDfn = layer.GetLayerDefn()
	fieldTypeCode = layerDfn.GetFieldDefn(fields.index(field)).GetType()
	classes.sort()
	for cl in classes:
		if fieldTypeCode == 4:
			layer.SetAttributeFilter(field+" = \'"+str(cl)+"\'")
   			featureCount = layer.GetFeatureCount()
			print "Class # %s: %s features " % (str(cl), str(featureCount))
			layer.ResetReading()
		else:
			layer.SetAttributeFilter(field+" = "+str(cl))
   			featureCount = layer.GetFeatureCount()
			print "Class # %s: %s features " % (str(cl), str(featureCount))
			layer.ResetReading()
	return 0

if __name__=='__main__':
	usage='usage: <shpfile> <attribute_field>'
	if len(sys.argv) != 3:
		print usage
		sys.exit(1)
    	else:
		countByAtt(sys.argv[1], sys.argv[2])
