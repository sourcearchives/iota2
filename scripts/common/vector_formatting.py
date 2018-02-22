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
import logging
import os
import shutil

import fileUtils as fut
fut.updatePyPath()
import serviceConfigFile as SCF
import vector_splits as subset

import spatialOperations as intersect

logger = logging.getLogger(__name__)


def vector_formatting(cfg, tile_name, workingDirectory=None, logger=logger):
    """
    TODO : gérer le cas ou la région est trop grande (la subdiviser aléatoirement)
           mettre les régions présentent dans le nom du output shape
    """
    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)
    
    #extract information into the configuration file
    output_directory = os.path.join(cfg.getParam('chain', 'outputPath'),"formattingVectors")
    if workingDirectory:
        output_directory = workingDirectory
    output_name = tile_name + ".shp"
    output = os.path.join(output_directory, output_name)

    groundTruth_vec = cfg.getParam('chain', 'groundTruth')
    dataField = (cfg.getParam('chain', 'dataField')).lower()
    
    cloud_threshold = cfg.getParam('chain', 'cloud_threshold')
    features_directory = cfg.getParam('chain', 'featuresPath')
    cloud_vec = os.path.join(features_directory,tile_name,"CloudThreshold_" + str(cloud_threshold) + ".shp")
    region_vec = cfg.getParam('chain', 'regionPath')
    regionField = (cfg.getParam('chain', 'regionField')).lower()
    tileEnv_vec = os.path.join(cfg.getParam('chain', 'outputPath'),"envelope", tile_name + ".shp")
    ratio = cfg.getParam('chain', 'ratio')
    seeds = cfg.getParam('chain', 'runs')
    epsg = int((cfg.getParam('GlobChain', 'proj')).split(":")[-1])

    output_driver = "SQlite"
    if os.path.splitext(os.path.basename(output))[-1] == ".shp":
        output_driver = "ESRI Shapefile"

    #log
    logger.info("formatting vector for tile : {}".format(tile_name))
    logger.debug("output : {}".format(output))
    logger.debug("groundTruth : {}".format(groundTruth_vec))
    logger.debug("cloud : {}".format(cloud_vec))
    logger.debug("region : {}".format(region_vec))
    logger.debug("tile envelope : {}".format(tileEnv_vec))
    logger.debug("data field : {}".format(dataField))
    logger.debug("region field : {}".format(regionField))
    logger.debug("ratio : {}".format(ratio))
    logger.debug("seeds : {}".format(seeds))
    logger.debug("epsg : {}".format(epsg))
    logger.debug("workingDirectory : {}".format(workingDirectory))

    logger.info("launch intersection between tile's envelope and regions")
    tileRegion = os.path.join(workingDirectory, "tileRegion_" + tile_name + ".sqlite")
    intersect.intersectSqlites(tileEnv_vec, region_vec, workingDirectory, tileRegion,
                               epsg, "intersection", [regionField], vectformat='SQLite')

    logger.info("launch intersection between tile's envelopeRegion and groundTruth")
    tileRegionGroundTruth = os.path.join(workingDirectory, "tileRegionGroundTruth_" + tile_name + ".sqlite")
    intersect.intersectSqlites(tileRegion, groundTruth_vec, workingDirectory, tileRegionGroundTruth,
                               epsg, "intersection", [dataField, regionField], vectformat='SQLite')

    logger.info("remove unsable samples")
    intersect.intersectSqlites(tileRegionGroundTruth, cloud_vec, workingDirectory, output,
                               epsg, "intersection", [dataField, regionField], vectformat='SQLite')

    #os.remove(tileRegion)
    #os.remove(tileRegionGroundTruth)

    logger.info("split {} in {} subsets with the ratio {}".format(output, seeds, ratio))
    subset.splitInSubSets(output, dataField, ratio, seeds, output_driver)

    if workingDirectory:
        if output_driver == "SQLite":
            shutil.copy(output, os.path.join(cfg.getParam('chain', 'outputPath'), "formattingVectors"))
            os.remove(output)
        elif output_driver == "ESRI Shapefile":
            fut.cpShapeFile(output.replace(".shp", ""), os.path.join(cfg.getParam('chain', 'outputPath'), "formattingVectors"), [".prj", ".shp", ".dbf", ".shx"], True)
            fut.removeShape(output.replace(".shp", ""), [".prj", ".shp", ".dbf", ".shx"])


if __name__ == "__main__":

    func_description = "This function is dedicated to intersects some vector files\
                        and then, prepare them to sampling"

    parser = argparse.ArgumentParser(description=func_description)

    parser.add_argument("-config", dest="config",
                        help="path to a configuration path",
                        required=False)
    
    parser.add_argument("-tile", dest="tile_name",
                        help="tile to compute",
                        required=False)

    parser.add_argument("-workingDirectory", dest="workingDirectory",
                        help="path to a working directory",
                        required=False)

    args = parser.parse_args()
    cfg = SCF.serviceConfigFile(config)
    vector_formatting(cfg, args.tile_name, args.workingDirectory)
