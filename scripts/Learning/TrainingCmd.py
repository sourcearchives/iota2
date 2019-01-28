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
import numpy as np
from Common import FileUtils as fu
from osgeo import ogr
from Common import ServiceConfigFile as SCF

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


def buildTrainCmd_points(r, paths, classif, options, dataField, out,
                         stat, features_labels, model_name):

    """
    shape_ref [param] [string] path to a shape use to determine how many fields
                               are already present before adding features
    """
    cmd = "otbcli_TrainVectorClassifier -io.vd "
    if paths.count("learn") != 0:
        cmd = cmd +" "+paths 

    cmd = cmd+" -classifier "+classif+" "+options+" -cfield "+dataField.lower()+" -io.out "+out+"/" + model_name
    cmd = cmd+" -feat "+features_labels

    #~ if ("svm" in classif):
        #~ cmd = cmd+" -io.stats "+stat+"/Model_"+str(r)+".xml"

    return cmd


def getFeatures_labels(learning_vector):
    """
    """
    nb_no_features = 4
    fields = fu.getAllFieldsInShape(learning_vector, driver='SQLite')
    return fields[nb_no_features::]


def config_model(outputPath, region_field):
    """
    usage : determine which model will class which tile
    """
    #const
    output = None
    posTile = 0
    formatting_vec_dir = os.path.join(outputPath, "formattingVectors")
    samples = fu.FileSearch_AND(formatting_vec_dir, True, ".shp")

    #init
    all_regions = []
    for sample in samples:
        tile_name = os.path.splitext(os.path.basename(sample))[0].split("_")[posTile]
        regions = fu.getFieldElement(sample, driverName="ESRI Shapefile", field=region_field, mode="unique",
                                     elemType="str")
        for region in regions:
            all_regions.append((region, tile_name))

    #{'model_name':[TileName, TileName...],'...':...,...}
    model_tiles = dict(fu.sortByFirstElem(all_regions))

    #add tiles if they are missing by checking in /shapeRegion/ directory
    shape_region_dir = os.path.join(outputPath, "shapeRegion")
    shape_region_path = fu.FileSearch_AND(shape_region_dir, True, ".shp")

    #check if there is actually polygons
    shape_regions = [elem for elem in shape_region_path if len(fu.getFieldElement(elem,
                                                                                  driverName="ESRI Shapefile",
                                                                                  field=region_field,
                                                                                  mode="all",
                                                                                  elemType="str")) >= 1]
    for shape_region in shape_regions:
        tile = os.path.splitext(os.path.basename(shape_region))[0].split("_")[-1]
        region = os.path.splitext(os.path.basename(shape_region))[0].split("_")[-2]
        for model_name, tiles_model in model_tiles.items():
            if model_name.split("f")[0] == region and tile not in tiles_model:
                tiles_model.append(tile)

    #Construct output file string
    output = "AllModel:\n["
    for model_name, tiles_model in model_tiles.items():
        output_tmp = "\n\tmodelName:'{}'\n\ttilesList:'{}'".format(model_name, "_".join(tiles_model))
        output = output + "\n\t{" + output_tmp + "\n\t}"
    output += "\n]"

    return output


def launchTraining(cfg, dataField, stat, N,
                   pathToCmdTrain, out, pathWd):

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
    regionField = cfg.getParam('chain', 'regionField')
    runs = cfg.getParam('chain', 'runs')

    pathToModelConfig = outputPath + "/config_model/configModel.cfg"
    learning_directory = os.path.join(outputPath, "learningSamples")
    samples = fu.FileSearch_AND(learning_directory, True, "Samples_region", "sqlite", "learn")

    configModel = config_model(outputPath, regionField)
    if not os.path.exists(pathToModelConfig):
        with open(pathToModelConfig, "w") as configFile:
            configFile.write(configModel)

    cmd_out = []
    
    for sample in samples:
        features_labels = getFeatures_labels(sample)
        suffix = ""
        posModel_sample = posModel
        posSeed_sample = posSeed
        if "SAR.sqlite" in os.path.basename(sample):
            posModel_sample = posModel - 1
            posSeed_sample = posSeed -1
            suffix = "_SAR"
        model = os.path.split(sample)[-1].split("_")[posModel_sample]
        seed = os.path.split(sample)[-1].split("_")[posSeed_sample].split("seed")[-1]
        if classif == "svm":
            outStats = outputPath + "/stats/Model_" + model + ".xml"
            if os.path.exists(outStats):
                os.remove(outStats)
            writeStatsFromSample(sample, outStats)
        model_name = "model_{}_seed_{}{}.txt".format(model, seed, suffix)
        cmd = buildTrainCmd_points(model, sample, classif, options, dataField, out,
                                   stat, " ".join(features_labels), model_name)
        cmd_out.append(cmd)

    fu.writeCmds(pathToCmdTrain + "/train.txt", cmd_out)
    return cmd_out


if __name__ == "__main__":

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
