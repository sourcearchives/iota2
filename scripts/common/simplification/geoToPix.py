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

import os,argparse,osr
from osgeo import gdal
from osgeo import ogr
from osgeo.gdalconst import *
import numpy as np

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

def getRasterResolution(rasterIn):
	raster = gdal.Open(rasterIn, GA_ReadOnly)
	if raster is None:
		raise Exception("can't open "+rasterIn)
	geotransform = raster.GetGeoTransform()
	spacingX = geotransform[1]
	spacingY = geotransform[5]
	return spacingX,spacingY

def matchGrid(val,grid):
	return min(grid, key = lambda x:abs(x-val))


def geoToPix(raster,geoX,geoY):
	
	minXe,maxXe,minYe,maxYe = getRasterExtent(raster)
	spacingX,spacingY = getRasterResolution(raster)
	Xgrid = np.arange(minXe+spacingX,maxXe,spacingX)
	Ygrid = np.arange(maxYe-spacingY,minYe,spacingY)

	pixX = list(Xgrid).index(matchGrid(geoX,Xgrid))
	pixY = list(Ygrid).index(matchGrid(geoY,Ygrid))
	
	print "X : "+str(pixX)+"\nY : "+str(pixY)
	return pixX, pixY
	

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "convert geographics coordinates to pixels coordinates")
	parser.add_argument("-in.raster",help ="",dest = "raster",required=True)
	parser.add_argument("-geoX",help ="geoX coordinate",type = float,dest = "geoX",required=True)
	parser.add_argument("-geoY",help ="geoY coordinate",type = float,dest = "geoY",required=True)

	args = parser.parse_args()

	geoToPix(args.raster,args.geoX,args.geoY)
















