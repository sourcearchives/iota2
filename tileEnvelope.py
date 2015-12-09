#!/usr/bin/python
#-*- coding: utf-8 -*-

import argparse
import sys,os
from osgeo import gdal, ogr,osr
from osgeo.gdalconst import *

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

def computePriority(tilesList,pathOut,proj):

	"""
		from a shapeFile representing tile's envelope, create tile's envelope considering tile's priority
		the highest priority for the left tile and the upper tile.

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

	poly = []#poly [][]  = [[TileName,Xmin,Xmax,Ymin,Ymax],[...],[...]...]
	for y in range((maxY-minY)+1):#Y
		tmp = []
		for x in range((maxX-minX)+1):#X
			tmp.append([])
		poly.append(tmp)

	#-------------------------------------- priority to the left tile ------------------------------
	for y in range(maxY+1-minY):#Y
		for x in range(minX,maxX+1):#X
			tile_1 = "D000"+str(x)+"H000"+str(maxY-y)

			if tile_1 in tilesList:
				#pathTo_Ev = pathTiles+"/"+tile_1+"_Ev.shp" #path to enveloppe
				pathTo_Ev = pathToTmpFiles+"/"+tile_1+"_Ev.shp" #path to enveloppe
				#print pathTo_Ev
				#pause = raw_input("Pause")
				driver = ogr.GetDriverByName("ESRI Shapefile")
				dataSource = driver.Open(pathTo_Ev, 0)
				layer = dataSource.GetLayer()
				for feature1 in layer:
   					geom_1 = feature1.GetGeometryRef()
				g1_minX,g1_maxX,g1_minY,g1_maxY = geom_1.GetEnvelope()

				tile_2 = "D000"+str(x+1)+"H000"+str(maxY-y)
				if tile_2 in tilesList and x!=maxX+1:
					#pathTo_Ev = pathTiles+"/"+tile_2+"_Ev.shp" #path to enveloppe
					pathTo_Ev = pathToTmpFiles+"/"+tile_2+"_Ev.shp" #path to enveloppe
					driver = ogr.GetDriverByName("ESRI Shapefile")
					
					dataSource = driver.Open(pathTo_Ev, 0)
					
					layer = dataSource.GetLayer()
					
					for feature2 in layer:
   						geom_2 = feature2.GetGeometryRef()

					intersection = geom_1.Intersection(geom_2)

					inter_minX,inter_maxX,inter_minY,inter_maxY = intersection.GetEnvelope()
					
					g2_minX,g2_maxX,g2_minY,g2_maxY = geom_2.GetEnvelope()
					
					if inter_minX and inter_minY and inter_maxX and inter_maxY != 0: #si il y a intersection
						if x == minX:
							poly[y][x-minX].append(tile_1)
							poly[y][x-minX].append(g1_minX)
							poly[y][x-minX].append(inter_maxX)
						else :
							poly[y][x-minX].append(tile_1)
							poly[y][x-minX].append(svg_maxX)
							poly[y][x-minX].append(inter_maxX)
				if x == maxX:
					poly[y][x-minX].append(tile_1)
					poly[y][x-minX].append(svg_maxX)
					poly[y][x-minX].append(g1_maxX)
				if not tile_2 in tilesList :
					print tile_2+" is not in tiles list "
				
			else :
				print tile_1+" is not in tiles list"
			svg_minX,svg_maxX,svg_minY,svg_maxY = intersection.GetEnvelope()

	#-------------------------------------- priority to the upper tile ------------------------------
	for x in range(minX,maxX+1):#X
		for y in range(maxY+1-minY):#Y
			tile_1 = "D000"+str(x)+"H000"+str(maxY-y)
			if tile_1 in tilesList:
				
				#pathTo_Ev = pathTiles+"/"+tile_1+"_Ev.shp" #path to enveloppe
				pathTo_Ev = pathToTmpFiles+"/"+tile_1+"_Ev.shp" #path to enveloppe
				
				driver = ogr.GetDriverByName("ESRI Shapefile")
				dataSource = driver.Open(pathTo_Ev, 0)
				layer = dataSource.GetLayer()
				for feature1 in layer:
   					geom_1_y = feature1.GetGeometryRef()
				g1_minX,g1_maxX,g1_minY,g1_maxY = geom_1_y.GetEnvelope()

				tile_2 = "D000"+str(x)+"H000"+str(maxY-y-1)

				if tile_2 in tilesList and maxY-y!=minY:
					#print tile_1
					#print poly[y][x-minX][0]

					#pathTo_Ev = pathTiles+"/"+tile_2+"_Ev.shp" #path to enveloppe
					driver = ogr.GetDriverByName("ESRI Shapefile")
					
					dataSource = driver.Open(pathTo_Ev, 0)
					
					layer = dataSource.GetLayer()
					
					for feature2 in layer:
   						geom_2_y = feature2.GetGeometryRef()

					intersection_Y = geom_1_y.Intersection(geom_2_y)

					
					inter_minX,inter_maxX,inter_maxY,inter_minY = intersection_Y.GetEnvelope()
					
					g2_minX,g2_maxX,g2_minY,g2_maxY = geom_2_y.GetEnvelope()
					if inter_minX and inter_minY and inter_maxX and inter_maxY != 0: #si il y a intersection
						if maxY-y == maxY:
							poly[y][x-minX].append(g1_maxY)
							poly[y][x-minX].append(inter_maxY)
						if maxY-y>minY and maxY-y<maxY :
							poly[y][x-minX].append(svg_minY)
							poly[y][x-minX].append(inter_maxY)
	
				if maxY-y == minY:
					poly[y][x-minX].append(svg_minY)
					poly[y][x-minX].append(g1_minY)
				if not tile_2 in tilesList :
					print tile_2+" is not in tiles list"
				
			else :
				print tile_1+" is not in tiles list"
		
			svg_minX,svg_maxX,svg_minY,svg_maxY = intersection_Y.GetEnvelope()
	
	for i in range(len(poly)):
		for j in range(len(poly[i])):
			#Création du nouveau shapeFile
			ring = ogr.Geometry(ogr.wkbLinearRing)

			tile,minX_,maxX_,minY_,maxY_ = poly[i][j]
			
			ring.AddPoint(minX_, maxY_)
			ring.AddPoint(maxX_, maxY_)
			ring.AddPoint(maxX_, minY_)
			ring.AddPoint(minX_, minY_)
			ring.AddPoint(minX_, maxY_)

			poly_ = ogr.Geometry(ogr.wkbPolygon)
			poly_.AddGeometry(ring)
	
			#-----------------
			#-- Create output file
			driver = ogr.GetDriverByName("ESRI Shapefile")
			try:
				output = driver.CreateDataSource(pathOut)
			except:
				print 'Could not create output datasource '
				sys.exit(1)
	
			srs = osr.SpatialReference()
			srs.ImportFromEPSG(proj)
			tile = tile

			newLayer = output.CreateLayer(tile,geom_type=ogr.wkbPolygon,srs=srs)
			if newLayer is None:
				print "Could not create output layer"
				sys.exit(1)
			newLayer.CreateField(ogr.FieldDefn("FID", ogr.OFTInteger))
			newLayerDef = newLayer.GetLayerDefn()
			feature = ogr.Feature(newLayerDef)
			feature.SetGeometry(poly_)

			ring.Destroy()
			poly_.Destroy()
			newLayer.CreateFeature(feature)
			feature.Destroy()
			output.Destroy()
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
	























