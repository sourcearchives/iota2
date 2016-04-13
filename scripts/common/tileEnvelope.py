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
from config import Config
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from osgeo.gdalconst import *

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

def ClipVectorData(vectorFile, cutFile, opath,nameOut):
   """
   Cuts a shapefile with another shapefile
   ARGs:
       INPUT:
            -vectorFile: the shapefile to be cut
            -shpMask: the other shapefile 
       OUTPUT:
            -the vector file clipped
   """
   
   outname = opath+"/"+nameOut+".shp"
   if os.path.exists(outname):
      os.remove(outname)
   Clip = "ogr2ogr -clipsrc "+cutFile+" "+outname+" "+vectorFile+" -progress"
   print Clip
   os.system(Clip)
   return outname
#############################################################################################################################

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

	
#############################################################################################################################
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

#############################################################################################################################

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

#############################################################################################################################

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


#############################################################################################################################

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

#############################################################################################################################
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
#############################################################################################################################
def renameShapefile(path,filename,old_suffix,new_suffix):
    os.system("cp "+path+"/"+filename+old_suffix+".shp "+path+"/"+filename+new_suffix+".shp")
    os.system("cp "+path+"/"+filename+old_suffix+".shx "+path+"/"+filename+new_suffix+".shx")
    os.system("cp "+path+"/"+filename+old_suffix+".dbf "+path+"/"+filename+new_suffix+".dbf")
    os.system("cp "+path+"/"+filename+old_suffix+".prj "+path+"/"+filename+new_suffix+".prj")

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
	pathToTmpFiles = pathOut+"/AllTMP"
	subMeter = 500 #offset in order to manage nodata in image's border
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

	if pathWd == None:
		for y in range(maxY+1-minY):#Y
			for x in range(minX,maxX+1):#X

				"""
				currentTile = "D000"+str(x)+"H000"+str(maxY-y)
				c1 = "D000"+str(x)+"H000"+str(maxY-y+1) #up
				c2 = "D000"+str(x-1)+"H000"+str(maxY-y) #left
				"""
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
						ClipVectorData(pathTo_Left, pathToCurrent, pathToTmpFiles,intersectionX)

						#subtractShape(pathToCurrent,pathToTmpFiles+'/'+intersectionX+'.shp',pathToTmpFiles,currentTile)
					
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
				    			os.system("rm "+pathToTmpFiles+"/"+c2+"_T.shp "+pathToTmpFiles+"/"+c2+"_T.shx "+pathToTmpFiles+"/"+c2+"_T.dbf "+pathToTmpFiles+"/"+c2+"_T.prj")
							renameShapefile(pathToTmpFiles,c2,"_TMP","_T")
							os.system("rm "+pathToTmpFiles+"/"+c2+"_TMP.shp "+pathToTmpFiles+"/"+c2+"_TMP.shx "+pathToTmpFiles+"/"+c2+"_TMP.dbf "+pathToTmpFiles+"/"+c2+"_TMP.prj")
						#---------------------------------------------------------------------------------------
					
					else :
                                            renameShapefile(pathToTmpFiles,currentTile,"_Ev","_T")		
				
					#upper priority
					if c1 in tilesList :
					
						intersectionY  = c1+"_interY_"+currentTile
						ClipVectorData(pathTo_Up, pathToTmpFiles+'/'+currentTile+'_T.shp', pathToTmpFiles,intersectionY)
										
						#subtractShape(pathToTmpFiles+'/'+currentTile+'.shp',pathToTmpFiles+'/'+intersectionY+'.shp',pathToTmpFiles,currentTile+"_Prio")

						#Manage No Data -------------------------------------------------------------------------
					
						#get intersection coordinates
						miX,miY,maX,maY = getShapeExtent(pathToTmpFiles+'/'+intersectionY+'.shp')
						#create new intersection shape
						createShape(miX,miY+subMeter,maX,maY,pathToTmpFiles,intersectionY+'_NoData')
					
						#remove intersection for the current tile
						subtractShape(pathToTmpFiles+"/"+currentTile+"_T.shp",pathToTmpFiles+'/'+intersectionY+'_NoData.shp',pathToTmpFiles,currentTile+"_TMP")
					
						os.system("rm "+pathToTmpFiles+"/"+currentTile+"_T.shp "+pathToTmpFiles+"/"+currentTile+"_T.shx "+pathToTmpFiles+"/"+currentTile+"_T.dbf "+pathToTmpFiles+"/"+currentTile+"_T.prj")
						renameShapefile(pathToTmpFiles,currentTile,"_TMP","_T")
						os.system("rm "+pathToTmpFiles+"/"+currentTile+"_TMP.shp "+pathToTmpFiles+"/"+currentTile+"_TMP.shx "+pathToTmpFiles+"/"+currentTile+"_TMP.dbf "+pathToTmpFiles+"/"+currentTile+"_TMP.prj")
					
						#remove the noData part for the upper tile
						if os.path.exists(pathToTmpFiles+"/"+c1+"_T.shp"):
							subtractShape(pathToTmpFiles+"/"+c1+"_T.shp",pathToTmpFiles+'/'+currentTile+'_T.shp',pathToTmpFiles,c1+"_TMP")

							os.system("rm "+pathToTmpFiles+"/"+c1+"_T.shp "+pathToTmpFiles+"/"+c1+"_T.shx "+pathToTmpFiles+"/"+c1+"_T.dbf "+pathToTmpFiles+"/"+c1+"_T.prj")
						        renameShapefile(pathToTmpFiles,c1,"_TMP","_T")

							os.system("rm "+pathToTmpFiles+"/"+c1+"_TMP.shp "+pathToTmpFiles+"/"+c1+"_TMP.shx "+pathToTmpFiles+"/"+c1+"_TMP.dbf "+pathToTmpFiles+"/"+c1+"_TMP.prj")
						#---------------------------------------------------------------------------------------

				    
				
		#manage the case NorthEst/SouthWest priority
		for y in range(maxY+1-minY):#Y
			for x in range(minX,maxX+1):#X
				"""
				currentTile = "D000"+str(x)+"H000"+str(maxY-y)
				bl = "D000"+str(x-1)+"H000"+str(maxY-y-1)
				"""
				currentTile = "D"+coordinates(4,x)+"H"+coordinates(4,maxY-y)
				bl = "D"+coordinates(4,x-1)+"H"+coordinates(4,maxY-y-1)
				if currentTile in tilesList and bl in tilesList:
					subtractShape(pathToTmpFiles+'/'+currentTile+'_T.shp',pathToTmpFiles+'/'+bl+'_T.shp',pathToTmpFiles,"TMP")
			
					os.system("rm "+pathToTmpFiles+"/"+currentTile+"_T.shp")
					os.system("rm "+pathToTmpFiles+"/"+currentTile+"_T.shx")
					os.system("rm "+pathToTmpFiles+"/"+currentTile+"_T.dbf")
					os.system("rm "+pathToTmpFiles+"/"+currentTile+"_T.prj")
			
					os.system("cp "+pathToTmpFiles+"/TMP.shp "+pathToTmpFiles+"/"+currentTile+"_T.shp")
					os.system("cp "+pathToTmpFiles+"/TMP.shx "+pathToTmpFiles+"/"+currentTile+"_T.shx")
					os.system("cp "+pathToTmpFiles+"/TMP.dbf "+pathToTmpFiles+"/"+currentTile+"_T.dbf")
					os.system("cp "+pathToTmpFiles+"/TMP.prj "+pathToTmpFiles+"/"+currentTile+"_T.prj")

					os.system("rm "+pathToTmpFiles+"/TMP.shp")
					os.system("rm "+pathToTmpFiles+"/TMP.shx")
					os.system("rm "+pathToTmpFiles+"/TMP.dbf")
					os.system("rm "+pathToTmpFiles+"/TMP.prj")

		#manage the case NorthWest/SouthEst priority
		for y in range(maxY+1-minY):#Y
			for x in range(minX,maxX+1):#X
				"""
				currentTile = "D000"+str(x)+"H000"+str(maxY-y)
				ul = "D000"+str(x-1)+"H000"+str(maxY-y+1)
				"""
				currentTile = "D"+coordinates(4,x)+"H"+coordinates(4,maxY-y)
				ul = "D"+coordinates(4,x-1)+"H"+coordinates(4,maxY-y+1)
				if currentTile in tilesList and ul in tilesList:
					subtractShape(pathToTmpFiles+'/'+currentTile+'_T.shp',pathToTmpFiles+'/'+ul+'_T.shp',pathToTmpFiles,"TMP")
			
					os.system("rm "+pathToTmpFiles+"/"+currentTile+"_T.shp")
					os.system("rm "+pathToTmpFiles+"/"+currentTile+"_T.shx")
					os.system("rm "+pathToTmpFiles+"/"+currentTile+"_T.dbf")
					os.system("rm "+pathToTmpFiles+"/"+currentTile+"_T.prj")
			
					os.system("cp "+pathToTmpFiles+"/TMP.shp "+pathToTmpFiles+"/"+currentTile+"_T.shp")
					os.system("cp "+pathToTmpFiles+"/TMP.shx "+pathToTmpFiles+"/"+currentTile+"_T.shx")
					os.system("cp "+pathToTmpFiles+"/TMP.dbf "+pathToTmpFiles+"/"+currentTile+"_T.dbf")
					os.system("cp "+pathToTmpFiles+"/TMP.prj "+pathToTmpFiles+"/"+currentTile+"_T.prj")

					os.system("rm "+pathToTmpFiles+"/TMP.shp")
					os.system("rm "+pathToTmpFiles+"/TMP.shx")
					os.system("rm "+pathToTmpFiles+"/TMP.dbf")
					os.system("rm "+pathToTmpFiles+"/TMP.prj")
		
		prioFiles = FileSearch_AND(pathToTmpFiles,"_T.shp")
		for pathPrio in prioFiles :
			currentTile = pathPrio.split("/")[-1].split("_")[0]
			os.system("cp "+pathToTmpFiles+"/"+currentTile+"_T.shp "+pathOut+"/"+currentTile+".shp")
			os.system("cp "+pathToTmpFiles+"/"+currentTile+"_T.shx "+pathOut+"/"+currentTile+".shx")
			os.system("cp "+pathToTmpFiles+"/"+currentTile+"_T.dbf "+pathOut+"/"+currentTile+".dbf")
			os.system("cp "+pathToTmpFiles+"/"+currentTile+"_T.prj "+pathOut+"/"+currentTile+".prj")

		os.system("rm -r "+pathToTmpFiles)
	#working directory != None -> (cluster case)
	else:
		
		for y in range(maxY+1-minY):#Y
			for x in range(minX,maxX+1):#X
				"""
				currentTile = "D000"+str(x)+"H000"+str(maxY-y)
				c1 = "D000"+str(x)+"H000"+str(maxY-y+1) #up
				c2 = "D000"+str(x-1)+"H000"+str(maxY-y) #left
				"""
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
						ClipVectorData(pathTo_Left, pathToCurrent, pathWd,intersectionX)

						#subtractShape(pathToCurrent,pathToTmpFiles+'/'+intersectionX+'.shp',pathToTmpFiles,currentTile)
					
						#Manage No Data -------------------------------------------------------------------------
					
						#get intersection coordinates
						miX,miY,maX,maY = getShapeExtent(pathWd+'/'+intersectionX+'.shp')
						#create new intersection shape
						createShape(miX,miY,maX-subMeter,maY,pathWd,intersectionX+'_NoData')
						#remove intersection for the current tile
						if not os.path.exists(pathWd+"/"+currentTile+"_T.shp"):
							subtractShape(pathToCurrent,pathWd+'/'+intersectionX+'_NoData.shp',pathWd,currentTile+"_T")
						else:
							subtractShape(pathWd+"/"+currentTile+"_T.shp",pathWd+'/'+intersectionX+'_NoData.shp',pathWd,currentTile+"_T")
						#remove the noData part for the left tile
						if os.path.exists(pathWd+"/"+c2+"_T.shp"):
							subtractShape(pathWd+"/"+c2+"_T.shp",pathWd+'/'+currentTile+'_T.shp',pathWd,c2+"_TMP")
					
							os.system("rm "+pathWd+"/"+c2+"_T.shp "+pathWd+"/"+c2+"_T.shx "+pathWd+"/"+c2+"_T.dbf "+pathWd+"/"+c2+"_T.prj")

							os.system("cp "+pathWd+"/"+c2+"_TMP.shp "+pathWd+"/"+c2+"_T.shp")
							os.system("cp "+pathWd+"/"+c2+"_TMP.shx "+pathWd+"/"+c2+"_T.shx")
							os.system("cp "+pathWd+"/"+c2+"_TMP.dbf "+pathWd+"/"+c2+"_T.dbf")
							os.system("cp "+pathWd+"/"+c2+"_TMP.prj "+pathWd+"/"+c2+"_T.prj")

							os.system("rm "+pathWd+"/"+c2+"_TMP.shp "+pathWd+"/"+c2+"_TMP.shx "+pathWd+"/"+c2+"_TMP.dbf "+pathWd+"/"+c2+"_TMP.prj")
						#---------------------------------------------------------------------------------------
					
					else :

						os.system("cp "+pathToTmpFiles+"/"+currentTile+"_Ev.shp "+pathWd+"/"+currentTile+"_T.shp")
						os.system("cp "+pathToTmpFiles+"/"+currentTile+"_Ev.shx "+pathWd+"/"+currentTile+"_T.shx")
						os.system("cp "+pathToTmpFiles+"/"+currentTile+"_Ev.dbf "+pathWd+"/"+currentTile+"_T.dbf")
						os.system("cp "+pathToTmpFiles+"/"+currentTile+"_Ev.prj "+pathWd+"/"+currentTile+"_T.prj")
		
				
					#upper priority
					if c1 in tilesList :
					
						intersectionY  = c1+"_interY_"+currentTile
						ClipVectorData(pathTo_Up, pathWd+'/'+currentTile+'_T.shp', pathWd,intersectionY)
										
						#subtractShape(pathToTmpFiles+'/'+currentTile+'.shp',pathToTmpFiles+'/'+intersectionY+'.shp',pathToTmpFiles,currentTile+"_Prio")

						#Manage No Data -------------------------------------------------------------------------
					
						#get intersection coordinates
						miX,miY,maX,maY = getShapeExtent(pathWd+'/'+intersectionY+'.shp')
						#create new intersection shape
						createShape(miX,miY+subMeter,maX,maY,pathWd,intersectionY+'_NoData')
					
						#remove intersection for the current tile
						subtractShape(pathWd+"/"+currentTile+"_T.shp",pathWd+'/'+intersectionY+'_NoData.shp',pathWd,currentTile+"_TMP")
					
						os.system("rm "+pathWd+"/"+currentTile+"_T.shp "+pathWd+"/"+currentTile+"_T.shx "+pathWd+"/"+currentTile+"_T.dbf "+pathWd+"/"+currentTile+"_T.prj")
						os.system("cp "+pathWd+"/"+currentTile+"_TMP.shp "+pathWd+"/"+currentTile+"_T.shp")
						os.system("cp "+pathWd+"/"+currentTile+"_TMP.shx "+pathWd+"/"+currentTile+"_T.shx")
						os.system("cp "+pathWd+"/"+currentTile+"_TMP.dbf "+pathWd+"/"+currentTile+"_T.dbf")
						os.system("cp "+pathWd+"/"+currentTile+"_TMP.prj "+pathWd+"/"+currentTile+"_T.prj")
						os.system("rm "+pathWd+"/"+currentTile+"_TMP.shp "+pathWd+"/"+currentTile+"_TMP.shx "+pathWd+"/"+currentTile+"_TMP.dbf "+pathWd+"/"+currentTile+"_TMP.prj")
					
						#remove the noData part for the upper tile
						if os.path.exists(pathWd+"/"+c1+"_T.shp"):
							subtractShape(pathWd+"/"+c1+"_T.shp",pathWd+'/'+currentTile+'_T.shp',pathWd,c1+"_TMP")

							os.system("rm "+pathWd+"/"+c1+"_T.shp "+pathWd+"/"+c1+"_T.shx "+pathWd+"/"+c1+"_T.dbf "+pathWd+"/"+c1+"_T.prj")

							os.system("cp "+pathWd+"/"+c1+"_TMP.shp "+pathWd+"/"+c1+"_T.shp")
							os.system("cp "+pathWd+"/"+c1+"_TMP.shx "+pathWd+"/"+c1+"_T.shx")
							os.system("cp "+pathWd+"/"+c1+"_TMP.dbf "+pathWd+"/"+c1+"_T.dbf")
							os.system("cp "+pathWd+"/"+c1+"_TMP.prj "+pathWd+"/"+c1+"_T.prj")

							os.system("rm "+pathWd+"/"+c1+"_TMP.shp "+pathWd+"/"+c1+"_TMP.shx "+pathWd+"/"+c1+"_TMP.dbf "+pathWd+"/"+c1+"_TMP.prj")
						#---------------------------------------------------------------------------------------

					
					#else :
					#	os.system("cp "+pathToTmpFiles+"/"+currentTile+"_Ev.shp "+pathToTmpFiles+"/"+currentTile+"_T.shp")
					#	os.system("cp "+pathToTmpFiles+"/"+currentTile+"_Ev.shx "+pathToTmpFiles+"/"+currentTile+"_T.shx")
					#	os.system("cp "+pathToTmpFiles+"/"+currentTile+"_Ev.dbf "+pathToTmpFiles+"/"+currentTile+"_T.dbf")
					#	os.system("cp "+pathToTmpFiles+"/"+currentTile+"_Ev.prj "+pathToTmpFiles+"/"+currentTile+"_T.prj")
				
		#manage the case NorthEst/SouthWest priority
		for y in range(maxY+1-minY):#Y
			for x in range(minX,maxX+1):#X

				"""
				currentTile = "D000"+str(x)+"H000"+str(maxY-y)
				bl = "D000"+str(x-1)+"H000"+str(maxY-y-1)
				"""
				currentTile = "D"+coordinates(4,x)+"H"+coordinates(4,maxY-y)
				bl = "D"+coordinates(4,x-1)+"H"+coordinates(4,maxY-y-1)
				
				if currentTile in tilesList and bl in tilesList:
					subtractShape(pathWd+'/'+currentTile+'_T.shp',pathWd+'/'+bl+'_T.shp',pathWd,"TMP")
			
					os.system("rm "+pathWd+"/"+currentTile+"_T.shp")
					os.system("rm "+pathWd+"/"+currentTile+"_T.shx")
					os.system("rm "+pathWd+"/"+currentTile+"_T.dbf")
					os.system("rm "+pathWd+"/"+currentTile+"_T.prj")
			
					os.system("cp "+pathWd+"/TMP.shp "+pathWd+"/"+currentTile+"_T.shp")
					os.system("cp "+pathWd+"/TMP.shx "+pathWd+"/"+currentTile+"_T.shx")
					os.system("cp "+pathWd+"/TMP.dbf "+pathWd+"/"+currentTile+"_T.dbf")
					os.system("cp "+pathWd+"/TMP.prj "+pathWd+"/"+currentTile+"_T.prj")

					os.system("rm "+pathWd+"/TMP.shp")
					os.system("rm "+pathWd+"/TMP.shx")
					os.system("rm "+pathWd+"/TMP.dbf")
					os.system("rm "+pathWd+"/TMP.prj")

		#manage the case NorthWest/SouthEst priority
		for y in range(maxY+1-minY):#Y
			for x in range(minX,maxX+1):#X

				"""
				currentTile = "D000"+str(x)+"H000"+str(maxY-y)
				ul = "D000"+str(x-1)+"H000"+str(maxY-y+1)
				"""
				currentTile = "D"+coordinates(4,x)+"H"+coordinates(4,maxY-y)
				ul = "D"+coordinates(4,x-1)+"H"+coordinates(4,maxY-y+1)
				
				if currentTile in tilesList and ul in tilesList:
					subtractShape(pathWd+'/'+currentTile+'_T.shp',pathWd+'/'+ul+'_T.shp',pathWd,"TMP")
			
					os.system("rm "+pathWd+"/"+currentTile+"_T.shp")
					os.system("rm "+pathWd+"/"+currentTile+"_T.shx")
					os.system("rm "+pathWd+"/"+currentTile+"_T.dbf")
					os.system("rm "+pathWd+"/"+currentTile+"_T.prj")
			
					os.system("cp "+pathWd+"/TMP.shp "+pathWd+"/"+currentTile+"_T.shp")
					os.system("cp "+pathWd+"/TMP.shx "+pathWd+"/"+currentTile+"_T.shx")
					os.system("cp "+pathWd+"/TMP.dbf "+pathWd+"/"+currentTile+"_T.dbf")
					os.system("cp "+pathWd+"/TMP.prj "+pathWd+"/"+currentTile+"_T.prj")

					os.system("rm "+pathWd+"/TMP.shp")
					os.system("rm "+pathWd+"/TMP.shx")
					os.system("rm "+pathWd+"/TMP.dbf")
					os.system("rm "+pathWd+"/TMP.prj")
		
		prioFiles = FileSearch_AND(pathWd,"_T.shp")
		for pathPrio in prioFiles :
			currentTile = pathPrio.split("/")[-1].split("_")[0]
			os.system("cp "+pathWd+"/"+currentTile+"_T.shp "+pathOut+"/"+currentTile+".shp")
			os.system("cp "+pathWd+"/"+currentTile+"_T.shx "+pathOut+"/"+currentTile+".shx")
			os.system("cp "+pathWd+"/"+currentTile+"_T.dbf "+pathOut+"/"+currentTile+".dbf")
			os.system("cp "+pathWd+"/"+currentTile+"_T.prj "+pathOut+"/"+currentTile+".prj")

		os.system("rm -r "+pathToTmpFiles)

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
	























