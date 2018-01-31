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
fu.updatePyPath()
from AddField import addField

def coordParse(s):
    try:
        x,y  = map(float,s.split(","))
        return (x,y)
    except:
        raise argparse.ArgumentTypeError("Coordinates must be x,y")

def getNbSample(shape, tile, dataField, valToFind, resol, region, coeff,
                region_field="region", region_val="-1"):
    
    driver = ogr.GetDriverByName("ESRI Shapefile")
    buff = []
    dataSource = driver.Open(shape, 0)
    layer = dataSource.GetLayer()
    for feature in layer:
        if str(feature.GetField(dataField)) in valToFind and feature.GetField(region_field) == str(region_val):
            geom = feature.GetGeometryRef()
            buff.append((feature.GetField(dataField),geom.GetArea()))
    rep = fu.sortByFirstElem(buff)
    repDict = {}
    for currentClass, currentAreas in rep:
        array = np.asarray(currentAreas)
        totalArea = np.sum(array)
        repDict[currentClass] = int((float(coeff)*totalArea)/(int(resol)*int(resol)))
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

def genAnnualShapePoints(coord, gdalDriver, workingDirectory, rasterResolution,
                         classToKeep, dataField, tile, validityThreshold,
                         validityRaster, classificationRaster, masks,
                         inlearningShape, outlearningShape, coeff, epsg):

    #Const
    region_pos = 2#in mask name if splited by '_'
    seed_pos = -1#in learningsample if splited by '_'
    tile_pos = 0
    current_seed = os.path.splitext(os.path.split(inlearningShape)[-1])[0].split("_")[seed_pos]
    currentTile = inlearningShape.split("/")[-1].split("_")[tile_pos]
    classifName = currentTile+"_Classif.tif"

    #check HPC mode
    try:
        PathWd = os.environ['TMPDIR']
    except:
        PathWd = None
    projection = int(epsg)

    vector_regions = []
    add = 0
    for currentMask in masks:
        currentRegion = os.path.split(currentMask)[-1].split("_")[region_pos]
        vector_region = os.path.join(workingDirectory,
                                     "Annual_" + currentTile + "_region_" + currentRegion + "_seed_" + current_seed + ".sqlite")
        vector_regions.append(vector_region)
        rasterRdy = workingDirectory+"/"+classifName.replace(".tif","_RDY_"+str(currentRegion)+".tif")
        
        mapReg = otb.Registry.CreateApplication("ClassificationMapRegularization")
        mapReg.SetParameterString("io.in",classificationRaster)
        mapReg.SetParameterString("ip.undecidedlabel","0")
        mapReg.Execute()
        
        useless = otb.Registry.CreateApplication("BandMath")
        useless.SetParameterString("exp","im1b1")
        useless.SetParameterStringList("il",[validityRaster])
        useless.SetParameterString("ram","10000")
        useless.Execute()

        uselessMask = otb.Registry.CreateApplication("BandMath")
        uselessMask.SetParameterString("exp","im1b1")
        uselessMask.SetParameterStringList("il",[currentMask])
        uselessMask.SetParameterString("ram","10000")
        uselessMask.Execute()

        valid = otb.Registry.CreateApplication("BandMath")
        valid.SetParameterString("exp","im1b1>"+str(validityThreshold)+"?im2b1:0")
        valid.AddImageToParameterInputImageList("il",useless.GetParameterOutputImage("out"))
        valid.AddImageToParameterInputImageList("il",mapReg.GetParameterOutputImage("io.out"))
        valid.SetParameterString("ram","10000")
        valid.Execute()

        rdy = otb.Registry.CreateApplication("BandMath")
        rdy.SetParameterString("exp","im1b1*(im2b1>=1?1:0)")
        rdy.AddImageToParameterInputImageList("il",valid.GetParameterOutputImage("out"))
        rdy.AddImageToParameterInputImageList("il",uselessMask.GetParameterOutputImage("out"))
        rdy.SetParameterString("out",rasterRdy+"?&streaming:type=stripped&streaming:sizemode=nbsplits&streaming:sizevalue=10")
        rdy.SetParameterOutputImagePixelType("out",otb.ImagePixelType_uint8)
        rdy.ExecuteAndWriteOutput()

        rasterArray = raster2array(rasterRdy)
        rasterFile = gdal.Open(rasterRdy)
        x_origin,y_origin = rasterFile.GetGeoTransform()[0],rasterFile.GetGeoTransform()[3]
        sizeX,sizeY = rasterFile.GetGeoTransform()[1],rasterFile.GetGeoTransform()[5]

        rep = getNbSample(inlearningShape, tile, dataField, classToKeep,
                          rasterResolution, currentRegion, coeff,
                          region_field="region", region_val=currentRegion)

        driver = ogr.GetDriverByName(gdalDriver)
        if os.path.exists(vector_region):
            driver.DeleteDataSource(vector_region)

        data_source = driver.CreateDataSource(vector_region)

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(projection)

        layerName = "output"
        layerOUT = data_source.CreateLayer(layerName, srs, ogr.wkbPoint)
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
                    add+=1
        
        data_source.Destroy()
        os.remove(rasterRdy)
        layerOUT = None
        addField(vector_region, "region", str(currentRegion),
                 valueType=str, driver="SQLite")

    outlearningShape_name = os.path.splitext(os.path.split(outlearningShape)[-1])[0]
    outlearningShape_dir = os.path.split(outlearningShape)[0]
    
    """
    print "AJOUT REGION"
    for vector in vector_regions:
        print currentRegion
        addField(vector, "region", str(currentRegion), valueType=str)
    print "FIN REGION"
    """
    fu.mergeSQLite(outlearningShape_name, outlearningShape_dir, vector_regions)
    if add == 0:return False
    else : return True

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "")
	parser.add_argument("-in.learningShape",help ="must be a shapeFile",dest = "inlearningShape",required=True)
	parser.add_argument("-out.learningShape",help ="",dest = "outlearningShape",required=True)
	parser.add_argument("-mask",help ="",dest = "mask",required=True)
	parser.add_argument("-classificationRaster",help ="",dest = "classificationRaster",required=True)
	parser.add_argument("-validityRaster",help ="",dest = "validityRaster",required=True)
	parser.add_argument("-validityThreshold",type = int,help ="",dest = "validityThreshold",required=True)
	parser.add_argument("-tile",help ="",dest = "tile",required=True)
	parser.add_argument("-dataField",help ="",dest = "dataField",required=True)
	parser.add_argument("-workingDirectory",help ="",dest = "workingDirectory",default = None,required=None)
	parser.add_argument("-classToKeep",type = int,nargs='+',help ="",dest = "classToKeep",required=True)
	parser.add_argument("-targetResolution",type = int,help ="",dest = "rasterResolution",required=True)
	parser.add_argument("-gdalDriver",help ="",dest = "gdalDriver",required=True)
	parser.add_argument("-coeff",help ="between 0 and 1",dest = "coeff",required=True)
	parser.add_argument("-epsg",help ="epsg code",dest = "coeff",required=True)
	parser.add_argument("-wc",type = coordParse,nargs='+',help ="do not use these coordinates (list of tuple) X,Y X,Y ... in projection system",dest = "coord",required=False,default = [()])

	args = parser.parse_args()

	genAnnualShapePoints(args.coord,args.gdalDriver,args.workingDirectory,args.rasterResolution,args.classToKeep,args.dataField,args.tile,args.validityThreshold,args.validityRaster,args.classificationRaster,args.mask,args.inlearningShape,args.outlearningShape,args.coeff,args.epsg)











