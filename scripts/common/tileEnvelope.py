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
import sys,os,shutil,subprocess
from config import Config
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from osgeo.gdalconst import *
import fileUtils as fu

def createShape(minX,minY,maxX,maxY,out,name,proj=2154):
	"""
		create a shape with only one geometry (a rectangle) described by minX,minY,maxX,maxY and save in 'out' as name
	"""
	ring = ogr.Geometry(ogr.wkbLinearRing)
	ring.AddPoint(minX, minY)
	ring.AddPoint(maxX, minY)
	ring.AddPoint(maxX, maxY)
	ring.AddPoint(minX, maxY)
	ring.AddPoint(minX, minY)
		
	poly = ogr.Geometry(ogr.wkbPolygon)
	poly.AddGeometry(ring)

	#-----------------
	#-- Create output file

	folder = ""
	
	driver = ogr.GetDriverByName("ESRI Shapefile")
	try:
		output = driver.CreateDataSource(out)
	except ValueError:
		raise Exception("Could not create output datasource "+out)

	srs = osr.SpatialReference()
	srs.ImportFromEPSG(proj)
	newLayer = output.CreateLayer(name,geom_type=ogr.wkbPolygon,srs=srs)
	if newLayer is None:
		raise Exception("Could not create output layer")

	newLayer.CreateField(ogr.FieldDefn("FID", ogr.OFTInteger))
	newLayerDef = newLayer.GetLayerDefn()
	feature = ogr.Feature(newLayerDef)
	feature.SetGeometry(poly)
	ring.Destroy()
	poly.Destroy()
	newLayer.CreateFeature(feature)
		
	output.Destroy()

def getShapeExtent(shape_in):
	"""
		Get shape extent of shape_in. The shape must have only one geometry
	"""

	driver = ogr.GetDriverByName("ESRI Shapefile")
	dataSource = driver.Open(shape_in, 0)
	layer = dataSource.GetLayer()

	for feat in layer:
   		geom = feat.GetGeometryRef()
	env = geom.GetEnvelope()
	return env[0],env[2],env[1],env[3]

def getRasterExtent(raster_in):
	"""
		Get raster extent of raster_in from GetGeoTransform()
		ARGs:
			INPUT:
				- raster_in: input raster
			OUTPUT
				- ex: extent with [minX,maxX,minY,maxY]
	"""
	if not os.path.isfile(raster_in):
		return []
	raster = gdal.Open(raster_in, GA_ReadOnly)
	if raster is None:
		return []
	geotransform = raster.GetGeoTransform()
	originX = geotransform[0]
	originY = geotransform[3]
	spacingX = geotransform[1]
	spacingY = geotransform[5]
	r, c = raster.RasterYSize, raster.RasterXSize
	
	minX = originX
	maxY = originY
	maxX = minX + c*spacingX
	minY = maxY + r*spacingY
	
	return [minX,maxX,minY,maxY]

def createRasterFootprint(ListTiles,pathTiles,pathOut,pathWd,pathConf, proj=2154):

	"""
		create envelope of the images in the list

		IN :
			- ListTiles : list of tiles
					ex : ["D0003H0005","D0004H0005","D0005H0005","D0003H0004",...] 
			- pathTiles : path where are stored tile's image
					ex : "/mnt/MD1200/DONNEES/S2_AGRI/GAPFILLING/FranceSudOuest"
			- pathOut : path to store image's envelope
					ex : "/mnt/MD1200/DONNEES/S2_AGRI/GAPFILLING/France2015/analyseTHR/tmp"
			- pathWd : path to working directory (not mandatory, due to cluster's architecture)

		OUT :
			tile's envelope in a shapefile called XXXX.shp where XXXX is the current tile
	"""
	cfg = Config(pathConf)
	listIndices = cfg.GlobChain.features
	if len(listIndices)>1:
		listIndices = list(listIndices)
		listIndices = sorted(listIndices)
		listFeat = "_".join(listIndices)
	else:
		listFeat = listIndices[0]

	Stack_ind = "SL_MultiTempGapF_"+listFeat+"__.tif"

        if not os.path.exists(pathOut+"/AllTMP"):
                os.system("mkdir "+pathOut+"/AllTMP")
        pathToTmpFiles = pathOut+"/AllTMP"
        for tile in ListTiles:
                contenu = os.listdir(pathTiles+"/"+tile+"/Final")
                pathToTile = pathTiles+"/"+tile+"/Final/"+Stack_ind
                minX,maxX,minY,maxY =  getRasterExtent(pathToTile)

                ring = ogr.Geometry(ogr.wkbLinearRing)
                ring.AddPoint(minX, minY)
                ring.AddPoint(maxX, minY)
                ring.AddPoint(maxX, maxY)
                ring.AddPoint(minX, maxY)
                ring.AddPoint(minX, minY)

                poly = ogr.Geometry(ogr.wkbPolygon)
                poly.AddGeometry(ring)

                #-----------------
                #-- Create output file
                driver = ogr.GetDriverByName("ESRI Shapefile")
                try:
                    if pathWd==None:
                        output = driver.CreateDataSource(pathToTmpFiles)
                    else:
                        output = driver.CreateDataSource(pathWd)
                except ValueError:
                        raise Exception('Could not create output datasource '+str(shp_name))

                srs = osr.SpatialReference()
                srs.ImportFromEPSG(proj)
                newLayer = output.CreateLayer(tile+"_Ev",geom_type=ogr.wkbPolygon,srs=srs)
                if newLayer is None:
                        raise Exception("Could not create output layer")
                newLayer.CreateField(ogr.FieldDefn("FID", ogr.OFTInteger))
                newLayerDef = newLayer.GetLayerDefn()
                feature = ogr.Feature(newLayerDef)
                feature.SetGeometry(poly)
                ring.Destroy()
                poly.Destroy()
                newLayer.CreateFeature(feature)
                output.Destroy()
                if pathWd!=None:
                    os.system("cp "+pathWd+"/"+str(tile)+"_Ev* "+pathToTmpFiles)

def subtractShape(shape1,shape2,shapeout,nameShp):

	"""
		shape 1 - shape 2 in shapeout/nameshp.shp
	"""
	driver = ogr.GetDriverByName("ESRI Shapefile")
	dataSource1 = driver.Open(shape1, 0)
	dataSource2 = driver.Open(shape2, 0)

	layer1 = dataSource1.GetLayer()
	for feature1 in layer1:
   		geom_1 = feature1.GetGeometryRef()

	layer2 = dataSource2.GetLayer()
	for feature2 in layer2:
   		geom_2 = feature2.GetGeometryRef()

	newgeom = geom_1.Difference(geom_2)
	poly = ogr.Geometry(ogr.wkbPolygon)

	#-----------------
	#-- Create output file
	try:
		output = driver.CreateDataSource(shapeout)
	except ValueError:
		raise Exception('Could not create output datasource '+str(shapeout))
	
	srs = osr.SpatialReference()
	srs.ImportFromEPSG(2154)

	newLayer = output.CreateLayer(nameShp,geom_type=ogr.wkbPolygon,srs=srs)
	if newLayer is None:
		raise Exception("Could not create output layer")

	newLayer.CreateField(ogr.FieldDefn("FID", ogr.OFTInteger))
	newLayerDef = newLayer.GetLayerDefn()
	feature = ogr.Feature(newLayerDef)
	feature.SetGeometry(newgeom)
	newgeom.Destroy()
	poly.Destroy()
	newLayer.CreateFeature(feature)
		
	output.Destroy()

def coordinates(nb,coordinates):
	
	"""
		IN :
			nb [int] : number of digits in coordinates system
			coordinates [int] : coodinates in coordinates system

		OUT :  
			out [string]

		Exemple :
		for a tile : D0005H0010
		X = coordinates(4,5)#0005
		Y = coordinates(4,10)#0010
		#finale tile :
		ft = "D"+X+"H"+Y
	"""
	out_tmp = []
	out = ""
	c_str = str(coordinates)
	for i in range(nb):
		out_tmp.append("0")

	for i in range(len(c_str)):
		out_tmp[len(out)-i-1]=c_str[len(c_str)-i-1]

	for ch in out_tmp:
		out = out + ch
	return out

def initCoordinates(tilesList):
	minX = 100000
	maxX = 0
	minY = 100000
	maxY = 0
	for tile in tilesList:
		if int(tile[1:5])>maxX:
			maxX = int(tile[1:5])
		if int(tile[1:5])<minX:
			minX = int(tile[1:5])
		if int(tile[-4:len(tile)])>maxY:
			maxY = int(tile[-4:len(tile)])
		if int(tile[-4:len(tile)])<minY:
			minY = int(tile[-4:len(tile)])
	return minX,minY,maxX,maxY

def computePriority(tilesList,pathOut,proj,pathWd):
	"""
		from a shapeFile representing tile's envelope, create tile's envelope considering tile's priority
		the highest priority for the left tile and the upper tile. AND MANAGE MISSING TILES

		IN :
			- tilesList : list of tiles
					ex : ["D0003H0005","D0004H0005","D0005H0005","D0003H0004",...]
			- pathOut : path to store image's envelope
					ex : "/mnt/MD1200/DONNEES/S2_AGRI/GAPFILLING/France2015/analyseTHR/tmp"
			- proj : projection
					ex : 2154
                        - pathWd : path to working directory (not mandatory, due to cluster's architecture)

		OUT : 
			- tile's envelope considering priority in a shapefile called XXXX.shp where XXXX is the current tile		 
	"""

	if pathWd == None:	
		pathToTmpFiles = pathOut+"/AllTMP"
		
	else :
		pathToTmpFiles = pathWd+"/AllTMP"
		subprocess.call(["cp", "-R",pathOut+"/AllTMP",pathToTmpFiles])
		

	if not os.path.exists(pathToTmpFiles):
			os.mkdir(pathToTmpFiles)

	subMeter = 500 #offset in order to manage nodata in image's border
	minX,minY,maxX,maxY = initCoordinates(tilesList)

	for y in range(maxY+1-minY):#Y
		for x in range(minX,maxX+1):#X

			currentTile = "D"+coordinates(4,x)+"H"+coordinates(4,maxY-y)
			c1 = "D"+coordinates(4,x)+"H"+coordinates(4,maxY-y+1) #up
			c2 = "D"+coordinates(4,x-1)+"H"+coordinates(4,maxY-y) #left

			pathToCurrent = pathToTmpFiles+"/"+currentTile+"_Ev.shp"
			pathTo_Up = pathToTmpFiles+"/"+c1+"_Ev.shp" #path to enveloppe
			pathTo_Left = pathToTmpFiles+"/"+c2+"_Ev.shp" #path to enveloppe

			if currentTile in tilesList:
				#left priority
				if c2 in tilesList:
					intersectionX  = c2+"_interX_"+currentTile
					fu.ClipVectorData(pathTo_Left, pathToCurrent, pathToTmpFiles,intersectionX)
					#Manage No Data -------------------------------------------------------------------------
					#get intersection coordinates
					miX,miY,maX,maY = getShapeExtent(pathToTmpFiles+'/'+intersectionX+'.shp')
					#create new intersection shape
					createShape(miX,miY,maX-subMeter,maY,pathToTmpFiles,intersectionX+'_NoData')
					#remove intersection for the current tile
					if not os.path.exists(pathToTmpFiles+"/"+currentTile+"_T.shp"):
						subtractShape(pathToCurrent,pathToTmpFiles+'/'+intersectionX+'_NoData.shp',pathToTmpFiles,currentTile+"_T")
					else:
						subtractShape(pathToTmpFiles+"/"+currentTile+"_T.shp",pathToTmpFiles+'/'+intersectionX+'_NoData.shp',pathToTmpFiles,currentTile+"_T")
					#remove the noData part for the left tile
					if os.path.exists(pathToTmpFiles+"/"+c2+"_T.shp"):
						subtractShape(pathToTmpFiles+"/"+c2+"_T.shp",pathToTmpFiles+'/'+currentTile+'_T.shp',pathToTmpFiles,c2+"_TMP")
						fu.removeShape(pathToTmpFiles+"/"+c2+"_T",[".prj",".shp",".dbf",".shx"])
						fu.renameShapefile(pathToTmpFiles,c2,"_TMP","_T")
						fu.removeShape(pathToTmpFiles+"/"+c2+"_TMP",[".prj",".shp",".dbf",".shx"])
					#---------------------------------------------------------------------------------------
				else :
                                           fu.renameShapefile(pathToTmpFiles,currentTile,"_Ev","_T")		
				#upper priority
				if c1 in tilesList :
					
					intersectionY  = c1+"_interY_"+currentTile
					fu.ClipVectorData(pathTo_Up, pathToTmpFiles+'/'+currentTile+'_T.shp', pathToTmpFiles,intersectionY)
					#Manage No Data -------------------------------------------------------------------------
					#get intersection coordinates
					miX,miY,maX,maY = getShapeExtent(pathToTmpFiles+'/'+intersectionY+'.shp')
					#create new intersection shape
					createShape(miX,miY+subMeter,maX,maY,pathToTmpFiles,intersectionY+'_NoData')
					#remove intersection for the current tile
					subtractShape(pathToTmpFiles+"/"+currentTile+"_T.shp",pathToTmpFiles+'/'+intersectionY+'_NoData.shp',pathToTmpFiles,currentTile+"_TMP")
					fu.removeShape(pathToTmpFiles+"/"+currentTile+"_T",[".prj",".shp",".dbf",".shx"])
					fu.renameShapefile(pathToTmpFiles,currentTile,"_TMP","_T")
					fu.removeShape(pathToTmpFiles+"/"+currentTile+"_TMP",[".prj",".shp",".dbf",".shx"])
					
					#remove the noData part for the upper tile
					if os.path.exists(pathToTmpFiles+"/"+c1+"_T.shp"):
						subtractShape(pathToTmpFiles+"/"+c1+"_T.shp",pathToTmpFiles+'/'+currentTile+'_T.shp',pathToTmpFiles,c1+"_TMP")
						fu.removeShape(pathToTmpFiles+"/"+c1+"_T",[".prj",".shp",".dbf",".shx"])
						fu.renameShapefile(pathToTmpFiles,c1,"_TMP","_T")
						fu.removeShape(pathToTmpFiles+"/"+c1+"_TMP",[".prj",".shp",".dbf",".shx"])
	#manage the case NorthEst/SouthWest priority
	for y in range(maxY+1-minY):#Y
		for x in range(minX,maxX+1):#X
			currentTile = "D"+coordinates(4,x)+"H"+coordinates(4,maxY-y)
			bl = "D"+coordinates(4,x-1)+"H"+coordinates(4,maxY-y-1)
			if currentTile in tilesList and bl in tilesList:
				subtractShape(pathToTmpFiles+'/'+currentTile+'_T.shp',pathToTmpFiles+'/'+bl+'_T.shp',pathToTmpFiles,"TMP")
				fu.removeShape(pathToTmpFiles+"/"+currentTile+"_T",[".prj",".shp",".dbf",".shx"])
				fu.cpShapeFile(pathToTmpFiles+"/TMP",pathToTmpFiles+"/"+currentTile+"_T",[".prj",".shp",".dbf",".shx"])
				fu.removeShape(pathToTmpFiles+"/TMP",[".prj",".shp",".dbf",".shx"])

	#manage the case NorthWest/SouthEst priority
	for y in range(maxY+1-minY):#Y
		for x in range(minX,maxX+1):#X
			currentTile = "D"+coordinates(4,x)+"H"+coordinates(4,maxY-y)
			ul = "D"+coordinates(4,x-1)+"H"+coordinates(4,maxY-y+1)
			if currentTile in tilesList and ul in tilesList:
				subtractShape(pathToTmpFiles+'/'+currentTile+'_T.shp',pathToTmpFiles+'/'+ul+'_T.shp',pathToTmpFiles,"TMP")
				fu.removeShape(pathToTmpFiles+"/"+currentTile+"_T",[".prj",".shp",".dbf",".shx"])
				fu.cpShapeFile(pathToTmpFiles+"/TMP",pathToTmpFiles+"/"+currentTile+"_T",[".prj",".shp",".dbf",".shx"])
				fu.removeShape(pathToTmpFiles+"/TMP",[".prj",".shp",".dbf",".shx"])
		
	prioFiles = fu.FileSearch_AND(pathToTmpFiles,True,"_T.shp")
	for pathPrio in prioFiles :
		currentTile = pathPrio.split("/")[-1].split("_")[0]
		fu.cpShapeFile(pathToTmpFiles+"/"+currentTile+"_T",pathOut+"/"+currentTile,[".prj",".shp",".dbf",".shx"])

	shutil.rmtree(pathOut+"/AllTMP")

#############################################################################################################################

def GenerateShapeTile(tileList,pathTiles,pathOut,pathWd,pathConf):

	"""
		from a list of images, this function creates image's envelope considering tile's priority.
		higher priority for the left tile and the upper tiler

		Args: 
			IN :
				- ListTiles : list of envelope 
						ex : ListTiles = ["D0003H0005","D0004H0005","D0005H0005","D0003H0004","D0004H0004"]
				- pathTiles : where images are sored
						ex : pathTiles = "/mnt/MD1200/DONNEES/S2_AGRI/GAPFILLING/FranceSudOuest"
				- pathOut : where stored the envelopes
						ex : pathOut = "/mnt/MD1200/DONNEES/S2_AGRI/GAPFILLING/FranceSudOuest"
                                - pathWd : path to working directory (not mandatory, due to cluster's architecture default = None)
			OUT :
				- ShapeFile corresponding to tile envelope with priority 
					ex : the tile D0003H0005 become D0003H0005.shp in pathOut
	"""
	createRasterFootprint(tileList,pathTiles,pathOut,pathWd,pathConf)
	computePriority(tileList,pathOut,2154,pathWd)#2154 -> projection

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you to generate tile's envelope considering tile's priority")
	parser.add_argument("-t",dest = "tiles",help ="All the tiles", nargs='+',required=True)
	parser.add_argument("-t.path",dest = "pathTiles",help ="where are stored tiles",required=True)
	parser.add_argument("-out",dest = "pathOut",help ="path out",required=True)
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
	parser.add_argument("-conf",help ="path to the configuration file which describe the learning method (mandatory)",dest = "pathConf",required=True)
	args = parser.parse_args()

	GenerateShapeTile(args.tiles,args.pathTiles,args.pathOut,args.pathWd,args.pathConf)
	























