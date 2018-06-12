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

from Common import OtbAppBank as otb
from Common import FileUtils as fut
from Common.Utils import run

logger = logging.getLogger(__name__)

def region_tile(sample_sel_dir):
    """
    """
    tile_field_name = "tile_o"
    region_vectors = fut.FileSearch_AND(sample_sel_dir, True, ".shp")
    output = []
    for region_vector in region_vectors:
        tiles = fut.getFieldElement(region_vector, driverName="ESRI Shapefile", field=tile_field_name, mode="unique",
                                    elemType="str")
        region_name = os.path.splitext(os.path.basename(region_vector))[0].split("_")[2]
        seed = os.path.splitext(os.path.basename(region_vector))[0].split("_")[4]

        for tile in tiles:
            output.append((region_name, seed, tile))

    return output


def samples_stats(region_seed_tile, cfg, workingDirectory=None, logger=logger):
    """
    tile_region [tuple] : tile_region[0] = tile's name
                          tile_region[1] = model's name
                          it comes from  get_models_byTile function
    """

    from Common import ServiceConfigFile as SCF
    #because serviceConfigFile's objects are not serializable
    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    #const
    region, seed, tile = region_seed_tile
    iota2_directory = cfg.getParam('chain', 'outputPath')
    region_field = cfg.getParam('chain', 'regionField')
    dataField = cfg.getParam('chain', 'dataField')
    runs = cfg.getParam('chain', 'runs')
    formatting_vec_dir = os.path.join(iota2_directory, "formattingVectors")
    samples_selection_dir = os.path.join(iota2_directory, "samplesSelection")
    tile_region_dir = os.path.join(iota2_directory, "shapeRegion")

    wd = samples_selection_dir
    if workingDirectory:
        wd = workingDirectory

    raster_mask = fut.FileSearch_AND(tile_region_dir, True, "region_" + region.split("f")[0] + "_", ".tif", tile)[0]
    region_vec = fut.FileSearch_AND(samples_selection_dir, True, "_region_" + region, "seed_" + seed, ".shp")[0]

    logger.info("Launch statistics on tile {} in region {} run {}".format(tile, region, seed))
    region_tile_stats_name = "{}_region_{}_seed_{}_stats.xml".format(tile, region, seed)
    region_tile_stats = os.path.join(wd, region_tile_stats_name)
    polygonStats = otb.CreatePolygonClassStatisticsApplication({"in": raster_mask,
                                                                "mask": raster_mask,
                                                                "vec": region_vec,
                                                                "field": dataField,
                                                                "out": region_tile_stats})
    polygonStats.ExecuteAndWriteOutput()
    if workingDirectory:
        shutil.copy(region_tile_stats, samples_selection_dir)
