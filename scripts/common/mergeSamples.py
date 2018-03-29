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

import logging
import os
import shutil

import fileUtils as fut


logger = logging.getLogger(__name__)


def get_models(formatting_vector_directory, regionField, runs):
    """
    usage :
    describe samples spatial repartition
    function use to determine with shapeFile as to be merged in order to compute
    statistics thanks to otb_SampleSelection
    
    OUT:
    regions_tiles_seed [list] : 
    example
    regions_tiles_seed = [('1', ['T1', 'T2'], 0), ('1', ['T1', T2], 1), ('2', ['T2', 'T3], 0), ('2', ['T2', 'T3], 1)]
    mean the region '1' is present in tiles 'T1' and 'T2' in run 0 and 1 and region '2' in 'T2', 'T3' in runs 0 and 1
    """
    #the way of getting region could be improve ?
    tiles = fut.FileSearch_AND(formatting_vector_directory, True, ".shp")
    region_tile = []
    all_regions = []
    for tile in tiles:
        tile_name = os.path.splitext(os.path.basename(tile))[0]

        r_tmp = fut.getFieldElement(tile, driverName="ESRI Shapefile", field=regionField, mode="unique",
                                           elemType="str")

        for r_tile in r_tmp:
            if not r_tile in all_regions:
                all_regions.append(r_tile)

        for region in all_regions:
            region_tile.append((region, tile_name))
    
    region_tile_tmp = dict(fut.sortByFirstElem(region_tile))
    region_tile_dic = {}
    for region, region_tiles in region_tile_tmp.items():
        region_tile_dic[region] = list(set(region_tiles))
    
    regions_tiles_seed = [(region, region_tile_dic[region], run) for run in range(runs) for region in all_regions ]

    return regions_tiles_seed


def extract_POI(tile_vector, region, seed, region_field, POI):
    """
    """
    from Utils import run
    cmd = "ogr2ogr -where \"{}='{}' AND seed_{}='learn'\" {} {}".format(region_field,
                                                                        region, seed,
                                                                        POI, tile_vector)
    run(cmd)


def samples_merge(region_tiles_seed, cfg, workingDirectory):
    """
    """
    import serviceConfigFile as SCF

    #because serviceConfigFile's objects are not serializable
    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    region, tiles, seed = region_tiles_seed

    iota2_directory = cfg.getParam('chain', 'outputPath')
    region_field = cfg.getParam('chain', 'regionField')
    formatting_vec_dir = os.path.join(iota2_directory, "formattingVectors")
    samples_selection_dir = os.path.join(iota2_directory, "samplesSelection")

    wd = samples_selection_dir
    if workingDirectory:
        wd = workingDirectory

    vector_region = []
    for tile in tiles:
        vector_tile = fut.FileSearch_AND(formatting_vec_dir, True, tile, ".shp")[0]
        POI_name = "{}_region_{}_seed_{}_samples.shp".format(tile, region, seed)
        POI = os.path.join(wd, POI_name)
        extract_POI(vector_tile, region, seed, region_field, POI)
        vector_region.append(POI)

    merged_POI_name = "samples_region_{}_seed_{}".format(region, seed)
    merged_POI = fut.mergeVectors(merged_POI_name, wd, vector_region)

    for vector_r in vector_region:
        fut.removeShape(vector_r.replace(".shp",""), [".prj",".shp",".dbf",".shx"])
        
    if workingDirectory:
        fut.cpShapeFile(merged_POI.replace(".shp",""), samples_selection_dir, [".prj",".shp",".dbf",".shx"], spe=True)
