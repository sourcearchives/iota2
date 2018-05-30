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

import sys
import os
import unittest
import filecmp
import string
import random
import shutil
import logging
import argparse
import subprocess
from config import Config
import numpy as np
import osr
import ogr
from gdalconst import *
from osgeo import gdal

iota2dir = os.environ.get('IOTA2DIR')
iota2_script = iota2dir + "/scripts/common"
sys.path.append(iota2_script)


import Utils
import RandomInSituByTile
import createRegionsByTiles
import vectorSampler
import oso_directory as osoD
import fileUtils as fu
import test_genGrid as test_genGrid
import tileEnvelope
import Sensors
import otbApplication as otb
import serviceConfigFile as SCF
from Utils import run
import serviceLogger as sLog
fu.updatePyPath()

from DeleteField import deleteField
from AddField import addField

iota2_dataTest = os.environ.get('IOTA2DIR') + "/data/"

# Init of logging service
# We need an instance of serviceConfigFile
cfg = SCF.serviceConfigFile(iota2_dataTest + "/config/test_config_serviceConfigFile.cfg")
# We force the logFile value
cfg.setParam('chain', 'logFile', iota2_dataTest + "/OSOlogFile.log")
# We call the serviceLogger
sLog.serviceLogger(cfg, __name__)
SCF.clearConfig()


def shapeReferenceVector(refVector, outputName):
    """
    modify reference vector (add field, rename...)
    """

    path, name = os.path.split(refVector)
    
    tmp = path+"/"+outputName+"_TMP"
    fu.cpShapeFile(refVector.replace(".shp", ""), tmp, [".prj", ".shp", ".dbf", ".shx"])
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
    from Common import OtbAppBank as otb
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
            for (k1, v1), (k2, v2) in zip(val_1[2].items(), val_2[2].items()):
                if not k1 in ignored_fields and k2 in ignored_fields:
                    sameFeat.append(cmp(v1, v2) == 0)
        if False in sameFeat:
            return False
        return True
    else:
        raise Exception("CmpMode parameter must be 'table' or 'coordinates'")



class iota_testFeatures(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        #Unzip
        self.largeScaleDir = "/work/OT/theia/oso/dataTest/test_LargeScale"
        #self.largeScaleDir = "/mnt/data/home/vincenta/test_LargeScale"
        self.SARDirectory = self.largeScaleDir+"/SAR_directory"

        self.test_vector = iota2_dataTest+"/test_vector"
        self.RefConfig = iota2dir+"/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"
        self.TestConfig = iota2_dataTest+"/test_vector/ConfigurationFile_Test.cfg"
        self.referenceShape = iota2_dataTest+"/references/sampler/D0005H0002_polygons_To_Sample.shp"

        #self.S2_largeScale = "/work/OT/theia/oso/dataTest/test_LargeScale/S2"
        self.S2_largeScale = self.largeScaleDir+"/S2_50x50"

        self.RefSARconfig = iota2dir+"/config/SARconfig.cfg"
        self.RefSARconfigTest = iota2_dataTest+"/test_vector/ConfigurationFile_SAR_Test.cfg"
        self.SARfeaturesPath = self.test_vector+"/checkOnlySarFeatures_features_SAR"

        self.SARdata = self.SARDirectory+"/raw_data"
        
        self.SRTM = self.SARDirectory+"/SRTM"
        self.geoid = self.SARDirectory+"/egm96.grd"
        self.tilesShape = self.SARDirectory+"/Features.shp"
        self.srtmShape = self.SARDirectory+"/srtm.shp"

        self.vectorRef = iota2dir+"/data/references/sampler/SARfeaturesProdRef.sqlite"

        self.testPath = self.test_vector+"/checkOnlySarFeatures"
        self.featuresPath = self.test_vector+"/checkOnlySarFeatures_features"
        
        # instanciation of serviceConfigFile class
        SCF.clearConfig()
        self.cfg = SCF.serviceConfigFile(self.RefConfig)
        
    """
    TEST : Compute SAR features, from raw Sentinel-1 data
    and generate sample points
    """
    def test_checkOnlySarFeatures(self):

        def prepareSARconfig():
            from ConfigParser import SafeConfigParser
            parser = SafeConfigParser()
            parser.read(self.RefSARconfig)
            parser.set('Paths', 'Output', self.SARfeaturesPath)
            parser.set('Paths', 'S1Images', self.SARdata)
            parser.set('Paths', 'SRTM', self.SRTM)
            parser.set('Paths', 'GeoidFile', self.geoid)
            parser.set('Processing', 'ReferencesFolder', self.S2_largeScale)
            parser.set('Processing', 'RasterPattern', "STACK.tif")
            parser.set('Processing', 'OutputSpatialResolution', '10')
            parser.set('Processing', 'TilesShapefile', self.tilesShape)
            parser.set('Processing', 'SRTMShapefile', self.srtmShape)

            with open(self.RefSARconfigTest, "w+") as configFile:
                parser.write(configFile)

        def prepareTestsEnvironment(testPath, featuresPath,
                                    cfg, SARconfig):
            
            """

            """
            # We force a list of parameters to a specific value
            # These values are only in memory, in the instance of class SCF
            # It will never write on disc.
            cfg.setParam('chain', 'outputPath', testPath)
            cfg.setParam('chain', 'listTile', "T31TCJ")
            cfg.setParam('chain', 'featuresPath', featuresPath)
            cfg.setParam('chain', 'L5Path', "None")
            cfg.setParam('chain', 'L8Path', "None")
            cfg.setParam('chain', 'S2Path', "None")
            cfg.setParam('chain', 'S1Path', self.RefSARconfigTest)
            cfg.setParam('chain', 'userFeatPath', "None")
            cfg.setParam('GlobChain', 'useAdditionalFeatures', False)
            cfg.setParam('argTrain', 'cropMix', False)

            osoD.GenerateDirectories(cfg)
        
        if os.path.exists(self.featuresPath):
            shutil.rmtree(self.featuresPath)
        os.mkdir(self.featuresPath)
        if os.path.exists(self.featuresPath+"/T31TCJ"):
            shutil.rmtree(self.featuresPath+"/T31TCJ")
        os.mkdir(self.featuresPath+"/T31TCJ")
        if os.path.exists(self.featuresPath+"/T31TCJ/tmp"):
            shutil.rmtree(self.featuresPath+"/T31TCJ/tmp")
        os.mkdir(self.featuresPath+"/T31TCJ/tmp")
        if os.path.exists(self.SARfeaturesPath):
            shutil.rmtree(self.SARfeaturesPath)
        os.mkdir(self.SARfeaturesPath)
        
        prepareSARconfig()
        
        prepareTestsEnvironment(self.testPath, self.featuresPath,
                                self.cfg, self.RefSARconfigTest)

        referenceShape_test = shapeReferenceVector(self.referenceShape, "T31TCJ")
        
        fu.getCommonMasks("T31TCJ", self.cfg, workingDirectory=None)

        selection_test = os.path.join(self.testPath, "T31TCJ.sqlite")
        raster_ref = fu.FileSearch_AND(self.featuresPath, True, ".tif")[0]
        prepare_test_selection(referenceShape_test, raster_ref, selection_test, self.testPath, "code")

        tileEnvelope.GenerateShapeTile(["T31TCJ"], self.featuresPath,
                                       self.testPath+"/envelope",
                                       None, self.cfg)
        vectorSampler.generateSamples(referenceShape_test,
                                      None, self.cfg, sampleSelection=selection_test)

        test_vector = fu.FileSearch_AND(self.testPath+"/learningSamples",
                                        True, ".sqlite")[0]
        delete_uselessFields(test_vector)
        compare = compareSQLite(test_vector, self.vectorRef, CmpMode='coordinates')
        self.assertTrue(compare)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Tests for iota2")
#    parser.add_argument("-mode", dest="mode", help="Tests mode",
#                        choices=["all", "largeScale", "sample"],
#                       default="sample", required=False)

    args = parser.parse_args()

    loader = unittest.TestLoader()

    largeScaleTests = [iota_testFeatures]
    testsToRun = unittest.TestSuite([loader.loadTestsFromTestCase(cTest)for cTest in largeScaleTests])
    runner = unittest.TextTestRunner()
    results = runner.run(testsToRun)


