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
from AddField import addField
from Utils import run
import spatialOperations as intersect

logger = logging.getLogger(__name__)


def create_tile_region_masks(tileRegion, regionField, tile_name, outputDirectory,
                             origin_name, img_ref):
    """
    """
    import otbAppli as otb

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
        output_name = "{}_region_{}_{}.shp".format(origin_name, region, tile_name)
        output_path = os.path.join(outputDirectory, output_name)
        db_name = (os.path.splitext(os.path.basename(tileRegion))[0]).lower()
        cmd = "ogr2ogr -f 'ESRI Shapefile' -sql \"SELECT * FROM {} WHERE {}='{}'\" {} {}".format(db_name,
                                                                                                 regionField,
                                                                                                 region,
                                                                                                 output_path,
                                                                                                 tileRegion)
        run(cmd)

        path, ext = os.path.splitext(output_path)
        tile_region_raster = "{}.tif".format(path)
        tile_region_app = otb.CreateRasterizationApplication({"in": output_path,
                                                          "out": tile_region_raster,
                                                          "im": img_ref,
                                                          "mode": "binary",
                                                          "pixType": "uint8",
                                                          "background": "0",
                                                          "mode.binary.foreground" : "1"})
        tile_region_app.ExecuteAndWriteOutput()
    
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


def extract_maj_vote_samples(vec_in, vec_out, ratio_to_keep, dataField,
                             regionField, driver_name="ESRI Shapefile"):
    """
    usage : dedicated to extract samples by class according to a ratio
            samples are remove from vec_in and place in vec_out
    vec_in [string] path to a shapeFile (.shp)
    vec_out [string] path to a sqlite (.sqlite)
    ratio_to_keep [float] percentage of samples to extract 
                          ratio_to_keep = 0.1 mean extract 10% of each class in 
                          each regions.
    """
    from osgeo import gdal
    from osgeo import ogr
    from osgeo import osr
    from osgeo.gdalconst import *
    import sqlite3 as lite
    from Utils import run
    class_avail = fut.getFieldElement(vec_in, driverName=driver_name,
                                      field=dataField, mode="unique", elemType="int")
    region_avail = fut.getFieldElement(vec_in, driverName=driver_name,
                                       field=regionField, mode="unique", elemType="str")

    driver = ogr.GetDriverByName(driver_name)
    source = driver.Open(vec_in, 1)
    layer = source.GetLayer(0)

    sample_id_to_extract, _ = subset.get_randomPoly(layer, dataField,
                                                    class_avail, ratio_to_keep,
                                                    regionField, region_avail)

    #Create new file with targeted FID
    fid_samples = "({})".format(",".join(map(str, sample_id_to_extract)))
    cmd = "ogr2ogr -where 'fid in {}' -f 'SQLite' {} {}".format(fid_samples, vec_out, vec_in)
    run(cmd)

    #remove in vec_in targeted FID
    vec_in_rm = vec_in.replace(".shp", "_tmp.shp")
    cmd = "ogr2ogr -where 'fid not in {}' {} {}".format(fid_samples, vec_in_rm, vec_in)
    run(cmd)

    fut.removeShape(vec_in.replace(".shp",""), [".prj",".shp",".dbf",".shx"])

    cmd = "ogr2ogr {} {}".format(vec_in, vec_in_rm)
    run(cmd)
    
    fut.removeShape(vec_in_rm.replace(".shp",""), [".prj",".shp",".dbf",".shx"])


def vector_formatting(cfg, tile_name, workingDirectory=None, logger=logger):
    """
    usage : dedicated to extract samples by class according to a ratio
            samples are remove from vec_in and place in vec_out
    vec_in [string] path to a shapeFile (.shp)
    vec_out [string] path to a sqlite (.sqlite)
    ratio_to_keep [float] percentage of samples to extract 
                          ratio_to_keep = 0.1 mean extract 10% of each class in 
                          each regions.
    """
    from osgeo import gdal
    from osgeo import ogr
    from osgeo import osr
    from osgeo.gdalconst import *
    import sqlite3 as lite
    from Utils import run
    class_avail = fut.getFieldElement(vec_in, driverName=driver_name,
                                      field=dataField, mode="unique", elemType="int")
    region_avail = fut.getFieldElement(vec_in, driverName=driver_name,
                                       field=regionField, mode="unique", elemType="str")

    driver = ogr.GetDriverByName(driver_name)
    source = driver.Open(vec_in, 1)
    layer = source.GetLayer(0)

    sample_id_to_extract, _ = subset.get_randomPoly(layer, dataField,
                                                    class_avail, ratio_to_keep,
                                                    regionField, region_avail)

    #Create new file with targeted FID
    fid_samples = "({})".format(",".join(map(str, sample_id_to_extract)))
    cmd = "ogr2ogr -where 'fid in {}' -f 'SQLite' {} {}".format(fid_samples, vec_out, vec_in)
    run(cmd)

    #remove in vec_in targeted FID
    vec_in_rm = os.path.basename(vec_in).replace(".shp", "_tmp.shp")
    cmd = "ogr2ogr -where 'fid not in {}' {} {}".format(fid_samples, vec_in_rm, vec_in)
    run(cmd)

    fut.removeShape(vec_in.replace(".shp",""), [".prj",".shp",".dbf",".shx"])

    cmd = "ogr2ogr {} {}".format(vec_in, vec_in_rm)
    run(cmd)
    
    fut.removeShape(vec_in_rm.replace(".shp",""), [".prj",".shp",".dbf",".shx"])


def vector_formatting(cfg, tile_name, workingDirectory=None, logger=logger):
    """
    """
    import ChangeNameField

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
    formatting_directory = os.path.join(cfg.getParam('chain', 'outputPath'), "formattingVectors")
    final_directory = os.path.join(cfg.getParam('chain', 'outputPath'), "final")
    try:
        generateMajorityVoteMap = cfg.getParam('chain', 'generateMajorityVoteMap')
        if generateMajorityVoteMap:
            majorityVoteMap_ratio = cfg.getParam('chain', 'majorityVoteMap_ratio')
            wd_maj_vote = os.path.join(final_directory, "majVoteValid")
            if workingDirectory:
                wd_maj_vote = workingDirectory
    except:
        generateMajorityVoteMap = False

    output_driver = "SQlite"
    if os.path.splitext(os.path.basename(output))[-1] == ".shp":
        output_driver = "ESRI Shapefile"

    wd = formatting_directory
    if workingDirectory:
        wd = workingDirectory
    
    wd = os.path.join(wd, tile_name)
    try:
        os.mkdir(wd)
    except OSError:
        logger.warning(wd + "allready exists")

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
    logger.debug("workingDirectory : {}".format(wd))

    img_ref = fut.FileSearch_AND(os.path.join(features_directory, tile_name), True, ".tif")[0]
    
    logger.info("launch intersection between tile's envelope and regions")
    tileRegion = os.path.join(wd, "tileRegion_" + tile_name + ".sqlite")

    intersect.intersectSqlites(tileEnv_vec, region_vec, wd, tileRegion,
                               epsg, "intersection", [regionField], vectformat='SQLite')

    region_vector_name = os.path.splitext(os.path.basename(region_vec))[0]
    create_tile_region_masks(tileRegion, regionField, tile_name,
                             os.path.join(cfg.getParam('chain', 'outputPath'),
                             "shapeRegion"), region_vector_name, img_ref)
                             
    logger.info("launch intersection between tile's envelopeRegion and groundTruth")
    tileRegionGroundTruth = os.path.join(wd, "tileRegionGroundTruth_" + tile_name + ".sqlite")

    intersect.intersectSqlites(tileRegion, groundTruth_vec, wd, tileRegionGroundTruth,
                               epsg, "intersection", [dataField, regionField, "ogc_fid"], vectformat='SQLite')

    logger.info("remove un-usable samples")

    intersect.intersectSqlites(tileRegionGroundTruth, cloud_vec, wd, output,
                               epsg, "intersection", [dataField, regionField, "t2_ogc_fid"], vectformat='SQLite')

    os.remove(tileRegion)
    os.remove(tileRegionGroundTruth)

    #rename field t2_ogc_fid to originfig which correspond to the polygon number
    ChangeNameField.changeName(output, "t2_ogc_fid", "originfid")

    if generateMajorityVoteMap:
        maj_vote_sample_tile_name = "{}_majvote.sqlite".format(tile_name)
        maj_vote_sample_tile = os.path.join(wd_maj_vote, maj_vote_sample_tile_name)
        extract_maj_vote_samples(output, maj_vote_sample_tile,
                                 majorityVoteMap_ratio, dataField, regionField,
                                 driver_name="ESRI Shapefile")
    
    logger.info("split {} in {} subsets with the ratio {}".format(output, seeds, ratio))
    subset.splitInSubSets(output, dataField, regionField, ratio, seeds, output_driver)

    addField(output, tile_field, tile_name, valueType=str, driver_name=output_driver)

    split_dir = split_directory
    if workingDirectory:
        split_dir = wd
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
        
        if generateMajorityVoteMap:
            shutil.copy(maj_vote_sample_tile, os.path.join(final_directory, "majVoteValid"))

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
