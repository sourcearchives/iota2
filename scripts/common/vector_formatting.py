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
from AddField import addField
from Utils import run

logger = logging.getLogger(__name__)

def create_tile_region_masks(tileRegion, regionField, tile_name, outputDirectory):
    """
    """
    all_regions_tmp = fut.getFieldElement(tileRegion, driverName="SQLite",
                                          field=regionField.lower(), mode="unique",
                                          elemType="str")
    #transform sub region'name into complete region (region '1f1' become region '1')
    all_regions = []
    for region in all_regions_tmp:
        r = region.split("f")[0]
        all_regions.append(r)
    region = None
    for region in all_regions:
        output_name = "SampleRegions_region_{}_{}.shp".format(region, tile_name)
        output_path = os.path.join(outputDirectory, output_name)
        db_name = (os.path.splitext(os.path.basename(tileRegion))[0]).lower()
        cmd = "ogr2ogr -f 'ESRI Shapefile' -sql \"SELECT * FROM {} WHERE {}='{}'\" {} {}".format(db_name,
                                                                                                 regionField,
                                                                                                 region,
                                                                                                 output_path,
                                                                                                 tileRegion)
        run(cmd)
    
def keepFields(vec_in, vec_out, fields=[], proj_in=2154, proj_out=2154):
    """
    """
    table_in = (os.path.splitext(os.path.split(vec_in)[-1])[0]).lower()
    table_out = (os.path.splitext(os.path.split(vec_out)[-1])[0]).lower()

    sql_clause = "select GEOMETRY,{} from {}".format(",".join(fields), table_in)

    cmd = "ogr2ogr -s_srs EPSG:{} -t_srs EPSG:{} -dialect 'SQLite' -f 'SQLite' -nln {} -sql '{}' {} {}".format(proj_in,
                                                                                                               proj_out,
                                                                                                               table_out,
                                                                                                               sql_clause,
                                                                                                               vec_out,
                                                                                                               vec_in)
    run(cmd)


def splitbySets(vector, seeds, split_directory, proj_in, proj_out, tile_name):
    """
    """
    out_vectors = []

    valid_flag = "validation"
    learn_flag = "learn"
    tileOrigin_field_name = "tile_o"

    vector_layer_name = (os.path.splitext(os.path.split(vector)[-1])[0]).lower()

    #predict fields to keep
    fields_to_rm = ["seed_"+str(seed) for seed in range(seeds)]
    fields_to_rm.append(tileOrigin_field_name)
    all_fields = fut.getAllFieldsInShape(vector)
    fields = [field_name for field_name in all_fields if not field_name in fields_to_rm]

    #start split
    for seed in range(seeds):
        valid_clause = "seed_{}='{}'".format(seed, valid_flag)
        learn_clause = "seed_{}='{}'".format(seed, learn_flag)
        
        sql_cmd_valid = "select * FROM {} WHERE {}".format(vector_layer_name, valid_clause)
        output_vec_valid_name = "_".join([tile_name, "seed_" + str(seed) , "val"])
        output_vec_valid_name_tmp = "_".join([tile_name, "seed_" + str(seed) , "val", "tmp"])
        output_vec_valid_tmp = os.path.join(split_directory, output_vec_valid_name_tmp + ".sqlite")
        output_vec_valid = os.path.join(split_directory, output_vec_valid_name + ".sqlite")
        cmd_valid = 'ogr2ogr -t_srs EPSG:{} -s_srs EPSG:{} -nln {} -f "SQLite" -sql "{}" {} {}'.format(proj_out,
                                                                                       proj_in,
                                                                                       output_vec_valid_name_tmp,
                                                                                       sql_cmd_valid,
                                                                                       output_vec_valid_tmp,
                                                                                       vector)
        run(cmd_valid)

        sql_cmd_learn = "select * FROM {} WHERE {}".format(vector_layer_name, learn_clause)
        output_vec_learn_name = "_".join([tile_name, "seed_" + str(seed) , "learn"])
        output_vec_learn_name_tmp = "_".join([tile_name, "seed_" + str(seed) , "learn", "tmp"])
        output_vec_learn_tmp = os.path.join(split_directory, output_vec_learn_name_tmp + ".sqlite" )
        output_vec_learn = os.path.join(split_directory, output_vec_learn_name + ".sqlite" )
        cmd_learn = 'ogr2ogr -t_srs EPSG:{} -s_srs EPSG:{} -nln {} -f "SQLite" -sql "{}" {} {}'.format(proj_out,
                                                                                       proj_in,
                                                                                       output_vec_learn_name_tmp,
                                                                                       sql_cmd_learn,
                                                                                       output_vec_learn_tmp,
                                                                                       vector)
        run(cmd_learn)

        #remove useless fields
        keepFields(output_vec_learn_tmp, output_vec_learn,
                   fields=fields, proj_in=proj_in, proj_out=proj_out)

        keepFields(output_vec_valid_tmp, output_vec_valid,
                   fields=fields, proj_in=proj_in, proj_out=proj_out)

        out_vectors.append(output_vec_valid)
        out_vectors.append(output_vec_learn)

        os.remove(output_vec_learn_tmp)
        os.remove(output_vec_valid_tmp)

    return out_vectors


def vector_formatting(cfg, tile_name, workingDirectory=None, logger=logger):
    """
    """
    
    #const
    tile_field = "tile_o"

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
    split_directory = os.path.join(cfg.getParam('chain', 'outputPath'), "dataAppVal")
    
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

    create_tile_region_masks(tileRegion, regionField, tile_name,
                             os.path.join(cfg.getParam('chain', 'outputPath'), "shapeRegion"))
                             
    logger.info("launch intersection between tile's envelopeRegion and groundTruth")
    tileRegionGroundTruth = os.path.join(workingDirectory, "tileRegionGroundTruth_" + tile_name + ".sqlite")
    intersect.intersectSqlites(tileRegion, groundTruth_vec, workingDirectory, tileRegionGroundTruth,
                               epsg, "intersection", [dataField, regionField], vectformat='SQLite')
    
    logger.info("remove unsable samples")
    intersect.intersectSqlites(tileRegionGroundTruth, cloud_vec, workingDirectory, output,
                               epsg, "intersection", [dataField, regionField], vectformat='SQLite')

    os.remove(tileRegion)
    os.remove(tileRegionGroundTruth)

    logger.info("split {} in {} subsets with the ratio {}".format(output, seeds, ratio))
    subset.splitInSubSets(output, dataField, regionField, ratio, seeds, output_driver)

    addField(output, tile_field, tile_name, valueType=str, driver_name=output_driver)

    split_dir = split_directory
    if workingDirectory:
        split_dir = workingDirectory
    #splits by learning and validation sets (use in validations steps)
    output_splits = splitbySets(output, seeds, split_dir, epsg, epsg, tile_name)

    if workingDirectory:
        if output_driver == "SQLite":
            shutil.copy(output, os.path.join(cfg.getParam('chain', 'outputPath'), "formattingVectors"))
            os.remove(output)

        elif output_driver == "ESRI Shapefile":
            fut.cpShapeFile(output.replace(".shp", ""), os.path.join(cfg.getParam('chain', 'outputPath'), "formattingVectors"), [".prj", ".shp", ".dbf", ".shx"], True)
            fut.removeShape(output.replace(".shp", ""), [".prj", ".shp", ".dbf", ".shx"])

        for currentSplit in output_splits:
                shutil.copy(currentSplit, os.path.join(cfg.getParam('chain', 'outputPath'), "dataAppVal"))
                os.remove(currentSplit)

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
