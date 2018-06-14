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
from config import Config
import GetModel as GM
from Common import FileUtils as fu
from Common import ServiceConfigFile as SCF

def generateStatModel(pathShapes, pathToTiles, pathToStats, pathToCmdStats, pathWd, cfg):

    AllCmd = []
    #remove splited shape
    outputPath = cfg.getParam('chain', 'outputPath')
    classifier = cfg.getParam('argTrain', 'classifier')
    pathConf = cfg.pathConf

    allShape = fu.fileSearchRegEx(outputPath+"/dataAppVal/*.shp")
    for currentShape in allShape:
        #name = currentShape.split("/")[-1]
        path, name = os.path.split(currentShape)
        if len(name.split("_")[2].split("f")) > 1:
            fold = name.split("_")[2].split("f")[-1]
            #path = currentShape.split("/")[0]
            nameToRm = name.replace("f"+fold, "").replace(".shp", "")
            print "remove : "+path+"/"+nameToRm+".shp"
            if os.path.exists(path+"/"+nameToRm+".shp"):
                fu.removeShape(path+"/"+nameToRm, [".prj", ".shp", ".dbf", ".shx"])

    modTiles = GM.getModel(pathShapes)
    Stack_ind = fu.getFeatStackName(pathConf)

    for mod, Tiles in modTiles:
        allpath = ""
        for tile in Tiles:
            pathToFeat = pathToTiles+"/"+tile+"/Final/"+Stack_ind
            allpath = allpath+" "+pathToFeat+" "
        if classifier == "svm":
            cmd = "otbcli_ComputeImagesStatistics -il "+allpath+" -out "+pathToStats+"/Model_"+str(mod)+".xml"
        else:
            cmd = "echo 'radom forest does not need stats'"
        AllCmd.append(cmd)

    fu.writeCmds(pathToCmdStats+"/stats.txt", AllCmd)
    return AllCmd

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="This function compute the statistics for a model compose by N tiles")
    parser.add_argument("-shapesIn", help="path to the folder which ONLY contains shapes for the classification (learning and validation) (mandatory)", dest="pathShapes", required=True)
    parser.add_argument("-tiles.path", dest="pathToTiles", help="path where tiles are stored (mandatory)", required=True)
    parser.add_argument("-Stats.out", dest="pathToStats", help="path where all statistics will be stored (mandatory)", required=True)
    parser.add_argument("-Stat.out.cmd", dest="pathToCmdStats", help="path where all statistics cmd will be stored in a text file(mandatory)", required=True)
    parser.add_argument("--wd", dest="pathWd", help="path to the working directory", default=None, required=False)
    parser.add_argument("-conf", help="path to the configuration file which describe the learning method (mandatory)", dest="pathConf", required=True)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)

    generateStatModel(args.pathShapes, args.pathToTiles, args.pathToStats, args.pathToCmdStats, args.pathWd, cfg)






































