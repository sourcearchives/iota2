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
        
        layer.ResetReading()
        totalarea = 0
        for feat in layer:
                geom = feat.GetGeometryRef()
		totalarea += geom.GetArea()
                
        stats = []        
	for cl in classes:
		if fieldTypeCode == 4:
			layer.SetAttributeFilter(field+" = \'"+str(cl)+"\'")
   			featureCount = layer.GetFeatureCount()
                        area = 0
                        for feat in layer:
                                geom = feat.GetGeometryRef()
			        area += geom.GetArea()
                        partcl = area / totalarea * 100
			print "Class # %s: %s features and a total area of %s (rate : %s)"%(str(cl), \
                                                                                            str(featureCount),\
                                                                                            str(area), \
                                                                                            str(round(partcl,2)))
                        stats.append([cl, featureCount, area, partcl])
			layer.ResetReading()
		else:
			layer.SetAttributeFilter(field+" = "+str(cl))
   			featureCount = layer.GetFeatureCount()
                        area = 0
                        for feat in layer:
                                geom = feat.GetGeometryRef()
			        area += geom.GetArea()
                        partcl = area / totalarea * 100       
			print "Class # %s: %s features and a total area of %s (rate : %s)"%(str(cl), \
                                                                                            str(featureCount),\
                                                                                            str(area),\
                                                                                            str(round(partcl,2)))           
                        stats.append([cl, featureCount, area, partcl])
			layer.ResetReading()
	return stats

if __name__=='__main__':
	usage='usage: <shpfile> <attribute_field>'
	if len(sys.argv) != 3:
		print usage
		sys.exit(1)
    	else:
		countByAtt(sys.argv[1], sys.argv[2])
