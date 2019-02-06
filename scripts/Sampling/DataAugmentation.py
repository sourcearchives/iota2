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
import shutil

from Common import OtbAppBank
from Common import FileUtils as fut

logger = logging.getLogger(__name__)


def GetDataAugmentationSyntheticParameters(IOTA2_dir):
    """ read the */learningSample* directory

    parse the directory */learningSamples* and return a list of all sqlite files

    Parameters
    ----------

    IOTA2_dir : string
        absolute path to the IOTA2's directory

    Example
    -------

    >>> os.listdir("/learningSamples")
    ["Samples_region_2_seed0_learn.sqlite",
     "Samples_region_2_seed1_learn.sqlite",
     "Samples_region_1_seed0_learn.sqlite",
     "Samples_region_1_seed1_learn.sqlite"]

    >>> GetAugmentationSamplesParameters("/IOTA2")
        [Samples_region_1_seed0_learn.sqlite, Samples_region_2_seed0_learn.sqlite,
         Samples_region_1_seed1_learn.sqlite, Samples_region_2_seed1_learn.sqlite]

    Return
    ------
    list
        a list of sqlite files containing samples
    """
    IOTA2_dir_learningSamples = os.path.join(IOTA2_dir, "learningSamples")
    return fut.FileSearch_AND(IOTA2_dir_learningSamples, True, ".sqlite")


def GetDataAugmentationByCopyParameters(iota2_dir_samples):
    """ read the */learningSample* directory

    parse the IOTA2's directory */learningSamples* and return a list by seed
    in order to feed DataAugmentationByCopy function

    Parameters
    ----------

    iota2_dir_samples : string
        absolute path to the /learningSamples IOTA2's directory

    Example
    -------

    >>> os.listdir("/learningSamples")
    ["Samples_region_2_seed0_learn.sqlite",
     "Samples_region_2_seed1_learn.sqlite",
     "Samples_region_1_seed0_learn.sqlite",
     "Samples_region_1_seed1_learn.sqlite"]

    >>> GetSamplesSet("/learningSamples")
        [[Samples_region_1_seed0_learn.sqlite, Samples_region_2_seed0_learn.sqlite],
         [Samples_region_1_seed1_learn.sqlite, Samples_region_2_seed1_learn.sqlite]]

    Return
    ------
    list
        a list of list where each inner list contains all samples for a given run
    """
    seed_pos = 3
    samples_set = [(os.path.basename(samples).split("_")[seed_pos], samples) for samples in fut.FileSearch_AND(iota2_dir_samples, True, "Samples_region", "sqlite")]
    samples_set = [samplesSeed for seed, samplesSeed in fut.sortByFirstElem(samples_set)]
    return samples_set


def getUserSamplesManagement(csv_path):
    """parse CSV file

    Parameters
    ----------
    csv_path : string
        path to a csv file

    Return
    ------
    list
        rules to fill samples set

    Example
    -------
    >>> cat /MyFile.csv
            1,2,4,2

    Mean:

    +--------+-------------+------------+----------+
    | source | destination | class name | quantity |
    +========+=============+============+==========+
    |   1    |      2      |      4     |     2    |
    +--------+-------------+------------+----------+

    2 samples of class 4 will be added from model 1 to 2
    """
    import csv

    with open(csv_path, 'rb') as csvfile:
        csv_reader = csv.reader(csvfile)
        extraction_rules = [line for line in csv_reader]
    return extraction_rules


def getSamplesFromModelName(model_name, samplesSet, logger=logger):
    """use to get the sample file by the model name
    
    Parameters
    ----------
    model_name : string
        the model's name
    samplesSet: list
        paths to samples
    logger : logging object
        root logger

    Return
    ------
    string
        path to the targeted sample-set.
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


def countClassInSQLite(source_samples, dataField, class_name,
                       table_name="output",logger=logger):
    """usage : In a SQLite file, count the appearance of a specific value

    Parameters
    ----------
    source_samples : string
        Path to a SQLite file
    dataField : string
        Field's name
    class_name : string
        Class name
    table_name : string
        Table's name
    logger : logging object
        root logger

    Return
    ------
    int
        occurrence of the class into the SQLite file 
    """
    import sqlite3
    conn = sqlite3.connect(source_samples)
    cursor = conn.cursor()
    sql = "select * from {} where {}={}".format(table_name, dataField, class_name)
    cursor.execute(sql)
    features_number = cursor.fetchall()
    features_number = len(features_number)
    if not features_number:
        logger.warning("There is no class with the label {} in {}".format(class_name, source_samples))
        features_number = 0
    return features_number


def get_projection(vectorFile, driverName="SQLite"):
    """return the projection of a vector file
    
    Parameters
    ----------
    vectorFile : string
        Path to a vector file
    driverName : string
        Ogr driver's name

    Return
    ------
    int
        EPSG's code
    """
    from osgeo import ogr

    driver = ogr.GetDriverByName(driverName)
    vector = driver.Open(vectorFile)
    layer = vector.GetLayer()
    spatialRef = layer.GetSpatialRef()
    ProjectionCode = spatialRef.GetAttrValue("AUTHORITY", 1)
    return ProjectionCode


def GetRegionFromSampleName(samples):
    """from samples's path file, get the model's name
    """
    region_pos = 2
    return os.path.basename(samples).split("_")[region_pos]


def SamplesAugmentationCounter(class_count, mode, minNumber=None, byClass=None):
    """Compute how many samples must be add into the sample-set according to user's request

    Parameters
    ----------
    class_count : dict
        count by class
    mode : string
        minNumber/balance/byClass
    minNumber : int
        vector should have at least class samples
    byClass : string
        csv path

    Example
    -------
    >>> class_count = {51: 147, 11: 76, 12: 37, 42: 19}
    >>>
    >>> print SamplesAugmentationCounter(class_count, mode="minNumber", minNumber=120)
    >>> {42: 101, 11: 44, 12: 83}
    >>>
    >>> print SamplesAugmentationCounter(class_count, mode="balance")
    >>> {42: 128, 11: 71, 12: 110}
    >>>
    >>> print SamplesAugmentationCounter(class_count, mode="byClass",
    >>>                                  minNumber=None, byClass="/pathTo/MyFile.csv")
    >>> {42: 11, 51: 33, 12: 1}
    
    If 
    
    >>> cat /pathTo/MyFile.csv
        51,180
        11,70
        12,38
        42,30
        
    Return
    ------
    dict
        by class, the number of samples to add in the samples set.
    """
    augmented_class = {}
    if mode.lower() == "minnumber":
        for class_name, count in class_count.items():
            if count < minNumber:
                augmented_class[class_name] = minNumber - count

    elif mode.lower() == "balance":
        max_class_count = class_count[max(class_count, key=lambda key: class_count[key])]
        for class_name, count in class_count.items():
            if count < max_class_count:
                augmented_class[class_name] = max_class_count - count

    elif mode.lower() == "byclass":
        import csv
        with open(byClass, 'rb') as csvfile:
            csv_reader = csv.reader(csvfile)
            for class_name, class_samples in csv_reader:
                class_name = int(class_name)
                class_samples = int(class_samples)
                if class_samples > class_count[class_name]:
                    augmented_class[class_name] = class_samples - class_count[class_name]
    return augmented_class


def DoAugmentation(samples, class_augmentation, strategy, field,
                   excluded_fields=[], Jstdfactor=None, Sneighbors=None,
                   workingDirectory=None, logger=logger):
    """perform data augmentation according to input parameters

    Parameters
    ----------

    samples : string
        path to the set of samples to augment (OGR geometries must be 'POINT')
    class_augmentation : dict
        number of new samples to compute by class
    strategy : string
        which method to use in order to perform data augmentation (replicate/jitter/smote)
    field : string
        data's field
    excluded_fields : list
        do not consider these fields to perform data augmentation
    Jstdfactor : float
        Factor for dividing the standard deviation of each feature
    Sneighbors : int
        Number of nearest neighbors (smote's method)
    workingDirectory : string
        path to a working directory

    Note
    ----
    This function use the OTB's application **SampleAugmentation**,
    more documentation
    `here <http://www.orfeo-toolbox.org/Applications/SampleAugmentation.html>`_
    """
    from Common import OtbAppBank

    samples_dir_o, samples_name = os.path.split(samples)
    samples_dir = samples_dir_o
    if workingDirectory:
        samples_dir = workingDirectory
        shutil.copy(samples, samples_dir)
    samples = os.path.join(samples_dir, samples_name)

    augmented_files = []
    for class_name, class_samples_augmentation in class_augmentation.items():
        logger.info("{} samples of class {} will be generated by data augmentation ({} method) in {}".format(class_samples_augmentation,
                                                                                                             class_name,
                                                                                                             strategy, samples))
        sample_name_augmented = "_".join([os.path.splitext(samples_name)[0],
                                          "aug_class_{}.sqlite".format(class_name)])
        output_sample_augmented = os.path.join(samples_dir, sample_name_augmented)
        parameters = {"in": samples,
                      "field": field,
                      "out": output_sample_augmented,
                      "label": class_name,
                      "strategy": strategy,
                      "samples": class_samples_augmentation
                      }
        if excluded_fields:
            parameters["exclude"] = excluded_fields
        if strategy.lower() == "jitter":
            parameters["strategy.jitter.stdfactor"] = Jstdfactor
        elif strategy.lower() == "smote":
            parameters["strategy.smote.neighbors"] = Sneighbors

        augmentation_application = OtbAppBank.CreateSampleAugmentationApplication(parameters)
        augmentation_application.ExecuteAndWriteOutput()
        logger.debug("{} samples of class {} were added in {}".format(class_samples_augmentation,
                                                                      class_name, samples))
        augmented_files.append(output_sample_augmented)

    outputVector = os.path.join(samples_dir, "_".join([os.path.splitext(samples_name)[0],
                                                       "augmented.sqlite"]))

    fut.mergeSQLite("_".join([os.path.splitext(samples_name)[0], "augmented"]),
                    samples_dir, [samples] + augmented_files)
    logger.info("Every data augmentation done in {}".format(samples))
    shutil.move(outputVector, os.path.join(samples_dir_o, samples_name))

    #clean-up
    for augmented_file in augmented_files:
        os.remove(augmented_file)


def GetFieldsType(vectorFile):
    """Get field's type

    Parameters
    ----------
    vectorFile : string
        path to a shape file
    Return
    ------
    dict
        dictionary with field's name as key and type as value

    Example
    -------
    >>> print GetFieldsType("/path/to/MyVector.shp")
        {'CODE': 'integer64', 'id': 'integer64', 'Area': 'integer64'}
    """
    from osgeo import ogr
    dataSource = ogr.Open(vectorFile)
    daLayer = dataSource.GetLayer(0)
    layerDefinition = daLayer.GetLayerDefn()
    field_dict = {}
    for i in range(layerDefinition.GetFieldCount()):
        fieldName =  layerDefinition.GetFieldDefn(i).GetName()
        fieldTypeCode = layerDefinition.GetFieldDefn(i).GetType()
        fieldType = layerDefinition.GetFieldDefn(i).GetFieldTypeName(fieldTypeCode)
        field_dict[fieldName] = fieldType.lower()
    return field_dict


def DataAugmentationSynthetic(samples, groundTruth, dataField, strategies, workingDirectory=None):
    """Compute how many samples should be add in the sample set and launch data augmentation method

    Parameters
    ----------
    samples : string
        path to a vector file to augment samples
    groundTruth : string
        path to the original ground truth vector file, in order to list interger / float fields
    dataField : string
        data field's name in samples
    strategies : dict
        dictionary
    workingDirectory : string
        path to a working directory
    """

    if GetRegionFromSampleName(samples) in strategies["target_models"] or "all" in strategies["target_models"]:
        from collections import Counter
        class_count = Counter(fut.getFieldElement(samples, driverName="SQLite", field=dataField,
                                                  mode="all", elemType="int"))

        class_augmentation = SamplesAugmentationCounter(class_count, mode=strategies["samples.strategy"],
                                                        minNumber=strategies.get("samples.strategy.minNumber", None),
                                                        byClass=strategies.get("samples.strategy.byClass", None))

        fields_types = GetFieldsType(groundTruth)

        excluded_fields_origin = [field_name.lower() for field_name, field_type in fields_types.items()
                                                     if "int" in field_type or "flaot" in field_type]
        samples_fields = fut.getAllFieldsInShape(samples, driver='SQLite')
        excluded_fields = list(set(excluded_fields_origin).intersection(samples_fields))
        excluded_fields.append("originfid")

        DoAugmentation(samples, class_augmentation, strategy=strategies["strategy"],
                       field=dataField, excluded_fields=excluded_fields,
                       Jstdfactor=strategies.get("strategy.jitter.stdfactor", None),
                       Sneighbors=strategies.get("strategy.smote.neighbors", None),
                       workingDirectory=workingDirectory)


def DoCopy(source_samples, destination_samples, class_name, dataField, extract_quantity,
           PRIM_KEY="ogc_fid", source_samples_tableName="output", logger=logger):
    """copy samples to one subset to an other one using a SQLite query.

    Parameters
    ----------
    source_samples : string
        path to the sample-set to extract features
    destination_samples : string
        path to the sample-set to fill-up features
    class_name : string
        class name
    dataField : string
        data's field
    extract_quantity : int
        number of samples to extract
    PRIM_KEY : string
        OGR primary key
    source_samples_tableName : string
        input vector file table's name
    logger : logging object
        root logger
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


def DataAugmentationByCopy(dataField, csv_path, samplesSet, workingDirectory=None,
                           PRIM_KEY="ogc_fid", source_samples_tableName="output",
                           logger=logger):
    """use to copy samples between models

    Parameters
    ----------

    dataField : string
        Data's field in vectors
    csv_path : string
        Absolute path to a csv file which describe samples movements
        check :py:meth:`getUserSamplesManagement` function to know about
        format
    samplesSet : list
        Absolute paths to all samples set
    workingDirectory : string
        Path to a working directory
    PRIM_KEY : string
        OGR primary key
    source_samples_tableName : string
        input vector file table's name
    logger : logging object
        root logger
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

        DoCopy(source_samples, dst_samples, class_name, dataField, extract_quantity,
               PRIM_KEY, source_samples_tableName)

    if workingDirectory:
        for o_dir, sample_aug in zip(origin_dir, samplesSet):
            os.remove(os.path.join(o_dir, os.path.split(sample_aug)[-1]))
            shutil.copy(sample_aug, o_dir)
