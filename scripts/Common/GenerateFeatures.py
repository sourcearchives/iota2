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
import shutil
import logging
from config import Config
from Common import FileUtils as fu
from Common import OtbAppBank
from Common import ServiceConfigFile as SCF

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
                     useGapFilling=True, enable_Copy=False,
                     mode="usually"):
    """
    usage : Function use to compute features according to a configuration file.

    IN

    OUT

    AllFeatures [OTB Application object] : otb object ready to Execute()
    feat_labels [list] : list of strings, labels for each output band
    dep [list of OTB Applications]
    """
    from Sensors.Sensors_container import Sensors_container
    from Common.OtbAppBank import CreateConcatenateImagesApplication

    logger.info("prepare features for tile : " + tile)
    wMode = cfg.getParam('GlobChain', 'writeOutputs')
    config_path = cfg.pathConf
    sensor_tile_container = Sensors_container(config_path,
                                              tile,
                                              working_dir=pathWd)
    feat_labels = []
    dep = []
    feat_app = []
    sensors_features = sensor_tile_container.get_sensors_features(available_ram=1000)
    for sensor_name, ((sensor_features, sensor_features_dep), features_labels) in sensors_features:
        sensor_features.Execute()
        feat_app.append(sensor_features)
        dep.append(sensor_features_dep)
        feat_labels = feat_labels + features_labels

    dep.append(feat_app)
    
    features_name = "{}_Features.tif".format(tile)
    features_dir = os.path.join(cfg.getParam("chain", "outputPath"),
                                "features", tile, "tmp")
    features_raster = os.path.join(features_dir, features_name)
    AllFeatures = CreateConcatenateImagesApplication({"il": feat_app,
                                                      "out": features_raster})
    return AllFeatures, feat_labels, dep


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Computes a time series of features")
    parser.add_argument("-wd", dest="pathWd", help="path to the working directory", default=None, required=False)
    parser.add_argument("-tile", dest="tile", help="tile to be processed", required=True)
    parser.add_argument("-gapFilling", type=str2bool, dest="useGapFilling",
                        help="flag to set if you want to use gapFilling (default = True)", default=True, required=False)
    parser.add_argument("-conf", dest="pathConf", help="path to the configuration file (mandatory)", required=True)
    parser.add_argument("-writeFeatures", type=str2bool, dest="writeFeatures",
                        Shelp="path to the working directory", default=False, required=False)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)

    generateFeatures(args.pathWd, args.tile, cfg, args.writeFeatures, args.useGapFilling)
