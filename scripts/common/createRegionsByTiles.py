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
import sys
import os
import logging
import random
from osgeo import gdal, ogr, osr
from Common import FileUtils as fu
from Common.Utils import run

logger = logging.getLogger(__name__)


def splitVectorLayer(shp_in, attribute, attribute_type, field_vals, pathOut):
    """
        Split a vector layer in function of its attribute
        ARGs:
            INPUT:
                - shp_in: input shapefile
                - attribute: attribute to look for
                - attribute_type: attribute type which could be "string" or "int"
            OUTPUT
                - shp_out_list: list of shapefile names
    """
    short_shp_in = shp_in.split('.')
    shp_out_list = []
    name = shp_in.split("/")[-1].split(".")[0]

    if attribute_type == "string":
        for val in field_vals:
            if val != "None":
                shp_out = pathOut+"/"+name+"_region_"+str(val)+".shp"
                if (not os.path.isfile(shp_out)):
                    cmd = "ogr2ogr "
                    cmd += "-where '" + attribute + ' = "' + val + '"' + "' "
                    cmd += shp_out + " "
                    cmd += shp_in + " "
                    run(cmd)
                shp_out_list.append(shp_out)

    elif attribute_type == "int":
        for val in field_vals:
            shp_out = pathOut+"/"+name+"_region_"+str(val)+".shp"

            if (not os.path.isfile(shp_out)):
                cmd = "ogr2ogr "
                cmd += "-where '" + attribute + " = " + str(val) + "' "
                cmd += shp_out + " "
                cmd += shp_in + " "
                run(cmd)
            shp_out_list.append(shp_out)
    else:
        raise Exception("Error for attribute_type ", attribute_type, '! Should be "string" or "int"')

    return shp_out_list


def createRegionsByTiles(shapeRegion, field_Region, pathToEnv, pathOut, pathWd,
                         logger_=logger):

    """
    create a shapeFile into tile's envelope for each regions in shapeRegion and for each tiles
    IN :
        - shapeRegion : the shape which contains all regions
        - field_Region : the field into the region's shape which describes each tile belong to which model
        - pathToEnv : path to the tile's envelope with priority
        - pathOut : path to store all resulting shapeFile
        - pathWd : path to working directory (not mandatory, due to cluster's architecture default = None)
    """
    pathName = pathWd
    if pathWd == None:
        #sequential case
        pathName = pathOut

    #getAllTiles
    AllTiles = fu.FileSearch_AND(pathToEnv, True, ".shp")
    regionList = fu.getFieldElement(shapeRegion, "ESRI Shapefile", field_Region, "unique")
    shpRegionList = splitVectorLayer(shapeRegion, field_Region, "int", regionList, pathName)
    AllClip = []
    for shp in shpRegionList:
        for tile in AllTiles:
            logger_.info("Extract %s in %s", shp, tile)
            pathToClip = fu.ClipVectorData(shp, tile, pathName)
            AllClip.append(pathToClip)
        
    if pathWd:
        for clip in AllClip:
            cmd = "cp "+clip.replace(".shp", "*")+" "+pathOut
            run(cmd)
    else:
        for shp in shpRegionList:
            path = shp.replace(".shp", "")
            os.remove(path+".shp")
            os.remove(path+".shx")
            os.remove(path+".dbf")
            os.remove(path+".prj")

    return AllClip
	
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="This function allow you to create a region per tile")

    parser.add_argument("-region.shape", help="path to the region shape (mandatory)", dest="region", required=True)
    parser.add_argument("-region.field", dest="regionField", help="region's field into shapeFile, must be an integer field (mandatory)", required=True)
    parser.add_argument("-tiles.envelope", dest="pathToEnv", help="path where tile's Envelope are stored (mandatory)", required=True)
    parser.add_argument("-out", dest="pathOut", help="path where to store all shapes by tiles (mandatory)", required=True)
    parser.add_argument("--wd", dest="pathWd", help="path to the working directory", default=None, required=True)
    args = parser.parse_args()

    createRegionsByTiles(args.region, args.regionField, args.pathToEnv, args.pathOut, args.pathWd)















