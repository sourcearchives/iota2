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
import shutil
import argparse
import sqlite3 as lite
from config import Config
from Common import FileUtils as fut
from Common import OtbAppBank as otbApp

def extractStats(vectorIn, pathConf, wD=None):

    dataField = Config(file(pathConf)).chain.dataField
    iota2Folder = Config(file(pathConf)).chain.outputPath

    tileToCompute = vectorIn.split("/")[-1].split("_")[0]
    modelToCompute = vectorIn.split("/")[-1].split("_")[2].split("f")[0]
    seed = vectorIn.split("/")[-1].split("_")[3].replace("seed", "")
    workingDirectory = iota2Folder+"/final/TMP"
    shapeMode = vectorIn.split("/")[-1].split("_")[-1].split(".")[0]#'learn' or 'val'
    if wD:
        workingDirectory = wD

    try:
        refImg = fut.FileSearch_AND(iota2Folder+"/final/TMP", True, tileToCompute, ".tif")[0]
    except:
        raise Exception("reference image can not be found in "+iota2Folder+"/final/TMP")

    statsFile = workingDirectory+"/"+tileToCompute+"_stats_model_"+modelToCompute+".xml"
    stats = otbApp.CreatePolygonClassStatisticsApplication({"in":refImg, "vec":vectorIn,\
                                                            "out":statsFile, "field":dataField})
    stats.ExecuteAndWriteOutput()

    selVector = workingDirectory+"/"+tileToCompute+"_selection_model_"+modelToCompute+".sqlite"
    sampleS = otbApp.CreateSampleSelectionApplication({"in":refImg, "vec":vectorIn, "out":selVector,\
                                                       "instats":statsFile, "strategy":"all",\
                                                       "field":dataField})
    sampleS.ExecuteAndWriteOutput()

    classificationRaster = fut.FileSearch_AND(iota2Folder+"/final/TMP", True, tileToCompute+"_seed_"+seed+".tif")[0]
    validity = fut.FileSearch_AND(iota2Folder+"/final/TMP", True, tileToCompute+"_Cloud.tif")[0]
    confiance = fut.FileSearch_AND(iota2Folder+"/final/TMP", True, tileToCompute+"_GlobalConfidence_seed_"+seed+".tif")[0]

    stack = [classificationRaster, validity, confiance]
    dataStack = otbApp.CreateConcatenateImagesApplication({"il" : stack,
                                                           "ram" : '1000',
                                                           "pixType" : "uint8",
                                                           "out" : ""})
    dataStack.Execute()

    outSampleExtraction = workingDirectory+"/"+tileToCompute+"_extraction_model_"+modelToCompute+"_"+shapeMode+".sqlite"

    extraction = otbApp.CreateSampleExtractionApplication({"in":dataStack, "vec":selVector,\
                                                           "field":dataField, " out":outSampleExtraction,\
                                                           "outfield":"list",\
                                                           "outfield.list.names":["predictedClass", "validity", "confidence"]})
    extraction.ExecuteAndWriteOutput()

    conn = lite.connect(outSampleExtraction)
    cursor = conn.cursor()
    SQL = "alter table output add column TILE TEXT"
    cursor.execute(SQL)
    SQL = "update output set TILE='"+tileToCompute+"'"
    cursor.execute(SQL)

    SQL = "alter table output add column MODEL TEXT"
    cursor.execute(SQL)
    SQL = "update output set MODEL='"+modelToCompute+"'"
    cursor.execute(SQL)

    conn.commit()

    os.remove(statsFile)
    os.remove(selVector)
    if wD:
        shutil.copy(outSampleExtraction, iota2Folder+"/final/TMP")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="from a shape containing polygons,\
                                                    create a vector of points, with usefull\
                                                    data for stats")
    parser.add_argument("-vector", dest="vector", help="path to the shapeFile to sampled", default=None, required=True)
    parser.add_argument("-wd", dest="pathWd", help="path to the working directory", default=None, required=False)
    parser.add_argument("-conf", help="path to the configuration file (mandatory)", dest="pathConf", required=True)
    args = parser.parse_args()

    extractStats(args.vector, args.pathConf, args.pathWd)

    """
    Example :
    python extractStats.py -vector /work/OT/theia/oso/classifications/ToulouseS1S2_4Tiles_MultiDespeckle/dataAppVal/T31TDJ_region_4_seed0_learn.shp -wd /work/OT/theia/oso/TMP/sampleExtraction -conf /home/uz/vincenta/config/configS1S2_4Tiles_multiSARdespeckle.cfg
    """
