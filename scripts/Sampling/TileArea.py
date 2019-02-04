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
import logging
import os
import math
from config import Config
from osgeo import gdal, ogr, osr
from Common import FileUtils as fu
from Common import ServiceConfigFile as SCF
from Common.Utils import run

logger = logging.getLogger(__name__)

def AddFieldModel(shpIn, modNum, fieldOut, logger=logger):

    """
        add a field to a shapeFile and for every feature, add an ID
        IN :
            - shpIn : a shapeFile
            - modNum : the number to associate to features
            - fieldOut : the new field name
        OUT :
            - an update of the shape file in
    """
    source = ogr.Open(shpIn, 1)
    layer = source.GetLayer()
    layer_defn = layer.GetLayerDefn()
    new_field = ogr.FieldDefn(fieldOut, ogr.OFTInteger)
    layer.CreateField(new_field)

    for feat in layer:
        if feat.GetGeometryRef():
            layer.SetFeature(feat)
            feat.SetField(fieldOut, modNum)
            layer.SetFeature(feat)
        else:
            logger.debug("feature " + str(feat.GetFID()) + " has not geometry")


def CreateModelShapeFromTiles(tilesModel, pathTiles, proj, pathOut, OutSHPname, fieldOut, pathWd):

    """
        create one shapeFile where all features belong to a model number according to the model description

        IN :
            - tilesModel : a list of list which describe which tile belong to which model
                ex : for 3 models
                    tile model 1 : D0H0,D0H1
                    tile model 2 : D0H2,D0H3
                    tile model 3 : D0H4,D0H5,D0H6

                    tilesModel = [["D0H0","D0H1"],["D0H2","D0H3"],["D0H4","D0H5","D0H6"]]
            - pathTiles : path to the tile's envelope with priority consideration
                ex : /xx/x/xxx/x
                /!\ the folder which contain the envelopes must contain only the envelopes   <========
            - proj : projection
                ex : 2154
            - pathOut : path to store the resulting shapeFile
                ex : x/x/x/xxx
            - OutSHPname : the name of the resulting shapeFile
                ex : "model"
            - fieldOut : the name of the field which will contain the model number
                ex : "Mod"
            - pathWd : path to working directory (not mandatory, due to cluster's architecture default = None)

        OUT :
            a shapeFile which contains for all feature the model number which it belong to
    """
    if pathWd is None:
        pathToTMP = pathOut + "/AllTMP"
    else:
        # HPC case
        pathToTMP = pathWd
    if not os.path.exists(pathToTMP):
        run("mkdir " + pathToTMP)

    to_remove = []
    for i in range(len(tilesModel)):
        for j in range(len(tilesModel[i])):
            to_remove.append(fu.renameShapefile(pathTiles, tilesModel[i][j], "", "", pathToTMP))

    AllTilePath = []
    AllTilePath_ER = []

    for i in range(len(tilesModel)):
        for j in range(len(tilesModel[i])):
            try:
                ind = AllTilePath.index(pathTiles + "/" + tilesModel[i][j] + ".shp")
            except ValueError:
                AllTilePath.append(pathToTMP + "/" + tilesModel[i][j] + ".shp")
                AllTilePath_ER.append(pathToTMP + "/" + tilesModel[i][j] + "_ERODE.shp")

    for i in range(len(tilesModel)):
        for j in range(len(tilesModel[i])):
            currentTile = pathToTMP + "/" + tilesModel[i][j] + ".shp"
            AddFieldModel(currentTile, i + 1, fieldOut)

    for path in AllTilePath:
        fu.erodeShapeFile(path, path.replace(".shp", "_ERODE.shp"), 0.1)

    fu.mergeVectors(OutSHPname, pathOut, AllTilePath_ER)
    if not pathWd:
        run("rm -r " + pathToTMP)
    else:
        for rm in to_remove:
            fu.removeShape(rm.replace(".shp",""), [".prj",".shp",".dbf",".shx"])


def generateRegionShape(pathTiles, pathToModel, pathOut, fieldOut, cfg,
                        pathWd, logger=logger):
    """
        create one shapeFile where all features belong to a model number according to the model description

        IN :
            - pathTiles : path to the tile's envelope with priority consideration
                ex : /xx/x/xxx/x
                /!\ the folder which contain the envelopes must contain only the envelopes   <========
            - pathToModel : path to the text file which describe which tile belong to which model
                the text file must have the following format :

                R1 : D0003H0005,D0004H0005
                R2 : D0005H0005,D0005H0004
                R3 : D0003H0004,D0004H0004
                R4 : D0003H0003,D0004H0003,D0005H0003

                for 4 models and 9 tiles
            - pathOut : path to store the resulting shapeFile
            - fieldOut : the name of the field which will contain the model number
                ex : "Mod"
            - pathWd : path to working directory (not mandatory, due to cluster's architecture default = None)

        OUT :
            a shapeFile which contains for all feature the model number which it belong to
    """

    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)
    pathConf = cfg.pathConf

    tmp_proj = cfg.getParam('GlobChain', 'proj')
    proj = int(tmp_proj.split(":")[-1])
    
    region = []
    AllTiles = fu.FileSearch_AND(pathTiles, False, ".shp")
    region.append(AllTiles)
    
    if not pathOut:
        pathOut = os.path.join(cfg.getParam("chain", "outputPath") , "MyRegion.shp")

    p_f = pathOut.replace(" ", "").split("/")
    outName = p_f[-1].split(".")[0]
    
    pathMod = ""
    for i in range(1, len(p_f)-1):
        pathMod = pathMod+"/"+p_f[i]
    
    CreateModelShapeFromTiles(region, pathTiles, int(proj), pathMod, outName, fieldOut, pathWd)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=\
                                     "This function allow you to create a shape by tile for a given area and a given region")
    parser.add_argument("-fieldOut", dest="fieldOut",\
                            help="field out (mandatory)", required=True)
    parser.add_argument("-pathTiles", dest="pathTiles",\
                            help="path where are only stored tile's envelope (mandatory)", default="None", required=True)
    parser.add_argument("--multi.models", dest="pathToModel",\
                            help="path to the text file which link tiles/models", default="None", required=False)
    parser.add_argument("-out", dest="pathOut",\
                            help="path where to store all shape by tiles (mandatory)", default="None", required=True)
    parser.add_argument("--wd", dest="pathWd",\
                            help="path to the working directory", default=None, required=True)
    parser.add_argument("-conf", dest="pathConf",\
                            help="path to the configuration file which describe the learning method (mandatory)", required=True)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)

    generateRegionShape(args.pathTiles, args.pathToModel, args.pathOut,
                        args.fieldOut, cfg, args.pathWd)
