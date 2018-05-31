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
#import sys
#import os
#import random
#from random import randrange
import logging
from config import Config
#from osgeo import gdal, ogr, osr
#import repInShape as rs
from Common import FileUtils as fu

logger = logging.getLogger(__name__)


def SplitShape(shapeIN, dataField, folds, outPath, outName):
    """
    this function split a shape in "folds" new shape.
    IN :
        shapeIN [string] : path to the shape to split
        dataField [string] : data's Field into shape
        folds [int] : number of split
        outPath [string] : path to the store new shapes
        outName [string] : new shapes names
    OUT :
        "folds" new shapes
    """

    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(shapeIN, 0)
    layer = dataSource.GetLayer()
    buff = []
    for feature in layer:
        FID = feature.GetFID()
        cl = feature.GetField(dataField)
        buff.append([cl, FID])

    buff = fu.sortByFirstElem(buff)
    cl_fold = []
    for cl, FID_cl in buff:
        fold = fu.splitList(FID_cl, folds)
        cl_fold.append([cl, fold])

    id_fold = []
    for i in range(len(cl_fold)):
        foldNumber = 1
        for currentFold in cl_fold[i][1]:
            for FID in currentFold:
                id_fold.append([foldNumber, FID])
            foldNumber += 1

    id_fold = fu.sortByFirstElem(id_fold)#[[foldNumber,[allClassFID]],[],...]
    shapeCreated = []
    for foldNumber, AllFID in id_fold:
        listFid = []
        for fid in AllFID:
            listFid.append("FID="+str(fid))
        resultA = []
        for e in listFid:
            resultA.append(e)
            resultA.append(' OR ')
            resultA.pop()
        chA = ''.join(resultA)
        layer.SetAttributeFilter(chA)

        origin_name = outName.split("_")
        origin_name[2] = origin_name[2]+"f"+str(foldNumber)
        nameOut = "_".join(origin_name)

        outShapefile = outPath+"/"+nameOut
        AllFields = fu.getAllFieldsInShape(shapeIN, "ESRI Shapefile")
        fu.CreateNewLayer(layer, outShapefile, AllFields)
        shapeCreated.append(outShapefile)
    return shapeCreated


def split_All_shape(shape, folds, pathConf, pathWd, logger=logger):


    f = file(pathConf)
    cfg = Config(f)
    regionField = cfg.chain.regionField
    outputpath = cfg.chain.outputPath
    dataField = cfg.chain.dataField

    workingDirectory = outputpath+"/dataAppVal"
    if pathWd != None:
        workingDirectory = pathWd

    logger.info("Split in %s folds the shape : %s"%(folds, shape))
    createdShape = SplitShape(shape, dataField, folds, workingDirectory, shape.split("/")[-1])

    if pathWd != None:
        for NewShape in createdShape:
            fu.cpShapeFile(NewShape.replace(".shp", ""), outputpath+"/dataAppVal", [".prj", ".shp", ".dbf", ".shx"], spe=True)

    fu.removeShape(shape.replace(".shp", ""), [".prj", ".shp", ".dbf", ".shx"])


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="this function allow you to split a shape in N equivalent folds (by class)")
    parser.add_argument("-path.shape", dest="shape", help="path to the shapeFile to split", required=True)
    parser.add_argument("-Nsplit", type=int, dest="folds", help="number of split of the shapeFile", required=True)
    parser.add_argument("-config", help="path to the configuration file which describe the learning method (mandatory)", dest="pathConf", required=True)
    parser.add_argument("--wd", dest="pathWd", help="path to the working directory", default=None, required=False)
    args = parser.parse_args()

    split_All_shape(args.shape, args.folds, args.pathConf, args.pathWd)





