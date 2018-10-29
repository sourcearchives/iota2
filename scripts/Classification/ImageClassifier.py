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
import shutil
import os
import ast
from config import Config
import logging
import otbApplication as otb
from Common import FileUtils as fu
from Common import OtbAppBank
from Common import GenerateFeatures as genFeatures
from Common import ServiceConfigFile as SCF 
from Sampling import DimensionalityReduction as DR
import logging


logger = logging.getLogger(__name__)


def str2bool(v):
    if v.lower() not in ('yes', 'true', 't', 'y', '1', 'no', 'false', 'f', 'n', '0'):
        raise argparse.ArgumentTypeError('Boolean value expected.')

    retour = True
    if v.lower() in ('no', 'false', 'f', 'n', '0'):
        retour = False
    return retour


def filterOTB_output(raster, mask, output, RAM, outputType="uint8"):

    bandMathFilter = otb.Registry.CreateApplication("BandMath")
    bandMathFilter.SetParameterString("exp", "im2b1>=1?im1b1:0")
    bandMathFilter.SetParameterStringList("il", [raster, mask])
    bandMathFilter.SetParameterString("ram", str(0.9 * float(RAM)))
    bandMathFilter.SetParameterString("out", output+"?&writegeom=false")
    if outputType=="uint8":
        bandMathFilter.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint8)
    elif outputType=="uint16":
        bandMathFilter.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint16)
    elif outputType=="float":
        bandMathFilter.SetParameterOutputImagePixelType("out", otb.ImagePixelType_float)
    bandMathFilter.ExecuteAndWriteOutput()


def computeClassifications(model, outputClassif, confmap, MaximizeCPU,
                           Classifmask, stats, AllFeatures, RAM, pixType="uint8"):

    classifier = otb.Registry.CreateApplication("ImageClassifier")
    classifier.SetParameterInputImage("in", AllFeatures.GetParameterOutputImage("out"))
    classifier.SetParameterString("out", outputClassif+"?&writegeom=false")
    if pixType=="uint8":
        classifier.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint8)
    elif pixType=="uint16":
        classifier.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint16)
    classifier.SetParameterString("confmap", confmap+"?&writegeom=false")
    classifier.SetParameterString("model", model)
    classifier.SetParameterString("ram", str(0.7 * float(RAM)))

    if not MaximizeCPU:
        classifier.SetParameterString("mask", Classifmask)
    if stats:
        classifier.SetParameterString("imstat", stats)

    return classifier, AllFeatures


def launchClassification(tempFolderSerie, Classifmask, model, stats,
                         outputClassif, confmap, pathWd, cfg, pixType,
                         MaximizeCPU=True, RAM=500, logger=logger):

    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    tiles = (cfg.getParam('chain', 'listTile')).split()
    tile = fu.findCurrentTileInString(Classifmask, tiles)
    wMode = cfg.getParam('GlobChain', 'writeOutputs')
    outputPath = cfg.getParam('chain', 'outputPath')
    featuresPath = os.path.join(outputPath, "features")
    dimred = cfg.getParam('dimRed', 'dimRed')
    wd = pathWd
    if not pathWd: 
        wd = featuresPath

    try:
        useGapFilling = cfg.getParam('GlobChain', 'useGapFilling')
    except:
        useGapFilling = True
    wd = os.path.join(featuresPath, tile)

    if pathWd:
        wd = os.path.join(pathWd, tile)
        if not os.path.exists(wd):
            try:
                os.mkdir(wd)
            except:
                logger.warning(wd + "Allready exists")

    mode = "usually"
    if "SAR.tif" in outputClassif:
        mode = "SAR"
    AllFeatures, feat_labels, dep_features = genFeatures.generateFeatures(wd, tile, cfg, useGapFilling=useGapFilling, mode=mode)
    if wMode:
        AllFeatures.ExecuteAndWriteOutput()
    else:
        AllFeatures.Execute()

    ClassifInput = AllFeatures

    if dimred:
        logger.debug("Classification model : {}".format(model))
        dimRedModelList = DR.GetDimRedModelsFromClassificationModel(model)
        logger.debug("Dim red models : {}".format(dimRedModelList))
        [ClassifInput, other] = DR.ApplyDimensionalityReductionToFeatureStack(cfg,AllFeatures,
                                                                              dimRedModelList)
        
        if wMode:
            ClassifInput.ExecuteAndWriteOutput()
        else:
            ClassifInput.Execute()

    classifier, inputStack = computeClassifications(model, outputClassif,
                                                    confmap, MaximizeCPU,
                                                    Classifmask, stats,
                                                    ClassifInput, RAM, 
                                                    pixType=pixType)

    logger.info("Compute Classification : {}".format(outputClassif))
    classifier.ExecuteAndWriteOutput()
    logger.info("Classification : {} done.".format(outputClassif))
    if MaximizeCPU:
        filterOTB_output(outputClassif, Classifmask, outputClassif, RAM, outputType=pixType)
        filterOTB_output(confmap, Classifmask, confmap, RAM, outputType="float")

    if pathWd:
        shutil.copy(outputClassif, outputPath+"/classif")
        os.remove(outputClassif)
    if pathWd:
        shutil.copy(confmap, outputPath+"/classif")
        os.remove(confmap)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Performs a classification of the input image (compute in RAM) according to a model file, ")
    parser.add_argument("-in", dest="tempFolderSerie", help="path to the folder which contains temporal series", default=None, required=True)
    parser.add_argument("-mask", dest="mask", help="path to classification's mask", default=None, required=True)
    parser.add_argument("-pixType", dest="pixType", help="pixel format", default=None, required=True)
    parser.add_argument("-model", dest="model", help="path to the model", default=None, required=True)
    parser.add_argument("-imstat", dest="stats", help="path to statistics", default=None, required=False)
    parser.add_argument("-out", dest="outputClassif", help="output classification's path", default=None, required=True)
    parser.add_argument("-confmap", dest="confmap", help="output classification confidence map", default=None, required=True)
    parser.add_argument("-ram", dest="ram", help="pipeline's size", default=128, required=False)
    parser.add_argument("--wd", dest="pathWd", help="path to the working directory", default=None, required=False)
    parser.add_argument("-conf", help="path to the configuration file (mandatory)", dest="pathConf", required=True)
    parser.add_argument("-maxCPU", help="True : Class all the image and after apply mask",
                        dest="MaximizeCPU", default="False", choices=["True", "False"], required=False)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)

    launchClassification(args.tempFolderSerie, args.mask, args.model, args.stats, args.outputClassif,
                         args.confmap, args.pathWd, cfg, args.pixType, args.MaximizeCPU)







