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
import sys,os,random,shutil
import fileUtils as fu
from config import Config
from osgeo import gdal, ogr,osr

def get_randomPoly(dataSource,field,classes,ratio):
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
         	polbysel = round(featureCount*float(ratio))
		#polbysel = round(featureCount/2.0)
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

def RandomInSitu(vectorFile, field, nbdraws, opath,name,AllFields,ratio,pathWd):

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

   AllTrain = []
   AllValid = []
   for tirage in range(0,nbtirage):
      listallid,listValid = get_randomPoly(dataSource,field,classes,ratio)
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
      learningShape = opath+"/"+name+"_seed"+str(tirage)+"_learn.shp"
      if pathWd == None:
         outShapefile = opath+"/"+name+"_seed"+str(tirage)+"_learn.shp"
         fu.CreateNewLayer(layer, outShapefile,AllFields)
      else :
	 outShapefile = pathWd+"/"+name+"_seed"+str(tirage)+"_learn.shp"
         fu.CreateNewLayer(layer, outShapefile,AllFields)
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
      validationShape = opath+"/"+name+"_seed"+str(tirage)+"_val.shp"
      if pathWd == None:
         outShapefile2 = opath+"/"+name+"_seed"+str(tirage)+"_val.shp"
         fu.CreateNewLayer(layer, outShapefile2,AllFields)
      else :
	 outShapefile2 = pathWd+"/"+name+"_seed"+str(tirage)+"_val.shp"
         fu.CreateNewLayer(layer, outShapefile2,AllFields)
         fu.cpShapeFile(outShapefile2.replace(".shp",""),opath+"/"+name+"_seed"+str(tirage)+"_val",[".prj",".shp",".dbf",".shx"])

      AllTrain.append(learningShape)
      AllValid.append(validationShape)
   return AllTrain,AllValid

def RandomInSituByTile(path_mod_tile, dataField, N, pathOut,ratio,pathConf,pathWd):

	shapeMode = pathConf

	f = file(pathConf)
	cfg = Config(f)
	shapeMode = cfg.argTrain.shapeMode

	name = path_mod_tile.split("/")[-1].split("_")[-3]+"_region_"+path_mod_tile.split("/")[-1].split("_")[-4]
	dataSource = ogr.Open(path_mod_tile)
	daLayer = dataSource.GetLayer(0)
	layerDefinition = daLayer.GetLayerDefn()
	ratio = float(ratio)
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
			AllTrain,AllValid = RandomInSitu(path_mod_tile, dataField, N, pathOut,name,AllFields,ratio,pathWd)

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you to create N training and N validation shapes by regions cut by tiles")

	parser.add_argument("-shape.dataTile",help ="path to a shapeFile containing data's for one region in a tile (mandatory)",dest = "path",required=True)
	parser.add_argument("-shape.field",help ="data's field into shapeFile (mandatory)",dest = "dataField",required=True)
	parser.add_argument("--sample",dest = "N",help ="number of random sample (default = 1)",default = 1,type = int,required=False)
	parser.add_argument("-out",dest = "pathOut",help ="path where to store all shapes by tiles (mandatory)",required=True)
	parser.add_argument("-ratio",dest = "ratio",help ="Training and validation sample ratio  (mandatory, default value is 0.5)",default = '0.5',required=True)
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
	parser.add_argument("-conf",help ="path to the configuration file (mandatory)",dest = "pathConf",required=True)
	args = parser.parse_args()

	RandomInSituByTile(args.path, args.dataField, args.N, args.pathOut,args.ratio,args.pathConf,args.pathWd)

















