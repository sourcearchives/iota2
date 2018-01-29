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
import ast
import os
from config import Config
import fileUtils as fu
import otbAppli
import shutil
import logging

logger = logging.getLogger(__name__)

def str2bool(v):
    """
    usage : use in argParse as function to parse options

    IN:
    v [string]
    out [bool]
    """
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def generateFeatures(pathWd, tile, cfg, writeFeatures=False,
                     useGapFilling=True, enable_Copy=False):
    """
    usage : Function use to compute features according to a configuration file.

    IN

    OUT

    AllFeatures [OTB Application object] : otb object ready to Execute()
    feat_labels [list] : list of strings, labels for each output band
    dep [list of OTB Applications]
    """
    logger.info("prepare features for tile : " + tile)
    wMode = ast.literal_eval(cfg.getParam('GlobChain', 'writeOutputs'))
    featuresPath = cfg.getParam('chain', 'featuresPath')

    wd = pathWd
    if not pathWd:
        wd = None

    #compute gapfilling and reflectance
    (AllGapFill, AllRefl,
     AllMask, datesInterp,
     realDates, dep_gapFil) = otbAppli.gapFilling(cfg, tile, wMode=wMode,
                                                  featuresPath=os.path.join(featuresPath, tile),
                                                  workingDirectory=wd,enable_Copy=enable_Copy)

    #stack to extract features
    stack_dates = AllRefl
    dateFile = realDates
    if useGapFilling:
        stack_dates = AllGapFill
        dateFile = datesInterp

    for current_sensor_stack in stack_dates:
        if wMode:
            current_sensor_stack.ExecuteAndWriteOutput()
        else:
            current_sensor_stack.Execute()

    nbDates = [fu.getNbDateInTile(currentDateFile) for currentDateFile in dateFile]

    if nbDates[0] == 1 and useGapFilling==False:
        with open(dateFile[0],"w") as d:
            d.write("YYYYMMDD")
    #Compute features
    (AllFeatures, feat_labels,
     ApplicationList,
     a, b, c, d, e) = otbAppli.computeFeatures(cfg, nbDates, tile,
                                               stack_dates, AllRefl, AllMask,
                                               dateFile, realDates)
    if writeFeatures:
        AllFeatures.ExecuteAndWriteOutput()

    if pathWd and writeFeatures:
        outputDirectory = os.path.join(featuresPath, tile, "tmp")
        shutil.copy(AllFeatures.GetParameterValue("out"), outputDirectory)

    dep = [AllGapFill, AllRefl, AllMask, datesInterp, realDates, ApplicationList, a, b, c, d, e, dep_gapFil]
    return AllFeatures, feat_labels, dep


if __name__ == "__main__":

    import serviceConfigFile as SCF
    parser = argparse.ArgumentParser(description="Computes a time series of features")
    parser.add_argument("-wd", dest="pathWd", help="path to the working directory", default=None, required=False)
    parser.add_argument("-tile", dest="tile", help="tile to be processed", required=True)
    parser.add_argument("-gapFilling", type=str2bool, dest="useGapFilling", help="flag to set if you want to use gapFilling (default = True)", default=True, required=False)
    parser.add_argument("-conf", dest="pathConf", help="path to the configuration file (mandatory)", required=True)
    parser.add_argument("-writeFeatures", type=str2bool, dest="writeFeatures", help="path to the working directory", default=False, required=False)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)

    generateFeatures(args.pathWd, args.tile, cfg, args.writeFeatures, args.useGapFilling)
