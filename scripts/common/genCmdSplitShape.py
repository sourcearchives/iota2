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
import random
import math
from osgeo import gdal, ogr, osr
from random import randrange
import repInShape as rs
from config import Config
import fileUtils as fu

def getAreaByRegion(allShape):
    """
        IN :
            allShape [list] : list of path to ground truth shapeFile
        OUT :
            allArea [list] list of ground truth's area by regions in meter square
    """
    shapeSort = []
    for shape in allShape:
        region = shape.split("_")[-4]
        shapeSort.append([region, shape])
    shapeSort = fu.sortByFirstElem(shapeSort)
    allArea = []
    for region, shapesRegion in shapeSort:
        area = 0
        for shapeF in shapesRegion:
            area += rs.getShapeSurface(shapeF)
        allArea.append([region, area])
    return allArea

def genCmdSplitShape(cfg):

    config = cfg.pathConf

    maxArea = float(cfg.getParam('chain', 'mode_outside_RegionSplit'))
    outputpath = cfg.getParam('chain', 'outputPath')
    dataField = cfg.getParam('chain', 'dataField')
    execMode = cfg.getParam('chain', 'executionMode')
    scripts_path = cfg.getParam('chain', 'pyAppPath')

    allShape = fu.fileSearchRegEx(outputpath+"/dataRegion/*.shp")
    allArea = getAreaByRegion(allShape)

    workingDir = " --wd $TMPDIR "
    if execMode == "sequential":
        workingDir = " "

    print "all area [square meter]:"
    print allArea
    shapeToSplit = []

    dic = {}#{'region':Nsplits, ..}
    for region, area in allArea:
        fold = math.ceil(area/(maxArea*1e6))
        dic[region] = fold

    TooBigRegions = [region for region in dic if dic[region] > 1]

    print "Too big regions"
    print TooBigRegions

    for bigR in TooBigRegions:
        tmp = fu.fileSearchRegEx(outputpath+"/dataAppVal/*_region_"+bigR+"*.shp")
        for shapeTmp in tmp:
            shapeToSplit.append(shapeTmp)
    print shapeToSplit

    #write cmds
    AllCmd = []
    for currentShape in shapeToSplit:
        currentRegion = currentShape.split('/')[-1].split("_")[2].split("f")[0]
        cmd = "python "+scripts_path+"/splitShape.py -config "+config+" -path.shape "+currentShape+" -Nsplit "+str(int(dic[currentRegion]))+" "+workingDir
        AllCmd.append(cmd)
    fu.writeCmds(outputpath+"/cmd/splitShape/splitShape.txt", AllCmd)
    return AllCmd


if __name__ == "__main__":

    from Common import ServiceConfigFile as SCF
    parser = argparse.ArgumentParser(description="this function allow you to split a shape regarding a region shape")
    parser.add_argument("-config", dest="config", help="path to configuration file", required=True)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.config)

    genCmdSplitShape(cfg)










