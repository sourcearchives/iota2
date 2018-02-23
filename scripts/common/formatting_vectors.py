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
import fileUtils as fut
import serviceConfigFile as SCF
import shutil
import os
from Utils import run
fut.updatePyPath()

from AddField import addField
from DeleteField import deleteField
from mpi4py import MPI


def get_regions(vec_name):
    """
    """
    regions = []
    for elem in range(2, len(vec_name.split("_"))):
        if vec_name.split("_")[elem] == "seed":
            break
        else:
            regions.append(vec_name.split("_")[elem])
    return regions


def split_vector_by_region(in_vect, output_dir, region_field, runs=1, driver="ESRI shapefile",
                           proj_in="EPSG:2154", proj_out="EPSG:2154"):
    """
    usage : split a vector considering a field value
    
    IN
    in_vect [string] : input vector path
    output_dir [string] : path to output directory 
    region_field [string]
    driver [string]
    proj_in [string]
    proj_out [string]
    OUT
    output_paths [list of strings] : paths to new output vectors
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

    #regions = get_regions(vec_name)
    regions = fut.getFieldElement(in_vect, driverName=driver, field=region_field, mode="unique",
                                  elemType="str")
    
    table = vec_name.split(".")[0]
    if driver != "ESRI shapefile":
        table = "output"
    #split vector
    for seed in range(runs):
        fields_to_keep = ",".join([elem for elem in fut.getAllFieldsInShape(in_vect, "SQLite") if not "seed_" in elem])
        for region in regions:
            out_vec_name_learn = "_".join([tile, "region", region, "seed" + str(seed), "Samples_learn_tmp"])
            out_vec_name_valid = "_".join([tile, "region", region, "seed" + str(seed), "Samples_valid_tmp"])
            output_vec_learn = os.path.join(output_dir, out_vec_name_learn + extent)
            output_vec_val = os.path.join(output_dir, out_vec_name_valid + extent)

            seed_clause_learn = "seed_{}='{}'".format(seed, learn_flag)
            seed_clause_valid = "seed_{}='{}'".format(seed, valid_flag)
            region_clause = "{}='{}'".format(region_field, region)
            
            #split vectors by runs and learning / validation sets
            sql_cmd_learn = "select * FROM {} WHERE {} AND {}".format(table, seed_clause_learn, region_clause)
            cmd = 'ogr2ogr -t_srs {} -s_srs {} -nln {} -f "{}" -sql "{}" {} {}'.format(proj_out,
                                                                                       proj_in,
                                                                                       table,
                                                                                       driver,
                                                                                       sql_cmd_learn,
                                                                                       output_vec_learn,
                                                                                       in_vect)
            run(cmd)

            sql_cmd_valid = "select * FROM {} WHERE {} AND {}".format(table, seed_clause_valid, region_clause)
            cmd = 'ogr2ogr -t_srs {} -s_srs {} -nln {} -f "{}" -sql "{}" {} {}'.format(proj_out,
                                                                                       proj_in,
                                                                                       table,
                                                                                       driver,
                                                                                       sql_cmd_valid,
                                                                                       output_vec_val,
                                                                                       in_vect)
            run(cmd)

            #Drop useless column
            sql_clause = "select GEOMETRY,{} from {}".format(fields_to_keep, tableName)
            output_vec_learn_out = output_vec_learn.replace("_tmp", "")
            output_vec_val_out = output_vec_val.replace("_tmp", "")
            

            cmd = "ogr2ogr -s_srs {} -t_srs {} -dialect 'SQLite' -f 'SQLite' -nln {} -sql '{}' {} {}".format(proj_in,
                                                                                                            proj_out,
                                                                                                            tableName,
                                                                                                            sql_clause,
                                                                                                            output_vec_learn_out,
                                                                                                            output_vec_learn)
            run(cmd)
            cmd = "ogr2ogr -s_srs {} -t_srs {} -dialect 'SQLite' -f 'SQLite' -nln {} -sql '{}' {} {}".format(proj_in,
                                                                                                             proj_out,
                                                                                                             tableName,
                                                                                                             sql_clause,
                                                                                                             output_vec_val_out,
                                                                                                             output_vec_val)
            run(cmd)
            output_paths.append(output_vec_learn_out)
            output_paths.append(output_vec_val_out)
            
            os.remove(output_vec_learn)
            os.remove(output_vec_val)
    return output_paths


def merge_vectors(data_app_val_dir, output_dir, region_field, runs, tile):
    """
    usage : for each vectors in tile, add a region field and concatenates them

    IN
    data_app_val_dir [string] : path to the folder containing vectors
    output_dir [string] : path to output direcotry
    region_field [string] : ouput regions's field name
    runs [int] number of runs of iota2
    tile [string] : tile's name (ex : 'T31TCJ')

    OUT
    """
    #const
    region_pos = 2
    seed_pos = 3

    for run in range(runs):
        #get all shapes
        shapes_to_merge = fut.FileSearch_AND(data_app_val_dir, True, "seed" + str(run),
                                             "learn", ".shp", tile)
        for shape in shapes_to_merge:
            #get region
            region = os.path.split(shape)[-1].split("_")[2]
            fields = fut.getAllFieldsInShape(shape)
            if not region_field in fields:
                addField(shape, region_field, region, valueType=str)

        if shapes_to_merge:
            #get regions in shapes to merge
            regions = "_".join(set([os.path.split(shape)[-1].split("_")[2] for shape in shapes_to_merge]))
            output_name = "_".join([tile, "regions", regions, "seed_" + str(run)])
            output_path = os.path.join(output_dir, output_name + ".shp")
            if not os.path.exists(output_path):
                fut.mergeVectors(output_name, output_dir,shapes_to_merge)

def formatting_vectors(cfg, workingDirectory=None, tile_to_compute=None):
    """
    usage: prepare vector's file to sampling method (merge by regions)

    IN
    cfg [serviceConfig Object]
    workingDirectory [string] : path to a working directory
    tile_to_compute [string] : tile to compute, if None tiles are automatically
                               found by the script
               
    OUT
    """
    from distutils.dir_util import copy_tree

    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)
    iota2_output = cfg.getParam('chain', 'outputPath')
    learning_val_dir = os.path.join(iota2_output, "dataAppVal")
    outputDir = os.path.join(iota2_output, "formattingVectors")

    tiles = cfg.getParam('chain', 'listTile').split()
    runs = cfg.getParam('chain', 'runs')
    region_field = "region"

    if not tile_to_compute:
        for tile in tiles:
            merge_vectors(learning_val_dir, outputDir, region_field, runs, tile)
    else:
        merge_vectors(learning_val_dir, outputDir, region_field, runs, tile_to_compute)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="prepare vector's file to sampling method (merge by regions)")
    parser.add_argument("-conf", help="path to the configuration file (mandatory)",
                        dest="pathConf", required=True)
    parser.add_argument("-wD", help="working directory",
                        dest="workingDirectory", required=False, default=None)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)

    formatting_vectors(cfg, args.workingDirectory)
