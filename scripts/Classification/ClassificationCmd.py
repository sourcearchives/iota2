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
import re
from config import Config
from osgeo import gdal, ogr, osr
from Common import FileUtils as fu
from Common import ServiceConfigFile as SCF
from Common.Utils import run


def launchClassification(model, cfg, stat, pathToRT, pathToImg, pathToRegion,
                         fieldRegion, N, pathToCmdClassif, pathOut, RAM, pathWd):

    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)
    pathConf = cfg.pathConf
    classif = cfg.getParam('argTrain', 'classifier')
    shapeRegion = cfg.getParam('chain', 'regionPath')
    outputPath = cfg.getParam('chain', 'outputPath')
    scriptPath = os.path.join(os.environ.get('IOTA2DIR'), "scripts")
    classifMode = cfg.getParam('argClassification', 'classifMode')
    pixType = fu.getOutputPixType(cfg.getParam('chain', 'nomenclaturePath'))
    Stack_ind = fu.getFeatStackName(pathConf)
    AllCmd = []

    allTiles_s = cfg.getParam('chain', 'listTile')
    allTiles = allTiles_s.split(" ")

    maskFiles = pathOut+"/MASK"
    if not os.path.exists(maskFiles):
        run("mkdir "+maskFiles)

    if pathToRegion is None:
        pathToRegion = os.path.join(cfg.getParam("chain", "outputPath"),
                                    "MyRegion.shp")

    shpRName = pathToRegion.split("/")[-1].replace(".shp", "")

    AllModel_tmp = fu.FileSearch_AND(model, True, "model", ".txt")
    AllModel = fu.fileSearchRegEx(model+"/*model*.txt")

    for currentFile in AllModel_tmp:
        if currentFile not in AllModel:
            os.remove(currentFile)

    for path in AllModel:
        model = path.split("/")[-1].split("_")[1]
        tiles = fu.getListTileFromModel(model, outputPath+"/config_model/configModel.cfg")
        model_Mask = model
        if re.search('model_.*f.*_', path.split("/")[-1]):
            model_Mask = path.split("/")[-1].split("_")[1].split("f")[0]
        seed = path.split("/")[-1].split("_")[-1].replace(".txt", "")
        suffix = ""
        if "SAR.txt" in os.path.basename(path):
            seed = path.split("/")[-1].split("_")[-2]
            suffix = "_SAR" 
        tilesToEvaluate = tiles

        if ("fusion" in classifMode and shapeRegion is None) or (shapeRegion is None):
            tilesToEvaluate = allTiles
        #construction du string de sortie
        for tile in tilesToEvaluate:
            pathToFeat = fu.FileSearch_AND(pathToImg+"/"+tile+"/tmp/", True, fu.getCommonMaskName(pathConf), ".tif")[0]
            maskSHP = pathToRT+"/"+shpRName+"_region_"+model_Mask+"_"+tile+".shp"
            maskTif = shpRName+"_region_"+model_Mask+"_"+tile+".tif"
            CmdConfidenceMap = ""
            confidenceMap = ""
            if "fusion" in classifMode:
                if shapeRegion is None:
                    tmp = pathOut.split("/")
                    if pathOut[-1] == "/":
                        del tmp[-1]
                    tmp[-1] = "envelope"
                    pathToEnvelope = "/".join(tmp)
                    maskSHP = pathToEnvelope+"/"+tile+".shp"

            confidenceMap_name = "{}_model_{}_confidence_seed_{}{}.tif".format(tile, model, seed, suffix)
            CmdConfidenceMap = " -confmap "+ os.path.join(pathOut, confidenceMap_name)

            if not os.path.exists(maskFiles+"/"+maskTif):
                pathToMaskCommun = pathToImg+"/"+tile+"/tmp/"+fu.getCommonMaskName(pathConf)+".shp"
                #cas cluster
                if pathWd != None:
                    maskFiles = pathWd
                nameOut = fu.ClipVectorData(maskSHP, pathToMaskCommun, maskFiles, maskTif.replace(".tif", ""))
                cmdRaster = "otbcli_Rasterization -in "+nameOut+" -mode attribute -mode.attribute.field "+\
                        fieldRegion+" -im "+pathToFeat+" -out "+maskFiles+"/"+maskTif
                if "fusion" in classifMode:
                    cmdRaster = "otbcli_Rasterization -in "+nameOut+" -mode binary -mode.binary.foreground 1 -im "+\
                                pathToFeat+" -out "+maskFiles+"/"+maskTif
                run(cmdRaster)
                if pathWd != None:
                    run("cp "+pathWd+"/"+maskTif+" "+pathOut+"/MASK")
                    os.remove(pathWd+"/"+maskTif)

            out = pathOut+"/Classif_"+tile+"_model_"+model+"_seed_"+seed+suffix+".tif"

            cmdcpy = ""
            #hpc case
            if pathWd != None:
                out = "$TMPDIR/Classif_"+tile+"_model_"+model+"_seed_"+seed+suffix+".tif"
                CmdConfidenceMap = " -confmap $TMPDIR/"+confidenceMap_name

            appli = "python " + scriptPath + "/Classification/ImageClassifier.py -conf "+pathConf+" "
            pixType_cmd = " -pixType "+pixType
            if pathWd != None:
                pixType_cmd = pixType_cmd+" --wd $TMPDIR "
            cmdcpy = ""
            cmd = appli+" -in "+pathToFeat+" -model "+path+" -mask "+pathOut+"/MASK/"+maskTif+" -out "+out+" "+pixType_cmd+" -ram "+ str(RAM) + " " + CmdConfidenceMap

            # ajout des stats lors de la phase de classification
            #~ if classif == "svm":
                #~ cmd = cmd+" -imstat "+stat+"/Model_"+str(model)+".xml"
            AllCmd.append(cmd)
    fu.writeCmds(pathToCmdClassif+"/class.txt", AllCmd)
    return AllCmd

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="This function allow you to create all classification command")
    parser.add_argument("-path.model", help="path to the folder which ONLY contains models for the classification(mandatory)", dest="model", required=True)
    parser.add_argument("-conf", help="path to the configuration file which describe the learning method (mandatory)", dest="pathConf", required=True)
    parser.add_argument("--stat", dest="stat", help="statistics for classification", required=False)
    parser.add_argument("-path.region.tile", dest="pathToRT", help="path to the folder which contains all region shapefile by tiles (mandatory)", required=True)
    parser.add_argument("-path.img", dest="pathToImg", help="path where all images are stored", required=True)
    parser.add_argument("-path.region", dest="pathToRegion", help="path to the global region shape", required=True)
    parser.add_argument("-region.field", dest="fieldRegion", help="region field into region shape", required=True)
    parser.add_argument("-N", dest="N", help="number of random sample(mandatory)", required=True)
    parser.add_argument("-classif.out.cmd", dest="pathToCmdClassif", help="path where all classification cmd will be stored in a text file(mandatory)", required=True)
    parser.add_argument("-out", dest="pathOut", help="path where to stock all classifications", required=True)
    parser.add_argument("--wd", dest="pathWd", help="path to the working directory", default=None, required=False)

    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)

    launchClassification(args.model, cfg, args.stat, args.pathToRT,
                         args.pathToImg, args.pathToRegion, args.fieldRegion,
                         args.N, args.pathToCmdClassif, args.pathOut,
                         args.pathWd)
