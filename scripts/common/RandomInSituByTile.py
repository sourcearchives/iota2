#!/usr/bin/python
#-*- coding: utf-8 -*-

# =========================================================================
#   Program:   iota2
#
#   Copyright (c) CESBIO. All rights reserved.
#
#   See LICENSE for details.
#
#   This software is distributed WITHOUT ANY WARRANTY; without even
#   the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the above copyright notices for more information.
#
# =========================================================================

import argparse
import sys,os,random
import fileUtils as fu
from osgeo import gdal, ogr,osr

def get_randomPoly(dataSource,field,classes):
	listallid = []
	listValid = []

	for cl in classes:
         listid = []
         layer = dataSource.GetLayer()
         layer.SetAttributeFilter(field+" = "+str(cl))
         featureCount = float(layer.GetFeatureCount())
	 if featureCount == 1:
	 	for feat in layer:
           	   _id = feat.GetFID()
		   listallid.append(_id)
                   listValid.append(_id)
         else:
         	polbysel = round(featureCount / 2)
         	if polbysel <= 1:
	    		polbysel = 1
         	for feat in layer:
            		_id = feat.GetFID()
            		listid.append(_id)
            		listid.sort()
         	listToChoice = random.sample(listid, int(polbysel))
         	#print listToChoice
         	for fid in listToChoice:
            		listallid.append(fid)  
	listallid.sort()
	return listallid,listValid

def RandomInSitu(vectorFile, field, nbdraws, opath,name,AllFields,pathWd):

   """
		
   """

   AllPath = []
   crop = 0
   classes = []
   shapefile = vectorFile
   field = field
   dicoprop = {}
   allFID = []
   nbtirage = nbdraws
   nameshp = shapefile.split('.')
   namefile = nameshp[0].split('/')

   driver = ogr.GetDriverByName("ESRI Shapefile")
   dataSource = driver.Open(shapefile, 0)
   layer = dataSource.GetLayer()

# Count the total features of cropland
   if crop == 1:
   	layer.SetAttributeFilter("CROP =1")
   count = float(layer.GetFeatureCount())
   #print count
   
# Find the number of polygons by class
   for feature in layer:
       pid = feature.GetFID()
       allFID.append(pid)
       cl =  feature.GetField(field)
       if cl not in classes:
          classes.append(cl)

   AllPath = []
   for tirage in range(0,nbtirage):
      listallid,listValid = get_randomPoly(dataSource,field,classes)
      ch = ""
      listFid = []
      for fid in listallid:
         listFid.append("FID="+str(fid))

      resultA = []
      for e in listFid:
          resultA.append(e)
          resultA.append(' OR ')
      resultA.pop()

      chA =  ''.join(resultA)
      layer.SetAttributeFilter(chA)

      if pathWd == None:
         outShapefile = opath+"/"+name+"_seed"+str(tirage)+"_learn.shp"
         CreateNewLayer(layer, outShapefile,AllFields)
      else :
	 outShapefile = pathWd+"/"+name+"_seed"+str(tirage)+"_learn.shp"
         CreateNewLayer(layer, outShapefile,AllFields)
         fu.cpShapeFile(outShapefile.replace(".shp",""),opath+"/"+name+"_seed"+str(tirage)+"_learn",[".prj",".shp",".dbf",".shx"])

      for i in allFID:
         if i not in listallid:
            listValid.append(i)

      chV = ""
      listFidV = []
      for fid in listValid:
         listFidV.append("FID="+str(fid))

      resultV = []
      for e in listFidV:
          resultV.append(e)
          resultV.append(' OR ')
      resultV.pop()

      chV =  ''.join(resultV)
      layer.SetAttributeFilter(chV)
      if pathWd == None:
         outShapefile2 = opath+"/"+name+"_seed"+str(tirage)+"_val.shp"
         CreateNewLayer(layer, outShapefile2,AllFields)
      else :
	 outShapefile2 = pathWd+"/"+name+"_seed"+str(tirage)+"_val.shp"
         CreateNewLayer(layer, outShapefile2,AllFields)
         fu.cpShapeFile(outShapefile.replace(".shp",""),opath+"/"+name+"_seed"+str(tirage)+"_val",[".prj",".shp",".dbf",".shx"])

      AllPath.append(outShapefile)
      AllPath.append(outShapefile2)
   return AllPath

def CreateNewLayer(layer, outShapefile,AllFields):

      outDriver = ogr.GetDriverByName("ESRI Shapefile")
      if os.path.exists(outShapefile):
        outDriver.DeleteDataSource(outShapefile)
      outDataSource = outDriver.CreateDataSource(outShapefile)
      out_lyr_name = os.path.splitext( os.path.split( outShapefile )[1] )[0]
      srsObj = layer.GetSpatialRef()
      outLayer = outDataSource.CreateLayer( out_lyr_name, srsObj, geom_type=ogr.wkbMultiPolygon )
      # Add input Layer Fields to the output Layer if it is the one we want
      inLayerDefn = layer.GetLayerDefn()
      for i in range(0, inLayerDefn.GetFieldCount()):
         fieldDefn = inLayerDefn.GetFieldDefn(i)
         fieldName = fieldDefn.GetName()
         if fieldName not in AllFields:
             continue
         outLayer.CreateField(fieldDefn)
     # Get the output Layer's Feature Definition
      outLayerDefn = outLayer.GetLayerDefn()

     # Add features to the ouput Layer
      for inFeature in layer:
      # Create output Feature
         outFeature = ogr.Feature(outLayerDefn)

        # Add field values from input Layer
         for i in range(0, outLayerDefn.GetFieldCount()):
            fieldDefn = outLayerDefn.GetFieldDefn(i)
            fieldName = fieldDefn.GetName()
            if fieldName not in AllFields:
                continue

            outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(),
                inFeature.GetField(i))
        # Set geometry as centroid
	 geom = inFeature.GetGeometryRef()
	 if geom:
         	outFeature.SetGeometry(geom.Clone())
        	outLayer.CreateFeature(outFeature)

def RandomInSituByTile(path_mod_tile, dataField, N, pathOut,pathWd):

	name = path_mod_tile.split("/")[-1].split("_")[-1].replace(".shp","")+"_region_"+path_mod_tile.split("/")[-1].split("_")[-2]

	dataSource = ogr.Open(path_mod_tile)
	daLayer = dataSource.GetLayer(0)
	layerDefinition = daLayer.GetLayerDefn()

	AllFields = []
	for i in range(layerDefinition.GetFieldCount()):
		try:
			ind = AllFields.index(layerDefinition.GetFieldDefn(i).GetName())
		except ValueError:
			AllFields.append(layerDefinition.GetFieldDefn(i).GetName())


	driver = ogr.GetDriverByName('ESRI Shapefile')
	dataSource = driver.Open(path_mod_tile, 0) # 0 means read-only. 1 means writeable.
	# Check to see if shapefile is found.
	if dataSource is None:
    		print 'Could not open %s' % (path_mod_tile)
	else:
    		layer = dataSource.GetLayer()
    		featureCount = layer.GetFeatureCount()
		if featureCount!=0:
			RandomInSitu(path_mod_tile, dataField, N, pathOut,name,AllFields,pathWd)


if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you to create N training and N validation shapes by regions cut by tiles")

	parser.add_argument("-shape.dataTile",help ="path to a shapeFile containing data's for one region in a tile (mandatory)",dest = "path",required=True)
	parser.add_argument("-shape.field",help ="data's field into shapeFile (mandatory)",dest = "dataField",required=True)
	parser.add_argument("--sample",dest = "N",help ="number of random sample (default = 1)",default = 1,type = int,required=False)
	parser.add_argument("-out",dest = "pathOut",help ="path where to store all shapes by tiles (mandatory)",required=True)
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
	args = parser.parse_args()

	RandomInSituByTile(args.path, args.dataField, args.N, args.pathOut,args.pathWd)


























