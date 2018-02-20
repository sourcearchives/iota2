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


def split_vector_by_region(in_vect, output_dir, region_field, driver="ESRI shapefile",
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
    
    vec_name = os.path.split(in_vect)[-1]
    tile = vec_name.split("_")[tile_pos]
    seed = vec_name.split("_")[seed_pos].split(".")[0]
    extent = os.path.splitext(vec_name)[-1]

    regions = get_regions(vec_name)
    
    table = vec_name.split(".")[0]
    if driver != "ESRI shapefile":
        table = "output"
    #split vector
    for region in regions:
        out_vec_name = "_".join([tile, "region", region, "seed" + seed, "Samples"])
        output_vec = os.path.join(output_dir, out_vec_name + extent)
        output_paths.append(output_vec)
        sql_cmd = "select * FROM " + table + " WHERE " + region_field + "='" + region + "'"
        cmd = 'ogr2ogr -t_srs ' + proj_out + ' -s_srs ' + proj_in + ' -nln ' + table + ' -f "' + driver + '" -sql "' + sql_cmd + '" ' + output_vec + ' ' + in_vect
        run(cmd)

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
