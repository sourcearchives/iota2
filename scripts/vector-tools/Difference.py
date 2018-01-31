#!/usr/bin/python


import sys,os
from osgeo import ogr, gdal, osr
import vector_functions as vf


"""
Difference  of geometries between two files
"""

distance = 10000
def DifferenceFiles(shp1, shp2):
	outShp = vf.copyShp(shp1, 'difference')
	fields = vf.getFields(shp1)
	ds1 = vf.openToRead(shp1)
	ds2 = vf.openToRead(shp2)
	lyr1 = ds1.GetLayer()
	lyr2 = ds2.GetLayer()
	layerDef = lyr1.GetLayerDefn()
	print lyr2.GetFeatureCount()
	for f1 in lyr1:
		lyr2.SetAttributeFilter(None)
		geom1 = f1.GetGeometryRef()
   		centroid = geom1.Centroid()
   		x = centroid.GetX()
   		y = centroid.GetY()
		minX = x - float(distance)
		minY = y - float(distance)
		maxX = x + float(distance)
		maxY = y + float(distance)
		lyr2.SetSpatialFilterRect(float(minX), float(minY), float(maxX), float(maxY))
		nbfeat2 =  lyr2.GetFeatureCount()
		intersection = False
		listFID = []
		copy = False
		for i in range(0, nbfeat2):
			ds3 = vf.openToRead(outShp)
			lyr3 = ds3.GetLayer()
			lyr3.SetSpatialFilterRect(float(minX), float(minY), float(maxX), float(maxY))
			f2 = lyr2.GetFeature(i)
			print str(f1.GetFID())+" - "+str(i)
			geom2 = f2.GetGeometryRef()
			if geom1.Intersect(geom2) == True:
				print "True"
				if geom1.Equal(geom2) == True:
					if vf.VerifyGeom(geom,lyr3) == False:
						vf.copyFeatInShp(f1, outShp)
				elif geom1.Equal(geom2) == False:
					newgeom = vf.Difference(geom1, geom2)
					newgeom2 =  ogr.CreateGeometryFromWkb(newgeom.wkb)
					newgeom2 = geom1.Difference(geom2)
					#print newgeom2
					newFeature = ogr.Feature(layerDef)
					newFeature.SetGeometry(newgeom2)
					for field in fields:
						newFeature.SetField(field, f1.GetField(field))
					if vf.VerifyGeom(newgeom2,lyr3) == False:
		        			vf.copyFeatInShp(newFeature, outShp)
					newFeature.Destroy()
			elif geom1.Intersect(geom2) ==  False:
				print "False"
				if not vf.VerifyGeom(geom1,lyr3):
					vf.copyFeatInShp(f1, outShp)
			f2.Destroy()

		f1.Destroy()

	ds2 = vf.openToRead(shp2)
	lyr2 = ds2.GetLayer()
	ds3 = vf.openToWrite(outShp)
	lyr3 = ds3.GetLayer()
	for feat in lyr3:
		geom1 = feat.GetGeometryRef()
	   	centroid = geom1.Centroid()
   		x = centroid.GetX()
   		y = centroid.GetY()
		minX = x - float(distance)
		minY = y - float(distance)
		maxX = x + float(distance)
		maxY = y + float(distance)
		lyr2.SetSpatialFilterRect(float(minX), float(minY), float(maxX), float(maxY))
		nbfeat2 =  lyr2.GetFeatureCount()
		intersection = False
		listFID = []
		copy = False
		for i in range(0, nbfeat2):
			f2 = lyr2.GetFeature(i)
			geom2 = f2.GetGeometryRef()	
			if geom1.Intersect(geom2) == True:
				lyr3.DeleteFeature(feat.GetFID())
			ds3.ExecuteSQL('REPACK '+lyr3.GetName())
	return outShp

if __name__=='__main__':
	usage='usage: <shpfile1> <shpfile2>'
	if len(sys.argv) != 3:
		print usage
		sys.exit(1)
    	else:
		DifferenceFiles(sys.argv[1], sys.argv[2])
	

