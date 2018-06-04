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

import os
import argparse
import numpy as np
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from osgeo.gdalconst import *
from Common.Utils import run


def getRasterResolution(rasterIn):
    raster = gdal.Open(rasterIn, GA_ReadOnly)
    if raster is None:
        raise Exception("can't open "+rasterIn)
    geotransform = raster.GetGeoTransform()
    spacingX = geotransform[1]
    spacingY = geotransform[5]
    return spacingX, spacingY

def getRasterExtent(raster_in):
    """
        Get raster extent of raster_in from GetGeoTransform()
		ARGs:
              INPUT:
                  - raster_in: input raster
              OUTPUT
                  - ex: extent with [minX,maxX,minY,maxY]
    """

    retour = []
    if not os.path.isfile(raster_in):
        pass
    else:
        raster = gdal.Open(raster_in, GA_ReadOnly)
        if raster is None:
            pass
        else:
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
            retour = [minX, maxX, minY, maxY]

    # On renvoie la liste en fonction des cas
    return retour

def getFieldType(layer, field):

    layerDefinition = layer.GetLayerDefn()
    fieldDef = {}
    fieldList = []
    for i in range(layerDefinition.GetFieldCount()):
        fieldName = layerDefinition.GetFieldDefn(i).GetName()
        fieldList.append('"'+fieldName+'"')
        fieldTypeCode = layerDefinition.GetFieldDefn(i).GetType()
        fieldType = layerDefinition.GetFieldDefn(i).GetFieldTypeName(fieldTypeCode)
        if fieldType == "Integer": fieldDef[fieldName] = int
        elif fieldType == "String": fieldDef[fieldName] = str

    retour = None
    try:
        retour = fieldDef[field]
    except:
        raise Exception('Field : "'+field+'" not in field\'s list : '+' , '.join(fieldList))
    return retour

def getAllGeom(layer, field, valField):
    fieldType = getFieldType(layer, field)
    allGeom = []
    for currentFeat in layer:
        for currentVal in valField:
            if currentFeat.GetField(field) == fieldType(currentVal):
                geom = currentFeat.GetGeometryRef()
                if geom.GetGeometryName() == 'MULTIPOLYGON':
                    for geom_part in geom:
                        allGeom.append(geom_part.Clone())
                else:
                    allGeom.append(geom.Clone())
    return allGeom

def matchGrid(val, grid):
    return min(grid, key=lambda x: abs(x-val))

def getBBox(raster_in, allGeom):

    multipolygon = ogr.Geometry(ogr.wkbMultiPolygon)
    for currentGeom in allGeom:
        multipolygon.AddGeometry(currentGeom)
    minX, maxX, minY, maxY = multipolygon.GetEnvelope()
    minXe, maxXe, minYe, maxYe = getRasterExtent(raster_in)
    spacingX, spacingY = getRasterResolution(raster_in)

    #match polygon's envelope and raster grid
    Xgrid = np.arange(minXe, maxXe+spacingX)
    Ygrid = np.arange(minYe, maxYe-spacingY)

    minX = matchGrid(minX, Xgrid)
    maxX = matchGrid(maxX, Xgrid)
    minY = matchGrid(minY, Ygrid)
    maxY = matchGrid(maxY, Ygrid)

    return minX, maxX, minY, maxY

def generateRaster(raster_path, features_path, driver, field, valField, output, epsg):
    """
    """

    driver = ogr.GetDriverByName(driver)
    features = driver.Open(features_path, 0)
    if features is None: 
        raise Exception("Could not open "+features_path)
    lyr = features.GetLayer()
    allGeom = getAllGeom(lyr, field, valField)
    minX, maxX, minY, maxY = getBBox(raster_path, allGeom)

    layerName = features_path.split("/")[-1].split(".")[0]
    fieldType = getFieldType(lyr, field)
    sep = ""
    if not isinstance(fieldType, int): sep = "'"
    valField = ["("+field+"="+sep+currentValToKeep+sep+")" for currentValToKeep in valField]
    csql = " OR ".join(valField)

    sizeX, sizeY = getRasterResolution(raster_path)
    cmd = "gdalwarp -overwrite -t_srs EPSG:"+str(epsg)+" -tr "+str(sizeX)+" "+str(sizeX)+" -of GTiff -cl "+layerName+" -csql \"SELECT * FROM "+layerName+" WHERE ("+csql+")\" -ot Byte -te "+str(minX)+" "+str(minY)+" "+str(maxX)+" "+str(maxY)+" -cutline "+features_path+" -crop_to_cutline "+raster_path+" "+output
    run(cmd)

    ds = gdal.Open(output, GA_Update)
    proj = ds.GetProjection()
    gt = ds.GetGeoTransform()
    gt2 = (minX, sizeX, gt[2], maxY, gt[4], sizeY)

    ds.SetGeoTransform(gt2)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="extract ROI in raster defined by a shapeFile")
    parser.add_argument("-in.raster", dest="raster_path", help="path to the classification.tif", default=None, required=True)
    parser.add_argument("-in.vector", dest="features_path", help="vector's path", default=None, required=True)
    parser.add_argument("-in.vector.type", dest="driver", help="vector's type", choices=["ESRI Shapefile", "SQLite"], required=True)
    parser.add_argument("-in.vector.dataField", dest="field", help="data's field", default=None, required=True)
    parser.add_argument("-in.vector.dataField.values", dest="valField", help="features to consider", default=None, required=True, nargs='+')
    parser.add_argument("--out.EPSG.code", dest="epsg", help="epsg code, default : 2154", type=int, default=2154, required=False)
    parser.add_argument("-out", dest="output", help="output raster", default=None, required=True)
    args = parser.parse_args()

    generateRaster(args.raster_path, args.features_path, args.driver, args.field, args.valField, args.output, args.epsg)
