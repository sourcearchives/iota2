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
import fileUtils as fu
from osgeo import ogr
import numpy as np


def getStatsFromSamples(InSamples):

    """
        IN:
            InSamples [string] : path to a sqlite file containing N fields value_0 .... value_N-1 representing features values
        OUT:
            allMean [list of float] : all mean sort by band number
            allStdDev [list of float] : all stdDev sort by band number
    """
    driver = ogr.GetDriverByName("SQLite")
    if driver.Open(InSamples, 0):
        ds = driver.Open(InSamples, 0)
    else:
        raise Exception("Can not open : " + InSamples)

    layer = ds.GetLayer()
    featuresFields = fu.getVectorFeatures(InSamples)
    allStat = []
    for currentBand in featuresFields:
        bandValues = []
        for feature in layer:
            val = feature.GetField(currentBand)
            if isinstance(val, int) or isinstance(val, float):
                bandValues.append(val)
        bandValues = np.asarray(bandValues)
        mean = np.mean(bandValues)
        stddev = np.std(bandValues)
        allStat.append((mean, stddev))
    allMean = [mean for mean, stddev in allStat]
    allStdDev = [stddev for mean, stddev in allStat]
    return allMean, allStdDev


def writeStatsFromSample(InSamples, outStats):

    allMean, allStdDev = getStatsFromSamples(InSamples)

    with open(outStats, "w") as statsFile:
        statsFile.write('<?xml version="1.0" ?>\n\
            <FeatureStatistics>\n\
            <Statistic name="mean">\n')
        for currentMean in allMean:
            statsFile.write('        <StatisticVector value="' + str(currentMean) + '" />\n')
        statsFile.write('    </Statistic>\n\
                            <Statistic name="stddev">\n')
        for currentStd in allStdDev:
            statsFile.write('        <StatisticVector value="' + str(currentStd) + '" />\n')
        statsFile.write('    </Statistic>\n\
                            </FeatureStatistics>')


def writeConfigName(r, tileList, configfile):
    configModel = open(configfile, "a")
    configModel.write("\n\t{\n\tmodelName:'" + r + "'\n\ttilesList:'" + tileList + "'\n\t}")
    configModel.close()

def buildTrainCmd_points(r, paths, classif, options, dataField, out, seed,
                         stat, pathlog, shape_ref):

    """
    shape_ref [param] [string] path to a shape use to determine how many fields
                               are already present before adding features
    """
    cmd = "otbcli_TrainVectorClassifier -io.vd "
    if paths.count("learn")!=0:
        cmd = cmd +" "+paths 

    cmd = cmd+" -classifier "+classif+" "+options+" -cfield "+dataField.lower()+" -io.out "+out+"/model_"+str(r)+"_seed_"+str(seed)+".txt"
    
    nb_origin_fields = len(fu.getAllFieldsInShape(shape_ref))+1
    features_labels = " ".join(fu.getAllFieldsInShape(paths,"SQLite")[nb_origin_fields:])
    cmd = cmd+" -feat "+features_labels

    if ("svm" in classif):
        cmd = cmd+" -io.stats "+stat+"/Model_"+str(r)+".xml"
    if pathlog:
        cmd = cmd + " > " + pathlog + "/LOG_model_" + str(r) + "_seed_" + str(seed) + ".out"
    return cmd


def launchTraining(pathShapes, cfg, pathToTiles, dataField, stat, N,
                   pathToCmdTrain, out, pathWd, pathlog):

    """
    OUT : les commandes pour l'app
    """
    cmd_out = []

    pathConf = cfg.pathConf
    classif = cfg.getParam('argTrain', 'classifier')
    options = cfg.getParam('argTrain', 'options')
    outputPath = cfg.getParam('chain', 'outputPath')
    dataField = cfg.getParam('chain', 'dataField')
    
    shape_ref = fu.FileSearch_AND(os.path.join(outputPath,"formattingVectors"), True, ".shp")[0]
    posModel = -3 #model's position, if training shape is split by "_"

    Stack_ind = fu.getFeatStackName(pathConf)

    pathToModelConfig = outputPath + "/config_model/configModel.cfg"
    configModel = open(pathToModelConfig, "w")
    configModel.write("AllModel:\n[\n")
    configModel.close()
    for seed in range(N):
        pathAppVal = fu.FileSearch_AND(pathShapes, True, "seed" + str(seed), ".shp", "learn")
        sort = [(path.split("/")[-1].split("_")[posModel], path) for path in pathAppVal]
        sort = fu.sortByFirstElem(sort)
        #get tiles by model
        names = []
        for r, paths in sort:
            tmp = ""
            for i in range(len(paths)):
                if i < len(paths) - 1:
                    tmp = tmp + paths[i].split("/")[-1].split("_")[0] + "_"
                else:
                    tmp = tmp + paths[i].split("/")[-1].split("_")[0]
            names.append(tmp)
        cpt = 0
        for r, paths in sort:
            writeConfigName(r, names[cpt], pathToModelConfig)
            cpt += 1

        pathAppVal = fu.FileSearch_AND(outputPath + "/learningSamples", True, "seed" + str(seed), ".sqlite", "learn")
        sort = [(path.split("/")[-1].split("_")[posModel], path) for path in pathAppVal]

        for r, paths in sort:
            if classif == "svm":
                outStats = outputPath + "/stats/Model_" + r + ".xml"
                if os.path.exists(outStats):
                    os.remove(outStats)
                writeStatsFromSample(paths, outStats)
            cmd = buildTrainCmd_points(r, paths, classif, options, dataField,
                                       out, seed, stat, pathlog, shape_ref)
            cmd_out.append(cmd)

    configModel = open(pathToModelConfig, "a")
    configModel.write("\n]\n")
    configModel.close()

    fu.writeCmds(pathToCmdTrain + "/train.txt", cmd_out)

    return cmd_out

if __name__ == "__main__":

    import serviceConfigFile as SCF

    parser = argparse.ArgumentParser(description="This function allow you to create a training command for a classifieur according to a configuration file")
    parser.add_argument("-shapesIn", help="path to the folder which ONLY contains shapes for the classification (learning and validation) (mandatory)", dest="pathShapes", required=True)
    parser.add_argument("-conf", help="path to the configuration file which describe the learning method (mandatory)", dest="pathConf", required=True)
    parser.add_argument("-tiles.path", dest="pathToTiles", help="path where tiles are stored (mandatory)", required=True)
    parser.add_argument("-data.field", dest="dataField", help="data field into data shape (mandatory)", required=True)
    parser.add_argument("-N", dest="N", type=int, help="number of random sample(mandatory)", required=True)
    parser.add_argument("--stat", dest="stat", help="statistics for classification", required=False)
    parser.add_argument("-train.out.cmd", dest="pathToCmdTrain", help="path where all training cmd will be stored in a text file(mandatory)", required=True)
    parser.add_argument("-out", dest="out", help="path where all models will be stored(mandatory)", required=True)
    parser.add_argument("--wd", dest="pathWd", help="path to the working directory", default=None, required=False)
    parser.add_argument("--path.log", dest="pathlog", help="path to the log file", default=None, required=False)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)

    launchTraining(args.pathShapes, cfg, args.pathToTiles, args.dataField,
                   args.stat, args.N, args.pathToCmdTrain, args.out,
                   args.pathWd, args.pathlog)
