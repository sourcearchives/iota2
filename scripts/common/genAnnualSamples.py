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
import fileUtils as fu
from osgeo import gdal
from osgeo import ogr
from osgeo.gdalconst import *
import numpy as np
import random
import otbApplication as otb

def coordParse(s):
	try:
		x,y  = map(float,s.split(","))
		return (x,y)
	except:
		raise argparse.ArgumentTypeError("Coordinates must be x,y")

def getNbSample(shape,tile,dataField,valToFind,resol,region):
	
	driver = ogr.GetDriverByName("ESRI Shapefile")
	buff = []
	dataSource = driver.Open(shape, 0)
	layer = dataSource.GetLayer()
	for feature in layer:
		if str(feature.GetField(dataField)) in valToFind:
	    		geom = feature.GetGeometryRef()
			buff.append((feature.GetField(dataField),geom.GetArea()))
	rep = fu.sortByFirstElem(buff)
	repDict = {}
	for currentClass, currentAreas in rep:
		array = np.asarray(currentAreas)
		totalArea = np.sum(array)
		repDict[currentClass] = int(totalArea/(int(resol)*int(resol)))
	print repDict
	return repDict

def raster2array(rasterfn):
    raster = gdal.Open(rasterfn)
    band = raster.GetRasterBand(1)
    return band.ReadAsArray()

def pixCoordinates(x,y,x_origin,y_origin,sizeX,sizeY):
	return ((x+1)*sizeX + x_origin)-sizeX*0.5,((y)*sizeY + y_origin)-sizeX*0.5

def getAll_regions(tileName,folder):
	allRegion = []
	allShape = fu.FileSearch_AND(folder,True,"learn",tileName,".shp")
	for currentShape in allShape:
		currentRegion = currentShape.split("/")[-1].split("_")[2]
		if not currentRegion in allRegion:
			allRegion.append(currentRegion)
	return allRegion

def genAnnualShapePoints(coord,gdalDriver,workingDirectory,rasterResolution,classToKeep,dataField,tile,validityThreshold,validityRaster,classificationRaster,maskFolder,inlearningShape,outlearningShape):
	
	currentRegion = inlearningShape.split("/")[-1].split("_")[2]
	classifName = os.path.split(classificationRaster)[1]
	sizeX,sizeY = fu.getRasterResolution(classificationRaster)
	mapReg = workingDirectory+"/"+classifName.replace(".tif","_MapReg_"+str(currentRegion)+".tif")
	cmd = "otbcli_ClassificationMapRegularization -io.in "+classificationRaster+" -io.out "+mapReg+" -ip.undecidedlabel 0 "
	print cmd 
	os.system(cmd)
	rasterVal = workingDirectory+"/"+classifName.replace(".tif","_VAL_"+str(currentRegion)+".tif")
	rasterRdy = workingDirectory+"/"+classifName.replace(".tif","_RDY_"+str(currentRegion)+".tif")
	projection = int(fu.getRasterProjectionEPSG(classificationRaster))
	cmd = 'otbcli_BandMath -il '+validityRaster+' '+mapReg+' -out '+rasterVal+' uint8 -exp "im1b1>'+str(validityThreshold)+'?im2b1:0 "'
	print cmd 
	os.system(cmd)

	Mask = fu.FileSearch_AND(maskFolder,True,tile,".tif","region_"+str(currentRegion.split("f")[0]))[0]
	cmd = 'otbcli_BandMath -il '+rasterVal+' '+Mask+' -out '+rasterRdy+' uint8 -exp "im1b1*im2b1"'
	#cmd = 'otbcli_BandMath -il '+mapReg+' '+Mask+' -out '+rasterRdy+' uint8 -exp "im1b1*im2b1"'
	print cmd 
	os.system(cmd)

	#Resample ?
	"""
	if int(sizeX) != int(rasterResolution):
		resize = float(sizeX)/float(rasterResolution)
		resample = folder+"/"+classifName.replace(".tif","_Resample_"+str(currentRegion)+".tif")
		rasterRdy_svg = rasterRdy
		cmd = "otbcli_RigidTransformResample -in "+rasterRdy+" -out "+resample+" -transform.type.id.scalex "+resize+" -transform.type.id.scaley "+resize
		print cmd 
		os.system(cmd)
		rasterRdy = resample
	"""

	rasterArray = raster2array(rasterRdy)
	rasterFile = gdal.Open(classificationRaster)
	x_origin,y_origin = rasterFile.GetGeoTransform()[0],rasterFile.GetGeoTransform()[3]
	sizeX,sizeY = rasterFile.GetGeoTransform()[1],rasterFile.GetGeoTransform()[5]
	rep = getNbSample(inlearningShape,tile,dataField,classToKeep,rasterResolution,currentRegion)
	driver = ogr.GetDriverByName(gdalDriver)
	if os.path.exists(outlearningShape):
		driver.DeleteDataSource(outlearningShape)
	data_source = driver.CreateDataSource(outlearningShape)

	srs = osr.SpatialReference()
	srs.ImportFromEPSG(projection)

	layerOUT = data_source.CreateLayer(dataField, srs, ogr.wkbPoint)
	field_name = ogr.FieldDefn(dataField, ogr.OFTInteger)
	#field_name.SetWidth(0)
	layerOUT.CreateField(field_name)

	for currentVal in classToKeep :
		try:
			nbSamples = rep[int(currentVal)]
		except:
			print "class : "+str(currentVal)+" doesn't exist in "+inlearningShape
			continue
		Y,X = np.where(rasterArray==int(currentVal))
		XYcoordinates = []
		for y,x in zip(Y,X):
			X_c,Y_c = pixCoordinates(x,y,x_origin,y_origin,sizeX,sizeY)
			XYcoordinates.append((X_c,Y_c))
		if nbSamples>len(XYcoordinates):nbSamples=len(XYcoordinates)
		for Xc,Yc in random.sample(XYcoordinates,nbSamples):#"0" for nbSamples allready manage ?
			if coord and not (Xc,Yc) in coord:
				feature = ogr.Feature(layerOUT.GetLayerDefn())
				feature.SetField(dataField, int(currentVal))
				wkt = "POINT(%f %f)" % (Xc,Yc)
				point = ogr.CreateGeometryFromWkt(wkt)
				feature.SetGeometry(point)
				layerOUT.CreateFeature(feature)
				feature.Destroy()
	data_source.Destroy()
	os.remove(mapReg)
	os.remove(rasterVal)
	os.remove(rasterRdy)
	"""
	if int(sizeX) != int(rasterResolution):
		os.remove(rasterRdy_svg)
	"""
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "")
	parser.add_argument("-in.learningShape",help ="must be a shapeFile",dest = "inlearningShape",required=True)
	parser.add_argument("-out.learningShape",help ="",dest = "outlearningShape",required=True)
	parser.add_argument("-maskFolder",help ="",dest = "maskFolder",required=True)
	parser.add_argument("-classificationRaster",help ="",dest = "classificationRaster",required=True)
	parser.add_argument("-validityRaster",help ="",dest = "validityRaster",required=True)
	parser.add_argument("-validityThreshold",type = int,help ="",dest = "validityThreshold",required=True)
	parser.add_argument("-tile",help ="",dest = "tile",required=True)
	parser.add_argument("-dataField",help ="",dest = "dataField",required=True)
	parser.add_argument("-workingDirectory",help ="",dest = "workingDirectory",default = None,required=None)
	parser.add_argument("-classToKeep",type = int,nargs='+',help ="",dest = "classToKeep",required=True)
	parser.add_argument("-targetResolution",type = int,help ="",dest = "rasterResolution",required=True)
	parser.add_argument("-gdalDriver",help ="",dest = "gdalDriver",required=True)
	parser.add_argument("-wc",type = coordParse,nargs='+',help ="do not use these coordinates (list of tuple) X,Y X,Y ... in projection system",dest = "coord",required=False,default = [()])

	args = parser.parse_args()

	genAnnualShapePoints(args.coord,args.gdalDriver,args.workingDirectory,args.rasterResolution,args.classToKeep,args.dataField,args.tile,args.validityThreshold,args.validityRaster,args.classificationRaster,args.maskFolder,args.inlearningShape,args.outlearningShape)











