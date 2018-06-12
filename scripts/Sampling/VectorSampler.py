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
import time
import ast
import sys
import os
import random
import shutil
from Sensors import Sensors
import osr
import sqlite3 as lite
from osgeo import ogr
from osgeo import gdal
import otbApplication as otb
import logging
import time

from Common import FileUtils as fu
from Common.Utils import run
from Sampling import GenAnnualSamples as genAS
from Common import ServiceConfigFile as SCF
from Sampling.VectorFormatting import split_vector_by_region

logger = logging.getLogger(__name__)


#in order to avoid issue 'No handlers could be found for logger...'
logger.addHandler(logging.NullHandler())
    
def verifPolyStats(inXML):
    """
    due to OTB error, use this parser to check '0 values' in class sampling and remove them
    IN : xml polygons statistics
    OUT : same xml without 0 values
    """
    flag = False
    buff = ""
    with open(inXML, "r") as xml:
        for inLine in xml:
            buff += inLine
            if 'name="samplesPerClass"' in inLine.rstrip('\n\r'):
                for inLine2 in xml:
                    if 'value="0" />' in inLine2:
                        flag = True
                        continue
                    else:
                        buff += inLine2
                    if 'name="samplesPerVector"' in inLine2:
                        break
    if flag:
        os.remove(inXML)
        output = open(inXML, "w")
        output.write(buff)
        output.close()
    return flag


def getPointsCoordInShape(inShape, gdalDriver):
    """

    IN:
    inShape [string] : path to the vector shape containing points
    gdalDriver [string] : gdalDriver of inShape

    OUT:
    allCoord [list of tuple] : coord X and Y of points
    """
    driver = ogr.GetDriverByName(gdalDriver)
    dataSource = driver.Open(inShape, 0)
    layer = dataSource.GetLayer()

    allCoord = []
    for feature in layer:
        geom = feature.GetGeometryRef()
        allCoord.append((geom.GetX(), geom.GetY()))
    return allCoord


def filterShpByClass(datafield, shapeFiltered, keepClass, shape):
    """
    Filter a shape by class allow in keepClass
    IN :
    shape [string] : path to input vector shape
    datafield [string] : data's field'
    keepClass [list of string] : class to keep
    shapeFiltered [string] : output path to filtered shape
    """
    if not keepClass:
        return False
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(shape, 0)
    layer = dataSource.GetLayer()

    AllFields = []
    layerDefinition = layer.GetLayerDefn()

    for i in range(layerDefinition.GetFieldCount()):
        currentField = layerDefinition.GetFieldDefn(i).GetName()
        AllFields.append(currentField)

    exp = " OR ".join(datafield + " = '" + str(currentClass) + "'" for currentClass in keepClass)
    layer.SetAttributeFilter(exp)
    if layer.GetFeatureCount() == 0:
        return False
    fu.CreateNewLayer(layer, shapeFiltered, AllFields)
    return True


def prepareSelection(sample_sel_directory, tile_name, workingDirectory=None, logger=logger):
    """
    usage : merge all sample selection vectors for the designated tile
    """
    import DeleteDuplicateGeometriesSqlite
    
    wd = sample_sel_directory
    if workingDirectory:
        wd = workingDirectory

    vectors = fu.FileSearch_AND(sample_sel_directory, True, tile_name, ".sqlite")
    merge_selection_name = "{}_selection_merge".format(tile_name)

    if os.path.exists(os.path.join(sample_sel_directory, merge_selection_name + ".sqlite")):
        os.remove(os.path.join(sample_sel_directory, merge_selection_name + ".sqlite"))

    if os.path.exists(os.path.join(wd, merge_selection_name + ".sqlite")):
        os.remove(os.path.join(wd, merge_selection_name + ".sqlite"))

    fu.mergeVectors(merge_selection_name, wd, vectors, ext="sqlite", out_Tbl_name="output")

    return os.path.join(wd, merge_selection_name + ".sqlite")


def gapFillingToSample(trainShape, workingDirectory, samples,
                       dataField, cfg, wMode=False,
                       onlyMaskComm=False,
                       onlySensorsMasks=False):
    """
    usage : compute from a stack of data -> gapFilling -> features computation -> sampleExtractions
    thanks to OTB's applications'

    IN:
        trainShape [string] : path to a vector shape containing points
        workingDirectory [string] : working directory path
        samples [string] : output path
        dataField [string] : data's field in trainShape
        featuresPath [string] : path to all stack (/featuresPath/tile/tmp/*.tif)
        tile [string] : actual tile to compute. (ex : T31TCJ)
        cfg [ConfigObject/string] : config Obj OR path to configuation file
        onlyMaskComm [bool] :  flag to stop the script after common Mask computation
        onlySensorsMasks [bool] : compute only masks

    OUT:
        sampleExtr [SampleExtraction OTB's object]:
    """
    #const
    seed_position = -1

    from Common import GenerateFeatures as genFeatures

    if not isinstance(cfg, SCF.serviceConfigFile) and isinstance(cfg, str):
        cfg = SCF.serviceConfigFile(cfg)

    tile = trainShape.split("/")[-1].split(".")[0].split("_")[0]

    workingDirectoryFeatures = os.path.join(workingDirectory, tile)
    cMaskDirectory = os.path.join(cfg.getParam('chain', 'featuresPath'), tile, "tmp")
    
    iota2_directory = cfg.getParam('chain', 'outputPath')
    sample_sel_directory = os.path.join(iota2_directory, "samplesSelection")
    
    if "S1" in fu.sensorUserList(cfg):
        cMaskDirectory = cfg.getParam('chain', 'featuresPath') + "/" + tile
    if not os.path.exists(workingDirectoryFeatures):
        try:
            os.mkdir(workingDirectoryFeatures)
        except OSError:
            logger.warning(workingDirectoryFeatures + "allready exists")
    try: 
        useGapFilling = cfg.getParam('GlobChain', 'useGapFilling')
    except:
        useGapFilling = True

    (AllFeatures,
     feat_labels,
     dep_features) = genFeatures.generateFeatures(workingDirectoryFeatures, tile,
                                                  cfg, useGapFilling=useGapFilling,
                                                  enable_Copy=False)

    if onlySensorsMasks:
        #return AllRefl,AllMask,datesInterp,realDates
        return dep_features[1], dep_features[2], dep_features[3], dep_features[4]

    AllFeatures.Execute()

    try:
        ref = fu.FileSearch_AND(cMaskDirectory, True,
                                fu.getCommonMaskName(cfg) + ".tif")[0]
    except:
        raise Exception("can't find Mask " + fu.getCommonMaskName(cfg) + ".tif \
                        in " + cMaskDirectory)

    if onlyMaskComm:
        return ref

    sampleExtr = otb.Registry.CreateApplication("SampleExtraction")
    sampleExtr.SetParameterString("ram", "512")
    sampleExtr.SetParameterString("vec", trainShape)
    sampleExtr.SetParameterInputImage("in", AllFeatures.GetParameterOutputImage("out"))
    sampleExtr.SetParameterString("out", samples)
    sampleExtr.SetParameterString("outfield", "list")
    sampleExtr.SetParameterStringList("outfield.list.names", feat_labels)
    sampleExtr.UpdateParameters()
    sampleExtr.SetParameterStringList("field", [dataField.lower()])

    All_dep = [AllFeatures, dep_features]

    return sampleExtr, All_dep


def generateSamples_simple(folderSample, workingDirectory, trainShape, pathWd,
                           featuresPath, cfg, dataField,
                           wMode=False, folderFeatures=None, testMode=False, sampleSel=None,
                           logger=logger):
    """
    usage : from a strack of data generate samples containing points with features

    IN:
    folderSample [string] : output folder
    workingDirectory [string] : computation folder
    trainShape [string] : vector shape (polygons) to sample
    pathWd [string] : working Directory, if different from None
                      enable HPC mode (copy at ending)
    featuresPath [string] : path to all stack
    cfg [string] : configuration file class
    dataField [string] : data's field into vector shape
    testMode [bool] : enable testMode -> iota2tests.py
    testFeatures [string] : path to features allready compute (refl + NDVI ...)
    testFeaturePath [string] : path to the stack of data, without features

    OUT:
    samples [string] : vector shape containing points
    """

    tile = trainShape.split("/")[-1].split(".")[0].split("_")[0]

    dataField = (cfg.getParam('chain', 'dataField')).lower()
    regionField = (cfg.getParam('chain', 'regionField')).lower()
    outputPath = cfg.getParam('chain', 'outputPath')
    userFeatPath = cfg.getParam('chain', 'userFeatPath')
    outFeatures = cfg.getParam('GlobChain', 'features')
    runs = cfg.getParam('chain', 'runs')
    sample_sel_directory = os.path.join(outputPath, "samplesSelection")

    samples = workingDirectory + "/" + trainShape.split("/")[-1].replace(".shp", "_Samples.sqlite")

    if sampleSel:
        sampleSelection = sampleSel
    else:
        sampleSelection = prepareSelection(sample_sel_directory, tile, workingDirectory=None)

    sampleExtr, dep_gapSample = gapFillingToSample(sampleSelection, workingDirectory,
                                                   samples, dataField, cfg, wMode)

    if not os.path.exists(folderSample + "/" + trainShape.split("/")[-1].replace(".shp", "_Samples.sqlite")):
        logger.info("--------> Start Sample Extraction <--------")
        sampleExtr.ExecuteAndWriteOutput()
        logger.info("--------> END Sample Extraction <--------")
        proj = cfg.getParam('GlobChain', 'proj')
        split_vec_directory = os.path.join(outputPath, "learningSamples")
        if workingDirectory:
            split_vec_directory = workingDirectory

        #split vectors by there regions
        split_vectors = split_vector_by_region(in_vect=sampleExtr.GetParameterValue("out"),
                                               output_dir=split_vec_directory,
                                               region_field=regionField, runs=int(runs),
                                               driver="SQLite", proj_in=proj, proj_out=proj)
        os.remove(sampleExtr.GetParameterValue("out"))

    if not sampleSel:
        os.remove(sampleSelection)

    if pathWd:
        for sample in split_vectors:
            shutil.copy(sample, folderSample)
    if wMode:
        if not os.path.exists(folderFeatures + "/" + tile):
            try:
                os.mkdir(folderFeatures + "/" + tile)
            except OSError:
                logger.warning(workingDirectoryFeatures + "allready exists")
            try:
                os.mkdir(folderFeatures + "/" + tile + "/tmp")
            except OSError:
                logger.warning(workingDirectoryFeatures + "allready exists")

        fu.updateDirectory(workingDirectory + "/" + tile + "/tmp",
                           folderFeatures + "/" + tile + "/tmp")


def extract_class(vec_in, vec_out, target_class, dataField):
    """
    """
    where = " OR ".join(["{}={}".format(dataField.lower(), klass) for klass in target_class])
    cmd = "ogr2ogr -f 'SQLite' -nln output -where '{}' {} {}".format(where, vec_out, vec_in)
    run(cmd)

    return len(fu.getFieldElement(vec_out, driverName="SQLite", field=dataField.lower(),
                                  mode="all", elemType="int"))

def generateSamples_cropMix(folderSample, workingDirectory, trainShape, pathWd,
                            nonAnnualData, annualData,
                            annualCrop, AllClass, dataField, cfg, folderFeature,
                            folderFeaturesAnnual, Aconfig, wMode=False, testMode=False,
                            sampleSel=None, logger=logger):
    """
    usage : from stracks A and B, generate samples containing points where annual crop are compute with A
    and non annual crop with B.

    IN:
    folderSample [string] : output folder
    workingDirectory [string] : computation folder
    trainShape [string] : vector shape (polygons) to sample
    pathWd [string] : if different from None, enable HPC mode (copy at ending)
    featuresPath [string] : path to all stack
    prevFeatures [string] : path to the configuration file which compute features A
    annualCrop [list of string/int] : list containing annual crops ex : [11,12]
    AllClass [list of string/int] : list containing permanant classes in vector shape ex : [51..]
    cfg [string] : configuration file class
    dataField [string] : data's field into vector shape
    testMode [bool] : enable testMode -> iota2tests.py
    testFeatures [string] : path to features allready compute (refl + NDVI ...)
    testFeaturePath [string] : path to the stack of data, without features dedicated to non
                               annual crops
    testAnnualFeaturePath [string] : path to the stack of data, without features dedicated to
                                     annual crops

    OUT:
    samples [string] : vector shape containing points
    """

    if os.path.exists(folderSample + "/" + trainShape.split("/")[-1].replace(".shp", "_Samples.sqlite")):
        return None

    outFeatures = cfg.getParam('GlobChain', 'features')
    outputPath = cfg.getParam('chain', 'outputPath')
    regionField = (cfg.getParam('chain', 'regionField')).lower()
    dataField = dataField.lower()
    runs = cfg.getParam('chain', 'runs')

    featuresFind_NA = ""
    featuresFind_A = ""
    userFeatPath = cfg.getParam('chain', 'userFeatPath')
    sample_sel_directory = os.path.join(outputPath, "samplesSelection")
    currentTile = (os.path.splitext(os.path.basename(trainShape))[0])

    #filter vector file
    wd = sample_sel_directory
    if workingDirectory:
        wd = workingDirectory

    if sampleSel:
        sampleSelection = sampleSel
    else:
        sampleSelection = prepareSelection(sample_sel_directory, currentTile, workingDirectory=None)

    nonAnnual_vector_sel = os.path.join(wd, "{}_nonAnnual_selection.sqlite".format(currentTile))
    annual_vector_sel = os.path.join(wd, "{}_annual_selection.sqlite".format(currentTile))
    nb_feat_Nannu = extract_class(sampleSelection, nonAnnual_vector_sel, AllClass, dataField)
    nb_feat_annu = extract_class(sampleSelection, annual_vector_sel, annualCrop, dataField)

    SampleExtr_NA = os.path.join(wd, "{}_nonAnnual_extraction.sqlite".format(currentTile))
    SampleExtr_A = os.path.join(wd, "{}_annual_extraction.sqlite".format(currentTile))

    start_extraction = time.time()
    if nb_feat_Nannu > 0:
        Na_workingDirectory = workingDirectory + "/" + currentTile + "_nonAnnual"
        if not os.path.exists(Na_workingDirectory):
            try:
                os.mkdir(Na_workingDirectory)
            except OSError:
                logger.warning(Na_workingDirectory + "allready exists")
                
        sampleExtr_NA, dep_gapSampleA = gapFillingToSample(nonAnnual_vector_sel, 
                                                           Na_workingDirectory, SampleExtr_NA,
                                                           dataField, 
                                                           cfg, wMode)
        sampleExtr_NA.ExecuteAndWriteOutput()

    if nb_feat_annu > 0:
        A_workingDirectory = workingDirectory + "/" + currentTile + "_annual"
        if not os.path.exists(A_workingDirectory):
            try:
                os.mkdir(A_workingDirectory)
            except OSError:
                logger.warning(A_workingDirectory + "allready exists")
        SCF.clearConfig()
        Aconfig = SCF.serviceConfigFile(Aconfig)

        sampleExtr_A, dep_gapSampleNA = gapFillingToSample(annual_vector_sel,
                                                           A_workingDirectory, SampleExtr_A,
                                                           dataField, Aconfig, wMode)
        sampleExtr_A.ExecuteAndWriteOutput()
    if not sampleSel:
        os.remove(sampleSelection)
    end_extraction = time.time()
    logger.debug("Samples Extraction time : " + str(end_extraction - start_extraction) + " seconds")
    #rename annual fields in order to fit non annual dates
    if os.path.exists(SampleExtr_A):
        annual_fields = fu.getAllFieldsInShape(SampleExtr_A, "SQLite")
    if os.path.exists(SampleExtr_NA):        
        non_annual_fields = fu.getAllFieldsInShape(SampleExtr_NA, "SQLite")
    if os.path.exists(SampleExtr_NA) and os.path.exists(SampleExtr_A):
        if len(annual_fields) != len(non_annual_fields):
            raise Exception("annual data's fields and non annual data's fields can"
                            "not fitted")

    if os.path.exists(SampleExtr_A):
        driver = ogr.GetDriverByName("SQLite")
        dataSource = driver.Open(SampleExtr_A, 1)
        if dataSource is None:
            #TODO: define vector (currently vector)
            raise Exception("Could not open " + vector)
        layer = dataSource.GetLayer()

        # Connection to shapefile sqlite database
        conn = lite.connect(SampleExtr_A)

        # Create cursor
        cursor = conn.cursor()

        cursor.execute("PRAGMA writable_schema=1")

        # TODO à modifier pour généraliser
        if not os.path.exists(SampleExtr_NA):
            non_annual_fields = [x.replace('2016', '2017') for x in annual_fields]
            
        for field_non_a, field_a in zip(non_annual_fields, annual_fields):
            cursor.execute("UPDATE sqlite_master SET SQL=REPLACE(SQL, '" + field_a + "', '" + field_non_a + "') WHERE name='" + layer.GetName() + "'")
        cursor.execute("PRAGMA writable_schema=0")
        conn.commit()
        conn.close()

    #Merge samples
    MergeName = trainShape.split("/")[-1].replace(".shp", "_Samples")

    if (nb_feat_Nannu > 0) and (nb_feat_annu > 0):
        fu.mergeSQLite(MergeName, workingDirectory, [SampleExtr_NA, SampleExtr_A])
    elif (nb_feat_Nannu > 0) and not (nb_feat_annu > 0):
        shutil.copyfile(SampleExtr_NA, workingDirectory + "/" + MergeName + ".sqlite")
    elif not (nb_feat_Nannu > 0) and (nb_feat_annu > 0):
        shutil.copyfile(SampleExtr_A, workingDirectory + "/" + MergeName + ".sqlite")

    samples = workingDirectory + "/" + trainShape.split("/")[-1].replace(".shp", "_Samples.sqlite")


    if nb_feat_Nannu > 0:
        os.remove(SampleExtr_NA)
        os.remove(nonAnnual_vector_sel)

    if nb_feat_annu > 0:
        os.remove(SampleExtr_A)
        os.remove(annual_vector_sel)

    if wMode:
        targetDirectory = folderFeature + "/" + currentTile
        if not os.path.exists(targetDirectory):
            try:
                os.mkdir(targetDirectory)
            except OSError:
                logger.warning(targetDirectory + "allready exists")
            try:
                os.mkdir(targetDirectory + "/tmp")
            except OSError:
                logger.warning(targetDirectory + "/tmp allready exists")

        fu.updateDirectory(workingDirectory + "/" + currentTile + "_nonAnnual/" + currentTile + "/tmp",
                           targetDirectory + "/tmp")

        targetDirectory = folderFeaturesAnnual + "/" + currentTile
        if not os.path.exists(targetDirectory):
            try:
                os.mkdir(targetDirectory)
            except OSError:
                logger.warning(targetDirectory + "allready exists")
            try:
                os.mkdir(targetDirectory + "/tmp")
            except OSError:
                logger.warning(targetDirectory + "/tmp allready exists")
        fu.updateDirectory(workingDirectory + "/" + currentTile + "_annual/" + currentTile + "/tmp",
                           targetDirectory + "/tmp")

    #split vectors by there regions
    proj = cfg.getParam('GlobChain', 'proj')
    split_vec_directory = os.path.join(outputPath, "learningSamples")
    if workingDirectory:
        split_vec_directory = workingDirectory

    split_vectors = split_vector_by_region(in_vect=samples,
                                           output_dir=split_vec_directory,
                                           region_field=regionField, runs=int(runs),
                                           driver="SQLite", proj_in=proj, proj_out=proj)

    if testMode:
        return split_vectors
    if pathWd and os.path.exists(samples):
        for sample in split_vectors:
            shutil.copy(sample, folderSample)
    os.remove(samples)


def extractROI(raster, currentTile, cfg, pathWd, name, ref,
               testMode=None, testOutput=None):
    """
    usage : extract ROI in raster

    IN:
    raster [string] : path to the input raster
    currentTile [string] : current tile to compute
    cfg [string] : configuration file class
    pathWd [string] : path to the working directory
    name [string] : output name
    ref [strin] : raster reference use to get it's extent

    OUT:
    raterROI [string] : path to the extracted raster.
    """

    outputPath = cfg.getParam('chain', 'outputPath')
    featuresPath = cfg.getParam('chain', 'featuresPath')

    workingDirectory = outputPath + "/learningSamples/"
    if pathWd:
        workingDirectory = pathWd
    if testMode:
        workingDirectory = testOutput
    currentTile_raster = ref
    minX, maxX, minY, maxY = fu.getRasterExtent(currentTile_raster)
    rasterROI = workingDirectory + "/" + currentTile + "_" + name + ".tif"
    cmd = "gdalwarp -of GTiff -te " + str(minX) + " " + str(minY) + " " +\
          str(maxX) + " " + str(maxY) + " -ot Byte " + raster + " " + rasterROI
    run(cmd)
    return rasterROI


def getRegionModelInTile(currentTile, currentRegion, pathWd, cfg, refImg,
                         testMode, testPath, testOutputFolder):
    """
    usage : rasterize region shape.
    IN:
        currentTile [string] : tile to compute
        currentRegion [string] : current region in tile
        pathWd [string] : working directory
        cfg [string] : configuration file class
        refImg [string] : reference image
        testMode [bool] : flag to enable test mode
        testPath [string] : path to the vector shape
        testOutputFolder [string] : path to the output folder

    OUT:
        rasterMask [string] : path to the output raster
    """

    outputPath = cfg.getParam('chain', 'outputPath')
    fieldRegion = cfg.getParam('chain', 'regionField')

    workingDirectory = outputPath + "/learningSamples/"
    if pathWd:
        workingDirectory = pathWd
    nameOut = "Mask_region_" + currentRegion + "_" + currentTile + ".tif"

    if testMode:
        maskSHP = testPath
        workingDirectory = testOutputFolder
    else:
        maskSHP = fu.FileSearch_AND(outputPath + "/shapeRegion/", True,
                                    currentTile, "region_" + currentRegion.split("f")[0], ".shp")[0]

    rasterMask = workingDirectory + "/" + nameOut
    cmdRaster = "otbcli_Rasterization -in " + maskSHP + " -mode attribute -mode.attribute.field " +\
                fieldRegion + " -im " + refImg + " -out " + rasterMask
    run(cmdRaster)
    return rasterMask


def get_repartition(vec, labels, dataField, regionField, regions, runs):
    """
    usage : count label apparition in vector
    IN
    vec [string] path to a sqlite file
    labels [list of string]
    dataField [string] data field name
    """
    
    conn = lite.connect(vec)
    cursor = conn.cursor()

    repartition = {}
    """
    for label in labels:
        sql_clause = "SELECT * FROM output WHERE {}={}".format(dataField, label)
        cursor.execute(sql_clause)
        results = cursor.fetchall()
        repartition[label] = len(results)
    """
    for label in labels:
        repartition[label] = {}
        for region in regions:
            repartition[label][region] = {}
            for run in range(runs):
                sql_clause = "SELECT * FROM output WHERE {}={} AND {}='{}' AND {}='{}'".format(dataField,
                                                                                               label,
                                                                                               regionField,
                                                                                               region,
                                                                                               "seed_" + str(run),
                                                                                               "learn")
                cursor.execute(sql_clause)
                results = cursor.fetchall()
                repartition[label][region][run] = len(results)

    return repartition


def get_number_annual_sample(annu_repartition):
    """
    usage : use to flatten annu_repartition to compute number of annual samples
    """
    nb_feat_annu = 0
    for kc, vc in annu_repartition.items():
        for kr, vr in vc.items():
            for ks, vs in vr.items():
                nb_feat_annu += vs

    return nb_feat_annu


def generateSamples_classifMix(folderSample, workingDirectory, trainShape,
                               pathWd, annualCrop, AllClass,
                               dataField, cfg, previousClassifPath,
                               folderFeatures=None,
                               wMode=False,
                               testMode=None,
                               testShapeRegion=None,
                               sampleSel=None):
    """
    usage : from one classification, chose randomly annual sample merge with non annual sample and extract features.
    IN:
        folderSample [string] : output folder
        workingDirectory [string] : computation folder
        trainShape [string] : vector shape (polygons) to sample
        pathWd [string] : if different from None, enable HPC mode (copy at ending)
        featuresPath [string] : path to all stack
        annualCrop [list of string/int] : list containing annual crops ex : [11,12]
        AllClass [list of string/int] : list containing all classes in vector shape ex : [11,12,51..]
        cfg [string] : configuration file class
        previousClassifPath [string] : path to the iota2 output directory which generate previous classification
        dataField [string] : data's field into vector shape
        testMode [bool] : enable testMode -> iota2tests.py
        testPrevConfig [string] : path to the configuration file which generate previous classification
        testShapeRegion [string] : path to the shapefile representing region in the tile.
        testFeaturePath [string] : path to the stack of data

    OUT:
        samples [string] : vector shape containing points
    """

    if os.path.exists(folderSample + "/" + trainShape.split("/")[-1].replace(".shp", "_Samples.sqlite")):
        return None

    targetResolution = cfg.getParam('chain', 'spatialResolution')
    validityThreshold = cfg.getParam('argTrain', 'validityThreshold')
    projEPSG = cfg.getParam('GlobChain', 'proj')
    projOut = int(projEPSG.split(":")[-1])
    userFeatPath = cfg.getParam('chain', 'userFeatPath')
    features_path = cfg.getParam('chain', 'featuresPath')
    outFeatures = cfg.getParam('GlobChain', 'features')
    runs = cfg.getParam('chain', 'runs')
    regionField = (cfg.getParam('chain', 'regionField')).lower()
    outputPath = cfg.getParam('chain', 'outputPath')
    sample_sel_directory = os.path.join(outputPath, "samplesSelection")
    
    wd = sample_sel_directory
    if workingDirectory:
        wd = workingDirectory

    dataField = dataField.lower()

    if testMode:
        #TODO: define testPrevClassif (currently undefined)
        previousClassifPath = testPrevClassif

    currentTile = (os.path.splitext(os.path.basename(trainShape))[0])

    if sampleSel:
        sampleSelection = sampleSel
    else:
        sampleSelection = prepareSelection(sample_sel_directory, currentTile)

    nonAnnualShape = os.path.join(wd, "{}_nonAnnual_selection.sqlite".format(currentTile))
    AnnualShape = os.path.join(wd, "{}_annual_selection.sqlite".format(currentTile))
    nb_feat_Nannu = extract_class(sampleSelection, nonAnnualShape, AllClass, dataField)

    regions = fu.getFieldElement(trainShape, driverName="ESRI Shapefile", field=regionField, mode="unique",
                                 elemType="str")
    print sampleSelection
    print trainShape
    #avoir la répartition des classes anuelles par seed et par region -> pouvoir faire annu_repartition[11][R][S]
    annu_repartition = get_repartition(sampleSelection, annualCrop, dataField, regionField, regions, runs)
    
    nb_feat_annu = get_number_annual_sample(annu_repartition)

    #raster ref (in order to extract ROIs)
    ref = fu.FileSearch_AND(os.path.join(features_path, currentTile), True, "MaskCommunSL.tif")[0]

    if nb_feat_Nannu > 0:
        allCoord = getPointsCoordInShape(nonAnnualShape, "SQLite")
    else:
        allCoord = [0]

    classificationRaster = extractROI(previousClassifPath + "/final/Classif_Seed_0.tif",
                                      currentTile, cfg, pathWd, "Classif_"+str(currentTile),
                                      ref, testMode, testOutput=folderSample)
    validityRaster = extractROI(previousClassifPath + "/final/PixelsValidity.tif",
                                currentTile, cfg, pathWd, "Cloud"+str(currentTile),
                                ref, testMode, testOutput=folderSample)



    #build regions mask into the tile
    masks = [getRegionModelInTile(currentTile, currentRegion, pathWd, cfg,
                                  classificationRaster, testMode, testShapeRegion,
                                  testOutputFolder=folderSample) for currentRegion in regions]

    if nb_feat_annu > 0:
        annualPoints = genAS.genAnnualShapePoints(allCoord, "SQLite", workingDirectory,
                                                  targetResolution, annualCrop, dataField,
                                                  currentTile, validityThreshold, validityRaster,
                                                  classificationRaster, masks, trainShape,
                                                  AnnualShape, projOut, regionField, runs, annu_repartition)

    MergeName = trainShape.split("/")[-1].replace(".shp", "_selectionMerge")
    sampleSelection = workingDirectory + "/" + MergeName + ".sqlite"

    if (nb_feat_Nannu > 0) and (nb_feat_annu > 0 and annualPoints):
        fu.mergeSQLite(MergeName, workingDirectory, [nonAnnualShape, AnnualShape])
        
    elif (nb_feat_Nannu > 0) and not (nb_feat_annu > 0 and annualPoints):
        #TODO: define SampleSel_NA (currently undefined)
        shutil.copy(SampleSel_NA, sampleSelection)
    elif not (nb_feat_Nannu > 0) and (nb_feat_annu > 0 and annualPoints):
        #TODO: define annualShape (currently undefined)        
        shutil.copy(annualShape, sampleSelection)
    samples = workingDirectory + "/" + trainShape.split("/")[-1].replace(".shp", "_Samples.sqlite")

    sampleExtr, dep_tmp = gapFillingToSample(sampleSelection,
                                             workingDirectory, samples,
                                             dataField, cfg, wMode)
                                            

    sampleExtr.ExecuteAndWriteOutput()

    split_vectors = split_vector_by_region(in_vect=samples,
                                           output_dir=workingDirectory,
                                           region_field=regionField, runs=int(runs),
                                           driver="SQLite", proj_in="EPSG:"+str(projOut), proj_out="EPSG:"+str(projOut))
    if testMode:
        return split_vectors
    if pathWd and os.path.exists(samples):
        for sample in split_vectors:
            shutil.copy(sample, folderSample)

    if os.path.exists(nonAnnualShape):
        os.remove(nonAnnualShape)
    if os.path.exists(AnnualShape):
        os.remove(AnnualShape)

    if not sampleSel:
        os.remove(sampleSelection)

    if wMode:
        targetDirectory = folderFeatures + "/" + currentTile
        if not os.path.exists(targetDirectory):
            try:
                os.mkdir(targetDirectory)
            except OSError:
                logger.warning(targetDirectory + "allready exists")
            try:
                os.mkdir(targetDirectory + "/tmp")
            except OSError:
                logger.warning(targetDirectory + "/tmp allready exists")
        fu.updateDirectory(workingDirectory + "/" + currentTile + "/tmp", targetDirectory + "/tmp")

    os.remove(samples)
    os.remove(classificationRaster)
    os.remove(validityRaster)
    for mask in masks:
        os.remove(mask)


def cleanContentRepo(outputPath):
    """
    remove all content in TestPath+"learningSamples"
    """
    LearningContent = os.listdir(outputPath+"/learningSamples")
    for c_content in LearningContent:
        c_path = outputPath+"/learningSamples/"+c_content
        if os.path.isdir(c_path):
            shutil.rmtree(c_path)
        else:
            os.remove(c_path)

def generateSamples(trainShape, pathWd, cfg, wMode=False, folderFeatures=None,
                    folderAnnualFeatures=None, testMode=False,
                    testShapeRegion=None, sampleSelection=None,
                    logger=logger):
    """
    usage : generation of vector shape of points with features

    IN:
    trainShape [string] : path to a shapeFile
    pathWd [string] : working directory
    cfg [class] : class serviceConfigFile

    testMode [bool] : enable test
    features [string] : path to features allready compute (refl + NDVI ...)
    testFeaturePath [string] : path to stack of data without features
    testAnnualFeaturePath [string] : path to stack of data without features
    testPrevConfig [string] : path to a configuration file
    testShapeRegion [string] : path to a vector shapeFile, representing region in tile

    OUT:
    samples [string] : path to output vector shape
    """

    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    dataField = cfg.getParam('chain', 'dataField')
    cropMix = cfg.getParam('argTrain', 'cropMix')
    samplesClassifMix = cfg.getParam('argTrain', 'samplesClassifMix')
    annualCrop = cfg.getParam('argTrain', 'annualCrop')

    AllClass = fu.getFieldElement(trainShape, "ESRI Shapefile", dataField,
                                  mode="unique", elemType="str")
    folderFeaturesAnnual = folderAnnualFeatures

    # Get logger
    logger = logging.getLogger(__name__)

    for CurrentClass in annualCrop:
        try:
            AllClass.remove(str(CurrentClass))
        except ValueError:
            logger.warning("Class {} doesn't exist in {}".format(CurrentClass, trainShape))

    logger.info("All classes: {}".format(AllClass))
    logger.info("Annual crop: {}".format(annualCrop))

    featuresPath = cfg.getParam('chain', 'featuresPath')
    wMode = cfg.getParam('GlobChain', 'writeOutputs')
    folderFeatures = cfg.getParam('chain', 'featuresPath')
    folderFeaturesAnnual = cfg.getParam('argTrain', 'outputPrevFeatures')
    TestPath = cfg.getParam('chain', 'outputPath')
    prevFeatures = cfg.getParam('argTrain', 'outputPrevFeatures')
    configPrevClassif = cfg.getParam('argTrain', 'annualClassesExtractionSource')
    config_annual_data = cfg.getParam('argTrain', 'prevFeatures')

    folderSample = TestPath + "/learningSamples"
    if not os.path.exists(folderSample):
        try:
            os.mkdir(folderSample)
        except OSError:
            logger.warning(folderSample + "allready exists")

    workingDirectory = folderSample
    if pathWd:
        workingDirectory = pathWd

    if cropMix is False:
        #TODO: fix this error.
        # the function generateSamples_simple doesn't return anything
        samples = generateSamples_simple(folderSample, workingDirectory,
                                         trainShape, pathWd, folderFeatures,
                                         cfg, dataField,
                                         wMode, folderFeatures,
                                         testMode, sampleSelection)

    elif cropMix is True and samplesClassifMix is False:
        samples = generateSamples_cropMix(folderSample, workingDirectory,
                                          trainShape, pathWd, featuresPath,
                                          prevFeatures, annualCrop, AllClass,
                                          dataField, cfg, folderFeatures, folderFeaturesAnnual,
                                          config_annual_data, wMode, testMode, sampleSelection)

    elif cropMix is True and samplesClassifMix is True:
        samples = generateSamples_classifMix(folderSample, workingDirectory,
                                             trainShape, pathWd, annualCrop,
                                             AllClass, dataField, cfg,
                                             configPrevClassif, folderFeatures,
                                             wMode, testMode, 
                                             testShapeRegion, sampleSelection)
    if testMode:
        return samples


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="This function sample a shapeFile")
    parser.add_argument("-shape", dest="shape", help="path to the shapeFile to sampled",
                        default=None, required=True)
    parser.add_argument("--wd", dest="pathWd", help="path to the working directory",
                        default=None, required=False)
    parser.add_argument("-conf", help="path to the configuration file (mandatory)",
                        dest="pathConf", required=True)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)

    generateSamples(args.shape, args.pathWd, cfg)
