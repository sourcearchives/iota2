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
import os
import gdal
import ogr
import osr
from Common import FileUtils as fut
import random
from Common.Utils import run
import shutil

def genRasterEnvelope(raster, outputShape):
    """
    raster [string]
    workingDir [string] workingDirectory
    """
    rasterName = os.path.splitext(os.path.split(raster)[-1])[0]

    minX, maxX, minY, maxY = fut.getRasterExtent(raster)
    epsg = fut.getRasterProjectionEPSG(raster)

    driver = ogr.GetDriverByName("ESRI Shapefile")
    data_source = driver.CreateDataSource(outputShape)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(int(epsg))

    out_lyr = data_source.CreateLayer(rasterName, srs, geom_type=ogr.wkbPolygon)

    field_ext = ogr.FieldDefn("ext", ogr.OFTString)
    field_ext.SetWidth(24)
    out_lyr.CreateField(field_ext)

    #geom
    ul = (minX, maxY)
    ur = (maxX, maxY)
    lr = (maxX, minY)
    ll = (minX, minY)
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(ul[0], ul[1])
    ring.AddPoint(ur[0], ur[1])
    ring.AddPoint(lr[0], lr[1])
    ring.AddPoint(ll[0], ll[1])
    ring.AddPoint(ul[0], ul[1])

    # Create polygon
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)

    feature = ogr.Feature(out_lyr.GetLayerDefn())
    feature.SetField("ext", "extent")
    feature.SetGeometry(poly)
    out_lyr.CreateFeature(feature)
    feature = data_source = None

    return outputShape


def genIntersectionShape(vector1, vector2, vector_out):
    """
    create intersection between vector1 and vector2 in vector_out
    vector1 and vector2 must contains only one geometry and being in
    the same projection

    Output
    intersection area
    """

    #V1
    driver1 = ogr.GetDriverByName('ESRI Shapefile')
    dataSource1 = driver1.Open(vector1, 0)
    layer1 = dataSource1.GetLayer()
    spatialRef = layer1.GetSpatialRef()
    for feature in layer1:
        geom1 = feature.GetGeometryRef()

    #V2
    driver2 = ogr.GetDriverByName('ESRI Shapefile')
    dataSource2 = driver2.Open(vector2, 0)
    layer2 = dataSource2.GetLayer()

    for feat in layer2:
        geom2 = feat.GetGeometryRef()

    intersection_geom = geom1.Intersection(geom2)

    vector_out_name = os.path.splitext(os.path.split(vector_out)[-1])[0]
    driver = ogr.GetDriverByName("ESRI Shapefile")
    data_source = driver.CreateDataSource(vector_out)
    out_lyr = data_source.CreateLayer(vector_out_name, spatialRef, geom_type=ogr.wkbPolygon)

    field_inter = ogr.FieldDefn("inters", ogr.OFTString)
    field_inter.SetWidth(24)
    out_lyr.CreateField(field_inter)
    feature = ogr.Feature(out_lyr.GetLayerDefn())
    feature.SetField("inters", "inters")

    feature.SetGeometry(intersection_geom)
    out_lyr.CreateFeature(feature)
    feature = data_source = None

    if intersection_geom.GetArea() != 0:
        return True
    return False


def upperLeft(item):
    """
    function use to sort a list
    item[1] = minX, maxX, minY, maxY
    """
    #upperLeft
    return item[1][2], item[1][1]


def mosaicFromShape(rasters, shape, rasterOut, workingDir=None):
    """
    usage : from a shape clip rasters and mosaic them (upper left priority).

    IN
    rasters [list of string] : path to rasters
    shape [string] : vector pathg
    rasterOut [string] : output path
    workingDir [string]

    OUT
    """

    #sort input raster by origin (upperLeft)
    rasters_p = sorted([(raster, fut.getRasterExtent(raster)) for raster in rasters], key=upperLeft)[::-1]

    outputDirectory = os.path.split(rasterOut)[0]
    wDir = outputDirectory
    tmp_files_vec = []
    tmp_files_raster = []

    if workingDir:
        wDir = workingDir

    for raster, coordinates in rasters_p:
        rasterName = os.path.splitext(os.path.split(raster)[-1])[0]
        raster_footPrint = os.path.join(wDir, rasterName + ".shp")
        if os.path.exists(raster_footPrint):
            while os.path.exists(raster_footPrint):
                raster_footPrint = raster_footPrint.replace(".shp", "_" + str(random.randint(1, 1000)) + ".shp")

        #raster footPrint
        genRasterEnvelope(raster, raster_footPrint)
        tmp_files_vec.append(raster_footPrint)

        clip = raster_footPrint.replace(".shp", "_Clip.shp")
        clip_raster = raster_footPrint.replace(".shp", "_Clip.tif")
        inter = genIntersectionShape(raster_footPrint, shape, clip)

        cmd = "gdalwarp -crop_to_cutline -cutline " + clip + " " + raster + " " + clip_raster
        run(cmd)
        tmp_files_raster.append(clip_raster)
        tmp_files_vec.append(clip)

    #mosaic using gdal_merge.py, the last image will be copied over earlier ones
    rasters_clip = " ".join(tmp_files_raster[::-1])
    cmd = "gdal_merge.py -o " + rasterOut + " -n 0 " + rasters_clip
    run(cmd)

    #clean tmp files
    for vec in tmp_files_vec:
        fut.removeShape(vec.replace(".shp", ""), [".prj", ".shp", ".dbf", ".shx"])
    for img in tmp_files_raster:
        os.remove(img)

    if workingDir:
        shutil.copy(rasterOut, outputDirectory)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="This function allow you to mosaic rasters thanks to shape extent")
    parser.add_argument("-rasters", help="path to rasters to clip (mandatory)",
                        dest="rasters", required=True, nargs='+')
    parser.add_argument("-shape", help="path to the shape use to clip rasters. It must contain only one geometry (mandatory)",
                        dest="shape", required=True)
    parser.add_argument("-out", help="output raster path (mandatory)",
                        dest="rasterOut", required=True)
    parser.add_argument("-working.directory", help="working directory",
                        dest="wD", required=False)

    args = parser.parse_args()
    mosaicFromShape(args.rasters, args.shape, args.rasterOut, args.wD)
