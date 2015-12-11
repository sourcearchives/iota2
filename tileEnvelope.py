#!/usr/bin/python
#-*- coding: utf-8 -*-

import argparse
import sys,os
from osgeo import gdal, ogr,osr
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

def createRasterEmprise(ListTiles,pathTiles,pathOut):

	"""
		create envelope of the images in the list

		IN :
			- ListTiles : list of tiles
					ex : ["D0003H0005","D0004H0005","D0005H0005","D0003H0004",...] 
			- pathTiles : path where are stored tile's image
					ex : "/mnt/MD1200/DONNEES/S2_AGRI/GAPFILLING/FranceSudOuest"
			- pathOut : path to store image's envelope
					ex : "/mnt/MD1200/DONNEES/S2_AGRI/GAPFILLING/France2015/analyseTHR/tmp"

		OUT :
			tile's envelope in a shapefile called XXXX.shp where XXXX is the current tile
	"""
	proj = 2154
	if not os.path.exists(pathOut+"/AllTMP"):
		os.system("mkdir "+pathOut+"/AllTMP")
	pathToTmpFiles = pathOut+"/AllTMP"
	for tile in ListTiles:
		
		pathToTile = pathTiles+"/Landsat8_"+tile+"/Final/NDVI.tif"
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
			output = driver.CreateDataSource(pathToTmpFiles)
		except ValueError:
			print 'Could not create output datasource ', shp_name
			sys.exit(1)
	
		srs = osr.SpatialReference()
		srs.ImportFromEPSG(proj)
		newLayer = output.CreateLayer(tile+"_Ev",geom_type=ogr.wkbPolygon,srs=srs)
		if newLayer is None:
			print "Could not create output layer"
			sys.exit(1)
		newLayer.CreateField(ogr.FieldDefn("FID", ogr.OFTInteger))
		newLayerDef = newLayer.GetLayerDefn()
		feature = ogr.Feature(newLayerDef)
		feature.SetGeometry(poly)
		ring.Destroy()
		poly.Destroy()
		newLayer.CreateFeature(feature)
		
		output.Destroy()

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
		print 'Could not create output datasource ', shapeout
		sys.exit(1)
	
	srs = osr.SpatialReference()
	srs.ImportFromEPSG(2154)

	newLayer = output.CreateLayer(nameShp,geom_type=ogr.wkbPolygon,srs=srs)
	if newLayer is None:
		print "Could not create output layer"
		sys.exit(1)

	newLayer.CreateField(ogr.FieldDefn("FID", ogr.OFTInteger))
	newLayerDef = newLayer.GetLayerDefn()
	feature = ogr.Feature(newLayerDef)
	feature.SetGeometry(newgeom)
	newgeom.Destroy()
	poly.Destroy()
	newLayer.CreateFeature(feature)
		
	output.Destroy()

#############################################################################################################################
def computePriority(tilesList,pathOut,proj):
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

		OUT : 
			- tile's envelope considering priority in a shapefile called XXXX.shp where XXXX is the current tile		 
	"""

	pathToTmpFiles = pathOut+"/AllTMP"

	#Construction de la matrice des tuiles
	minX = 100000
	maxX = 0
	minY = 100000
	maxY = 0
	for tile in tilesList:
		if int(tile[4])>maxX:
			maxX = int(tile[4])
		if int(tile[4])<minX:
			minX = int(tile[4])
		if int(tile[-1])>maxY:
			maxY = int(tile[-1])
		if int(tile[-1])<minY:
			minY = int(tile[-1])

	for y in range(maxY+1-minY):#Y
		for x in range(minX,maxX+1):#X

			currentTile = "D000"+str(x)+"H000"+str(maxY-y)
			c1 = "D000"+str(x)+"H000"+str(maxY-y+1) #up
			c2 = "D000"+str(x-1)+"H000"+str(maxY-y) #left

			pathToCurrent = pathToTmpFiles+"/"+currentTile+"_Ev.shp"
			pathTo_Up = pathToTmpFiles+"/"+c1+"_Ev.shp" #path to enveloppe
			pathTo_Left = pathToTmpFiles+"/"+c2+"_Ev.shp" #path to enveloppe

			if currentTile in tilesList:
				#left priority
				if c2 in tilesList:
					intersectionX  = c2+"_interX_"+currentTile
					ClipVectorData(pathTo_Left, pathToCurrent, pathToTmpFiles,intersectionX)
					subtractShape(pathToCurrent,pathToTmpFiles+'/'+intersectionX+'.shp',pathToTmpFiles,currentTile)
				else :

					os.system("cp "+pathToTmpFiles+"/"+currentTile+"_Ev.shp "+pathToTmpFiles+"/"+currentTile+".shp")
					os.system("cp "+pathToTmpFiles+"/"+currentTile+"_Ev.shx "+pathToTmpFiles+"/"+currentTile+".shx")
					os.system("cp "+pathToTmpFiles+"/"+currentTile+"_Ev.dbf "+pathToTmpFiles+"/"+currentTile+".dbf")
					os.system("cp "+pathToTmpFiles+"/"+currentTile+"_Ev.prj "+pathToTmpFiles+"/"+currentTile+".prj")
			
				#upper priority
				if c1 in tilesList :
					intersectionY  = c1+"_interY_"+currentTile
					ClipVectorData(pathTo_Up, pathToTmpFiles+'/'+currentTile+'.shp', pathToTmpFiles,intersectionY)
					subtractShape(pathToTmpFiles+'/'+currentTile+'.shp',pathToTmpFiles+'/'+intersectionY+'.shp',pathToTmpFiles,currentTile+"_Prio")
				else :
					os.system("cp "+pathToTmpFiles+"/"+currentTile+".shp "+pathToTmpFiles+"/"+currentTile+"_Prio.shp")
					os.system("cp "+pathToTmpFiles+"/"+currentTile+".shx "+pathToTmpFiles+"/"+currentTile+"_Prio.shx")
					os.system("cp "+pathToTmpFiles+"/"+currentTile+".dbf "+pathToTmpFiles+"/"+currentTile+"_Prio.dbf")
					os.system("cp "+pathToTmpFiles+"/"+currentTile+".prj "+pathToTmpFiles+"/"+currentTile+"_Prio.prj")

	
	
	#manage the case "little square" priority to the left bottom
	for y in range(maxY+1-minY):#Y
		for x in range(minX,maxX+1):#X

			currentTile = "D000"+str(x)+"H000"+str(maxY-y)
			bl = "D000"+str(x-1)+"H000"+str(maxY-y-1)
			if currentTile in tilesList and bl in tilesList:
				subtractShape(pathToTmpFiles+'/'+currentTile+'_Prio.shp',pathToTmpFiles+'/'+bl+'_Prio.shp',pathToTmpFiles,"TMP")
			
				os.system("rm "+pathToTmpFiles+"/"+currentTile+"_Prio.shp")
				os.system("rm "+pathToTmpFiles+"/"+currentTile+"_Prio.shx")
				os.system("rm "+pathToTmpFiles+"/"+currentTile+"_Prio.dbf")
				os.system("rm "+pathToTmpFiles+"/"+currentTile+"_Prio.prj")
			
				os.system("cp "+pathToTmpFiles+"/TMP.shp "+pathToTmpFiles+"/"+currentTile+"_Prio.shp")
				os.system("cp "+pathToTmpFiles+"/TMP.shx "+pathToTmpFiles+"/"+currentTile+"_Prio.shx")
				os.system("cp "+pathToTmpFiles+"/TMP.dbf "+pathToTmpFiles+"/"+currentTile+"_Prio.dbf")
				os.system("cp "+pathToTmpFiles+"/TMP.prj "+pathToTmpFiles+"/"+currentTile+"_Prio.prj")

				os.system("rm "+pathToTmpFiles+"/TMP.shp")
				os.system("rm "+pathToTmpFiles+"/TMP.shx")
				os.system("rm "+pathToTmpFiles+"/TMP.dbf")
				os.system("rm "+pathToTmpFiles+"/TMP.prj")
		
	prioFiles = FileSearch_AND(pathToTmpFiles,"_Prio.shp")
	for pathPrio in prioFiles :
		currentTile = pathPrio.split("/")[-1].split("_")[0]
		os.system("cp "+pathToTmpFiles+"/"+currentTile+"_Prio.shp "+pathOut+"/"+currentTile+".shp")
		os.system("cp "+pathToTmpFiles+"/"+currentTile+"_Prio.shx "+pathOut+"/"+currentTile+".shx")
		os.system("cp "+pathToTmpFiles+"/"+currentTile+"_Prio.dbf "+pathOut+"/"+currentTile+".dbf")
		os.system("cp "+pathToTmpFiles+"/"+currentTile+"_Prio.prj "+pathOut+"/"+currentTile+".prj")

	os.system("rm -r "+pathToTmpFiles)

#############################################################################################################################

def GenerateShapeTile(tileList,pathTiles,pathOut):

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
			OUT :
				- ShapeFile corresponding to tile envelope with priority 
					ex : the tile D0003H0005 become D0003H0005.shp in pathOut
	"""

	createRasterEmprise(tileList,pathTiles,pathOut)
	computePriority(tileList,pathOut,2154)#2154 -> projection

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you to generate tile's envelope considering tile's priority")
	parser.add_argument("-t",dest = "tiles",help ="All the tiles", nargs='+',metavar = "")
	parser.add_argument("-t.path",dest = "pathTiles",help ="where are stored tiles",metavar = "")
	parser.add_argument("-out",dest = "pathOut",help ="path out",metavar = "")
	args = parser.parse_args()

	GenerateShapeTile(args.tiles,args.pathTiles,args.pathOut)
	























