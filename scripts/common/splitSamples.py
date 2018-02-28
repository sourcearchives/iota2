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
import os
from pyspatialite import dbapi2 as db

import serviceConfigFile as SCF
import fileUtils as fut
from Utils import run


def get_regions_area(vectors, regions, formatting_vectors_dir,
                     workingDirectory, region_field):
    """
    usage : get all models polygons area
    IN
    vectors [list of strings] : path to vector file
    regions [list of string] : all possible regions
    formatting_vectors_dir [string] : path to /iota2/formattingVectors
    workingDirectory [string]
    region_field [string]
    
    OUT
    dico_region_area [dict] : dictionnary containing area by region's key
    """
    
    #init dict
    dico_region_area = {}
    dico_region_tile = {}
    for reg in regions:
        dico_region_area[reg] = 0.0
        dico_region_tile[reg] = []

    for vector in vectors:
        #move vectors to sqlite (faster format)
        transform_dir = formatting_vectors_dir
        if workingDirectory:
            transform_dir = workingDirectory
        transform_vector_name = os.path.split(vector)[-1].replace(".shp", ".sqlite")
        sqlite_vector = os.path.join(transform_dir, transform_vector_name)
        cmd = "ogr2ogr -f 'SQLite' {} {}".format(sqlite_vector, vector)
        run(cmd)
        
        region_vector = fut.getFieldElement(sqlite_vector, driverName="SQLite",
                                            field=region_field, mode="unique",
                                            elemType="str")
        conn = db.connect(sqlite_vector)
        cursor = conn.cursor()
        table_name = (transform_vector_name.replace(".sqlite","")).lower()
        for current_region in region_vector:
            sql_clause = "SELECT AREA(GEOMFROMWKB(GEOMETRY)) FROM {} WHERE {}={}".format(table_name,
                                                                                         region_field,
                                                                                         current_region)
            cursor.execute(sql_clause)
            res = cursor.fetchall()

            dico_region_area[current_region] += sum([area[0] for area in res])
            
            if not vector in dico_region_tile[current_region]:
                dico_region_tile[current_region].append(vector)

        conn = cursor = None
        os.remove(sqlite_vector)
    return dico_region_area, dico_region_tile


def get_splits_regions(areas, region_threshold):
    """
    
    return regions which must be split
    """
    import math
    dic = {}#{'region':Nsplits,..}
    for region, area in areas.items():
        fold = int(math.ceil(area/(region_threshold*1e6)))
        if fold > 1:
            dic[region]=fold
    return dic


def split(regions_split, regions_tiles):
    """
    """
    for region, fold in regions_split.items():
        vector_paths = regions_tiles[region]
        
def splitSamples(cfg, workingDirectory=None):
    """
    """
    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)
    
    #const
    iota2_dir = cfg.getParam('chain', 'outputPath')
    region_threshold = float(cfg.getParam('chain', 'mode_outside_RegionSplit'))
    region_field = (cfg.getParam('chain', 'regionField')).lower()
    regions_pos = 2

    formatting_vectors_dir = os.path.join(iota2_dir, "formattingVectors")
    shape_region_dir = os.path.join(iota2_dir, "shapeRegion")
    
    vectors = fut.FileSearch_AND(formatting_vectors_dir, True, ".shp")
    
    #get All possible regions by parsing shapeFile's name
    shapes_region = fut.FileSearch_AND(shape_region_dir, True, ".shp")
    regions = list(set([os.path.split(shape)[-1].split("_")[regions_pos] for shape in shapes_region]))
    
    #compute region's area
    areas, regions_tiles = get_regions_area(vectors, regions, formatting_vectors_dir, workingDirectory, region_field)
    regions_split = get_splits_regions(areas, region_threshold)
    split(regions_split, regions_tiles)

