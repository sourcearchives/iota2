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

from Common import FileUtils as fut
from Common import ServiceConfigFile as SCF
from Sampling import SplitInSubSets as subset
from VectorTools.AddField import addField
from Common.Utils import run

logger = logging.getLogger(__name__)


def split_vector_by_region(in_vect, output_dir, region_field, runs=1, driver="ESRI shapefile",
                           proj_in="EPSG:2154", proj_out="EPSG:2154", mode="usually"):
    """
    create new files by regions in input vector.

    Parameters
    ----------
    in_vect : string
        input vector path
    output_dir : string
        path to output directory
    region_field : string
        field in in_vect describing regions
    driver : string
        ogr driver
    proj_in : string
        input projection
    proj_out : string
        output projection
    mode : string
        define if we split SAR sensor to the other
    Return
    ------
    list
        paths to new output vectors
    """

    output_paths = []

    #const
    tile_pos = 0
    seed_pos = -2
    learn_flag = "learn"
    valid_flag = "validation"
    tableName = "output"

    vec_name = os.path.split(in_vect)[-1]
    tile = vec_name.split("_")[tile_pos]
    extent = os.path.splitext(vec_name)[-1]

    regions = fut.getFieldElement(in_vect, driverName=driver, field=region_field, mode="unique",
                                  elemType="str")

    table = vec_name.split(".")[0]
    if driver != "ESRI shapefile":
        table = "output"
    #split vector
    for seed in range(runs):
        fields_to_keep = ",".join([elem for elem in fut.getAllFieldsInShape(in_vect, "SQLite") if "seed_" not in elem])
        for region in regions:
            out_vec_name_learn = "_".join([tile, "region", region, "seed" + str(seed), "Samples_learn_tmp"])
            if mode != "usually":
                out_vec_name_learn = "_".join([tile, "region", region, "seed" + str(seed), "Samples", "SAR", "learn_tmp"])
            output_vec_learn = os.path.join(output_dir, out_vec_name_learn + extent)
            seed_clause_learn = "seed_{}='{}'".format(seed, learn_flag)
            region_clause = "{}='{}'".format(region_field, region)

            # split vectors by runs and learning sets
            sql_cmd_learn = "select * FROM {} WHERE {} AND {}".format(table, seed_clause_learn, region_clause)
            cmd = 'ogr2ogr -t_srs {} -s_srs {} -nln {} -f "{}" -sql "{}" {} {}'.format(proj_out,
                                                                                       proj_in,
                                                                                       table,
                                                                                       driver,
                                                                                       sql_cmd_learn,
                                                                                       output_vec_learn,
                                                                                       in_vect)
            run(cmd)

            # drop useless column
            sql_clause = "select GEOMETRY,{} from {}".format(fields_to_keep, tableName)
            output_vec_learn_out = output_vec_learn.replace("_tmp", "")

            cmd = "ogr2ogr -s_srs {} -t_srs {} -dialect 'SQLite' -f 'SQLite' -nln {} -sql '{}' {} {}".format(proj_in,
                                                                                                             proj_out,
                                                                                                             tableName,
                                                                                                             sql_clause,
                                                                                                             output_vec_learn_out,
                                                                                                             output_vec_learn)
            run(cmd)
            output_paths.append(output_vec_learn_out)
            os.remove(output_vec_learn)

    return output_paths


def create_tile_region_masks(tileRegion, regionField, tile_name, outputDirectory,
                             origin_name, img_ref):
    """
    
    Parameters
    ----------
    tileRegion : string
        path to a SQLite file containing polygons. Each feature is a region
    regionField : string
        region's field
    tile_name : string
        current tile name
    outputDirectory : string
        directory to save masks
    origin_name : string
        region's field vector file name
    img_ref : string
        path to a tile reference image
    """

    from Common import OtbAppBank as otb

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
    use to extract fields of an input SQLite file

    Parameters
    ----------
    vec_in : string
        input SQLite vector File
    vec_out : string
        output SQLite vector File
    fields : list
        list of fields to keep
    proj_in : int
        input projection
    proj_out : int
        output projection
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


def splitbySets(vector, seeds, split_directory, proj_in, proj_out, tile_name,
                crossValid=False, splitGroundTruth=True):
    """
    use to create new vector file by learning / validation sets

    Parameters
    ----------
    vector : string
        path to a shape file containg ground truth
    seeds : int
        number of run
    split_directory : string
        output directory
    proj_in : int
        input projection
    proj_out : int
        output projection
    tile_name : string
        tile's name
    crossValid : bool
        flag to enable cross validation
    splitGroundTruth : bool
        flat to split ground truth
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
    fields = [field_name for field_name in all_fields if field_name not in fields_to_rm]

    #start split
    for seed in range(seeds):
        valid_clause = "seed_{}='{}'".format(seed, valid_flag)
        learn_clause = "seed_{}='{}'".format(seed, learn_flag)

        sql_cmd_valid = "select * FROM {} WHERE {}".format(vector_layer_name, valid_clause)
        output_vec_valid_name = "_".join([tile_name, "seed_" + str(seed), "val"])
        output_vec_valid_name_tmp = "_".join([tile_name, "seed_" + str(seed), "val", "tmp"])
        output_vec_valid_tmp = os.path.join(split_directory, output_vec_valid_name_tmp + ".sqlite")
        output_vec_valid = os.path.join(split_directory, output_vec_valid_name + ".sqlite")
        cmd_valid = 'ogr2ogr -t_srs EPSG:{} -s_srs EPSG:{} -nln {} -f "SQLite" -sql "{}" {} {}'.format(proj_out,
                                                                                                       proj_in,
                                                                                                       output_vec_valid_name_tmp,
                                                                                                       sql_cmd_valid,
                                                                                                       output_vec_valid_tmp,
                                                                                                       vector)


        sql_cmd_learn = "select * FROM {} WHERE {}".format(vector_layer_name, learn_clause)
        output_vec_learn_name = "_".join([tile_name, "seed_" + str(seed), "learn"])
        output_vec_learn_name_tmp = "_".join([tile_name, "seed_" + str(seed), "learn", "tmp"])
        output_vec_learn_tmp = os.path.join(split_directory, output_vec_learn_name_tmp + ".sqlite")
        output_vec_learn = os.path.join(split_directory, output_vec_learn_name + ".sqlite")
        cmd_learn = 'ogr2ogr -t_srs EPSG:{} -s_srs EPSG:{} -nln {} -f "SQLite" -sql "{}" {} {}'.format(proj_out,
                                                                                                       proj_in,
                                                                                                       output_vec_learn_name_tmp,
                                                                                                       sql_cmd_learn,
                                                                                                       output_vec_learn_tmp,
                                                                                                       vector)
        if crossValid is False:
            if splitGroundTruth:
                run(cmd_valid)
                #remove useless fields
                keepFields(output_vec_valid_tmp, output_vec_valid,
                           fields=fields, proj_in=proj_in, proj_out=proj_out)
                os.remove(output_vec_valid_tmp)
            run(cmd_learn)
            #remove useless fields
            keepFields(output_vec_learn_tmp, output_vec_learn,
                       fields=fields, proj_in=proj_in, proj_out=proj_out)           
            os.remove(output_vec_learn_tmp)
            
            if splitGroundTruth is False:
                shutil.copy(output_vec_learn, output_vec_valid)

            out_vectors.append(output_vec_valid)
            out_vectors.append(output_vec_learn)
            
        else:
            if seed < seeds - 1:
                run(cmd_learn)
                keepFields(output_vec_learn_tmp, output_vec_learn,
                           fields=fields, proj_in=proj_in, proj_out=proj_out)
                out_vectors.append(output_vec_learn)
                os.remove(output_vec_learn_tmp)
            elif seed == seeds - 1:
                run(cmd_valid)
                keepFields(output_vec_valid_tmp, output_vec_valid,
                           fields=fields, proj_in=proj_in, proj_out=proj_out)
                out_vectors.append(output_vec_valid)
                os.remove(output_vec_valid_tmp)
    return out_vectors


def BuiltWhereSQL_exp(sample_id_to_extract, clause):
    """
    """
    import math
    if not clause in ["in", "not in"]:
        raise Exception("clause must be 'in' or 'not in'")
    SQL_LIMIT = 1000.0
    sample_id_to_extract = map(str, sample_id_to_extract)
    sample_id_to_extract = fut.splitList(sample_id_to_extract,
                                         nbSplit=int(math.ceil(float(len(sample_id_to_extract)) / SQL_LIMIT)))
    list_fid = ["fid {} ({})".format(clause, ",".join(chunk)) for chunk in sample_id_to_extract]
    sql_exp = " OR ".join(list_fid)
    return sql_exp


def extract_maj_vote_samples(vec_in, vec_out, ratio_to_keep, dataField,
                             regionField, driver_name="ESRI Shapefile"):
    """
    dedicated to extract samples by class according to a ratio.
    Samples are remove from vec_in and place in vec_out

    Parameters
    ----------
    vec_in : string
        path to a shapeFile (.shp)
    vec_out : string
        path to a sqlite (.sqlite)
    ratio_to_keep [float]
        percentage of samples to extract ratio_to_keep = 0.1
        mean extract 10% of each class in each regions
    dataField : string
        field containing class labels
    regionField : string
        field containing regions labels
    driver_name : string
        OGR driver
    """

    from osgeo import gdal
    from osgeo import ogr
    from osgeo import osr
    from osgeo.gdalconst import *
    import sqlite3 as lite
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
    fid_samples_in = BuiltWhereSQL_exp(sample_id_to_extract, clause="in")
    cmd = "ogr2ogr -where '{}' -f 'SQLite' {} {}".format(fid_samples_in, vec_out, vec_in)
    run(cmd)

    #remove in vec_in targeted FID
    vec_in_rm = vec_in.replace(".shp", "_tmp.shp")
    fid_samples_notIn = BuiltWhereSQL_exp(sample_id_to_extract, clause="not in")
    cmd = "ogr2ogr -where '{}' {} {}".format(fid_samples_notIn, vec_in_rm, vec_in)
    run(cmd)

    fut.removeShape(vec_in.replace(".shp", ""), [".prj", ".shp", ".dbf", ".shx"])

    cmd = "ogr2ogr {} {}".format(vec_in, vec_in_rm)
    run(cmd)

    fut.removeShape(vec_in_rm.replace(".shp", ""), [".prj", ".shp", ".dbf", ".shx"])


def VectorFormatting(cfg, tile_name, workingDirectory=None, logger=logger):
    """
    dedicated to extract samples by class according to a ratio
    or a fold number.

    Parameters
    ----------
    cfg : ServiceConfig object
    tile_name : string
    workingDirectory : string
    logger : Logging object
        root logger
    """
    from VectorTools import spatialOperations as intersect
    from VectorTools import ChangeNameField

    #const
    tile_field = "tile_o"

    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    #extract information into the configuration file
    output_directory = os.path.join(cfg.getParam('chain', 'outputPath'), "formattingVectors")
    if workingDirectory:
        output_directory = workingDirectory
    output_name = tile_name + ".shp"
    output = os.path.join(output_directory, output_name)

    groundTruth_vec = cfg.getParam('chain', 'groundTruth')
    dataField = (cfg.getParam('chain', 'dataField')).lower()

    cloud_threshold = cfg.getParam('chain', 'cloud_threshold')
    features_directory = os.path.join(cfg.getParam('chain', 'outputPath'),
                                      "features")
    cloud_vec = os.path.join(features_directory, tile_name, "CloudThreshold_" + str(cloud_threshold) + ".shp")
    tileEnv_vec = os.path.join(cfg.getParam('chain', 'outputPath'), "envelope", tile_name + ".shp")
    ratio = cfg.getParam('chain', 'ratio')
    enableCrossValidation = cfg.getParam('chain', 'enableCrossValidation')
    enableSplitGroundTruth = cfg.getParam('chain', 'splitGroundTruth')
    fusionMergeAllValidation = cfg.getParam('chain', 'fusionOfClassificationAllSamplesValidation')
    seeds = cfg.getParam('chain', 'runs')
    epsg = int((cfg.getParam('GlobChain', 'proj')).split(":")[-1])
    split_directory = os.path.join(cfg.getParam('chain', 'outputPath'), "dataAppVal")
    formatting_directory = os.path.join(cfg.getParam('chain', 'outputPath'), "formattingVectors")
    final_directory = os.path.join(cfg.getParam('chain', 'outputPath'), "final")
    region_vec = cfg.getParam('chain', 'regionPath')
    regionField = (cfg.getParam('chain', 'regionField')).lower()
    if not region_vec:
        region_vec = os.path.join(cfg.getParam("chain", "outputPath") , "MyRegion.shp")

    merge_final_classifications = cfg.getParam('chain', 'merge_final_classifications')
    if merge_final_classifications:
        merge_final_classifications_ratio = cfg.getParam('chain', 'merge_final_classifications_ratio')
        wd_maj_vote = os.path.join(final_directory, "merge_final_classifications")
        if workingDirectory:
            wd_maj_vote = workingDirectory

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
    region_tile_intersection = intersect.intersectSqlites(tileEnv_vec, region_vec, wd, tileRegion,
                                                          epsg, "intersection", [regionField], vectformat='SQLite')
    if not region_tile_intersection:
        error_msg = "there is no intersections between the tile '{}' and the region shape '{}'".format(tile_name, region_vec)
        logger.critical(error_msg)
        raise Exception(error_msg)

    region_vector_name = os.path.splitext(os.path.basename(region_vec))[0]
    create_tile_region_masks(tileRegion, regionField, tile_name,
                             os.path.join(cfg.getParam('chain', 'outputPath'),
                                          "shapeRegion"), region_vector_name, img_ref)

    logger.info("launch intersection between tile's envelopeRegion and groundTruth")
    tileRegionGroundTruth = os.path.join(wd, "tileRegionGroundTruth_" + tile_name + ".sqlite")

    if intersect.intersectSqlites(tileRegion, groundTruth_vec, wd, tileRegionGroundTruth,
                                  epsg, "intersection", [dataField, regionField, "ogc_fid"], vectformat='SQLite') is False:
        warning_msg = "there si no intersections between the tile '{}' and the grount truth '{}'".format(tile_name, groundTruth_vec)
        logger.warning(warning_msg)
        return None

    logger.info("remove un-usable samples")

    intersect.intersectSqlites(tileRegionGroundTruth, cloud_vec, wd, output,
                               epsg, "intersection", [dataField, regionField, "t2_ogc_fid"], vectformat='SQLite')

    os.remove(tileRegion)
    os.remove(tileRegionGroundTruth)

    #rename field t2_ogc_fid to originfig which correspond to the polygon number
    ChangeNameField.changeName(output, "t2_ogc_fid", "originfid")

    if merge_final_classifications and fusionMergeAllValidation is False:
        maj_vote_sample_tile_name = "{}_majvote.sqlite".format(tile_name)
        maj_vote_sample_tile = os.path.join(wd_maj_vote, maj_vote_sample_tile_name)
        if enableCrossValidation is False:
            extract_maj_vote_samples(output, maj_vote_sample_tile,
                                     merge_final_classifications_ratio, dataField, regionField,
                                     driver_name="ESRI Shapefile")

    logger.info("split {} in {} subsets with the ratio {}".format(output, seeds, ratio))
    subset.splitInSubSets(output, dataField, regionField, ratio, seeds,
                          output_driver,
                          crossValidation=enableCrossValidation,
                          splitGroundTruth=enableSplitGroundTruth)

    addField(output, tile_field, tile_name, valueType=str, driver_name=output_driver)

    split_dir = split_directory
    if workingDirectory:
        split_dir = wd

    #splits by learning and validation sets (use in validations steps)
    output_splits = splitbySets(output, seeds, split_dir, epsg, epsg,
                                tile_name,
                                crossValid=enableCrossValidation,
                                splitGroundTruth=enableSplitGroundTruth)
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

        if merge_final_classifications and enableCrossValidation is False:
            shutil.copy(maj_vote_sample_tile, os.path.join(final_directory, "merge_final_classifications"))

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
    VectorFormatting(cfg, args.tile_name, args.workingDirectory)
