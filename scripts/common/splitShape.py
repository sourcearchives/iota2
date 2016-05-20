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
from osgeo import gdal, ogr,osr
from random import randrange
from collections import defaultdict
import repInShape as rs
from config import Config
import fileUtils as fu

def CreateNewLayer(layer, outShapefile,AllFields):

      print outShapefile+" is going to be created"
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

def splitList(InList,nbSplit):
	"""
	IN : 
		InList [list]
		nbSplit [int] : number of output fold

	OUT :
		splitList [list of nbSplit list]

	Examples :
		foo = ['a', 'b', 'c', 'd', 'e']
		print splitList(foo,4)
		>> [['e', 'c'], ['d'], ['a'], ['b']]
		
		print splitList(foo,8)
		>> [['b'], ['d'], ['c'], ['e'], ['a'], ['d'], ['a'], ['b']]
	"""
	def chunk(xs, n):
  		ys = list(xs)
    		random.shuffle(ys)
    		size = len(ys) // n
    		leftovers= ys[size*n:]
    		for c in xrange(n):
       	 		if leftovers:
           			extra= [ leftovers.pop() ] 
        		else:
           			extra= []
        		yield ys[c*size:(c+1)*size] + extra

	splitList = list(chunk(InList,nbSplit))

	#check empty content (if nbSplit > len(Inlist)) 
	All = []
	for splits in splitList:
		for split in splits:
			if not split in All:
				All.append(split)

	for i in range(len(splitList)):
		if len(splitList[i])==0:
			randomChoice = random.sample(All,1)[0]
			splitList[i].append(randomChoice)

	return splitList

def getAllLayerFields(layer):
	
	layerDefinition = layer.GetLayerDefn()
	AllFields = []
	for i in range(layerDefinition.GetFieldCount()):
		try:
			ind = AllFields.index(layerDefinition.GetFieldDefn(i).GetName())
		except ValueError:
			AllFields.append(layerDefinition.GetFieldDefn(i).GetName())
	return AllFields

def SplitShape(shapeIN,dataField,folds,outPath,outName):
	"""
	this function split a shape in "folds" new shape.
	IN :
		shapeIN [string] : path to the shape to split
		dataField [string] : data's Field into shape 
		folds [int] : number of split
		outPath [string] : path to the store new shapes
		outName [string] : new shapes names
	OUT :
		"folds" new shapes
	"""
	driver = ogr.GetDriverByName("ESRI Shapefile")
   	dataSource = driver.Open(shapeIN, 0)
	layer = dataSource.GetLayer()

	AllFields = getAllLayerFields(layer)

	buff = []
	for feature in layer:
		FID = feature.GetFID()
		cl = feature.GetField(dataField)
       		buff.append([cl,FID])

	d = defaultdict(list)
	for k, v in buff:
   		d[k].append(v)
	buff = list(d.items())

	cl_fold = []
	for cl,FID_cl in buff:
		fold = splitList(FID_cl,folds)
		cl_fold.append([cl,fold])

	id_fold = []
	for i in range(len(cl_fold)):
		foldNumber = 1
		for currentFold in cl_fold[i][1]:
			for FID in currentFold:
				id_fold.append([foldNumber,FID])
			foldNumber+=1

	d = defaultdict(list)
	for k, v in id_fold:
   		d[k].append(v)
	id_fold = list(d.items())#[[foldNumber,[allClassFID]],[],...]

	shapeCreated = []
	for foldNumber, AllFID in id_fold:
		listFid = []
		for fid in AllFID:
         		listFid.append("FID="+str(fid))
		resultA = []
		for e in listFid:
         		resultA.append(e)
          		resultA.append(' OR ')
      		resultA.pop()
		chA =  ''.join(resultA)
     		layer.SetAttributeFilter(chA)

		origin_name = outName.split("_")
		origin_name[2]=origin_name[2]+"f"+str(foldNumber)
		#origin_name.insert(3,"f"+str(foldNumber))
		nameOut = "_".join(origin_name)

		outShapefile = outPath+"/"+nameOut
		print outShapefile
		CreateNewLayer(layer, outShapefile,AllFields)
		shapeCreated.append(outShapefile)
	return shapeCreated

def split_All_shape(shape,folds,pathConf,pathWd):

	f = file(pathConf)
	cfg = Config(f)
	regionField = cfg.chain.regionField
	outputpath = cfg.chain.outputPath
	dataField = cfg.chain.dataField

	workingDirectory = outputpath+"/dataAppVal"
	if pathWd != None :
		workingDirectory = pathWd

	createdShape = SplitShape(shape,dataField,folds,workingDirectory,shape.split("/")[-1])
	fu.removeShape(shape.replace(".shp",""),[".prj",".shp",".dbf",".shx"])

	if pathWd!=None:
		for NewShape in createdShape:
			fu.cpShapeFile(NewShape.replace(".shp",""),outputpath+"/dataAppVal",[".prj",".shp",".dbf",".shx"],spe=True)

	
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "this function allow you to split a shape regarding a region shape")
	parser.add_argument("-path.shape",dest = "shape",help ="path to the shapeFile to split",required=True)
	parser.add_argument("-Nsplit",type = int,dest = "folds",help ="number of split of the shapeFile",required=True)
	parser.add_argument("-config",help ="path to the configuration file which describe the learning method (mandatory)",dest = "pathConf",required=True)
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
	args = parser.parse_args()

	split_All_shape(args.shape,args.folds,args.pathConf,args.pathWd)




