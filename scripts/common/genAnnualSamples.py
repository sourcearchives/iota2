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
import logging
import os
import argparse
import random
import osr
import numpy as np
import fileUtils as fu
from osgeo import gdal
from osgeo import ogr
from osgeo.gdalconst import *
import otbApplication as otb
fu.updatePyPath()
from AddField import addField

logger = logging.getLogger(__name__)

def coordParse(s):
    try:
        x, y = map(float, s.split(", "))
        return (x, y)
    except:
        raise argparse.ArgumentTypeError("Coordinates must be x, y")

def getNbSample(shape, tile, dataField, valToFind, resol, region, coeff, current_seed,
                region_field, region_val="-1"):

    driver = ogr.GetDriverByName("ESRI Shapefile")
    buff = []
    dataSource = driver.Open(shape, 0)
    layer = dataSource.GetLayer()
    for feature in layer:
        if str(feature.GetField(dataField)) in valToFind and str(feature.GetField(region_field)) == str(region_val) and str(feature.GetField("seed_"+str(current_seed))) == "learn":
            geom = feature.GetGeometryRef()
            buff.append((feature.GetField(dataField), geom.GetArea()))
    rep = fu.sortByFirstElem(buff)
    repDict = {}
    for currentClass, currentAreas in rep:
        array = np.asarray(currentAreas)
        totalArea = np.sum(array)
        repDict[currentClass] = int((float(coeff)*totalArea)/(int(resol)*int(resol)))

    return repDict

def raster2array(rasterfn):
    raster = gdal.Open(rasterfn)
    band = raster.GetRasterBand(1)
    return band.ReadAsArray()

def pixCoordinates(x, y, x_origin, y_origin, sizeX, sizeY):
    return ((x+1)*sizeX + x_origin)-sizeX*0.5, ((y)*sizeY + y_origin)-sizeX*0.5

def getAll_regions(tileName, folder):
    allRegion = []
    allShape = fu.FileSearch_AND(folder, True, "learn", tileName, ".shp")
    for currentShape in allShape:
        currentRegion = currentShape.split("/")[-1].split("_")[2]
        if currentRegion not in allRegion:
            allRegion.append(currentRegion)
    return allRegion

def add_origin_fields(origin_shape, output_layer, region_field_name, runs,
                      origin_driver="ESRI Shapefile"):
    """
    usage add field definition from origin_shape to output_layer (except reiong field)

    origin_shape [string] path to a vector file
    output_layer [OGR layer object] output layer
    """

    #TODO ajouter les seeds_ au champs à ne pas rajouter ?
    driver = ogr.GetDriverByName(origin_driver)
    source = driver.Open(origin_shape, 0)
    layer = source.GetLayer()
    layerDefinition = layer.GetLayerDefn()

    output_layers_fields = [output_layer.GetLayerDefn().GetFieldDefn(i).GetName() for i in range(output_layer.GetLayerDefn().GetFieldCount())]
    output_layers_fields.append(region_field_name)
    for run in range(runs):
        output_layers_fields.append("seed_"+str(run))

    for i in range(layerDefinition.GetFieldCount()):
        fieldName = layerDefinition.GetFieldDefn(i).GetName()
        fieldTypeCode = layerDefinition.GetFieldDefn(i).GetType()
        fieldType = layerDefinition.GetFieldDefn(i).GetFieldTypeName(fieldTypeCode)
        fieldWidth = layerDefinition.GetFieldDefn(i).GetWidth()
        GetPrecision = layerDefinition.GetFieldDefn(i).GetPrecision()

        if fieldName not in output_layers_fields:
            output_layers_fields.append(fieldName)
            output_layer.CreateField(layerDefinition.GetFieldDefn(i))


def genAnnualShapePoints(coord, gdalDriver, workingDirectory, rasterResolution,
                         classToKeep, dataField, tile, validityThreshold,
                         validityRaster, classificationRaster, masks,
                         inlearningShape, outlearningShape, epsg,
                         region_field_name, runs, annu_repartition, logger=logger):

    #Const
    region_pos = 2#in mask name if splited by '_'
    learn_flag = "learn"
    undetermined_flag = "XXXX"

    tile_pos = 0
    currentTile = os.path.splitext(os.path.basename(inlearningShape))[0]
    classifName = currentTile+"_Classif.tif"

    #check HPC mode
    try:
        PathWd = os.environ['TMPDIR']
    except:
        PathWd = None
    projection = int(epsg)

    vector_regions = []
    add = 0

    for current_seed in range(runs):

        for currentMask in masks:
            currentRegion = os.path.split(currentMask)[-1].split("_")[region_pos]
            vector_region = os.path.join(workingDirectory,
                                         "Annual_" + currentTile + "_region_" + currentRegion + "_seed_" + str(current_seed) + ".sqlite")
            vector_regions.append(vector_region)
            rasterRdy = workingDirectory+"/"+classifName.replace(".tif", "_RDY_"+str(currentRegion)+"_seed_" + str(current_seed) + ".tif")


            mapReg = otb.Registry.CreateApplication("ClassificationMapRegularization")
            mapReg.SetParameterString("io.in", classificationRaster)
            mapReg.SetParameterString("ip.undecidedlabel", "0")
            mapReg.Execute()

            useless = otb.Registry.CreateApplication("BandMath")
            useless.SetParameterString("exp", "im1b1")
            useless.SetParameterStringList("il", [validityRaster])
            useless.SetParameterString("ram", "10000")
            useless.Execute()

            uselessMask = otb.Registry.CreateApplication("BandMath")
            uselessMask.SetParameterString("exp", "im1b1")
            uselessMask.SetParameterStringList("il", [currentMask])
            uselessMask.SetParameterString("ram", "10000")
            uselessMask.Execute()

            valid = otb.Registry.CreateApplication("BandMath")
            valid.SetParameterString("exp", "im1b1>"+str(validityThreshold)+"?im2b1:0")
            valid.AddImageToParameterInputImageList("il", useless.GetParameterOutputImage("out"))
            valid.AddImageToParameterInputImageList("il", mapReg.GetParameterOutputImage("io.out"))
            valid.SetParameterString("ram", "10000")
            valid.Execute()

            rdy = otb.Registry.CreateApplication("BandMath")
            rdy.SetParameterString("exp", "im1b1*(im2b1>=1?1:0)")
            rdy.AddImageToParameterInputImageList("il", valid.GetParameterOutputImage("out"))
            rdy.AddImageToParameterInputImageList("il", uselessMask.GetParameterOutputImage("out"))
            rdy.SetParameterString("out", rasterRdy+"?&streaming:type=stripped&streaming:sizemode=nbsplits&streaming:sizevalue=10")
            rdy.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint8)
            rdy.ExecuteAndWriteOutput()

            rasterArray = raster2array(rasterRdy)
            rasterFile = gdal.Open(rasterRdy)
            x_origin, y_origin = rasterFile.GetGeoTransform()[0], rasterFile.GetGeoTransform()[3]
            sizeX, sizeY = rasterFile.GetGeoTransform()[1], rasterFile.GetGeoTransform()[5]

            driver = ogr.GetDriverByName(gdalDriver)
            if os.path.exists(vector_region):
                driver.DeleteDataSource(vector_region)

            data_source = driver.CreateDataSource(vector_region)

            srs = osr.SpatialReference()
            srs.ImportFromEPSG(projection)

            layerName = "output"#layerName
            layerOUT = data_source.CreateLayer(layerName, srs, ogr.wkbPoint)

            add_origin_fields(inlearningShape, layerOUT, region_field_name, runs)

            for currentVal in classToKeep:
                try:
                    nbSamples = annu_repartition[str(currentVal)][currentRegion][current_seed]
                except:
                    logger.info("class : {} does not exists in {} at seed {} in region {}".format(currentVal,
                                                                                                  inlearningShape,
                                                                                                  current_seed,
                                                                                                  currentRegion))
                    continue
                Y, X = np.where(rasterArray == int(currentVal))
                XYcoordinates = []
                for y, x in zip(Y, X):
                    X_c, Y_c = pixCoordinates(x, y, x_origin, y_origin, sizeX, sizeY)
                    XYcoordinates.append((X_c, Y_c))
                if nbSamples > len(XYcoordinates):
                    nbSamples = len(XYcoordinates)
                for Xc, Yc in random.sample(XYcoordinates, nbSamples):#"0" for nbSamples allready manage ?
                    if coord and (Xc, Yc) not in coord:
                        feature = ogr.Feature(layerOUT.GetLayerDefn())
                        feature.SetField(dataField, int(currentVal))
                        wkt = "POINT(%f %f)" % (Xc, Yc)
                        point = ogr.CreateGeometryFromWkt(wkt)
                        feature.SetGeometry(point)
                        layerOUT.CreateFeature(feature)
                        feature.Destroy()
                        add += 1

            data_source.Destroy()
            os.remove(rasterRdy)
            layerOUT = None

            #Add region column and value
            addField(vector_region, region_field_name, str(currentRegion),
                     valueType=str, driver_name="SQLite")

            #Add seed columns and value
            for run in range(runs):
                if run == current_seed:
                    addField(vector_region, "seed_" + str(run), learn_flag,
                             valueType=str, driver_name="SQLite")
                else:
                    addField(vector_region, "seed_" + str(run), undetermined_flag,
                             valueType=str, driver_name="SQLite")

    outlearningShape_name = os.path.splitext(os.path.split(outlearningShape)[-1])[0]
    outlearningShape_dir = os.path.split(outlearningShape)[0]

    fu.mergeSQLite(outlearningShape_name, outlearningShape_dir, vector_regions)

    for vec in vector_regions:
        os.remove(vec)

    if add == 0:
        return False
    else:
        return True

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-in.learningShape", help="must be a shapeFile", dest="inlearningShape", required=True)
    parser.add_argument("-out.learningShape", help="", dest="outlearningShape", required=True)
    parser.add_argument("-mask", help="", dest="mask", required=True)
    parser.add_argument("-classificationRaster", help="", dest="classificationRaster", required=True)
    parser.add_argument("-validityRaster", help="", dest="validityRaster", required=True)
    parser.add_argument("-validityThreshold", type=int, help="", dest="validityThreshold", required=True)
    parser.add_argument("-tile", help="", dest="tile", required=True)
    parser.add_argument("-dataField", help="", dest="dataField", required=True)
    parser.add_argument("-workingDirectory", help="", dest="workingDirectory", default=None, required=None)
    parser.add_argument("-classToKeep", type=int, nargs='+', help="", dest="classToKeep", required=True)
    parser.add_argument("-targetResolution", type=int, help="", dest="rasterResolution", required=True)
    parser.add_argument("-gdalDriver", help="", dest="gdalDriver", required=True)
    parser.add_argument("-epsg", help="epsg code", dest="coeff", required=True)
    parser.add_argument("-wc", type=coordParse, nargs='+', help="do not use these coordinates (list of tuple) X, Y X, Y ... in projection system", dest="coord", required=False, default=[()])

    args = parser.parse_args()

    # TODO: Add the arguments "region_field_name", "runs" and "annu_repartition" that are missing !
    genAnnualShapePoints(args.coord, args.gdalDriver, args.workingDirectory, args.rasterResolution, args.classToKeep, args.dataField, args.tile, args.validityThreshold, args.validityRaster, args.classificationRaster, args.mask, args.inlearningShape, args.outlearningShape, args.epsg)











