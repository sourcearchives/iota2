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
import logging
from collections import Counter
import numpy as np
from osgeo import ogr
from osgeo.gdalconst import *
from config import Config
import fileUtils as fu

logger = logging.getLogger(__name__)

def getSeconde(item):
    return item[1]

def getShapeSurface(ShapeF):
    """
    In : a shapeFile
    out : area in square unit of the system reference of the shapeFile (for the chain, this must be meters)
    """
    surf = 0.0
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(ShapeF, 0)
    layer = dataSource.GetLayer()
    for feature in layer:
        geom = feature.GetGeometryRef()
        surf += geom.GetArea()
    return surf

def repartitionInShape(ShapeF, dataField, resol, logger=logger):

    """

    """
    driver = ogr.GetDriverByName("ESRI Shapefile")
    buff = []#[(class, Area)...]
    buff_statTMP = []
    AllClass = []

    print ShapeF
    dataSource = driver.Open(ShapeF, 0)
    layer = dataSource.GetLayer()
    #get all class in the current shape
    for feature in layer:
        try:
            ind = AllClass.index(feature.GetField(dataField))
        except ValueError:
            AllClass.append(int(feature.GetField(dataField)))

    AllClass.sort()
    for currentClass in AllClass:
        buff.append([currentClass, 0.0])

    dataSource = driver.Open(ShapeF, 0)
    layer = dataSource.GetLayer()
    for feature in layer:
        feat = feature.GetField(dataField)
        geom = feature.GetGeometryRef()
        Area = geom.GetArea()
        try:
            ind = AllClass.index(feat)
            if resol != None:
                buff[ind][1] += float(Area)/(float(resol)*float(resol))
                buff_statTMP.append([feat, float(Area)/(float(resol)*float(resol))])
            else:
                buff[ind][1] += float(Area)
                buff_statTMP.append([feat, Area])
        except ValueError:
            logger.error("Problem in repartitionClassByTile")

    buff = sorted(buff, key=getSeconde)

    Allsurf = 0
    for cl, surf in buff:
        Allsurf += surf
    genStat = []
    for cl, surf in buff:
        genStat.append([cl, float(surf)/float(Allsurf)])
    buff_statTMP = fu.sortByFirstElem(buff_statTMP)
    buff_stat = []
    for cla, listP in buff_statTMP:
        tmpL = np.asarray(listP)
        sumA = np.sum(tmpL)
        mini = tmpL.min()
        maxi = tmpL.max()
        mean = np.mean(tmpL)
        med = np.median(tmpL)

        buff_stat.append([cla, "min : "+str(mini), "max : "+str(maxi), "mean : "+str(mean), "med : "+str(med), "sum : "+str(sumA)])
    return buff

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="This function try to rearrange the repartition tile by model, considering class repartition")
    parser.add_argument("-path.shape", dest="shape", help="shape (mandatory)", nargs='+', required=True)
    parser.add_argument("-dataField", dest="dataField", help="field of datas (mandatory)", required=True)
    parser.add_argument("--resol", dest="resol", type=int, help="resolution", required=False, default=None)
    args = parser.parse_args()

    repartitionInShape(args.shape, args.dataField, args.resol)




