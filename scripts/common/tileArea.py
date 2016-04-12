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
import sys,os
from osgeo import gdal, ogr,osr


def mergeVectors(outname, opath,files):
   	"""
   	Merge a list of vector files in one 
   	"""

	file1 = files[0]
  	nbfiles = len(files)
  	filefusion = opath+"/"+outname+".shp"
	if os.path.exists(filefusion):
		os.system("rm "+filefusion)
  	fusion = "ogr2ogr "+filefusion+" "+file1
	print fusion
  	os.system(fusion)

	for f in range(1,nbfiles):
		fusion = "ogr2ogr -update -append "+filefusion+" "+files[f]+" -nln "+outname
		print fusion
		os.system(fusion)

	return filefusion

#############################################################################################################################

def FileSearch_AND(PathToFolder,*names):

	"""
		search all files in a folder or sub folder which contains all names in their name
		
		IN :
			- PathToFolder : target folder 
					ex : /xx/xxx/xx/xxx 
			- *names : target names
					ex : "target1","target2"
		OUT :
			- out : a list containing all file name (without extension) which are containing all name
	"""
	out = []
	for path, dirs, files in os.walk(PathToFolder):
   		 for i in range(len(files)):
			flag=0
			for name in names:
				if files[i].count(name)!=0 and files[i].count(".aux.xml")==0:
					flag+=1
			if flag == len(names):
       				out.append(files[i].split(".")[0])
	return out

#############################################################################################################################

def AddFieldModel(shpIn,modNum,fieldOut):
	
	"""
		add a field to a shapeFile and for all features, add a number

		IN :
			- shpIn : a shapeFile 
			- modNum : the number to associate to features
			- fieldOut : the new field name

		OUT :
			- an update of the shape file in
	"""
	source = ogr.Open(shpIn, 1)
	layer = source.GetLayer()
	layer_defn = layer.GetLayerDefn()
	new_field = ogr.FieldDefn(fieldOut, ogr.OFTInteger)
	layer.CreateField(new_field)

	for feat in layer:
		if feat.GetGeometryRef():
			layer.SetFeature(feat)
    			feat.SetField(fieldOut, modNum )
    			layer.SetFeature(feat)
		else: 
			print "not geom"
			print feat.GetFID()			
			size = 0

#############################################################################################################################

def Bound(infile,outfile,buffdist):

	"""
		dilate or erode all features in the shapeFile In
		
		IN :
 			- infile : the shape file 
					ex : /xxx/x/x/x/x/yyy.shp
			- outfile : the resulting shapefile
					ex : /x/x/x/x/x.shp
			- buffdist : the distance of dilatation or erosion
					ex : -10 for erosion
					     +10 for dilatation
	
		OUT :
			- the shapeFile outfile
	"""
	try:
       		ds=ogr.Open(infile)
        	drv=ds.GetDriver()
        	if os.path.exists(outfile):
            		drv.DeleteDataSource(outfile)
        	drv.CopyDataSource(ds,outfile)
        	ds.Destroy()
        
       		ds=ogr.Open(outfile,1)
        	lyr=ds.GetLayer(0)
        	for i in range(0,lyr.GetFeatureCount()):
            		feat=lyr.GetFeature(i)
            		lyr.DeleteFeature(i)
            		geom=feat.GetGeometryRef()
            		feat.SetGeometry(geom.Buffer(float(buffdist)))
            		lyr.CreateFeature(feat)
        	ds.Destroy()
    	except:return False
    	return True

#############################################################################################################################

def CreateModelShapeFromTiles(tilesModel,pathTiles,proj,pathOut,OutSHPname,fieldOut,pathWd):

	"""
		create one shapeFile where all features belong to a model number according to the model description 
		
		IN :
			- tilesModel : a list of list which describe which tile belong to which model
				ex : for 3 models 
					tile model 1 : D0H0,D0H1
					tile model 2 : D0H2,D0H3
					tile model 3 : D0H4,D0H5,D0H6
				
					tilesModel = [["D0H0","D0H1"],["D0H2","D0H3"],["D0H4","D0H5","D0H6"]]
			- pathTiles : path to the tile's envelope with priority consideration 
				ex : /xx/x/xxx/x
					/!\ the folder which contain the envelopes must contain only the envelopes   <========
			- proj : projection
				ex : 2154
			- pathOut : path to store the resulting shapeFile 
				ex : x/x/x/xxx
			- OutSHPname : the name of the resulting shapeFile
				ex : "model"
			- fieldOut : the name of the field which will contain the model number
				ex : "Mod"
                        - pathWd : path to working directory (not mandatory, due to cluster's architecture default = None)

		OUT :
			a shapeFile which contains for all feature the model number which it belong to 
	"""
	if pathWd == None:
		pathToTMP = pathOut+"/AllTMP"
		if not os.path.exists(pathToTMP):
			os.system("mkdir "+pathToTMP)

	
		for i in range(len(tilesModel)):
			for j in range(len(tilesModel[i])):
				os.system("cp "+pathTiles+"/"+tilesModel[i][j]+".shp"+" "+pathToTMP)
				os.system("cp "+pathTiles+"/"+tilesModel[i][j]+".shx"+" "+pathToTMP)
				os.system("cp "+pathTiles+"/"+tilesModel[i][j]+".dbf"+" "+pathToTMP)
				os.system("cp "+pathTiles+"/"+tilesModel[i][j]+".prj"+" "+pathToTMP)
	
		AllTilePath = []
		AllTilePath_ER = []

		for i in range(len(tilesModel)):
			for j in range(len(tilesModel[i])):
				try:
					ind = AllTilePath.index(pathTiles+"/"+tilesModel[i][j]+".shp")
				except ValueError :
					AllTilePath.append(pathToTMP+"/"+tilesModel[i][j]+".shp")
					AllTilePath_ER.append(pathToTMP+"/"+tilesModel[i][j]+"_ERODE.shp")
	
		for i in range(len(tilesModel)):
			for j in range(len(tilesModel[i])):
				currentTile = pathToTMP+"/"+tilesModel[i][j]+".shp"
				AddFieldModel(currentTile,i+1,fieldOut)

		for path in AllTilePath:
			Bound(path,path.replace(".shp","_ERODE.shp"),-0.1)

	
		mergeVectors(OutSHPname, pathOut, AllTilePath_ER)

		os.system("rm -r "+pathToTMP)

	#cluster case
	else :
		pathToTMP = pathWd
		if not os.path.exists(pathToTMP):
			os.system("mkdir "+pathToTMP)

	
		for i in range(len(tilesModel)):
			for j in range(len(tilesModel[i])):
				os.system("cp "+pathTiles+"/"+tilesModel[i][j]+".shp"+" "+pathToTMP)
				os.system("cp "+pathTiles+"/"+tilesModel[i][j]+".shx"+" "+pathToTMP)
				os.system("cp "+pathTiles+"/"+tilesModel[i][j]+".dbf"+" "+pathToTMP)
				os.system("cp "+pathTiles+"/"+tilesModel[i][j]+".prj"+" "+pathToTMP)
	
		AllTilePath = []
		AllTilePath_ER = []

		for i in range(len(tilesModel)):
			for j in range(len(tilesModel[i])):
				try:
					ind = AllTilePath.index(pathTiles+"/"+tilesModel[i][j]+".shp")
				except ValueError :
					AllTilePath.append(pathToTMP+"/"+tilesModel[i][j]+".shp")
					AllTilePath_ER.append(pathToTMP+"/"+tilesModel[i][j]+"_ERODE.shp")
	
		for i in range(len(tilesModel)):
			for j in range(len(tilesModel[i])):
				currentTile = pathToTMP+"/"+tilesModel[i][j]+".shp"
				AddFieldModel(currentTile,i+1,fieldOut)

		for path in AllTilePath:
			Bound(path,path.replace(".shp","_ERODE.shp"),-0.1)

	
		mergeVectors(OutSHPname, pathOut, AllTilePath_ER)
#############################################################################################################################

def generateRegionShape(mode,pathTiles,pathToModel,pathOut,fieldOut,pathWd):
	"""
		create one shapeFile where all features belong to a model number according to the model description

		IN :
			- mode : "one_region" or "multi_regions"
					if one_region is selected, the output shapeFile will contain only one region constructed with all tiles in pathTiles
					if multi_regions is selected, the output shapeFile will contain per feature a model number according to 
					the text file pathToModel
			- pathTiles : path to the tile's envelope with priority consideration 
				ex : /xx/x/xxx/x
					/!\ the folder which contain the envelopes must contain only the envelopes   <========
			- pathToModel : path to the text file which describe which tile belong to which model
				the text file must have the following format :
			
				R1 : D0003H0005,D0004H0005
				R2 : D0005H0005,D0005H0004
				R3 : D0003H0004,D0004H0004
				R4 : D0003H0003,D0004H0003,D0005H0003

				for 4 models and 9 tiles
			- pathOut : path to store the resulting shapeFile 
			- fieldOut : the name of the field which will contain the model number
				ex : "Mod"
                        - pathWd : path to working directory (not mandatory, due to cluster's architecture default = None)

		OUT :
			a shapeFile which contains for all feature the model number which it belong to 
	"""
	region = []
	if mode == "one_region":
		AllTiles = FileSearch_AND(pathTiles,".shp")
		region.append(AllTiles)
	elif mode == "multi_regions":

		if pathToModel!= None :
			modelFile = open(pathToModel,"r")
			while 1:
				data = modelFile.readline().rstrip('\n\r')
				if data == "":
					break
				line = data.split(":")[-1]
				tiles = line.replace(" ","").split(",")
				region.append(tiles)			
			modelFile.close
		else :
			raise Exception('if multi_regions is selected, you must specify a test file which describe the model')
		

	p_f = pathOut.replace(" ","").split("/")
	outName = p_f[-1].split(".")[0]
	pathMod = ""
	for i in range(1,len(p_f)-1):
		pathMod = pathMod+"/"+p_f[i]
	
	
	CreateModelShapeFromTiles(region,pathTiles,2154,pathMod,outName,fieldOut,pathWd)

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you to create a shape by tile for a given area and a given region")

	parser.add_argument("-mode",dest = "mode",help ="one_region/multi_regions (mandatory)",choices=['one_region', 'multi_regions'],required=True)
	parser.add_argument("-fieldOut",dest = "fieldOut",help ="field out (mandatory)",required=True)
	parser.add_argument("-pathTiles",dest = "pathTiles",help ="path where are only stored tile's envelope (mandatory)",default = "None",required=True)
	parser.add_argument("--multi.models",dest = "pathToModel",help ="path to the text file which link tiles/models",default = "None",required=False)
	parser.add_argument("-out",dest = "pathOut",help ="path where to store all shape by tiles (mandatory)",default = "None",required=True)
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=True)
	args = parser.parse_args()

	generateRegionShape(args.mode,args.pathTiles,args.pathToModel,args.pathOut,args.fieldOut,args.pathWd)
	

	


























































