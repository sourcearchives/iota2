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
fut.updatePyPath()

from AddField import addField

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
                addField(shape, region_field, region)
        #get regions in shapes to merge
        regions = "_".join(set([os.path.split(shape)[-1].split("_")[2] for shape in shapes_to_merge]))
        output_name = "_".join([tile, "regions", regions, "seed_" + str(run)])
        output_path = os.path.join(output_dir, output_name + ".shp")
        if not os.path.exists(output_path):
            fut.mergeVectors(output_name, output_dir,shapes_to_merge)

def formatting_vectors(cfg, workingDirectory=None):
    """
    usage

    IN
    OUT
    """
    from distutils.dir_util import copy_tree

    iota2_output = cfg.getParam('chain', 'outputPath')
    learning_val_dir = os.path.join(iota2_output, "dataAppVal")
    outputDir = os.path.join(iota2_output, "formattingVectors")


    if workingDirectory:
        outputDir = os.path.join(workingDirectory, "formattingVectors")
        learning_val_dir = os.path.join(workingDirectory, "dataAppVal")

        if os.path.exists(outputDir):
            shutil.rmtree(outputDir)
        if os.path.exists(learning_val_dir):
            shutil.rmtree(learning_val_dir)
        shutil.copytree(os.path.join(iota2_output, "dataAppVal"), learning_val_dir)
        shutil.copytree(os.path.join(iota2_output, "formattingVectors"), outputDir)

    tiles = cfg.getParam('chain', 'listTile').split()
    runs = cfg.getParam('chain', 'runs')
    region_field = "region"

    for tile in tiles:
        merge_vectors(learning_val_dir, outputDir, region_field, runs, tile)

    if workingDirectory:
        all_content = os.listdir(outputDir)
        for content in all_content:
            shutil.copy(os.path.join(outputDir, content),
                        os.path.join(iota2_output, "formattingVectors"))


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





