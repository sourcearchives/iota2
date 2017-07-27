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
import sys,os,random
from osgeo import gdal, ogr,osr
import fileUtils as fu
import NbView
from config import Config

def ExtractData(pathToClip, shapeData, pathOut, pathFeat, cfg, pathWd):
    """
        Clip the shapeFile pathToClip with the shapeFile shapeData and store it in pathOut
    """
    
    pathConf = cfg.pathConf

    cloud_threshold = str(cfg.getParam('chain', 'cloud_threshold'))
    featuresPath = cfg.getParam('chain', 'featuresPath')

    currentTile = pathToClip.split("_")[-1].split(".")[0]

    driver = ogr.GetDriverByName('ESRI Shapefile')

    dataSource = driver.Open(pathToClip, 0) # 0 means read-only. 1 means writeable.
    # Check to see if shapefile is found.
    if dataSource is None:
        print 'Could not open %s' % (pathToClip)
    else:
        layer = dataSource.GetLayer()
        featureCount = layer.GetFeatureCount()

        if featureCount!=0:
            pathName = pathWd
            if pathWd == None:
                pathName = pathOut
            CloudMask = featuresPath+"/"+currentTile+"/CloudThreshold_"+cloud_threshold+".shp"
            NbView.genNbView(featuresPath+"/"+currentTile,CloudMask,cloud_threshold,pathConf,pathWd)

            path_tmp = fu.ClipVectorData(shapeData,pathFeat+"/"+currentTile+"/tmp/MaskCommunSL.shp", pathName)
            path_tmp2 = fu.ClipVectorData(path_tmp, pathToClip, pathName)
            path = fu.ClipVectorData(path_tmp2, CloudMask, pathName)
            if fu.multiSearch(path):
                NoMulti = path.replace(".shp","_NoMulti.shp")
                fu.multiPolyToPoly(path,NoMulti)
                fu.removeShape(path.replace(".shp",""),[".prj",".shp",".dbf",".shx"])
                fu.cpShapeFile(NoMulti.replace(".shp",""),path.replace(".shp",""),[".prj",".shp",".dbf",".shx"])
                fu.removeShape(NoMulti.replace(".shp",""),[".prj",".shp",".dbf",".shx"])
            if pathWd != None:
                fu.cpShapeFile(path.replace(".shp",""),pathOut+"/"+path.split("/")[-1].replace(".shp",""),[".prj",".shp",".dbf",".shx"])
            else:
                fu.removeShape(path_tmp.replace(".shp",""),[".prj",".shp",".dbf",".shx"])
                fu.removeShape(path_tmp2.replace(".shp",""),[".prj",".shp",".dbf",".shx"])

if __name__ == "__main__":

    import serviceConfigFile as SCF
    parser = argparse.ArgumentParser(description = "This function allow you to create N training and N validation shapes by regions cut by tiles")
    parser.add_argument("-shape.region",help ="path to a shapeFile representing the region in one tile (mandatory)",dest = "clip",required=True)
    parser.add_argument("-shape.data",dest = "dataShape",help ="path to the shapeFile containing datas (mandatory)",required=True)
    parser.add_argument("-out",dest = "pathOut",help ="path where to store all shapes by tiles (mandatory)",required=True)
    parser.add_argument("-path.feat",dest = "pathFeat",help ="path where features are stored (mandatory)",required=True)
    parser.add_argument("-conf",help ="path to the configuration file which describe the classification (mandatory)",dest = "pathConf",required=False)
    parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)

    ExtractData(args.clip, args.dataShape, args.pathOut, args.pathFeat, cfg, args.pathWd)

