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

import os
import logging

import fileUtils as fut

logger = logging.getLogger(__name__)


def GetSamplesSet(iota2_dir_samples):
    """ read the /learningSample directory

    parse the directory /learningSamples and return a list by seed
    in order to feed manageSamples function

    Parameter
    ---------

    iota2_dir_samples : string
        absolute path to the /learningSamples IOTA2's directory

    Example
    -------

    ls /learningSamples
    Samples_region_2_seed0_learn.sqlite
    Samples_region_2_seed1_learn.sqlite
    Samples_region_1_seed0_learn.sqlite
    Samples_region_1_seed1_learn.sqlite

    >>> GetSamplesSet("/learningSamples")
        [[Samples_region_1_seed0_learn.sqlite, Samples_region_2_seed0_learn.sqlite],
         [Samples_region_1_seed1_learn.sqlite, Samples_region_2_seed1_learn.sqlite]]

    Return
    ------
    list
        a list of list where each inner list contains all samples for a given run
    """
    seed_pos = 3
    samples_set = [(os.path.basename(samples).split("_")[seed_pos], samples) for samples in fut.FileSearch_AND(iota2_dir_samples, True, "sqlite")]
    samples_set = [samplesSeed for seed, samplesSeed in fut.sortByFirstElem(samples_set)]
    return samples_set


def getUserSamplesManagement(csv_path):
    """
    """
    import csv

    with open(csv_path, 'rb') as csvfile:
        csv_reader = csv.reader(csvfile)
        extraction_rules = [line for line in csv_reader]
    return extraction_rules


def getSamplesFromModelName(model_name, samplesSet, logger=logger):
    """
    """
    model_pos = 2
    sample = [path for path in samplesSet if os.path.basename(path).split("_")[model_pos] == model_name]

    if len(sample) > 1:
        logger.error("Too many files detected in {} for the model {}".format(os.path.split(samplesSet[0])[0], model_name))
        raise Exception("ERROR in managementSamples.py, too many sample files detected for a given model name")
    elif not sample:
        logger.warning("Model {} not found".format(model_name))
        out_samples = None
    else:
        out_samples = sample[0]
    return out_samples


def countClassInSQLite(source_samples, dataField, class_name, logger=logger):
    """
    """
    import sqlite3
    table_name = "output"
    conn = sqlite3.connect(source_samples)
    cursor = conn.cursor()
    sql = "select * from {} where {}={}".format(table_name, dataField, class_name)
    cursor.execute(sql)
    features_number = cursor.fetchall()
    if not features_number:
        logger.warning("There is no class with the label {} in {}".format(class_name, source_samples))
        features_number = 0
    return len(features_number)


def get_projection(vectorFile, driverName="SQLite"):
    """
    """
    from osgeo import ogr

    driver = ogr.GetDriverByName(driverName)
    vector = driver.Open(vectorFile)
    layer = vector.GetLayer()
    spatialRef = layer.GetSpatialRef()
    ProjectionCode = spatialRef.GetAttrValue("AUTHORITY", 1)
    return ProjectionCode


def copy_samples(source_samples, destination_samples, class_name, dataField, extract_quantity,
                 PRIM_KEY="ogc_fid", source_samples_tableName="output", logger=logger):
    """
    """

    from pyspatialite import dbapi2 as db

    PRIM_KEY_index = None

    proj = get_projection(destination_samples)
    conn = db.connect(destination_samples)
    cursor = conn.cursor()

    cursor.execute("ATTACH '{}' AS db_source".format(source_samples))
    cursor.execute("pragma table_info(output)")
    fields = cursor.fetchall()
    listfields = []

    for index, field in enumerate(fields):
        if field[2] != '' and field[1].lower() != "geometry":
            listfields.append(field[1])
        if field[1] == PRIM_KEY:
            PRIM_KEY_index = index

    fields = ",".join(listfields)
    cursor.execute("SELECT MAX({}) FROM {}".format(PRIM_KEY,
                                                   source_samples_tableName))
    destination_rows = cursor.fetchall()[0][0]
    cursor.execute("CREATE TABLE tmp as select * from db_source.{}".format(source_samples_tableName))

    random_sql = "SELECT {}, ASTEXT(geomfromwkb(geometry, {})) FROM tmp WHERE {}={} ORDER BY RANDOM() LIMIT {}".format(fields,
                                                                                                                       proj,
                                                                                                                       dataField,
                                                                                                                       class_name,
                                                                                                                       extract_quantity)

    cursor.execute(random_sql)
    samples_to_extract = cursor.fetchall()

    for ID_offset, sample in enumerate(samples_to_extract):
        sample = list(sample)
        old_FID = sample[PRIM_KEY_index]
        sample[PRIM_KEY_index] = destination_rows + ID_offset + 1
        val = []
        for elem in sample:
            if isinstance(elem, str) or isinstance(elem, unicode):
                val.append("\"{}\"".format(elem))
            else:
                val.append(str(elem))

        insert = "INSERT INTO {} ({}, GEOMETRY) VALUES ({}, ST_AsBinary(ST_GeomFromText({})))".format(source_samples_tableName,
                                                                                                      fields,
                                                                                                      ','.join(val[:-1]),
                                                                                                      val[-1])

        try:
            logger.debug(insert)
            cursor.execute(insert)
        except:
            logger.error("failed to add the feature {} from {} to {}".format(old_FID,
                                                                             source_samples,
                                                                             destination_samples))
        conn.commit()
    cursor.execute("DROP TABLE tmp")
        
    cursor = conn = None


def samples_management_csv(dataField, csv_path, samplesSet, workingDirectory=None,
                           PRIM_KEY="ogc_fid", source_samples_tableName="output",
                           logger=logger):
    """ use to balance sample between models

    Parameters
    ----------

    dataField : string
        data's field in vectors
    csv_path : string
        absolute path to a csv file which describe samples movements
        column 1 = the model source name
        column 2 = the model destination name
        column 3 = target class label
        column 4 = number of samples to extract (-1 mean extract all)

        example :
        cat MyRepartition.csv
        1,2,11,5
        2,1,46,-1

        5 samples of class 11 will be extracted from model 1 and injected in the model 2
        all samples of class 46 will be extracted from model 2 and injected in the model 1
    samplesSet : list
        Absolute paths to all samples set
    """

    import shutil

    if workingDirectory:
        origin_dir = []
        for ind, sample in enumerate(samplesSet):
            shutil.copy(sample, workingDirectory)
            origin_dir.append(os.path.split(sample)[0])
            samplesSet[ind] = os.path.join(workingDirectory, os.path.split(sample)[-1])

    extraction_rules = getUserSamplesManagement(csv_path)

    for src_model, dst_model, class_name, extract_quantity in extraction_rules:
        source_samples = getSamplesFromModelName(src_model, samplesSet)
        dst_samples = getSamplesFromModelName(dst_model, samplesSet)
        if not source_samples or not dst_samples:
            continue
        if source_samples == dst_samples:
            continue
        if extract_quantity == "-1":
            extract_quantity = countClassInSQLite(source_samples, dataField, class_name)
        if extract_quantity == 0:
            continue

        copy_samples(source_samples, dst_samples, class_name, dataField, extract_quantity,
                     PRIM_KEY, source_samples_tableName)

    if workingDirectory:
        for o_dir, sample_aug in zip(origin_dir, samplesSet):
            os.remove(os.path.join(o_dir, os.path.split(sample_aug)[-1]))
            shutil.copy(sample_aug, o_dir)
