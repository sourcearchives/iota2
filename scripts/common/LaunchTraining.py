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


def buildTrainCmd_points(r, paths, classif, options, dataField, out, seed,
                         stat, pathlog, features_labels):

    """
    shape_ref [param] [string] path to a shape use to determine how many fields
                               are already present before adding features
    """
    cmd = "otbcli_TrainVectorClassifier -io.vd "
    if paths.count("learn")!=0:
        cmd = cmd +" "+paths 

    cmd = cmd+" -classifier "+classif+" "+options+" -cfield "+dataField.lower()+" -io.out "+out+"/model_"+str(r)+"_seed_"+str(seed)+".txt"
    cmd = cmd+" -feat "+features_labels

    if ("svm" in classif):
        cmd = cmd+" -io.stats "+stat+"/Model_"+str(r)+".xml"
    if pathlog:
        cmd = cmd + " > " + pathlog + "/LOG_model_" + str(r) + "_seed_" + str(seed) + ".out"
    return cmd


def getFeatures_labels(learning_vector):
    """
    """
    nb_no_features = 4
    fields = fu.getAllFieldsInShape(learning_vector, driver='SQLite')
    return fields[nb_no_features::]


def models_in_tiles(vectors):
    """
    usage : use to kwow in which tile models are present
    """
    
    #const
    #model's position, if training shape is split by "_"
    posModel = -3
    
    output = "AllModel:\n["
    for vector in vectors:
        model = os.path.split(vector)[-1].split("_")[posModel]
        tiles = fu.getFieldElement(vector, driverName="SQLite", field="tile_o",
                                   mode="unique", elemType="str")
        
        tmp = "modelName: '{}'\n\ttilesList: '{}'".format(model, "_".join(tiles))
        output += "\n\t{\n\t" + tmp + "\n\t}\n\t"
    output+="\n]"

    return output


def launchTraining(pathShapes, cfg, pathToTiles, dataField, stat, N,
                   pathToCmdTrain, out, pathWd, pathlog):

    """
    OUT : les commandes pour l'app
    """
    #const
    posModel = -3
    posSeed = -2
    cmd_out = []

    pathConf = cfg.pathConf
    classif = cfg.getParam('argTrain', 'classifier')
    options = cfg.getParam('argTrain', 'options')
    outputPath = cfg.getParam('chain', 'outputPath')
    dataField = cfg.getParam('chain', 'dataField')
    runs = cfg.getParam('chain', 'runs')

    pathToModelConfig = outputPath + "/config_model/configModel.cfg"
    learning_directory = os.path.join(outputPath, "learningSamples")
    samples = fu.FileSearch_AND(learning_directory, True, "Samples", "sqlite", "learn")
    
    features_labels = getFeatures_labels(samples[0])
    
    configModel = models_in_tiles(fu.FileSearch_AND(learning_directory, True, "Samples", "sqlite","seed0","learn"))
    if not os.path.exists(pathToModelConfig):
        with open(pathToModelConfig, "w") as configFile:
            configFile.write(configModel)
    
    cmd_out = []
    for sample in samples:
        model = os.path.split(sample)[-1].split("_")[posModel]
        seed = os.path.split(sample)[-1].split("_")[posSeed].split("seed")[-1]
        
        if classif == "svm":
            outStats = outputPath + "/stats/Model_" + model + ".xml"
            if os.path.exists(outStats):
                os.remove(outStats)
            writeStatsFromSample(sample, outStats)
        cmd = buildTrainCmd_points(model, sample, classif, options, dataField, out, seed,
                                   stat, pathlog, " ".join(features_labels))
        cmd_out.append(cmd)
    
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
