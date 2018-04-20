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
import unittest
import Sensors
import Utils
import filecmp
import string
import random
import shutil
import sys
import osr
import ogr
import subprocess
import RandomInSituByTile
import createRegionsByTiles
import vectorSampler
import oso_directory as osoD
import fileUtils as fu
import test_genGrid as test_genGrid
import tileEnvelope
from gdalconst import *
from osgeo import gdal
from config import Config
import numpy as np
import otbApplication as otb
import argparse
import serviceConfigFile as SCF
from Utils import run
#import logging
import serviceLogger as sLog
import oso_directory
fu.updatePyPath()

from DeleteField import deleteField
from AddField import addField


#export PYTHONPATH=$PYTHONPATH:/mnt/data/home/vincenta/modulePy/config-0.3.9       -> get python Module
#export PYTHONPATH=$PYTHONPATH:/mnt/data/home/vincenta/IOTA2/theia_oso/data/test_scripts -> get scripts needed to test
#export IOTA2DIR=/mnt/data/home/vincenta/IOTA2/theia_oso
#export PYTHONPATH=$PYTHONPATH:$IOTA2DIR/data/test_scripts

#python -m unittest iota2tests
#coverage run iota2tests.py
#coverage report
iota2dir = os.environ.get('IOTA2DIR')
iota2_script = os.environ.get('IOTA2DIR') + "/scripts/common"
iota2_dataTest = os.environ.get('IOTA2DIR') + "/data/"

# Init of logging service
# We need an instance of serviceConfigFile
cfg = SCF.serviceConfigFile(iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg")
# We force the logFile value
cfg.setParam('chain', 'logFile', iota2_dataTest + "/OSOlogFile.log")
# We call the serviceLogger
sLog.serviceLogger(cfg, __name__)
SCF.clearConfig()


def shapeReferenceVector(refVector, outputName):
    """
    modify reference vector (add field, rename...)
    """
    from AddField import addField
    from Utils import run

    path, name = os.path.split(refVector)
    
    tmp = path+"/"+outputName+"_TMP"
    fu.cpShapeFile(refVector.replace(".shp",""),tmp,[".prj",".shp",".dbf",".shx"])
    addField(tmp+".shp", "region", "1", str)
    addField(tmp+".shp", "seed_0", "learn", str)
    cmd = "ogr2ogr -dialect 'SQLite' -sql 'select GEOMETRY,seed_0, region, CODE as code from "+outputName+"_TMP' " + path+"/"+outputName+".shp "+tmp+".shp"
    run(cmd)
    
    os.remove(tmp+".shp")
    os.remove(tmp+".shx")
    os.remove(tmp+".prj")
    os.remove(tmp+".dbf")
    return path+"/"+outputName+".shp"

def prepare_test_selection(vector, raster_ref, outputSelection, wd, dataField):
    """
    """
    import otbAppli as otb
    stats_path = os.path.join(wd, "stats.xml")
    if os.path.exists(stats_path):
        os.remove(stats_path)
    stats = otb.CreatePolygonClassStatisticsApplication({"in": raster_ref,
                                                         "vec": vector,
                                                         "field": dataField,
                                                         "out": stats_path})
    stats.ExecuteAndWriteOutput()
    sampleSel = otb.CreateSampleSelectionApplication({"in": raster_ref,
                                                      "vec":vector, 
                                                      "out":outputSelection,
                                                      "instats":stats_path,
                                                      "sampler": "random",
                                                      "strategy": "all",
                                                      "field": dataField})
    if os.path.exists(outputSelection):
        os.remove(outputSelection)
    sampleSel.ExecuteAndWriteOutput()
    os.remove(stats_path)

def rasterToArray(InRaster):
    """
    convert a raster to an array
    """
    arrayOut = None
    ds = gdal.Open(InRaster)
    arrayOut = ds.ReadAsArray()
    return arrayOut


def arrayToRaster(inArray, outRaster):
    """
    usage : from an array, create a raster with (originX,originY) origin
    IN
    inArray [numpy.array] : input array
    outRaster [string] : output raster
    """
    rows = inArray.shape[0]
    cols = inArray.shape[1]
    originX = 777225.58
    originY = 6825084.53
    pixSize = 30
    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(outRaster, cols, rows, 1, gdal.GDT_UInt16)
    if not outRaster:
        raise Exception("can not create : "+outRaster)
    outRaster.SetGeoTransform((originX, pixSize, 0, originY, 0, pixSize))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(inArray)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromEPSG(2154)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()


def delete_uselessFields(test_vector, field_to_rm="region"):
    """
    """
    #const
    
    fields = fu.getAllFieldsInShape(test_vector, driver='SQLite')
    
    rm_field = [field for field in fields if field_to_rm in field]
    
    for rm in rm_field:
        deleteField(test_vector, rm)


def generateRandomString(size):
    """
    usage : generate a random string of 'size' character

    IN
    size [int] : size of output string

    OUT
    a random string of 'size' character
    """
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase +
                                                string.digits +
                                                string.ascii_lowercase) for _ in range(size))


def checkSameFile(files, patterns=["res_ref", "res_test"]):

    """
    usage : check if input files are the equivalent, after replacing all
    patters by XXXX

    IN
    files [list of string] : list of files to compare

    OUT
    [bool]
    """
    replacedBy = "XXXX"

    Alltmp = []
    for file_ in files:
        file_tmp = file_.split(".")[0]+"_tmp."+file_.split(".")[-1]
        if os.path.exists(file_tmp):
            os.remove(file_tmp)
        Alltmp.append(file_tmp)
        with open(file_, "r") as f1:
            for line in f1:
                line_tmp = line
                for patt in patterns:
                    if patt in line:
                        line_tmp = line.replace(patt, replacedBy)
                with open(file_tmp, "a") as f2:
                    f2.write(line_tmp)
    same = filecmp.cmp(Alltmp[0], Alltmp[1])

    for fileTmp in Alltmp:
        os.remove(fileTmp)

    return same


def checkSameEnvelope(EvRef, EvTest):
    """
    usage get input extent and compare them. Return true if same, else false

    IN
    EvRef [string] : path to a vector file
    EvTest [string] : path to a vector file

    OUT
    [bool]
    """
    miX_ref, miY_ref, maX_ref, maY_ref = fu.getShapeExtent(EvRef)
    miX_test, miY_test, maX_test, maY_test = fu.getShapeExtent(EvTest)

    if ((miX_ref == miX_test) and (miY_test == miY_ref) and
            (maX_ref == maX_test) and (maY_ref == maY_test)):
        return True
    return False


def prepareAnnualFeatures(workingDirectory, referenceDirectory, pattern):
    """
    double all rasters's pixels
    """
    shutil.copytree(referenceDirectory, workingDirectory)
    rastersPath = fu.FileSearch_AND(workingDirectory, True, pattern)
    for raster in rastersPath:
        cmd = 'otbcli_BandMathX -il '+raster+' -out '+raster+' -exp "im1+im1"'
        run(cmd)


class iota_testServiceCompareImageFile(unittest.TestCase):
    """
    Test class ServiceCompareImageFile
    """
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.refData = iota2_dataTest + "/references/ServiceCompareImageFile/"

    def test_SameImage(self):
        serviceCompareImageFile = fu.serviceCompareImageFile()
        file1 = self.refData + "raster1.tif"
        nbDiff = serviceCompareImageFile.gdalFileCompare(file1, file1)
        # we check if it is the same file
        self.assertEqual(nbDiff, 0)

    def test_DifferentImage(self):
        serviceCompareImageFile = fu.serviceCompareImageFile()
        file1 = self.refData + "raster1.tif"
        file2 = self.refData + "raster2.tif"
        nbDiff = serviceCompareImageFile.gdalFileCompare(file1, file2)
        # we check if differences are detected
        self.assertNotEqual(nbDiff, 0)

    def test_ErrorImage(self):
        serviceCompareImageFile = fu.serviceCompareImageFile()
        file1 = self.refData + "rasterNotHere.tif"
        file2 = self.refData + "raster2.tif"
        # we check if an error is detected
        self.assertRaises(Exception, serviceCompareImageFile.gdalFileCompare,
                          file1, file2)

class iota_testServiceCompareVectorFile(unittest.TestCase):
    """
    Test class serviceCompareVectorFile
    """
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.refData = iota2_dataTest + "/references/ServiceCompareVectorFile/"

    def test_SameVector(self):
        serviceCompareVectorFile = fu.serviceCompareVectorFile()
        file1 = self.refData + "vector1.shp"
        # we check if it is the same file
        self.assertTrue(serviceCompareVectorFile.testSameShapefiles(file1, file1))

    def test_DifferentVector(self):
        serviceCompareVectorFile = fu.serviceCompareVectorFile()
        file1 = self.refData + "vector1.shp"
        file2 = self.refData + "vector2.shp"
        # we check if differences are detected
        self.assertFalse(serviceCompareVectorFile.testSameShapefiles(file1, file2))

    def test_ErrorVector(self):
        serviceCompareVectorFile = fu.serviceCompareVectorFile()
        file1 = self.refData + "vectorNotHere.shp"
        file2 = self.refData + "vector2.shp"
        # we check if an error is detected
        self.assertRaises(Exception, serviceCompareVectorFile.testSameShapefiles,
                          file1, file2)


class iota_testStringManipulations(unittest.TestCase):
    """
    Test iota2 string manipulations
    """
    @classmethod
    def setUpClass(self):
        self.AllL8Tiles = "D00005H0010 D0002H0007 D0003H0006 D0004H0004 \
                           D0005H0002 D0005H0009 D0006H0006 D0007H0003 \
                           D0007H0010 D0008H0008 D0009H0007 D0010H0006 \
                           D0000H0001 D0002H0008 D0003H0007 D0004H0005 \
                           D0005H0003 D0005H0010 D0006H0007 D0007H0004 \
                           D0008H0002 D0008H0009 D0009H0008 D0010H0007 \
                           D0000H0002 D0003H0001 D0003H0008 D0004H0006 \
                           D0005H0004 D0006H0001 D0006H0008 D0007H0005 \
                           D0008H0003 D0009H0002 D0009H0009 D0010H0008 \
                           D00010H0005 D0003H0002 D0003H0009 D0004H0007 \
                           D0005H0005 D0006H0002 D0006H0009 D0007H0006 \
                           D0008H0004 D0009H0003 D0010H0002 D0001H0007 \
                           D0003H0003 D0004H0001 D0004H0008 D0005H0006 \
                           D0006H0003 D0006H0010 D0007H0007 D0008H0005 \
                           D0009H0004 D0010H0003 D0001H0008 D0003H0004 \
                           D0004H0002 D0004H0009 D0005H0007 D0006H0004 \
                           D0007H0001 D0007H0008 D0008H0006 D0009H0005 \
                           D0010H0004 D0002H0006 D0003H0005 D0004H0003 \
                           D0005H0001 D0005H0008 D0006H0005 D0007H0002 \
                           D0007H0009 D0008H0007 D0009H0006 D0010H0005".split()
        self.AllS2Tiles = "T30TVT T30TXP T30TYN T30TYT T30UWU T30UYA T31TCK \
                           T31TDJ T31TEH T31TEN T31TFM T31TGL T31UCR T31UDS \
                           T31UFP T32TLP T32TMN T32ULV T30TWP T30TXQ T30TYP \
                           T30UUU T30UWV T30UYU T31TCL T31TDK T31TEJ T31TFH \
                           T31TFN T31TGM T31UCS T31UEP T31UFQ T32TLQ T32TNL \
                           T32UMU T30TWS T30TXR T30TYQ T30UVU T30UXA T30UYV \
                           T31TCM T31TDL T31TEK T31TFJ T31TGH T31TGN T31UDP \
                           T31UEQ T31UFR T32TLR T32TNM T32UMV T30TWT T30TXS \
                           T30TYR T30UVV T30UXU T31TCH T31TCN T31TDM T31TEL \
                           T31TFK T31TGJ T31UCP T31UDQ T31UER T31UGP T32TLT \
                           T32TNN T30TXN T30TXT T30TYS T30UWA T30UXV T31TCJ \
                           T31TDH T31TDN T31TEM T31TFL T31TGK T31UCQ T31UDR \
                           T31UES T31UGQ T32TMM T32ULU".split()
        self.dateFile = iota2_dataTest+"/references/dates.txt"
        self.fakeDateFile = iota2_dataTest+"/references/fakedates.txt"

    def test_getTile(self):
        """
        get tile name in random string
        """
        rString_head = generateRandomString(100)
        rString_tail = generateRandomString(100)

        S2 = True
        for currentTile in self.AllS2Tiles:
            try:
                fu.findCurrentTileInString(rString_head +
                                           currentTile +
                                           rString_tail, self.AllS2Tiles)
            except StandardError:
                S2 = False
        self.assertTrue(S2)
        L8 = True
        for currentTile in self.AllL8Tiles:
            try:
                fu.findCurrentTileInString(rString_head +
                                           currentTile +
                                           rString_tail, self.AllL8Tiles)
            except StandardError:
                L8 = False
        self.assertTrue(L8)

    def test_getDates(self):
        """
        get number of dates
        """
        try:
            nbDates = fu.getNbDateInTile(self.dateFile, display=False)
            self.assertTrue(nbDates == 35)
        except StandardError:
            self.assertTrue(False)
        
        try:
            fu.getNbDateInTile(self.fakeDateFile, display=False)
            self.assertTrue(False)
        except :
            self.assertTrue(True)

def compareSQLite(vect_1, vect_2, CmpMode='table', ignored_fields=[]):

    """
    compare SQLite, table mode is faster but does not work with
    connected OTB applications.

    return true if vectors are the same
    """

    from collections import OrderedDict

    def getFieldValue(feat, fields):
        """
        usage : get all fields's values in input feature

        IN
        feat [gdal feature]
        fields [list of string] : all fields to inspect

        OUT
        [dict] : values by fields
        """
        return OrderedDict([(currentField, feat.GetField(currentField)) for currentField in fields])

    def priority(item):
        """
        priority key
        """
        return (item[0], item[1])

    def getValuesSortedByCoordinates(vector):
        """
        usage return values sorted by coordinates (x,y)

        IN
        vector [string] path to a vector of points

        OUT
        values [list of tuple] : [(x,y,[val1,val2]),()...]
        """
        values = []
        driver = ogr.GetDriverByName("SQLite")
        ds = driver.Open(vector, 0)
        lyr = ds.GetLayer()
        fields = fu.getAllFieldsInShape(vector, 'SQLite')
        for feature in lyr:
            x = feature.GetGeometryRef().GetX()
            y = feature.GetGeometryRef().GetY()
            fields_val = getFieldValue(feature, fields)
            values.append((x, y, fields_val))

        values = sorted(values, key=priority)
        return values

    fields_1 = fu.getAllFieldsInShape(vect_1, 'SQLite')
    fields_2 = fu.getAllFieldsInShape(vect_2, 'SQLite')

    if len(fields_1) != len(fields_2):
        return False

    if CmpMode == 'table':
        import sqlite3 as lite
        import pandas as pad
        connection_1 = lite.connect(vect_1)
        df_1 = pad.read_sql_query("SELECT * FROM output", connection_1)

        connection_2 = lite.connect(vect_2)
        df_2 = pad.read_sql_query("SELECT * FROM output", connection_2)

        try:
            table = (df_1 != df_2).any(1)
            if True in table.tolist():
                return False
            else:
                return True
        except ValueError:
            return False

    elif CmpMode == 'coordinates':
        values_1 = getValuesSortedByCoordinates(vect_1)
        values_2 = getValuesSortedByCoordinates(vect_2)
        sameFeat = []
        for val_1, val_2 in zip(values_1, values_2):
            for (k1,v1),(k2,v2) in zip(val_1[2].items(), val_2[2].items()):
                if not k1 in ignored_fields and k2 in ignored_fields:
                    sameFeat.append(cmp(v1, v2) == 0)
        if False in sameFeat:
            return False
        return True
    else:
        raise Exception("CmpMode parameter must be 'table' or 'coordinates'")

class iota_testSamplerApplications(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.test_vector = iota2_dataTest+"/test_vector"
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)

        self.referenceShape = iota2_dataTest+"/references/sampler/D0005H0002_polygons_To_Sample.shp"
        self.referenceShape_test = shapeReferenceVector(self.referenceShape, "D0005H0002")
        self.configSimple_NO_bindings = iota2_dataTest+"/config/test_config.cfg"
        self.configSimple_bindings = iota2_dataTest+"/config/test_config_bindings.cfg"
        self.configSimple_bindings_uDateFeatures = iota2_dataTest+"/config/test_config_bindings_uDateFeatures.cfg"
        self.configCropMix_NO_bindings = iota2_dataTest+"/config/test_config_cropMix.cfg"
        self.configCropMix_bindings = iota2_dataTest+"/config/test_config_cropMix_bindings.cfg"
        self.configClassifCropMix_NO_bindings = iota2_dataTest+"/config/test_config_classifCropMix.cfg"
        self.configClassifCropMix_bindings = iota2_dataTest+"/config/test_config_classifCropMix_bindings.cfg"
        self.configPrevClassif = iota2_dataTest+"/config/prevClassif.cfg"

        self.regionShape = iota2_dataTest+"/references/region_need_To_env.shp"
        self.features = iota2_dataTest+"/references/features/D0005H0002/Final/SL_MultiTempGapF_Brightness_NDVI_NDWI__.tif"
        self.MNT = iota2_dataTest+"/references/MNT/"
        self.expectedFeatures = {11: 74, 12: 34, 42: 19, 51: 147}
        self.SensData = iota2_dataTest+"/L8_50x50"
        self.iota2_directory = os.environ.get('IOTA2DIR')
        
        self.selection_test = os.path.join(self.test_vector, "D0005H0002.sqlite")
        raster_ref = fu.FileSearch_AND(os.path.join(self.SensData,"Landsat8_D0005H0002"), True, ".TIF")[0]
        prepare_test_selection(self.referenceShape_test, raster_ref, self.selection_test, self.test_vector, "code")

    def test_samplerSimple_bindings(self):

        def prepareTestsFolder(workingDirectory=False):
            wD = None
            if not os.path.exists(self.test_vector):
                os.mkdir(self.test_vector)
            testPath = self.test_vector+"/simpleSampler_vector_bindings"
            if os.path.exists(testPath):
                shutil.rmtree(testPath)
            os.mkdir(testPath)
            featuresOutputs = self.test_vector+"/simpleSampler_features_bindings"
            if os.path.exists(featuresOutputs):
                shutil.rmtree(featuresOutputs)
            os.mkdir(featuresOutputs)
            if workingDirectory:
                wD = self.test_vector+"/simpleSampler_bindingsTMP"
                if os.path.exists(wD):
                    shutil.rmtree(wD)
                os.mkdir(wD)
            return testPath, featuresOutputs, wD

        reference = iota2_dataTest+"/references/sampler/D0005H0002_polygons_To_Sample_Samples_ref_bindings.sqlite"
        SensData = iota2_dataTest+"/L8_50x50"
        
        import serviceConfigFile as SCF
        # load configuration file
        SCF.clearConfig()
    
        config_path = os.path.join(self.iota2_directory, "config",
                                   "Config_4Tuiles_Multi_FUS_Confidence.cfg")
        self.config = SCF.serviceConfigFile(config_path)
        testPath, featuresOutputs, wD = prepareTestsFolder(True)
        
        os.mkdir(featuresOutputs+"/D0005H0002")
        os.mkdir(featuresOutputs+"/D0005H0002/tmp")

        #fill up configuration file
        L8_rasters = os.path.join(self.iota2_directory, "data", "L8_50x50")
        self.config.setParam('chain', 'outputPath', testPath)
        self.config.setParam('chain', 'listTile', "D0005H0002")
        self.config.setParam('chain', 'featuresPath', featuresOutputs)
        self.config.setParam('chain', 'L8Path', L8_rasters)
        self.config.setParam('chain', 'userFeatPath', 'None')
        self.config.setParam('chain', 'regionField', 'region')
        self.config.setParam('argTrain', 'cropMix', False)
        self.config.setParam('argTrain', 'samplesClassifMix', False)
        self.config.setParam('GlobChain', 'useAdditionalFeatures', False)

        """
        TEST :
        prepare data to gapFilling -> gapFilling -> features generation -> samples extraction
        with otb's applications connected in memory
        and compare resulting samples extraction with reference.
        """
        #Launch sampling
        vectorSampler.generateSamples(self.referenceShape_test, None, self.config, sampleSelection=self.selection_test)
        #Compare
        test_vector = fu.fileSearchRegEx(testPath + "/learningSamples/*sqlite")[0]
        delete_uselessFields(test_vector)
        compare = compareSQLite(test_vector, reference, CmpMode='coordinates')
        self.assertTrue(compare)

        """
        TEST :
        prepare data to gapFilling -> gapFilling -> features generation -> samples extraction
        with otb's applications connected in memory and writing tmp files
        and compare resulting samples extraction with reference.
        """

        testPath, featuresOutputs, wD = prepareTestsFolder()
        os.mkdir(featuresOutputs+"/D0005H0002")
        os.mkdir(featuresOutputs+"/D0005H0002/tmp")
        self.config.setParam('GlobChain', 'writeOutputs', True)
        vectorSampler.generateSamples(self.referenceShape_test, None, self.config, sampleSelection=self.selection_test)
        self.config.setParam('GlobChain', 'writeOutputs', False)

        test_vector = fu.fileSearchRegEx(testPath + "/learningSamples/*sqlite")[0]
        delete_uselessFields(test_vector)
        compare = compareSQLite(test_vector, reference, CmpMode='coordinates')
        self.assertTrue(compare)

        """
        TEST :
        prepare data to gapFilling -> gapFilling -> features generation -> samples extraction
        with otb's applications connected in memory, write all necessary
        tmp files in a working directory and compare resulting samples
        extraction with reference.
        """
        testPath, featuresOutputs, wD = prepareTestsFolder()
        os.mkdir(featuresOutputs+"/D0005H0002")
        os.mkdir(featuresOutputs+"/D0005H0002/tmp")
        self.config.setParam('GlobChain', 'writeOutputs', True)
        vectorSampler.generateSamples(self.referenceShape_test, wD, self.config, sampleSelection=self.selection_test)
        self.config.setParam('GlobChain', 'writeOutputs', False)

        test_vector = fu.fileSearchRegEx(testPath + "/learningSamples/*sqlite")[0]
        delete_uselessFields(test_vector)
        compare = compareSQLite(test_vector, reference, CmpMode='coordinates')
        self.assertTrue(compare)

        #Test user features and additional features
        reference = iota2_dataTest+"/references/sampler/D0005H0002_polygons_To_Sample_Samples_UserFeat_UserExpr.sqlite"
        """
        TEST :
        prepare data to gapFilling -> gapFilling -> features generation (userFeatures + userDayFeatures) -> samples extraction
        with otb's applications connected in memory, compare resulting sample to extraction with reference.
        """
        self.config.setParam('GlobChain', 'writeOutputs', True)
        self.config.setParam('chain', 'userFeatPath', os.path.join(self.iota2_directory,"data/references/MNT/"))
        self.config.setParam('userFeat', 'arbo', '/*')
        self.config.setParam('userFeat', 'patterns', 'MNT')
        self.config.setParam('Landsat8', 'additionalFeatures', 'b1+b2,(b1-b2)/(b1+b2)')
        self.config.setParam('GlobChain', 'useAdditionalFeatures', True)
        
        testPath, featuresOutputs, wD = prepareTestsFolder(workingDirectory=False)
        os.mkdir(featuresOutputs+"/D0005H0002")
        os.mkdir(featuresOutputs+"/D0005H0002/tmp")
        vectorSampler.generateSamples(self.referenceShape_test, wD, self.config, sampleSelection=self.selection_test)

        test_vector = fu.fileSearchRegEx(testPath + "/learningSamples/*sqlite")[0]
        delete_uselessFields(test_vector)
        compare = compareSQLite(test_vector, reference, CmpMode='coordinates')
        self.assertTrue(compare)

        """
        TEST :
        prepare data to gapFilling -> gapFilling -> features generation (userFeatures + userDayFeatures) -> samples extraction
        with otb's applications connected in memory,
        write all necessary tmp files in a working directory
        and compare resulting sample extraction with reference.
        """
        testPath, featuresOutputs, wD = prepareTestsFolder(workingDirectory=True)
        os.mkdir(featuresOutputs+"/D0005H0002")
        os.mkdir(featuresOutputs+"/D0005H0002/tmp")
        vectorSampler.generateSamples(self.referenceShape_test, wD, self.config, sampleSelection=self.selection_test)

        test_vector = fu.fileSearchRegEx(testPath + "/learningSamples/*sqlite")[0]
        delete_uselessFields(test_vector)
        compare = compareSQLite(test_vector, reference, CmpMode='coordinates')
        self.assertTrue(compare)

    def test_samplerCropMix_bindings(self):
        """
        TEST cropMix 1 algorithm
        using connected OTB applications :

        Step 1 : on non annual class
        prepare data to gapFilling -> gapFilling -> features generation -> samples extraction non annual

        Step 2 : on annual class
        prepare data to gapFilling -> gapFilling -> features generation -> samples extraction annual

        Step 3 : merge samples extration nonAnnual / annual

        Step 4 : compare the merged sample to reference
        """

        from iota2tests_features_labels import prepareAnnualFeatures

        def prepareTestsFolder(workingDirectory=False):

            testPath = self.test_vector+"/cropMixSampler_bindings/"
            if os.path.exists(testPath):
                shutil.rmtree(testPath)
            os.mkdir(testPath)

            featuresNonAnnualOutputs = self.test_vector+"/cropMixSampler_featuresNonAnnual_bindings"
            if os.path.exists(featuresNonAnnualOutputs):
                shutil.rmtree(featuresNonAnnualOutputs)
            os.mkdir(featuresNonAnnualOutputs)
            os.mkdir(featuresNonAnnualOutputs+"/D0005H0002")
            os.mkdir(featuresNonAnnualOutputs+"/D0005H0002/tmp")

            featuresAnnualOutputs = self.test_vector+"/cropMixSampler_featuresAnnual_bindings"
            if os.path.exists(featuresAnnualOutputs):
                shutil.rmtree(featuresAnnualOutputs)
            os.mkdir(featuresAnnualOutputs)
            os.mkdir(featuresAnnualOutputs+"/D0005H0002")
            os.mkdir(featuresAnnualOutputs+"/D0005H0002/tmp")

            wD = self.test_vector+"/cropMixSampler_bindingsTMP"
            if os.path.exists(wD):
                shutil.rmtree(wD)
            wD = None
            if workingDirectory:
                wD = self.test_vector+"/cropMixSampler_bindingsTMP"
                os.mkdir(wD)
            return testPath, featuresNonAnnualOutputs, featuresAnnualOutputs, wD

        def generate_annual_config(directory, annualFeaturesPath, features_A_Outputs):
            
            config_path = os.path.join(iota2dir, "config",
                                   "Config_4Tuiles_Multi_FUS_Confidence.cfg")
            annual_config_path = os.path.join(directory, "AnnualConfig.cfg")
            shutil.copy(config_path, annual_config_path)
            cfg = Config(file(annual_config_path))
            cfg.chain.listTile = 'D0005H0002'
            cfg.chain.L8Path = annualFeaturesPath
            cfg.chain.featuresPath = features_A_Outputs
            cfg.chain.userFeatPath = 'None'
            cfg.GlobChain.annualClassesExtractionSource = 'False'
            cfg.GlobChain.useAdditionalFeatures = False
            cfg.save(file(annual_config_path, 'w'))
            
            return annual_config_path

        import serviceConfigFile as SCF
        
        featuresPath = iota2_dataTest+"/references/features/"
        sensorData = iota2_dataTest+"/L8_50x50"
        reference = iota2_dataTest+"/references/sampler/D0005H0002_polygons_To_Sample_Samples_CropMix_bindings.sqlite"
        
        #prepare outputs test folders
        testPath, features_NA_Outputs, features_A_Outputs, wD = prepareTestsFolder(True)
        annualFeaturesPath = testPath+"/annualFeatures"

        #prepare annual configuration file
        annual_config_path = generate_annual_config(wD, annualFeaturesPath, features_A_Outputs)

        testPath, features_NA_Outputs, features_A_Outputs, wD = prepareTestsFolder(True)

        #Prepare tests env
        import serviceConfigFile as SCF
        # load configuration file
        SCF.clearConfig()

        config_path = os.path.join(self.iota2_directory, "config",
                                   "Config_4Tuiles_Multi_FUS_Confidence.cfg")
        self.config = SCF.serviceConfigFile(config_path)

        L8_rasters_non_annual = os.path.join(self.iota2_directory, "data", "L8_50x50")
        L8_rasters_annual = os.path.join(wD, "annualData")
        os.mkdir(L8_rasters_annual)

        #annual sensor data generation (pix annual = 2 * pix non_annual)
        prepareAnnualFeatures(L8_rasters_annual, L8_rasters_non_annual, "CORR_PENTE",
                              rename=("2016", "2015"))
        #prepare annual configuration file
        annual_config_path = os.path.join(wD, "AnnualConfig.cfg")
        shutil.copy(self.config.pathConf, annual_config_path)

        cfg = Config(file(annual_config_path))
        cfg.chain.listTile = 'D0005H0002'
        cfg.chain.L8Path = L8_rasters_annual
        cfg.chain.featuresPath = features_A_Outputs
        cfg.chain.userFeatPath = 'None'
        cfg.GlobChain.useAdditionalFeatures = False
        cfg.save(file(annual_config_path, 'w'))

        #fill up configuration file
        """
        TEST
        using a working directory and write temporary files on disk
        """
        #fill up configuration file
        self.config.setParam('chain', 'outputPath', testPath)
        self.config.setParam('chain', 'listTile', "D0005H0002")
        self.config.setParam('chain', 'featuresPath', features_NA_Outputs)
        self.config.setParam('chain', 'L8Path', L8_rasters_non_annual)
        self.config.setParam('chain', 'userFeatPath', 'None')
        self.config.setParam('argTrain', 'cropMix', True)
        self.config.setParam('argTrain', 'prevFeatures', annual_config_path)
        self.config.setParam('argTrain', 'outputPrevFeatures', features_A_Outputs)
        self.config.setParam('argTrain', 'samplesClassifMix', False)
        self.config.setParam('GlobChain', 'useAdditionalFeatures', False)
        self.config.setParam('GlobChain', 'writeOutputs', True)

        #Launch sampler
        vectorSampler.generateSamples(self.referenceShape_test, None,
                                      self.config, sampleSelection=self.selection_test)
        
        #compare to reference
        test_vector = fu.fileSearchRegEx(testPath + "/learningSamples/*sqlite")[0]
        delete_uselessFields(test_vector)
        compare = compareSQLite(test_vector, reference, CmpMode='coordinates', ignored_fields=["originfid"])
        self.assertTrue(compare)

        """
        TEST
        using a working directory and without temporary files
        """
        self.config.setParam('GlobChain', 'writeOutputs', False)
        testPath, features_NA_Outputs, features_A_Outputs, wD = prepareTestsFolder(True)
        #annual sensor data generation (pix annual = 2 * pix non_annual)
        os.mkdir(L8_rasters_annual)
        prepareAnnualFeatures(L8_rasters_annual, L8_rasters_non_annual, "CORR_PENTE",
                              rename=("2016", "2015"))
        #prepare annual configuration file
        annual_config_path = os.path.join(wD, "AnnualConfig.cfg")
        shutil.copy(self.config.pathConf, annual_config_path)

        cfg = Config(file(annual_config_path))
        cfg.chain.listTile = 'D0005H0002'
        cfg.chain.L8Path = L8_rasters_annual
        cfg.chain.featuresPath = features_A_Outputs
        cfg.chain.userFeatPath = 'None'
        cfg.GlobChain.useAdditionalFeatures = False
        cfg.save(file(annual_config_path, 'w'))
        
        #Launch sampler
        vectorSampler.generateSamples(self.referenceShape_test, wD, self.config, sampleSelection=self.selection_test)

        test_vector = fu.fileSearchRegEx(testPath + "/learningSamples/*sqlite")[0]
        delete_uselessFields(test_vector)
        compare = compareSQLite(test_vector, reference, CmpMode='coordinates', ignored_fields=["originfid"])
        self.assertTrue(compare)
        
        """
        TEST
        without a working directory and without temporary files on disk
        """
        
        testPath, features_NA_Outputs, features_A_Outputs, wD = prepareTestsFolder(True)
        #annual sensor data generation (pix annual = 2 * pix non_annual)
        os.mkdir(L8_rasters_annual)
        prepareAnnualFeatures(L8_rasters_annual, L8_rasters_non_annual, "CORR_PENTE",
                              rename=("2016", "2015"))
        #prepare annual configuration file
        annual_config_path = os.path.join(wD, "AnnualConfig.cfg")
        shutil.copy(self.config.pathConf, annual_config_path)

        cfg = Config(file(annual_config_path))
        cfg.chain.listTile = 'D0005H0002'
        cfg.chain.L8Path = L8_rasters_annual
        cfg.chain.featuresPath = features_A_Outputs
        cfg.chain.userFeatPath = 'None'
        cfg.GlobChain.useAdditionalFeatures = False
        cfg.save(file(annual_config_path, 'w'))
        
        #Launch sampler
        vectorTest = vectorSampler.generateSamples(self.referenceShape_test, None,
                                                   self.config, sampleSelection=self.selection_test)

        test_vector = fu.fileSearchRegEx(testPath + "/learningSamples/*sqlite")[0]
        delete_uselessFields(test_vector)
        compare = compareSQLite(test_vector, reference, CmpMode='coordinates', ignored_fields=["originfid"])
        self.assertTrue(compare)
        
        """
        TEST
        without a working directory and write temporary files on disk
        """
        self.config.setParam('GlobChain', 'writeOutputs', True)
        testPath, features_NA_Outputs, features_A_Outputs, wD = prepareTestsFolder(True)
        
        #annual sensor data generation (pix annual = 2 * pix non_annual)
        os.mkdir(L8_rasters_annual)
        prepareAnnualFeatures(L8_rasters_annual, L8_rasters_non_annual, "CORR_PENTE",
                              rename=("2016", "2015"))
        #prepare annual configuration file
        annual_config_path = os.path.join(wD, "AnnualConfig.cfg")
        shutil.copy(self.config.pathConf, annual_config_path)

        cfg = Config(file(annual_config_path))
        cfg.chain.listTile = 'D0005H0002'
        cfg.chain.L8Path = L8_rasters_annual
        cfg.chain.featuresPath = features_A_Outputs
        cfg.chain.userFeatPath = 'None'
        cfg.GlobChain.useAdditionalFeatures = False
        cfg.save(file(annual_config_path, 'w'))

        #Launch Sampling
        vectorSampler.generateSamples(self.referenceShape_test, None, self.config, sampleSelection=self.selection_test)
        
        #Compare vector produce to reference
        test_vector = fu.fileSearchRegEx(testPath + "/learningSamples/*sqlite")[0]
        delete_uselessFields(test_vector)
        compare = compareSQLite(test_vector, reference, CmpMode='coordinates', ignored_fields=["originfid"])
        self.assertTrue(compare)


    def test_samplerClassifCropMix_bindings(self):
        """
        TEST cropMix 2 algorithm

        Step 1 : on non Annual classes, select samples
        Step 2 : select randomly annual samples into a provided land cover map.
        Step 3 : merge samples from step 1 and 2
        Step 4 : Compute feature to samples.

        random part in this script could not be control, no reference vector can be done.
        Only number of features can be check.
        """
        import serviceConfigFile as SCF
        import tileEnvelope as env
        import tileArea as area
        import createRegionsByTiles as RT

        def prepareTestsFolder(workingDirectory=False):
            wD = None
            testPath = self.test_vector+"/classifCropMixSampler_bindings/"

            if os.path.exists(testPath):
                shutil.rmtree(testPath)
            os.mkdir(testPath)

            featuresOutputs = self.test_vector+"/classifCropMixSampler_features_bindings"
            if os.path.exists(featuresOutputs):
                shutil.rmtree(featuresOutputs)
            os.mkdir(featuresOutputs)

            if workingDirectory:
                wD = self.test_vector+"/classifCropMixSampler_bindingsTMP"
                if os.path.exists(wD):
                    shutil.rmtree(wD)
                os.mkdir(wD)
            return testPath, featuresOutputs, wD

        L8_rasters = os.path.join(self.iota2_directory, "data", "L8_50x50")
        classifications_path = os.path.join(self.iota2_directory, "data",
                                            "references", "sampler")

        testPath, featuresOutputs, wD = prepareTestsFolder(True)

        #rename reference shape
        vector = shapeReferenceVector(self.referenceShape, "D0005H0002")

        # load configuration file
        SCF.clearConfig()
        config_path = os.path.join(self.iota2_directory, "config",
                                   "Config_4Tuiles_Multi_FUS_Confidence.cfg")
        self.config = SCF.serviceConfigFile(config_path)
        #fill up configuration file
        self.config.setParam('chain', 'outputPath', testPath)
        self.config.setParam('chain', 'listTile', "D0005H0002")
        self.config.setParam('chain', 'featuresPath', featuresOutputs)
        self.config.setParam('chain', 'L8Path', L8_rasters)
        self.config.setParam('chain', 'userFeatPath', 'None')
        self.config.setParam('argTrain', 'cropMix', True)
        self.config.setParam('argTrain', 'samplesClassifMix', True)
        self.config.setParam('argTrain', 'annualClassesExtractionSource', classifications_path)
        self.config.setParam('GlobChain', 'useAdditionalFeatures', False)

        """
        TEST
        with a working directory and with temporary files on disk
        """
        #generate IOTA output directory
        oso_directory.GenerateDirectories(self.config)

        #shapes genereation
        fu.getCommonMasks("D0005H0002", self.config, None)
        env.GenerateShapeTile(["D0005H0002"], wD, testPath + "/envelope", None, self.config)
        shapeRegion = os.path.join(wD, "MyFakeRegion.shp")
        area.generateRegionShape("one_region", testPath + "/envelope", "", shapeRegion, "region", self.config, None)
        RT.createRegionsByTiles(shapeRegion, "region", testPath + "/envelope", testPath + "/shapeRegion/", None)

        #launch sampling
        addField(vector, "region", "1", str)
        vectorSampler.generateSamples(vector, wD, self.config, sampleSelection=self.selection_test)
        test_vector = fu.fileSearchRegEx(testPath + "/learningSamples/*sqlite")[0]
        
        same = []
        for key, val in self.expectedFeatures.iteritems():
            if len(fu.getFieldElement(test_vector, 'SQLite', 'code', 'all')) != self.expectedFeatures[key]:
                same.append(True)
            else:
                same.append(False)

        if False in same:
            self.assertTrue(False)
        else:
            self.assertTrue(True)

        """
        TEST
        with a working directory and without temporary files on disk
        """
        testPath, featuresOutputs, wD = prepareTestsFolder(True)

        #generate IOTA output directory
        oso_directory.GenerateDirectories(self.config)

        #shapes genereation
        vector = shapeReferenceVector(self.referenceShape, "D0005H0002")
        fu.getCommonMasks("D0005H0002", self.config, None)
        env.GenerateShapeTile(["D0005H0002"], wD, testPath + "/envelope", None, self.config)
        shapeRegion = os.path.join(wD, "MyFakeRegion.shp")
        area.generateRegionShape("one_region", testPath + "/envelope", "", shapeRegion, "region", self.config, None)
        RT.createRegionsByTiles(shapeRegion, "region", testPath + "/envelope", testPath + "/shapeRegion/", None)

        addField(vector, "region", "1", str)
        vectorSampler.generateSamples(vector, wD, self.config, sampleSelection=self.selection_test)
        
        test_vector = fu.fileSearchRegEx(testPath + "/learningSamples/*sqlite")[0]
        same = []
        for key, val in self.expectedFeatures.iteritems():
            if len(fu.getFieldElement(test_vector, 'SQLite', 'code', 'all')) != self.expectedFeatures[key]:
                same.append(True)
            else:
                same.append(False)

        if False in same:
            self.assertTrue(False)
        else:
            self.assertTrue(True)

        """
        TEST
        without a working directory and without temporary files on disk
        """
        testPath, featuresOutputs, wD = prepareTestsFolder(True)

        #generate IOTA output directory
        oso_directory.GenerateDirectories(self.config)

        #shapes genereation
        vector = shapeReferenceVector(self.referenceShape, "D0005H0002")
        fu.getCommonMasks("D0005H0002", self.config, None)
        env.GenerateShapeTile(["D0005H0002"], wD, testPath + "/envelope", None, self.config)
        shapeRegion = os.path.join(wD, "MyFakeRegion.shp")
        area.generateRegionShape("one_region", testPath + "/envelope", "", shapeRegion, "region", self.config, None)
        RT.createRegionsByTiles(shapeRegion, "region", testPath + "/envelope", testPath + "/shapeRegion/", None)

        addField(vector, "region", "1", str)
        vectorSampler.generateSamples(vector, None, self.config, sampleSelection=self.selection_test)
        
        test_vector = fu.fileSearchRegEx(testPath + "/learningSamples/*sqlite")[0]
        same = []
        for key, val in self.expectedFeatures.iteritems():
            if len(fu.getFieldElement(test_vector, 'SQLite', 'code', 'all')) != self.expectedFeatures[key]:
                same.append(True)
            else:
                same.append(False)

        if False in same:
            self.assertTrue(False)
        else:
            self.assertTrue(True)
        
        """
        TEST
        without a working directory and with temporary files on disk
        """
        self.config.setParam('GlobChain', 'writeOutputs', True)
        testPath, featuresOutputs, wD = prepareTestsFolder(True)

        #generate IOTA output directory
        oso_directory.GenerateDirectories(self.config)

        #shapes genereation
        vector = shapeReferenceVector(self.referenceShape, "D0005H0002")
        fu.getCommonMasks("D0005H0002", self.config, None)
        env.GenerateShapeTile(["D0005H0002"], wD, testPath + "/envelope", None, self.config)
        shapeRegion = os.path.join(wD, "MyFakeRegion.shp")
        area.generateRegionShape("one_region", testPath + "/envelope", "", shapeRegion, "region", self.config, None)
        RT.createRegionsByTiles(shapeRegion, "region", testPath + "/envelope", testPath + "/shapeRegion/", None)

        addField(vector, "region", "1", str)
        vectorSampler.generateSamples(vector, None, self.config, sampleSelection=self.selection_test)
        
        test_vector = fu.fileSearchRegEx(testPath + "/learningSamples/*sqlite")[0]
        same = []
        for key, val in self.expectedFeatures.iteritems():
            if len(fu.getFieldElement(test_vector, 'SQLite', 'code', 'all')) != self.expectedFeatures[key]:
                same.append(True)
            else:
                same.append(False)

        if False in same:
            self.assertTrue(False)
        else:
            self.assertTrue(True)


class iota_testShapeManipulations(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.referenceShape = iota2_dataTest + "/references/D5H2_groundTruth_samples.shp"
        self.nbFeatures = 28
        self.fields = ['ID', 'LC', 'CODE', 'AREA_HA']
        self.dataField = 'CODE'
        self.epsg = 2154
        self.typeShape = iota2_dataTest + "/references/typo.shp"
        self.regionField = "DN"

        self.priorityEnvelope_ref = iota2_dataTest+"/references/priority_ref"
        self.splitRatio = 0.5

        self.test_vector = iota2_dataTest+"/test_vector"
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)

    def test_CountFeatures(self):
        features = fu.getFieldElement(self.referenceShape, driverName="ESRI Shapefile",
                                      field="CODE", mode="all", elemType="int")
        self.assertTrue(len(features) == self.nbFeatures)

    def test_MultiPolygons(self):
        detectMulti = fu.multiSearch(self.referenceShape)
        single = iota2_dataTest+"/test_MultiToSinglePoly.shp"
        fu.multiPolyToPoly(self.referenceShape, single)

        detectNoMulti = fu.multiSearch(single)
        self.assertTrue(detectMulti)
        self.assertFalse(detectNoMulti)

        testFiles = fu.fileSearchRegEx(iota2_dataTest+"/test_*")

        for testFile in testFiles:
            if os.path.isfile(testFile):
                os.remove(testFile)

    def test_getField(self):
        allFields = fu.getAllFieldsInShape(self.referenceShape, "ESRI Shapefile")
        self.assertTrue(self.fields == allFields)

    def test_Envelope(self):
        import fileUtils as fut
        self.test_envelopeDir = iota2_dataTest + "/test_vector/test_envelope"
        if os.path.exists(self.test_envelopeDir):
            shutil.rmtree(self.test_envelopeDir)
        os.mkdir(self.test_envelopeDir)

        self.priorityEnvelope_test = self.test_envelopeDir + "/priority_test"
        if os.path.exists(self.priorityEnvelope_test):
            shutil.rmtree(self.priorityEnvelope_test)
        os.mkdir(self.priorityEnvelope_test)

        #Create a 3x3 grid (9 vectors shapes). Each tile are 110.010 km with 10 km overlaping to fit L8 datas.
        test_genGrid.genGrid(self.test_envelopeDir, X=3, Y=3, overlap=10,
                             size=110.010, raster="True", pixSize=30)

        tilesPath = fu.fileSearchRegEx(self.test_envelopeDir+"/*.tif")

        ObjListTile = [tileEnvelope.Tile(currentTile, currentTile.split("/")[-1].split(".")[0].split("_")[0]) for currentTile in tilesPath]
        ObjListTile_sort = sorted(ObjListTile, key=tileEnvelope.priorityKey)

        tileEnvelope.genTileEnvPrio(ObjListTile_sort, self.priorityEnvelope_test,
                                    self.priorityEnvelope_test, self.epsg)

        envRef = fu.fileSearchRegEx(self.priorityEnvelope_ref+"/*.shp")

        comp = []
        for eRef in envRef:
            tile_number = os.path.split(eRef)[-1].split("_")[1]
            comp.append(fut.FileSearch_AND(self.priorityEnvelope_test, True, "Tile"+tile_number+"_PRIO.shp")[0])


        cmpEnv = [checkSameEnvelope(currentRef, test_env) for currentRef,test_env in zip(envRef,comp)]
        self.assertTrue(all(cmpEnv))

    def test_regionsByTile(self):

        self.test_regionsByTiles = iota2_dataTest+"/test_vector/test_regionsByTiles"
        if os.path.exists(self.test_regionsByTiles):
            shutil.rmtree(self.test_regionsByTiles)
        os.mkdir(self.test_regionsByTiles)

        createRegionsByTiles.createRegionsByTiles(self.typeShape,
                                                  self.regionField,
                                                  self.priorityEnvelope_ref,
                                                  self.test_regionsByTiles, None)

    def test_SplitVector(self):

        self.test_split = iota2_dataTest+"/test_vector/test_splitVector"
        if os.path.exists(self.test_split):
            shutil.rmtree(self.test_split)
        os.mkdir(self.test_split)

        AllTrain, AllValid = RandomInSituByTile.RandomInSituByTile(self.referenceShape,
                                                                   self.dataField, 1,
                                                                   self.test_split,
                                                                   self.splitRatio,
                                                                   None,
                                                                   None,
                                                                   test=True)

        featuresTrain = fu.getFieldElement(AllTrain[0], driverName="ESRI Shapefile",
                                           field="CODE", mode="all",
                                           elemType="int")
        self.assertTrue(len(featuresTrain) == self.nbFeatures*self.splitRatio)

        featuresValid = fu.getFieldElement(AllValid[0], driverName="ESRI Shapefile",
                                           field="CODE", mode="all",
                                           elemType="int")
        self.assertTrue(len(featuresValid) == self.nbFeatures*(1-self.splitRatio))

class iota_testServiceConfigFile(unittest.TestCase):

#TODO : ajouter un test pour les valeurs par défaut
    
    @classmethod
    def setUpClass(self):
        # List of different config files
        self.fichierConfig = iota2_dataTest+"/config/test_config_serviceConfigFile.cfg"
        self.fichierConfigBad1 = iota2_dataTest+"/config/test_config_serviceConfigFileBad1.cfg"
        self.fichierConfigBad2 = iota2_dataTest+"/config/test_config_serviceConfigFileBad2.cfg"
        self.fichierConfigBad3 = iota2_dataTest+"/config/test_config_serviceConfigFileBad3.cfg"

    def test_initConfigFile(self):

        # the class is instantiated with self.fichierConfig config file
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'runs', 2)
        cfg.setParam('chain', 'featuresPath', '../../data/references/features')
        cfg.setParam('chain', 'regionPath', '../../data/references/region_need_To_env.shp')
        cfg.setParam('chain', 'regionField', 'DN')
        cfg.setParam('chain', 'mode', 'one_region')
        cfg.setParam('argClassification', 'classifMode', 'separate')

        # we check the config file
        self.assertTrue(cfg.checkConfigParameters())
        
        # we get outputPath variable
        self.assertEqual(cfg.getParam('chain', 'outputPath'), '../../data/test_vector')
        
        # we check if bad section is detected
        self.assertRaises(Exception, cfg.getParam,'BADchain', 'outputPath')

        # we check if bad param is detected
        self.assertRaises(Exception, cfg.getParam, 'chain', 'BADoutputPath') 

            
    def test_initConfigFileBad1(self):

        # the class is instantiated with self.fichierConfigBad1 config file
        # A mandatory variable is missing
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfigBad1)
        # we check if the bad config file is detected
        self.assertRaises(Exception, cfg.checkConfigParameters)

    def test_initConfigFileBad2(self):

        # the class is instantiated with self.fichierConfigBad2 config file
        # Bad type of variable
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfigBad2)
        # we check if the bad config file is detected
        self.assertRaises(Exception, cfg.checkConfigParameters)

    def test_initConfigFileBad3(self):

        # the class is instantiated with self.fichierConfigBad3 config file
        # Bad value in a variable
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfigBad3)
        # we check if the bad config file is detected
        self.assertRaises(Exception, cfg.checkConfigParameters)


# test ok
class iota_testGenerateShapeTile(unittest.TestCase):
    
    @classmethod
    def setUpClass(self):
        # Test variables
        self.fichierConfig = iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"
        self.tiles = ['D0005H0002'] #, 'D0005H0003']
        self.pathTilesFeat = iota2_dataTest + "/references/features/"
        self.test_vector = iota2_dataTest + "/test_vector/"
        self.pathEnvelope = iota2_dataTest + "/test_vector/test_GenerateShapeTile/"
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)
        if not os.path.exists(self.pathEnvelope):
            os.mkdir(self.pathEnvelope)

    def test_GenerateShapeTile(self):
        import tileEnvelope as env
        
        #Test de création des enveloppes
        print "tiles: " + str(self.tiles)
        print "pathTilesFeat: " + self.pathTilesFeat
        print "pathEnvelope: " + self.pathEnvelope
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'featuresPath', '../../data/references/features')
        # Launch function
        env.GenerateShapeTile(self.tiles, self.pathTilesFeat, self.pathEnvelope, None, cfg)
        
        # For each tile test if the shapefile is ok
        for i in self.tiles:
            # generate filename
            referenceShapeFile = iota2_dataTest + "/references/GenerateShapeTile/" + i + ".shp"
            ShapeFile = self.pathEnvelope + i + ".shp"
            serviceCompareVectorFile = fu.serviceCompareVectorFile()
            # Launch shapefile comparison
            self.assertTrue(serviceCompareVectorFile.testSameShapefiles(referenceShapeFile, ShapeFile))

# test ok
class iota_testGenerateRegionShape(unittest.TestCase):
    
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.fichierConfig = iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"
        self.test_vector = iota2_dataTest + "/test_vector/"
        self.pathOut = iota2_dataTest + "/test_vector/test_GenerateRegionShape/"
        self.pathEnvelope = iota2_dataTest + "/references/GenerateShapeTile/"
        self.MODE = 'one_region'
        self.model = ''
        self.shapeRegion = self.pathOut + 'region_need_To_env.shp'
        self.field_Region = 'DN'
        
        # test and creation of test_vector
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)
        # test and creation of pathOut
        if not os.path.exists(self.pathOut):
            os.mkdir(self.pathOut)

    def test_GenerateRegionShape(self):
        import tileArea as area
        
        print "MODE: " + str(self.MODE)
        print "pathEnvelope: " + self.pathEnvelope
        print "model: " + self.model
        print "shapeRegion: " + self.shapeRegion        
        print "field_Region: " + self.field_Region
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        
        area.generateRegionShape(self.MODE, self.pathEnvelope, self.model, 
                                 self.shapeRegion, self.field_Region, cfg, None)

        # generate filename
        referenceShapeFile = iota2_dataTest + "references/GenerateRegionShape/region_need_To_env.shp"
        ShapeFile = self.pathOut + "region_need_To_env.shp"
        serviceCompareVectorFile = fu.serviceCompareVectorFile()
        # Launch shapefile comparison
        self.assertTrue(serviceCompareVectorFile.testSameShapefiles(referenceShapeFile, ShapeFile))

        
# test ok
class iota_testLaunchTraining(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.fichierConfig = iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"
        self.test_vector = iota2_dataTest + "/test_vector/"
        self.pathOut = iota2_dataTest + "/test_vector/test_LaunchTraining/"
        self.pathAppVal = self.pathOut + "/dataAppVal"
        self.pathTilesFeat = iota2_dataTest + "/references/features/"
        self.refData = iota2_dataTest + "/references/LaunchTraining/"
        self.pathStats = self.pathOut + "/stats"
        self.cmdPath = self.pathOut + "/cmd"
        self.pathModels = self.pathOut + "/model"
        self.pathConfigModels = self.pathOut + "/config_model"
        self.pathLearningSamples = self.pathOut + "/learningSamples"
        self.pathFormattingSamples = self.pathOut + "/formattingVectors"
        self.vector_formatting = self.refData + "/Input/D0005H0002.shp"
#        self.vector_formatting = iota2_dataTest + "/references/sampler/D0005H0002.shp"

        # test and creation of test_vector
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)
        # test and creation of pathOut
        if not os.path.exists(self.pathOut):
            os.mkdir(self.pathOut)
        else:
            shutil.rmtree(self.pathOut)
            os.mkdir(self.pathOut)
        # test and creation of pathAppVal
        if not os.path.exists(self.pathAppVal):
            os.mkdir(self.pathAppVal)
        # test and creation of pathStats
        if not os.path.exists(self.pathStats):
            os.mkdir(self.pathStats)
        # test and creation of cmdPath
        if not os.path.exists(self.cmdPath):
            os.mkdir(self.cmdPath)
        # test and creation of cmdPath
        if not os.path.exists(self.cmdPath + "/train"):
            os.mkdir(self.cmdPath + "/train")
        # test and creation of pathModels
        if not os.path.exists(self.pathModels):
            os.mkdir(self.pathModels)
        # test and creation of pathConfigModels
        if not os.path.exists(self.pathConfigModels):
            os.mkdir(self.pathConfigModels)
        # test and creation of pathLearningSamples
        if not os.path.exists(self.pathLearningSamples):
            os.mkdir(self.pathLearningSamples)
        if not os.path.exists(self.pathFormattingSamples):
            os.mkdir(self.pathFormattingSamples)
        # copy input data
        fu.cpShapeFile(self.vector_formatting.replace(".shp",""),
                       self.pathFormattingSamples, [".prj",".shp",".dbf",".shx"],
                       spe=True)
            
        src_files = os.listdir(self.refData + "/Input/learningSamples")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/learningSamples", file_name)
            shutil.copy(full_file_name, self.pathLearningSamples)


    def test_LaunchTraining(self):
        import LaunchTraining as LT 
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        dataField = 'CODE'
        N = 1
        cfg.setParam('chain', 'outputPath', self.pathOut)
        cfg.setParam('chain', 'regionField', "region")

        LT.launchTraining(self.pathAppVal, cfg, self.pathTilesFeat, dataField,
                self.pathStats, N, self.cmdPath + "/train", self.pathModels,
                None, None)

        # file comparison to ref file
        File1 = self.cmdPath + "/train/train.txt"
        self.assertTrue(os.path.getsize(File1) > 0)
        File2 = self.pathConfigModels + "/configModel.cfg"
        referenceFile2 = self.refData + "/Output/configModel.cfg"

        self.assertTrue(filecmp.cmp(File2, referenceFile2))


class iota_testLaunchClassification(unittest.TestCase):
# Test ok
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.fichierConfig = iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"
        self.test_vector = iota2_dataTest + "/test_vector/"
        self.pathOut = iota2_dataTest + "/test_vector/test_LaunchClassification/"
        self.shapeRegion = iota2_dataTest + "/references/GenerateRegionShape/region_need_To_env.shp"
        self.pathTileRegion = self.pathOut + "/shapeRegion/"
        self.pathTilesFeat = iota2_dataTest + "/references/features/"
        self.pathStats = self.pathOut + "/stats"
        self.cmdPath = self.pathOut + "/cmd"
        self.pathModels = self.pathOut + "/model"
        self.pathConfigModels = self.pathOut + "/config_model"
        self.pathClassif = self.pathOut + "/Classif"
        self.refData = iota2_dataTest + "/references/LaunchClassification/"

        # test and creation of test_vector
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)
        # test and creation of pathOut
        if not os.path.exists(self.pathOut):
            os.mkdir(self.pathOut)
        else:
            shutil.rmtree(self.pathOut)
            os.mkdir(self.pathOut)
        # test and creation of pathTileRegion
        if not os.path.exists(self.pathTileRegion):
            os.mkdir(self.pathTileRegion)
        # test and creation of pathTilesFeat
        if not os.path.exists(self.pathTilesFeat):
            os.mkdir(self.pathTilesFeat)
        # test and creation of pathStats
        if not os.path.exists(self.pathStats):
            os.mkdir(self.pathStats)
        # test and creation of cmdPath
        if not os.path.exists(self.cmdPath):
            os.mkdir(self.cmdPath)
        # test and creation of cmdPath
        if not os.path.exists(self.cmdPath + "/cla"):
            os.mkdir(self.cmdPath + "/cla")
        # test and creation of pathModels
        if not os.path.exists(self.pathModels):
            os.mkdir(self.pathModels)
        # test and creation of pathConfigModels
        if not os.path.exists(self.pathConfigModels):
            os.mkdir(self.pathConfigModels)
        # test and creation of pathClassif
        if not os.path.exists(self.pathClassif):
            os.mkdir(self.pathClassif)
        if not os.path.exists(self.pathClassif + "/MASK"):
            os.mkdir(self.pathClassif + "/MASK")
            
        # copy input data
        shutil.copy(self.refData + "/Input/configModel.cfg", self.pathConfigModels)
        shutil.copy(self.refData + "/Input/model_1_seed_0.txt", self.pathModels)
        src_files = os.listdir(self.refData + "/Input/shapeRegion")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/shapeRegion", file_name)
            shutil.copy(full_file_name, self.pathTileRegion)
        src_files = os.listdir(self.refData + "/Input/Classif/MASK")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/Classif/MASK", file_name)
            shutil.copy(full_file_name, self.pathClassif + "/MASK")



    def test_LaunchClassification(self):
        import launchClassification as LC
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'outputPath', self.pathOut)
        field_Region = cfg.getParam('chain', 'regionField')
        N = 1
        LC.launchClassification(self.pathModels, cfg, self.pathStats, 
                      self.pathTileRegion, self.pathTilesFeat,
                      self.shapeRegion, field_Region,
                      N, self.cmdPath+"/cla", self.pathClassif, None)
        
        # file comparison to ref file
        File1 = self.cmdPath + "/cla/class.txt"
        self.assertTrue(os.path.getsize(File1) > 0)

class iota_testVectorSamplesMerge(unittest.TestCase):
# Test ok
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.fichierConfig = iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"
        self.test_vector = iota2_dataTest + "/test_vector/"
        self.pathOut = iota2_dataTest + "/test_vector/test_VectorSamplesMerge/"
        self.learningSamples = self.pathOut + "/learningSamples/"
        self.cmdPath = self.pathOut + "/cmd"
        self.refData = iota2_dataTest + "/references/VectorSamplesMerge/"
        
        # test and creation of test_vector
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)
        # test and creation of pathOut
        if not os.path.exists(self.pathOut):
            os.mkdir(self.pathOut)
        else:
            shutil.rmtree(self.pathOut)
            os.mkdir(self.pathOut)
        # test and creation of learningSamples
        if not os.path.exists(self.learningSamples):
            os.mkdir(self.learningSamples)
        # test and creation of cmdPath
        if not os.path.exists(self.cmdPath):
            os.mkdir(self.cmdPath)

        # copy input data
        shutil.copy(self.refData + "/Input/D0005H0003_region_1_seed0_learn_Samples.sqlite", self.learningSamples)


    def test_VectorSamplesMerge(self):
        import vectorSamplesMerge as VSM
        import vectorSampler as vs
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'outputPath', self.pathOut)

        vl = fu.FileSearch_AND(self.learningSamples, True, ".sqlite")
        VSM.vectorSamplesMerge(cfg, vl)

        # file comparison to ref file
        File1 = self.learningSamples + "Samples_region_1_seed0_learn.sqlite"
        referenceFile1 = self.refData + "/Output/Samples_region_1_seed0_learn.sqlite"
        self.assertTrue(compareSQLite(File1, referenceFile1, CmpMode='coordinates', ignored_fields=[]))


class iota_testFusion(unittest.TestCase):
# Même problématique que ci-dessous
# Problème dans la préparation des données d'entrée
# Voir avec Arthur.
#
# FUS.fusion(pathClassif, cfg, None)
#
# TODO A terminer
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.fichierConfig = iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"
        self.test_vector = iota2_dataTest + "/test_vector/"
        self.pathOut = iota2_dataTest + "/test_vector/test_Fusion/"
        self.pathTilesFeat = iota2_dataTest + "/references/features/"
        self.shapeRegion = iota2_dataTest + "/references/GenerateRegionShape/region_need_To_env.shp"
        self.pathClassif = self.pathOut + "/classif"
        self.classifFinal = self.pathOut + "/final"
        self.refData = iota2_dataTest + "/references/Fusion/"
        self.cmdPath = self.pathOut + "/cmd"
        
        # test and creation of test_vector
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)
        # test and creation of pathOut
        if not os.path.exists(self.pathOut):
            os.mkdir(self.pathOut)
        else:
            shutil.rmtree(self.pathOut)
            os.mkdir(self.pathOut)
        # test and creation of pathClassif
        if not os.path.exists(self.pathClassif):
            os.mkdir(self.pathClassif)
        if not os.path.exists(self.pathClassif + "/MASK"):
            os.mkdir(self.pathClassif + "/MASK")
        if not os.path.exists(self.pathClassif + "/tmpClassif"):
            os.mkdir(self.pathClassif + "/tmpClassif")
        # test and creation of classifFinal
        if not os.path.exists(self.classifFinal):
            os.mkdir(self.classifFinal)
        # test and creation of cmdPath
        if not os.path.exists(self.cmdPath):
            os.mkdir(self.cmdPath)
        if not os.path.exists(self.cmdPath + "/fusion"):
            os.mkdir(self.cmdPath + "/fusion")

        src_files = os.listdir(self.refData + "/Input/Classif/MASK")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/Classif/MASK", file_name)
            shutil.copy(full_file_name, self.pathClassif + "/MASK")

        src_files = os.listdir(self.refData + "/Input/Classif/classif")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/Classif/classif/", file_name)
            shutil.copy(full_file_name, self.pathClassif)
    
    def test_Fusion(self):
        import fusion as FUS
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'outputPath', self.pathOut)
        cfg.setParam('argClassification', 'classifMode', 'fusion')
        
        field_Region = cfg.getParam('chain', 'regionField')
        N = 1
        
        cmdFus = FUS.fusion(self.pathClassif, cfg, None)



class iota_testNoData(unittest.TestCase):
# Problème dans la génération des données pour le test ci-dessous.
# A voir avec Arthur pour savoir comment générer la donnée adéquat pour réellement tester
# la fonction
# TODO A terminer
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.fichierConfig = iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"
        self.test_vector = iota2_dataTest + "/test_vector/"
        self.pathOut = iota2_dataTest + "/test_vector/test_NoData/"
        self.pathTilesFeat = iota2_dataTest + "/references/features/"
        self.shapeRegion = iota2_dataTest + "/references/GenerateRegionShape/region_need_To_env.shp"
        self.pathClassif = self.pathOut + "/classif"
        self.classifFinal = self.pathOut + "/final"
        self.refData = iota2_dataTest + "/references/NoData/"
        self.cmdPath = self.pathOut + "/cmd"
        
        # test and creation of test_vector
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)
        # test and creation of pathOut
        if not os.path.exists(self.pathOut):
            os.mkdir(self.pathOut)
        else:
            shutil.rmtree(self.pathOut)
            os.mkdir(self.pathOut)
        # test and creation of pathClassif
        if not os.path.exists(self.pathClassif):
            os.mkdir(self.pathClassif)
        if not os.path.exists(self.pathClassif + "/MASK"):
            os.mkdir(self.pathClassif + "/MASK")
        if not os.path.exists(self.pathClassif + "/tmpClassif"):
            os.mkdir(self.pathClassif + "/tmpClassif")
        # test and creation of classifFinal
        if not os.path.exists(self.classifFinal):
            os.mkdir(self.classifFinal)
        # test and creation of cmdPath
        if not os.path.exists(self.cmdPath):
            os.mkdir(self.cmdPath)
        if not os.path.exists(self.cmdPath + "/fusion"):
            os.mkdir(self.cmdPath + "/fusion")

        src_files = os.listdir(self.refData + "/Input/Classif/MASK")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/Classif/MASK", file_name)
            shutil.copy(full_file_name, self.pathClassif + "/MASK")

        src_files = os.listdir(self.refData + "/Input/Classif/classif")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/Classif/classif/", file_name)
            shutil.copy(full_file_name, self.pathClassif)
    
    def test_NoData(self):
        import noData as ND
        import fusion as FUS
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'outputPath', self.pathOut)
        cfg.setParam('argClassification', 'classifMode', 'fusion')
        
        field_Region = cfg.getParam('chain', 'regionField')
        N = 1
        
        cmdFus = FUS.fusion(self.pathClassif, cfg, None)
        for cmd in cmdFus:
            run(cmd)

        fusionFiles = fu.FileSearch_AND(self.pathClassif, True, "_FUSION_")
        print fusionFiles
        for fusionpath in fusionFiles:
            ND.noData(self.pathOut, self.fusionpath, field_Region, 
                      self.pathTilesFeat, self.shapeRegion, N, cfg, None)




class iota_testClassificationShaping(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.fichierConfig = iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"
        self.test_vector = iota2_dataTest + "/test_vector/"
        self.pathOut = iota2_dataTest + "/test_vector/test_ClassificationShaping/"
        self.pathTilesFeat = iota2_dataTest + "/references/features/"
        self.pathEnvelope = self.pathOut + "/envelope"
        self.pathClassif = self.pathOut + "/classif"
        self.classifFinal = self.pathOut + "/final"
        self.refData = iota2_dataTest + "/references/ClassificationShaping/"

        # test and creation of test_vector
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)
        # test and creation of pathOut
        if not os.path.exists(self.pathOut):
            os.mkdir(self.pathOut)
        else:
            shutil.rmtree(self.pathOut)
            os.mkdir(self.pathOut)
        # test and creation of pathClassif
        if not os.path.exists(self.pathClassif):
            os.mkdir(self.pathClassif)
        if not os.path.exists(self.pathClassif + "/MASK"):
            os.mkdir(self.pathClassif + "/MASK")
        if not os.path.exists(self.pathClassif + "/tmpClassif"):
            os.mkdir(self.pathClassif + "/tmpClassif")
        # test and creation of classifFinal
        if not os.path.exists(self.classifFinal):
            os.mkdir(self.classifFinal)

        # copy input file
        src_files = os.listdir(self.refData + "/Input/Classif/MASK")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/Classif/MASK", file_name)
            shutil.copy(full_file_name, self.pathClassif + "/MASK")

        src_files = os.listdir(self.refData + "/Input/Classif/classif")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/Classif/classif/", file_name)
            shutil.copy(full_file_name, self.pathClassif)
    
    def test_ClassificationShaping(self):
        import ClassificationShaping as CS
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'outputPath', self.pathOut)
        cfg.setParam('chain', 'listTile', "D0005H0002")
        cfg.setParam('chain', 'featuresPath', "../../data/references/features")
        cfg.setParam('argClassification', 'classifMode', "separate")
        N = 1
        fieldEnv = "FID"
        COLORTABLE = cfg.getParam('chain', 'colorTable')

        CS.ClassificationShaping(self.pathClassif, self.pathEnvelope, self.pathTilesFeat,
                                 fieldEnv, N, self.classifFinal, None, cfg, 
                                 COLORTABLE)

        # file comparison to ref file
        serviceCompareImageFile = fu.serviceCompareImageFile()
        src_files = os.listdir(self.refData + "/Output/")
        for file_name in src_files:
            File1 = os.path.join(self.classifFinal , file_name)
            referenceFile1 = os.path.join(self.refData + "/Output/", file_name)
            #File1 = self.classifFinal + "/PixelsValidity.tif"
            #referenceFile1 = self.refData + "/Output/PixelsValidity.tif"
            nbDiff = serviceCompareImageFile.gdalFileCompare(File1, referenceFile1)
            print file_name
            print nbDiff
            self.assertEqual(nbDiff, 0)

class iota_testGenConfMatrix(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.fichierConfig = iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"
        self.test_vector = iota2_dataTest + "/test_vector/"
        self.pathOut = iota2_dataTest + "/test_vector/test_GenConfMatrix/"
        self.pathTilesFeat = iota2_dataTest + "/references/features/"
        self.pathEnvelope = self.pathOut + "/envelope"
        self.pathAppVal = self.pathOut + "/dataAppVal"
        self.pathClassif = self.pathOut + "/classif"
        self.Final = self.pathOut + "/final"
        self.refData = iota2_dataTest + "/references/GenConfMatrix/"
        self.cmdPath = self.pathOut + "/cmd"
        
        # test and creation of test_vector
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)
        # test and creation of pathOut
        if not os.path.exists(self.pathOut):
            os.mkdir(self.pathOut)
        else:
            shutil.rmtree(self.pathOut)
            os.mkdir(self.pathOut)
        # test and creation of pathClassif
        if not os.path.exists(self.pathClassif):
            os.mkdir(self.pathClassif)
        if not os.path.exists(self.pathClassif + "/MASK"):
            os.mkdir(self.pathClassif + "/MASK")
        if not os.path.exists(self.pathClassif + "/tmpClassif"):
            os.mkdir(self.pathClassif + "/tmpClassif")
        # test and creation of Final
        if not os.path.exists(self.Final):
            os.mkdir(self.Final)
        if not os.path.exists(self.Final + "/TMP"):
            os.mkdir(self.Final + "/TMP")
            
        # test and creation of cmdPath
        if not os.path.exists(self.cmdPath):
            os.mkdir(self.cmdPath)
        if not os.path.exists(self.cmdPath + "/confusion"):
            os.mkdir(self.cmdPath + "/confusion")

        # test and creation of pathAppVal
        if not os.path.exists(self.pathAppVal):
            os.mkdir(self.pathAppVal)

        # copy input data
        src_files = os.listdir(self.refData + "/Input/dataAppVal")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/dataAppVal", file_name)
            shutil.copy(full_file_name, self.pathAppVal)
        src_files = os.listdir(self.refData + "/Input/Classif/MASK")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/Classif/MASK", file_name)
            shutil.copy(full_file_name, self.pathClassif + "/MASK")
        src_files = os.listdir(self.refData + "/Input/Classif/classif")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/Classif/classif/", file_name)
            shutil.copy(full_file_name, self.pathClassif)
        src_files = os.listdir(self.refData + "/Input/final/TMP")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/final/TMP/", file_name)
            shutil.copy(full_file_name, self.Final + "/TMP")

    def test_GenConfMatrix(self):
        import genConfusionMatrix as GCM
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'outputPath', self.pathOut)
        cfg.setParam('chain', 'listTile', 'D0005H0002')
        N = 1
        dataField = 'CODE'

        GCM.genConfMatrix(self.Final, self.pathAppVal, N, dataField,
                          self.cmdPath + "/confusion", cfg, None)

        # file comparison to ref file
        serviceCompareImageFile = fu.serviceCompareImageFile()
        referenceFile1 = self.refData + "/Output/diff_seed_0.tif"
        File1 = self.Final + "/diff_seed_0.tif"
        nbDiff = serviceCompareImageFile.gdalFileCompare(File1, referenceFile1)
        print nbDiff
        self.assertEqual(nbDiff, 0)



class iota_testConfFusion(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.fichierConfig = iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"
        self.test_vector = iota2_dataTest + "/test_vector/"
        self.pathOut = iota2_dataTest + "/test_vector/test_ConfFusion/"
        self.Final = self.pathOut + "/final"
        self.refData = iota2_dataTest + "/references/ConfFusion/"
        
        # test and creation of test_vector
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)
        # test and creation of pathOut
        if not os.path.exists(self.pathOut):
            os.mkdir(self.pathOut)
        else:
            shutil.rmtree(self.pathOut)
            os.mkdir(self.pathOut)

        # test and creation of Final
        if not os.path.exists(self.Final):
            os.mkdir(self.Final)
        if not os.path.exists(self.Final + "/TMP"):
            os.mkdir(self.Final + "/TMP")

        # copy input data
        src_files = os.listdir(self.refData + "/Input/final/TMP")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/final/TMP/", file_name)
            shutil.copy(full_file_name, self.Final + "/TMP")

    def test_ConfFusion(self):
        import confusionFusion as confFus
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'outputPath', self.pathOut)
        shapeData = cfg.getParam('chain', 'groundTruth')
        dataField = 'CODE'
        # deux cas à tester :
        # if CLASSIFMODE == "separate":
        # elif CLASSIFMODE == "fusion" and MODE != "one_region":
        confFus.confFusion(shapeData, dataField, self.Final+"/TMP",
                           self.Final+"/TMP", self.Final+"/TMP", cfg)

        # file comparison to ref file
        File1 = self.Final + "/TMP/ClassificationResults_seed_0.txt"
        referenceFile1 = self.refData + "/Output/ClassificationResults_seed_0.txt"
        self.assertTrue(filecmp.cmp(File1, referenceFile1))

class iota_testGenerateStatModel(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.fichierConfig = iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"
        self.test_vector = iota2_dataTest + "/test_vector/"
        self.pathOut = iota2_dataTest + "/test_vector/test_GenerateStatModel/"
        self.pathStats = self.pathOut + "/stats"
        self.pathAppVal = self.pathOut + "/dataAppVal"
        self.pathTilesFeat = iota2_dataTest + "/references/features/"
        self.refData = iota2_dataTest + "/references/GenerateStatModel/"
        self.cmdPath = self.pathOut + "/cmd"

        # test and creation of test_vector
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)
        # test and creation of pathOut
        if not os.path.exists(self.pathOut):
            os.mkdir(self.pathOut)
        # test and creation of pathStats
        if not os.path.exists(self.pathStats):
            os.mkdir(self.pathStats)
        # test and creation of pathAppVal
        if not os.path.exists(self.pathAppVal):
            os.mkdir(self.pathAppVal)
        # test and creation of cmdPath
        if not os.path.exists(self.cmdPath):
            os.mkdir(self.cmdPath)
        if not os.path.exists(self.cmdPath + "/stats"):
            os.mkdir(self.cmdPath + "/stats")

        # copy input data
        src_files = os.listdir(self.refData + "/Input/dataAppVal")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/dataAppVal", file_name)
            shutil.copy(full_file_name, self.pathAppVal)
            
    def test_GenerateStatModel(self):
        import ModelStat as MS
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'outputPath', self.pathOut)
        cfg.setParam('argTrain', 'classifier', 'svm')

        MS.generateStatModel(self.pathAppVal, self.pathTilesFeat, self.pathStats,
                             self.cmdPath+"/stats", None, cfg)

        # file comparison to ref file
        File1 = self.cmdPath + "/stats/stats.txt"
        self.assertTrue(os.path.getsize(File1) > 0)

class iota_testOutStats(unittest.TestCase):
# TODO A terminer ne marche pas pour le moment
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.fichierConfig = iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"
        self.test_vector = iota2_dataTest + "/test_vector/"
        self.pathOut = iota2_dataTest + "/test_vector/test_OutStats/"
        self.shapeRegion = self.pathOut + "/shapeRegion/"
        
        # test and creation of test_vector
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)
        # test and creation of pathOut
        if not os.path.exists(self.pathOut):
            os.mkdir(self.pathOut)
        # test and creation of pathOut
        if not os.path.exists(self.shapeRegion):
            os.mkdir(self.shapeRegion)
  

    def test_OutStats(self):
        import outStats as OutS
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        
        cfg.setParam('chain', 'outputPath', self.pathOut)
        currentTile = 'D0005H0002'
        N = 1
        #OutS.outStats(cfg, currentTile, N, None)

class iota_testServiceLogging(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.fichierConfig = iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"

    def test_ServiceLogging(self):

        import logging
        File1 = iota2_dataTest + "/OSOlogFile.log"
        if os.path.exists(File1):
            os.remove(File1)
            with open(File1, "w") as F1:
                pass
        SCF.clearConfig()

        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'logFileLevel', "DEBUG")
        cfg.setParam('chain', 'logConsole', "DEBUG")
        # We call the serviceLogger to set the logLevel parameter
        sLog.serviceLogger(cfg, __name__)
        # Init logging service
        logger = logging.getLogger("test_ServiceLogging1")
        
        logger.info("Enter in DEBUG mode for file")
        logger.error("This log should always be seen")
        logger.info("This log should always be seen")
        logger.debug("This log should only be seen in DEBUG mode")
        
        cfg.setParam('chain', 'logFileLevel', "INFO")
        cfg.setParam('chain', 'logConsole', "INFO")
        # We call the serviceLogger to set the logLevel parameter
        sLog.serviceLogger(cfg, __name__)
        # On initialise le service de log       
        logger = logging.getLogger("test_ServiceLogging2")
        logger.info("Enter in INFO mode for file")
        logger.error("This log should always be seen")
        logger.info("This log should always be seen")
        logger.debug("If we see this, there is a problem...")

        # file comparison to ref file
        
        referenceFile1 = iota2_dataTest + "/references/OSOlogFile.log"
        l1 = open(File1,"r").readlines()
        l2 = open(referenceFile1,"r").readlines()
        # we compare only the fourth column

        for i in range(l1.__len__()):
            self.assertEqual(l1[i].split(' ')[3], l2[i].split(' ')[3])


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Tests for iota2")
    parser.add_argument("-mode", dest="mode", help="Tests mode",
                        choices=["all", "largeScale", "sample"],
                        default="sample", required=False)

    args = parser.parse_args()

    mode = args.mode

    loader = unittest.TestLoader()

    largeScaleTests = [iota_testFeatures]
    sampleTests = [iota_testShapeManipulations, iota_testStringManipulations,
                   iota_testSamplerApplications]

    if mode == "sample":
        testsToRun = unittest.TestSuite([loader.loadTestsFromTestCase(cTest)for cTest in sampleTests])
        runner = unittest.TextTestRunner()
        results = runner.run(testsToRun)

    elif mode == "largeScale":
        testsToRun = unittest.TestSuite([loader.loadTestsFromTestCase(cTest)for cTest in largeScaleTests])
        runner = unittest.TextTestRunner()
        results = runner.run(testsToRun)

    elif mode == "all":
        allTests = sampleTests+largeScaleTests
        testsToRun = unittest.TestSuite([loader.loadTestsFromTestCase(cTest)for cTest in allTests])
        runner = unittest.TextTestRunner()
        results = runner.run(testsToRun)

