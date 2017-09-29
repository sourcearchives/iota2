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
import prepareStack
import ast
import sys
import os
import random
import shutil
import Sensors
import osr
import fileUtils as fu
from osgeo import ogr
from config import Config
import otbApplication as otb
from Utils import Opath, run
import genAnnualSamples as genAS
import otbAppli
import serviceConfigFile as SCF

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


def createSamplePoint(nonAnnual, annual, dataField, output, projOut):
    """
    IN:
    nonAnnual [string] : path to vector shape containing non annual points
    annual [string] : path to vector shape containing annual points
    dataField [string] : dataField in vector shape
    output [string] : output path
    projOut [int] : output EPSG code

    OUT :
    fusion of two vector shape in 'output' parameter
    """
    outDriver = ogr.GetDriverByName("SQLite")
    if os.path.exists(output):
        outDriver.DeleteDataSource(output)
    outDataSource = outDriver.CreateDataSource(output)
    out_lyr_name = os.path.splitext(os.path.split(output)[1])[0]
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(projOut)
    outLayer = outDataSource.CreateLayer(out_lyr_name, srs, ogr.wkbPoint)
    field_name = ogr.FieldDefn(dataField, ogr.OFTInteger)
    outLayer.CreateField(field_name)

    driverNonAnnual = ogr.GetDriverByName("SQLite")
    dataSourceNonAnnual = driverNonAnnual.Open(nonAnnual, 0)
    layerNonAnnual = dataSourceNonAnnual.GetLayer()

    driverAnnual = ogr.GetDriverByName("SQLite")
    dataSourceAnnual = driverAnnual.Open(annual, 0)
    layerAnnual = dataSourceAnnual.GetLayer()

    for feature in layerNonAnnual:
        geom = feature.GetGeometryRef()
        currentClass = feature.GetField(dataField)
        wkt = geom.Centroid().ExportToWkt()
        outFeat = ogr.Feature(outLayer.GetLayerDefn())
        outFeat.SetField(dataField, int(currentClass))
        outFeat.SetGeometry(ogr.CreateGeometryFromWkt(wkt))
        outLayer.CreateFeature(outFeat)
        outFeat.Destroy()

    for feature in layerAnnual:
        geom = feature.GetGeometryRef()
        currentClass = feature.GetField(dataField)
        wkt = geom.Centroid().ExportToWkt()
        outFeat = ogr.Feature(outLayer.GetLayerDefn())
        outFeat.SetField(dataField, int(currentClass))
        outFeat.SetGeometry(ogr.CreateGeometryFromWkt(wkt))
        outLayer.CreateFeature(outFeat)
        outFeat.Destroy()

    outDataSource.Destroy()


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
    if not keepClass:return False
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(shape, 0)
    layer = dataSource.GetLayer()

    AllFields = []
    layerDefinition = layer.GetLayerDefn()

    for i in range(layerDefinition.GetFieldCount()):
        currentField = layerDefinition.GetFieldDefn(i).GetName()
        AllFields.append(currentField)

    exp = " OR ".join(datafield+" = '"+str(currentClass)+"'" for currentClass in keepClass)
    layer.SetAttributeFilter(exp)
    if layer.GetFeatureCount() == 0:
        return False
    fu.CreateNewLayer(layer, shapeFiltered,AllFields)
    return True

def prepareSelection(ref,trainShape,dataField,samplesOptions,workingDirectory):

    stats=sampleSelection = None
    if not os.path.exists(workingDirectory):os.mkdir(workingDirectory)
    os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = "1"
    stats = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_stats.xml")
    cmd = "otbcli_PolygonClassStatistics -in "+ref+" -vec "+trainShape+" -out "+stats+" -field "+dataField
    print cmd
    run(cmd)
    verifPolyStats(stats)

    sampleSelection = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_SampleSel.sqlite")
    cmd = "otbcli_SampleSelection -out "+sampleSelection+" "+samplesOptions+" -field "+\
            dataField+" -in "+ref+" -vec "+trainShape+" -instats "+stats
    nbFeatures = len(fu.getFieldElement(trainShape,driverName="ESRI Shapefile",field=dataField))
    if nbFeatures >= 1 :
        print cmd
        run(cmd)
        return stats, sampleSelection

def gapFillingToSample(trainShape, samplesOptions, workingDirectory, samples,
                       dataField, featuresPath, tile, cfg, wMode=False,
                       inputSelection=False, testMode=False,
                       testSensorData=None, onlyMaskComm=False,
                       onlySensorsMasks=False, testUserFeatures=None):

    """
    usage : compute from a stack of data -> gapFilling -> features computation -> sampleExtractions
    thanks to OTB's applications'

    IN:
        sampleSelection [string] : path to a vector shape containing points (SampleSelection output)
        samples [string] : output path
        dataField [string] : data's field'
        featuresPath [string] : path to all stack (/featuresPath/tile/tmp/*.tif)
        tile [string] : actual tile to compute. (ex : T31TCJ)
        cfg [string] : path to configuation file

    OUT:
        sampleExtr [SampleExtraction OTB's object]:
    """
    if not isinstance(cfg, SCF.serviceConfigFile) and isinstance(cfg, str):
        cfg = SCF.serviceConfigFile(cfg)
    pathConf = cfg.pathConf
    workingDirectoryFeatures = workingDirectory
    cMaskDirectory = workingDirectoryFeatures+"/"+tile+"/tmp/"
    if "S1" in fu.sensorUserList(cfg):
        cMaskDirectory = cfg.getParam('chain', 'featuresPath') + "/" + tile
    if not os.path.exists(workingDirectoryFeatures):
        os.mkdir(workingDirectoryFeatures)
    AllGapFill,AllRefl,AllMask,datesInterp,realDates,dep_ = otbAppli.gapFilling(cfg,tile,\
                                                                    wMode=wMode,\
                                                                    featuresPath=featuresPath,\
                                                                    workingDirectory=workingDirectoryFeatures,\
                                                                    testMode=testMode,\
                                                                    testSensorData=testSensorData)
    nbDates = [fu.getNbDateInTile(currentDateFile) for currentDateFile in datesInterp]
    if onlySensorsMasks:
        return AllRefl,AllMask,datesInterp,realDates
    if wMode==True:
        for currentGapFillSensor in AllGapFill:
            currentGapFillSensor.ExecuteAndWriteOutput()
    else:
        for currentGapFillSensor in AllGapFill:
            currentGapFillSensor.Execute()
    try:
        ref = fu.FileSearch_AND(cMaskDirectory, True,
                                fu.getCommonMaskName(cfg)+".tif")[0]
    except:
        raise Exception("can't find Mask "+fu.getCommonMaskName(cfg)+".tif in "+cMaskDirectory)

    if onlyMaskComm:
        return ref
    sampleSelectionDirectory = workingDirectory+"/SampleSelection"
    if inputSelection == False:
        stats,sampleSelection = prepareSelection(ref,trainShape,dataField,samplesOptions,sampleSelectionDirectory)
    else: sampleSelection = inputSelection

    feat,ApplicationList,a,b,c,d,e = otbAppli.computeFeatures(cfg,nbDates,tile,\
                                                              AllGapFill,AllRefl,\
                                                              AllMask,datesInterp,\
                                                              realDates,\
                                                              testMode=testMode,\
                                                              testUserFeatures=testUserFeatures)
    if wMode == True:
        feat.ExecuteAndWriteOutput()
    else:
        feat.Execute()

    sampleExtr = otb.Registry.CreateApplication("SampleExtraction")
    sampleExtr.SetParameterString("ram","512")
    sampleExtr.SetParameterString("vec",sampleSelection)
    sampleExtr.SetParameterInputImage("in",feat.GetParameterOutputImage("out"))
    sampleExtr.SetParameterString("out",samples)
    sampleExtr.UpdateParameters()
    sampleExtr.SetParameterStringList("field",[dataField.lower()])

    return sampleExtr,feat,ApplicationList,a,b,c,d,e,AllGapFill,AllRefl,AllMask,dep_,sampleSelectionDirectory

def generateSamples_simple(folderSample,workingDirectory,trainShape,pathWd,\
                           featuresPath,samplesOptions, cfg, dataField,\
                           wMode=False,folderFeatures=None,testMode=False,\
                           testSensorData=None,testFeaturePath=None,testUserFeatures=None):
    """
    usage : from a strack of data generate samples containing points with features

    IN:
    folderSample [string] : output folder
    workingDirectory [string] : computation folder
    trainShape [string] : vector shape (polygons) to sample
    pathWd [string] : if different from None, enable HPC mode (copy at ending)
    featuresPath [string] : path to all stack
    samplesOptions [string] : sampling strategy according to OTB SampleSelection application
    cfg [string] : configuration file class
    dataField [string] : data's field into vector shape
    testMode [bool] : enable testMode -> iota2tests.py
    testFeatures [string] : path to features allready compute (refl + NDVI ...)
    testFeaturePath [string] : path to the stack of data, without features

    OUT:
    samples [string] : vector shape containing points
    """

    tile = trainShape.split("/")[-1].split("_")[0]
    dataField = cfg.getParam('chain', 'dataField')
    outputPath = cfg.getParam('chain', 'outputPath')
    userFeatPath = cfg.getParam('chain', 'userFeatPath')
    outFeatures = cfg.getParam('GlobChain', 'features')

    if userFeatPath == "None":
        userFeatPath = None

    extractBands = cfg.getParam('iota2FeatureExtraction', 'extractBands')

    if extractBands == "False":
        extractBands = None

    os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = "5"
    samples = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite")
    sampleExtr,a,b,c,d,e,f,g,h,i,j,k,sampleSel = gapFillingToSample(trainShape,samplesOptions,\
                                                                workingDirectory,samples,\
                                                                dataField,featuresPath,tile,\
                                                                cfg,wMode,False,testMode,\
                                                                testSensorData,testUserFeatures=testUserFeatures)
    sampleExtr.ExecuteAndWriteOutput()
    shutil.rmtree(sampleSel)
    if pathWd :
        shutil.copy(samples,folderSample+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite"))
    if wMode :
        if not os.path.exists(folderFeatures+"/"+tile):
            os.mkdir(folderFeatures+"/"+tile)
            os.mkdir(folderFeatures+"/"+tile+"/tmp")
        fu.updateDirectory(workingDirectory+"/"+tile+"/tmp",folderFeatures+"/"+tile+"/tmp")
    if os.path.exists(workingDirectory+"/"+tile) : shutil.rmtree(workingDirectory+"/"+tile)
    if testMode : return samples

def generateSamples_cropMix(folderSample,workingDirectory,trainShape,pathWd,nonAnnualData,samplesOptions,\
                            annualData,annualCrop,AllClass,dataField, cfg,\
                            folderFeature,folderFeaturesAnnual,wMode=False,testMode=False):
    """
    usage : from stracks A and B, generate samples containing points where annual crop are compute with A
    and non annual crop with B.

    IN:
    folderSample [string] : output folder
    workingDirectory [string] : computation folder
    trainShape [string] : vector shape (polygons) to sample
    pathWd [string] : if different from None, enable HPC mode (copy at ending)
    featuresPath [string] : path to all stack
    samplesOptions [string] : sampling strategy according to OTB SampleSelection application
    prevFeatures [string] : path to the configuration file which compute features A
    annualCrop [list of string/int] : list containing annual crops ex : [11,12]
    AllClass [list of string/int] : list containing all classes in vector shape ex : [11,12,51..]
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

    currentTile = trainShape.split("/")[-1].split("_")[0]
    corseTiles = ["T32TMN","T32TNN","T32TMM","T32TNM","T32TNL"]
                           
    if currentTile in corseTiles:
        generateSamples_simple(folderSample, workingDirectory, trainShape,
                               pathWd, cfg.GetParam('chain', 'featuresPath'),
                               samplesOptions, cfg,
                               dataField)
        return 0

    samplesClassifMix = cfg.getParam('argTrain', 'samplesClassifMix')
    outFeatures = cfg.getParam('GlobChain', 'features')
    featuresFind_NA = ""
    featuresFind_A = ""
    userFeatPath = cfg.getParam('chain', 'userFeatPath')
    if userFeatPath == "None" : userFeatPath = None

    extractBands = cfg.getParam('iota2FeatureExtraction', 'extractBands')
    if extractBands == "False" : extractBands = None

    #filter shape file
    nameNonAnnual = trainShape.split("/")[-1].replace(".shp","_NonAnnu.shp")
    nonAnnualShape = workingDirectory+"/"+nameNonAnnual
    nonAnnualCropFind = filterShpByClass(dataField,nonAnnualShape,AllClass,trainShape)
    nameAnnual = trainShape.split("/")[-1].replace(".shp","_Annu.shp")
    annualShape = workingDirectory+"/"+nameAnnual
    annualCropFind = filterShpByClass(dataField,annualShape,annualCrop,trainShape)

    SampleExtr_NA_name = nameNonAnnual.replace(".shp","_SampleExtr_NA.sqlite")
    SampleExtr_A_name = nameAnnual.replace(".shp","_SampleExtr_A.sqlite")
    SampleExtr_NA = workingDirectory+"/"+SampleExtr_NA_name
    SampleExtr_A = workingDirectory+"/"+SampleExtr_A_name

    sampleSel_A=sampleSel_NA=None
    if nonAnnualCropFind :
        Na_workingDirectory = workingDirectory+"/"+currentTile+"_nonAnnual"
        if not os.path.exists(Na_workingDirectory):os.mkdir(Na_workingDirectory)
        sampleExtr_NA,a,b,c,d,e,f,g,h,i,j,k,sampleSel_NA = gapFillingToSample(nonAnnualShape,samplesOptions,\
                                                                      Na_workingDirectory,SampleExtr_NA,\
                                                                      dataField,nonAnnualData,currentTile,\
                                                                      cfg,wMode,False,testMode,\
                                                                      nonAnnualData)
        sampleExtr_NA.ExecuteAndWriteOutput()
    if annualCropFind:
        A_workingDirectory = workingDirectory+"/"+currentTile+"_annual"
        if not os.path.exists(A_workingDirectory):os.mkdir(A_workingDirectory)
        sampleExtr_A,a,b,c,d,e,f,g,h,i,j,k,sampleSel_A = gapFillingToSample(annualShape,samplesOptions,\
                                                                    A_workingDirectory,SampleExtr_A,\
                                                                    dataField,annualData,currentTile,\
                                                                    cfg,wMode,False,testMode,\
                                                                    annualData)
        sampleExtr_A.ExecuteAndWriteOutput()

    #Merge samples
    MergeName = trainShape.split("/")[-1].replace(".shp","_Samples")

    if (nonAnnualCropFind and sampleSel_NA) and (annualCropFind and sampleSel_A):
        fu.mergeSQLite(MergeName, workingDirectory,[SampleExtr_NA,SampleExtr_A])
    elif (nonAnnualCropFind and sampleSel_NA) and not (annualCropFind and sampleSel_A):
        shutil.copyfile(SampleExtr_NA, workingDirectory+"/"+MergeName+".sqlite")
    elif not (nonAnnualCropFind and sampleSel_NA) and (annualCropFind and sampleSel_A):
        shutil.copyfile(SampleExtr_A, workingDirectory+"/"+MergeName+".sqlite")

    samples = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite")

    if nonAnnualCropFind and sampleSel_NA:
        if os.path.exists(sampleSel_NA):shutil.rmtree(sampleSel_NA)
        os.remove(SampleExtr_NA)
        fu.removeShape(nonAnnualShape.replace(".shp",""),[".prj",".shp",".dbf",".shx"])

    if annualCropFind and sampleSel_A:
        if os.path.exists(sampleSel_A):shutil.rmtree(sampleSel_A)
        os.remove(SampleExtr_A)
        fu.removeShape(annualShape.replace(".shp",""),[".prj",".shp",".dbf",".shx"])

    if wMode == True:
        targetDirectory = folderFeature+"/"+currentTile
        if not os.path.exists(targetDirectory) :
            os.mkdir(targetDirectory)
            os.mkdir(targetDirectory+"/tmp")
        fu.updateDirectory(workingDirectory+"/"+currentTile+"_nonAnnual/"+currentTile+"/tmp",targetDirectory+"/tmp")

        targetDirectory = folderFeaturesAnnual+"/"+currentTile
        if not os.path.exists(targetDirectory) :
            os.mkdir(targetDirectory)
            os.mkdir(targetDirectory+"/tmp")
        fu.updateDirectory(workingDirectory+"/"+currentTile+"_annual/"+currentTile+"/tmp",targetDirectory+"/tmp")

    if testMode : return samples
    if pathWd and os.path.exists(samples):
        shutil.copy(samples,folderSample+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite"))

def extractROI(raster,currentTile, cfg, pathWd,name,ref,testMode=None,testOutput=None):
    """
        usage : extract ROI in raster

        IN:
        raster [string] : path to the input raster
        currentTile [string] : current tile
        cfg [string] : configuration file class
        pathWd [string] : path to the working directory
        name [string] : output name

        OUT:
        raterROI [string] : path to the extracted raster.
    """

    outputPath = cfg.getParam('chain', 'outputPath')
    featuresPath = cfg.getParam('chain', 'featuresPath')

    workingDirectory = outputPath+"/learningSamples/"
    if pathWd:
        workingDirectory = pathWd
    if testMode:
        #currentTile_raster=testFeaturesPath
        workingDirectory=testOutput
    #else:currentTile_raster = fu.FileSearch_AND(featuresPath+"/"+currentTile,True,".tif")[0]
    currentTile_raster = ref
    minX,maxX,minY,maxY = fu.getRasterExtent(currentTile_raster)
    rasterROI = workingDirectory+"/"+currentTile+"_"+name+".tif"
    cmd = "gdalwarp -of GTiff -te "+str(minX)+" "+str(minY)+" "+str(maxX)+" "+str(maxY)+" -ot Byte "+raster+" "+rasterROI
    print cmd
    run(cmd)
    return rasterROI

def getRegionModelInTile(currentTile,currentRegion,pathWd, cfg, refImg,\
                         testMode,testPath,testOutputFolder):
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

    workingDirectory = outputPath+"/learningSamples/"
    if pathWd:
        workingDirectory = pathWd
    nameOut = "Mask_region_"+currentRegion+"_"+currentTile+".tif"

    if testMode:
        maskSHP = testPath
        workingDirectory = testOutputFolder
    else:
        maskSHP = fu.FileSearch_AND(outputPath+"/shapeRegion/",True,currentTile,"region_"+currentRegion,".shp")[0]

    rasterMask = workingDirectory+"/"+nameOut
    cmdRaster = "otbcli_Rasterization -in "+maskSHP+" -mode attribute -mode.attribute.field "+\
                fieldRegion+" -im "+refImg+" -out "+rasterMask
    print cmdRaster
    run(cmdRaster)
    return rasterMask

def generateSamples_classifMix(folderSample,workingDirectory,trainShape,pathWd,
                               samplesOptions,annualCrop,AllClass,dataField,
                               cfg,configPrevClassif,folderFeatures=None,
                               wMode=False,
                               testMode=None,
                               testSensorData=None,
                               testPrevClassif=None,
                               testShapeRegion=None):
    """
    usage : from one classification, chose randomly annual sample merge with non annual sample and extract features.
    IN:
        folderSample [string] : output folder
        workingDirectory [string] : computation folder
        trainShape [string] : vector shape (polygons) to sample
        pathWd [string] : if different from None, enable HPC mode (copy at ending)
        featuresPath [string] : path to all stack
        samplesOptions [string] : sampling strategy according to OTB SampleSelection application
        annualCrop [list of string/int] : list containing annual crops ex : [11,12]
        AllClass [list of string/int] : list containing all classes in vector shape ex : [11,12,51..]
        cfg [string] : configuration file class
        configPrevClassif [string] : path to the configuration file which generate previous classification
        dataField [string] : data's field into vector shape
        testMode [bool] : enable testMode -> iota2tests.py
        testFeatures [string] : path to features allready compute (refl + NDVI ...)
        testPrevClassif [string] : path to the classification
        testPrevConfig [string] : path to the configuration file which generate previous classification
        testShapeRegion [string] : path to the shapefile representing region in the tile.
        testFeaturePath [string] : path to the stack of data

    OUT:
        samples [string] : vector shape containing points
    """

    corseTiles = ["T32TMN","T32TNN","T32TMM","T32TNM","T32TNL"]
    currentTile = trainShape.split("/")[-1].split("_")[0]
    if currentTile in corseTiles:
        generateSamples_simple(folderSample, workingDirectory, trainShape,
                               pathWd, cfg.GetParam('chain', 'featuresPath'),
                               samplesOptions, cfg,
                               dataField)
        return 0

    targetResolution = cfg.getParam('chain', 'spatialResolution')
    validityThreshold = cfg.getParam('argTrain', 'validityThreshold')
    previousClassifPath = cfg.getParam('chain', 'outputPath')
    projOut = cfg.getParam('GlobChain', 'proj')
    projOut = int(projOut.split(":")[-1])
    userFeatPath = cfg.getParam('chain', 'userFeatPath')
    outFeatures = cfg.getParam('GlobChain', 'features')
    coeff = cfg.getParam('argTrain', 'coeffSampleSelection')
    extractBands = cfg.getParam('iota2FeatureExtraction', 'extractBands')

    if extractBands == "False":
        extractBands = None
    if userFeatPath == "None":
        userFeatPath = None

    seed = trainShape.split("_")[-2]

    if testMode:
        previousClassifPath = testPrevClassif

    nameNonAnnual = trainShape.split("/")[-1].replace(".shp","_NonAnnu.shp")
    nonAnnualShape = workingDirectory+"/"+nameNonAnnual
    nameAnnual = trainShape.split("/")[-1].replace(".shp","_Annu.shp")
    AnnualShape = workingDirectory+"/"+nameAnnual

    nonAnnualCropFind = filterShpByClass(dataField,nonAnnualShape,AllClass,trainShape)
    annualCropFind = filterShpByClass(dataField,AnnualShape,annualCrop,trainShape)

    gdalDriver = "SQLite"
    SampleSel_NA = workingDirectory+"/"+nameNonAnnual.replace(".shp","_SampleSel_NA.sqlite")
    stats_NA= workingDirectory+"/"+nameNonAnnual.replace(".shp","_STATS.xml")

    communDirectory = workingDirectory+"/commun"
    if not os.path.exists(communDirectory):
        os.mkdir(communDirectory)
    ref = gapFillingToSample(nonAnnualShape,samplesOptions,\
                             communDirectory,"",\
                             dataField,"",currentTile,\
                             cfg,wMode,False,testMode,\
                             testSensorData,onlyMaskComm=True)
    if nonAnnualCropFind:
        cmd = "otbcli_PolygonClassStatistics -in "+ref+" -vec "+nonAnnualShape+" -field "+dataField+" -out "+stats_NA
        print cmd
        run(cmd)
        verifPolyStats(stats_NA)
        cmd = "otbcli_SampleSelection -in "+ref+" -vec "+nonAnnualShape+" -field "+\
              dataField+" -instats "+stats_NA+" -out "+SampleSel_NA+" "+samplesOptions
        print cmd
        run(cmd)
        allCoord = getPointsCoordInShape(SampleSel_NA,gdalDriver)
        featuresFind_NA = fu.getFieldElement(SampleSel_NA,driverName="SQLite",\
                                             field = dataField.lower(),mode = "all",elemType = "int")
    else:
        allCoord=[0]

    nameAnnual = trainShape.split("/")[-1].replace(".shp","_Annu.sqlite")
    annualShape = workingDirectory+"/"+nameAnnual

    classificationRaster = extractROI(previousClassifPath+"/final/Classif_Seed_0.tif",
                                      currentTile,cfg ,pathWd,"Classif",
                                      ref,testMode,testOutput=folderSample)
    validityRaster = extractROI(previousClassifPath+"/final/PixelsValidity.tif",
                                currentTile,cfg ,pathWd,"Cloud",\
                                ref,testMode,testOutput=folderSample)
    shutil.rmtree(communDirectory)

    currentRegion = trainShape.split("/")[-1].split("_")[2].split("f")[0]
    mask = getRegionModelInTile(currentTile,currentRegion,pathWd, cfg, classificationRaster,\
                                testMode,testShapeRegion,testOutputFolder=folderSample)

    if annualCropFind : annualPoints = genAS.genAnnualShapePoints(allCoord,gdalDriver,workingDirectory,\
                                                                  targetResolution,annualCrop,dataField,\
                                                                  currentTile,validityThreshold,validityRaster,\
                                                                  classificationRaster,mask,trainShape,annualShape,coeff,projOut)
    MergeName = trainShape.split("/")[-1].replace(".shp","_selectionMerge")
    sampleSelection = workingDirectory+"/"+MergeName+".sqlite"

    if (nonAnnualCropFind and featuresFind_NA) and (annualCropFind and annualPoints):
        createSamplePoint(SampleSel_NA,annualShape,dataField,sampleSelection,projOut)
    elif (nonAnnualCropFind and featuresFind_NA) and not (annualCropFind and annualPoints):
        shutil.copy(SampleSel_NA,sampleSelection)
    elif not (nonAnnualCropFind and featuresFind_NA) and (annualCropFind and annualPoints):
        shutil.copy(annualShape,sampleSelection)
    samples = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite")

    sampleExtr,a,b,c,d,e,f,g,h,i,j,k,l = gapFillingToSample("","",workingDirectory,samples,\
                                                        dataField,folderFeatures,currentTile,\
                                                        cfg,wMode,sampleSelection,\
                                                        testMode,\
                                                        testSensorData)
    sampleExtr.ExecuteAndWriteOutput()
    finalSamples = folderSample+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite")
    if os.path.exists(samples) and pathWd:
        shutil.copy(samples,finalSamples)
    if os.path.exists(SampleSel_NA):
        os.remove(SampleSel_NA)
    if os.path.exists(sampleSelection):
        os.remove(sampleSelection)
    if os.path.exists(stats_NA):
        os.remove(stats_NA)

    if wMode:
        targetDirectory=folderFeatures+"/"+currentTile
        if not os.path.exists(targetDirectory):
            os.mkdir(targetDirectory)
            os.mkdir(targetDirectory+"/tmp")
        fu.updateDirectory(workingDirectory+"/"+currentTile+"/tmp",targetDirectory+"/tmp")

    if testMode:
        return finalSamples

def generateSamples(trainShape, pathWd, cfg, wMode=False,folderFeatures=None,\
                    folderAnnualFeatures=None,\
                    testMode=False,testSensorData=None,testNonAnnualData=None,\
                    testAnnualData=None,testPrevConfig=None,testShapeRegion=None,\
                    testTestPath=None,testPrevClassif=None,testUserFeatures=None):
    """
    usage :

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

    featuresPath = testNonAnnualData
    TestPath = testTestPath
    dataField = cfg.getParam('chain', 'dataField')
    configPrevClassif = testPrevConfig

    samplesOptions = cfg.getParam('argTrain', 'samplesOptions')
    cropMix = cfg.getParam('argTrain', 'cropMix')
    samplesClassifMix = cfg.getParam('argTrain', 'samplesClassifMix')

    prevFeatures = testAnnualData
    annualCrop = cfg.getParam('argTrain', 'annualCrop')
    AllClass = fu.getFieldElement(trainShape,"ESRI Shapefile",dataField,mode = "unique",elemType = "str")
    folderFeaturesAnnual = folderAnnualFeatures
    for CurrentClass in annualCrop:
        try:
            AllClass.remove(str(CurrentClass))
        except ValueError:
            print CurrentClass+" doesn't exist in "+trainShape
            print "All Class : "
            print AllClass
    print trainShape
    print AllClass
    print annualCrop

    if testMode==False :
        featuresPath = cfg.getParam('chain', 'featuresPath')
        wMode = ast.literal_eval(cfg.getParam('GlobChain', 'writeOutputs'))
        folderFeatures = cfg.getParam('chain', 'featuresPath')
        folderFeaturesAnnual = cfg.getParam('argTrain', 'outputPrevFeatures')
        TestPath = cfg.getParam('chain', 'outputPath')
        prevFeatures = cfg.getParam('argTrain', 'prevFeatures')
        configPrevClassif = cfg.getParam('argTrain', 'configClassif')

    folderSample = TestPath+"/learningSamples"
    if not os.path.exists(folderSample): os.mkdir(folderSample)

    workingDirectory = folderSample
    if pathWd:
        workingDirectory = pathWd

    if not cropMix == 'True':
        samples = generateSamples_simple(folderSample,workingDirectory,trainShape,pathWd,folderFeatures,\
                                         samplesOptions, cfg, dataField,wMode,folderFeatures,\
                                         testMode,testSensorData,testNonAnnualData,testUserFeatures)
    elif cropMix == 'True' and samplesClassifMix == "False":
        samples = generateSamples_cropMix(folderSample,workingDirectory,trainShape,pathWd,featuresPath,\
                                          samplesOptions,prevFeatures,annualCrop,AllClass,dataField, cfg,
                                          folderFeatures,folderFeaturesAnnual,wMode,testMode)
    elif cropMix == 'True' and samplesClassifMix == "True":
        samples = generateSamples_classifMix(folderSample,workingDirectory,trainShape,pathWd,samplesOptions,\
                                             annualCrop,AllClass,dataField,cfg ,configPrevClassif,folderFeatures,
                                             wMode,\
                                             testMode,\
                                             testSensorData,\
                                             testPrevClassif,\
                                             testShapeRegion)
    if testMode : return samples

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "This function sample a shapeFile")
    parser.add_argument("-shape",dest = "shape",help ="path to the shapeFile to sampled",default=None,required=True)
    parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
    parser.add_argument("-conf",help ="path to the configuration file (mandatory)",dest = "pathConf",required=True)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)

    generateSamples(args.shape, args.pathWd, cfg)
