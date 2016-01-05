#!/usr/bin/python
#-*- coding: utf-8 -*-

import argparse
import sys,os,random
from osgeo import gdal, ogr,osr

def ClipVectorData(vectorFile, cutFile, opath):
   """
   Cuts a shapefile with another shapefile
   ARGs:
       INPUT:
            -vectorFile: the shapefile to be cut
            -shpMask: the other shapefile 
       OUTPUT:
            -the vector file clipped
   """
   
   nameVF = vectorFile.split("/")[-1].split(".")[0]
   nameCF = cutFile.split("/")[-1].split(".")[0]
   outname = opath+"/"+nameVF+"_"+nameCF+".shp"
   if os.path.exists(outname):
      os.remove(outname)
   Clip = "ogr2ogr -clipsrc "+cutFile+" "+outname+" "+vectorFile+" -progress"
   print Clip
   os.system(Clip)
   return outname

#############################################################################################################################

def ExtractData(pathToClip,shapeData,pathOut):
	
	"""
		Clip the shapeFile pathToClip with the shapeFile shapeData and store it in pathOut
	"""

	driver = ogr.GetDriverByName('ESRI Shapefile')
	dataSource = driver.Open(pathToClip, 0) # 0 means read-only. 1 means writeable.
	# Check to see if shapefile is found.
	if dataSource is None:
    		print 'Could not open %s' % (pathToClip)
	else:
    		layer = dataSource.GetLayer()
    		featureCount = layer.GetFeatureCount()
		if featureCount!=0:
			path = ClipVectorData(shapeData, pathToClip, pathOut)
			#check if shapeFile is empty
			"""
			dataSource_poly = driver.Open(path, 0)
			
			layer_poly = dataSource_poly.GetLayer()

			
			featureCount_poly = layer_poly.GetFeatureCount()
			if featureCount_poly != 0:
				return path
			"""

#############################################################################################################################

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you to create N training and N validation shapes by regions cut by tiles")

	parser.add_argument("-shape.region",help ="path to a shapeFile representing the region in one tile (mandatory)",dest = "clip",required=True)
	parser.add_argument("-shape.data",dest = "dataShape",help ="path to the shapeFile containing datas (mandatory)",required=True)
	parser.add_argument("-out",dest = "pathOut",help ="path where to store all shapes by tiles (mandatory)",required=True)
	args = parser.parse_args()

	ExtractData(args.clip,args.dataShape,args.pathOut)











































