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
from osgeo import gdal, ogr,osr
import vector_functions as vf        

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

def RandomInSitu(vectorFile, field, nbdraws, opath, name, ratio, pathWd):

   """
		
   """

   classes = []
   shapefile = vectorFile
   allFID = []
   nbtirage = nbdraws
   nameshp = shapefile.split('.')
   namefile = nameshp[0].split('/')
   driver = ogr.GetDriverByName("ESRI Shapefile")
   dataSource = driver.Open(shapefile, 0)
   layer = dataSource.GetLayer()

   
# Find the number of polygons by class
   for feature in layer:
       pid = feature.GetFID()
       allFID.append(pid)
       cl =  feature.GetField(field)
       if cl not in classes:
          classes.append(cl)

   AllTrain = []
   AllValid = []
   for tirage in range(0, nbtirage):
      listallid, listValid = get_randomPoly(dataSource,field,classes,ratio)
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
      learningShape = opath + "/" + name + "_seed" + str(tirage) + "_learn.shp"
      if pathWd == None:
         outShapefile = opath + "/" + name + "_seed" + str(tirage)+ "_learn.shp"
         vf.CreateNewLayer(layer, outShapefile)
      else :
	 outShapefile = pathWd + "/" +name + "_seed" + str(tirage) + "_learn.shp"
         vf.CreateNewLayer(layer, outShapefile)
         vf.copyShapefile(outShapefile, opath + "/" + name + "_seed" + str(tirage) + "_learn.shp")

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
      validationShape = opath + "/" + name + "_seed" + str(tirage) + "_val.shp"
      if pathWd == None:
         outShapefile2 = opath + "/" + name + "_seed" + str(tirage) + "_val.shp"
         vf.CreateNewLayer(layer, outShapefile2)
      else :
	 outShapefile2 = pathWd + "/" + name + "_seed" + str(tirage) + "_val.shp"
         vf.CreateNewLayer(layer, outShapefile2)
         vf.copyShapefile(outShapefile2, opath + "/" + name + "_seed" + str(tirage) + "_val.shp")

      AllTrain.append(learningShape)
      AllValid.append(validationShape)

   return AllTrain,AllValid

def RandomInSituByTile(shapefile, dataField, N, pathOut,ratio, pathWd):

	name = os.path.basename(shapefile)[:-4]
	dataSource = ogr.Open(shapefile)
	daLayer = dataSource.GetLayer(0)
	layerDefinition = daLayer.GetLayerDefn()
	ratio = float(ratio)
 
	driver = ogr.GetDriverByName('ESRI Shapefile')
	dataSource = driver.Open(shapefile, 0) 
	# Check to see if shapefile is found.
	if dataSource is None:
		raise Exception("Could not open " + shapefile)
	else:
    		layer = dataSource.GetLayer()
    		featureCount = layer.GetFeatureCount()
		if featureCount!=0:
			AllTrain,AllValid = RandomInSitu(shapefile, dataField, N, pathOut, name, ratio, pathWd)

        return AllTrain,AllValid

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you to create N training and N validation shapes by regions cut by tiles")

	parser.add_argument("-shape",help ="path to a shapeFile (mandatory)", dest = "path", required=True)
	parser.add_argument("-field",help ="data's field into shapeFile (mandatory)", dest = "dataField",required=True)
	parser.add_argument("--sample", dest = "N", help ="number of random sample (default = 1)", default = 1, type = int, required=False)
	parser.add_argument("-out",dest = "pathOut", help ="path where to store all shapes by tiles (mandatory)", required=True)
	parser.add_argument("-ratio",dest = "ratio", help ="Training and validation sample ratio  (mandatory, default value is 0.5)",default = '0.5',required=True)
	parser.add_argument("--wd",dest = "pathWd", help ="path to the working directory", default=None, required=False)
	args = parser.parse_args()

	RandomInSituByTile(args.path, args.dataField, args.N, args.pathOut,args.ratio,args.pathWd)

















