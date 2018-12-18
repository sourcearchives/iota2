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
import logging

from Common import ServiceConfigFile as SCF
from Common import FileUtils as fut
from Common.Utils import run
from Sampling import SplitInSubSets as subset

logger = logging.getLogger(__name__)

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
    from pyspatialite import dbapi2 as db
    tmp_data = []
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
        tmp_data.append(sqlite_vector)
        region_vector = fut.getFieldElement(sqlite_vector, driverName="SQLite",
                                            field=region_field, mode="unique",
                                            elemType="str")
        conn = db.connect(sqlite_vector)
        cursor = conn.cursor()
        table_name = (transform_vector_name.replace(".sqlite", "")).lower()
        for current_region in region_vector:
            sql_clause = "SELECT AREA(GEOMFROMWKB(GEOMETRY)) FROM {} WHERE {}={}".format(table_name,
                                                                                         region_field,
                                                                                         current_region)
            cursor.execute(sql_clause)
            res = cursor.fetchall()

            dico_region_area[current_region] += sum([area[0] for area in res])

            if vector not in dico_region_tile[current_region]:
                dico_region_tile[current_region].append(sqlite_vector)

        conn = cursor = None

    return dico_region_area, dico_region_tile, tmp_data


def get_splits_regions(areas, region_threshold):
    """

    return regions which must be split
    """
    import math
    dic = {}#{'region':Nsplits,..}
    for region, area in areas.items():
        fold = int(math.ceil(area/(region_threshold*1e6)))
        if fold > 1:
            dic[region] = fold
    return dic


def get_FID_values(vector_path, dataField, regionField, region, value):
    """
    """
    from pyspatialite import dbapi2 as db
    conn = db.connect(vector_path)
    cursor = conn.cursor()
    table_name = (os.path.splitext(os.path.basename(vector_path))[0]).lower()

    sql_clause = "SELECT ogc_fid FROM {} WHERE {}={} AND {}='{}'".format(table_name,
                                                                         dataField,
                                                                         value,
                                                                         regionField,
                                                                         region)
    cursor.execute(sql_clause)
    FIDs = cursor.fetchall()
    conn = cursor = None
    return [fid[0] for fid in FIDs]


def update_vector(vector_path, regionField, new_regions_dict, logger=logger):
    """
    """
    #const
    sqlite3_query_limit = 1000.0

    import math
    from pyspatialite import dbapi2 as db
    conn = db.connect(vector_path)
    cursor = conn.cursor()
    table_name = (os.path.splitext(os.path.basename(vector_path))[0]).lower()

    for new_region_name, FIDs in new_regions_dict.items():
        nb_sub_split_SQLITE = int(math.ceil(len(FIDs)/sqlite3_query_limit))
        sub_FID_sqlite = fut.splitList(FIDs, nb_sub_split_SQLITE)

        subFid_clause = []
        for subFID in sub_FID_sqlite:
            subFid_clause.append("(ogc_fid in ({}))".format(", ".join(map(str, subFID))))
        fid_clause = " OR ".join(subFid_clause)
        sql_clause = "UPDATE {} SET {}='{}' WHERE {}".format(table_name, regionField,
                                                             new_region_name, fid_clause)
        logger.debug("update fields")
        logger.debug(sql_clause)

        cursor.execute(sql_clause)
        conn.commit()

    conn = cursor = None

def split(regions_split, regions_tiles, dataField, regionField):
    """
    function dedicated to split to huge regions in sub-regions
    """
    from pyspatialite import dbapi2 as db
    updated_vectors = []

    for region, fold in regions_split.items():
        vector_paths = regions_tiles[region]
        for vec in vector_paths:
            #init dict new regions
            new_regions_dict = {}
            for f in range(fold):
                #new region's name are define here
                new_regions_dict["{}f{}".format(region, f+1)] = []

            #get possible class
            class_vector = fut.getFieldElement(vec, driverName="SQLite",
                                               field=dataField, mode="unique",
                                               elemType="str")
            dic_class = {}
            #get FID values for all class of current region into the current tile
            for c_class in class_vector:
                dic_class[c_class] = get_FID_values(vec, dataField, regionField, region, c_class)

            nb_feat = 0
            for class_name, FID_cl in dic_class.items():
                if FID_cl:
                    FID_folds = fut.splitList(FID_cl, fold)
                    #fill new_regions_dict
                    for i, fid_fold in enumerate(FID_folds):
                        new_regions_dict["{}f{}".format(region, i+1)] += fid_fold
                nb_feat += len(FID_cl)
            update_vector(vec, regionField, new_regions_dict)
            if vec not in updated_vectors:
                updated_vectors.append(vec)

    return updated_vectors


def transform_to_shape(sqlite_vectors, formatting_vectors_dir):
    """
    """
    out = []
    for sqlite_vector in sqlite_vectors:
        out_name = os.path.splitext(os.path.basename(sqlite_vector))[0]
        out_path = os.path.join(formatting_vectors_dir, "{}.shp".format(out_name))
        if os.path.exists(out_path):
            fut.removeShape(out_path.replace(".shp", ""), [".prj", ".shp", ".dbf", ".shx"])
        cmd = "ogr2ogr -f 'ESRI Shapefile' {} {}".format(out_path, sqlite_vector)
        run(cmd)
        out.append(out_path)
    return out


def update_learningValination_sets(new_regions_shapes, dataAppVal_dir,
                                   dataField, regionField, ratio,
                                   seeds, epsg, enableCrossValidation):
    """
    """
    from Sampling.VectorFormatting import splitbySets

    for new_region_shape in new_regions_shapes:
        tile_name = os.path.splitext(os.path.basename(new_region_shape))[0]
        vectors_to_rm = fut.FileSearch_AND(dataAppVal_dir, True, tile_name)
        for vect in vectors_to_rm:
            os.remove(vect)
        #remove seeds fields
        subset.splitInSubSets(new_region_shape, dataField, regionField,
                              ratio, seeds, "ESRI Shapefile",
                              crossValidation=enableCrossValidation)
        output_splits = splitbySets(new_region_shape, seeds, dataAppVal_dir,
                                    epsg, epsg, tile_name,
                                    crossValid=enableCrossValidation)


def splitSamples(cfg, workingDirectory=None, logger=logger):
    """
    """
    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    #const
    iota2_dir = cfg.getParam('chain', 'outputPath')
    dataField = cfg.getParam('chain', 'dataField')
    enableCrossValidation = cfg.getParam('chain', 'enableCrossValidation')
    region_threshold = float(cfg.getParam('chain', 'mode_outside_RegionSplit'))
    region_field = (cfg.getParam('chain', 'regionField')).lower()
    regions_pos = -2

    formatting_vectors_dir = os.path.join(iota2_dir, "formattingVectors")
    shape_region_dir = os.path.join(iota2_dir, "shapeRegion")
    ratio = float(cfg.getParam('chain', 'ratio'))
    seeds = int(cfg.getParam('chain', 'runs'))
    epsg = int((cfg.getParam('GlobChain', 'proj')).split(":")[-1])
    vectors = fut.FileSearch_AND(formatting_vectors_dir, True, ".shp")

    #get All possible regions by parsing shapeFile's name
    shapes_region = fut.FileSearch_AND(shape_region_dir, True, ".shp")
    regions = list(set([os.path.split(shape)[-1].split("_")[regions_pos] for shape in shapes_region]))

    #compute region's area
    areas, regions_tiles, data_to_rm = get_regions_area(vectors, regions,
                                                        formatting_vectors_dir,
                                                        workingDirectory,
                                                        region_field)

    #get how many sub-regions must be created by too huge regions.
    regions_split = get_splits_regions(areas, region_threshold)

    for region_name, area in areas.items():
        logger.info("region : {} , area : {}".format(region_name, area))

    updated_vectors = split(regions_split, regions_tiles, dataField, region_field)

    #transform sqlites to shape file, according to input data format
    new_regions_shapes = transform_to_shape(updated_vectors, formatting_vectors_dir)
    for data in data_to_rm:
        os.remove(data)

    dataAppVal_dir = os.path.join(iota2_dir, "dataAppVal")
    update_learningValination_sets(new_regions_shapes, dataAppVal_dir, dataField,
                                   region_field, ratio, seeds, epsg, enableCrossValidation)
