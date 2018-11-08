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

import filecmp
import string
import random
import shutil
import sys
import osr
import ogr
import subprocess

iota2dir = os.environ.get('IOTA2DIR')
iota2_script = iota2dir + "/scripts"
iota2_script_tests = iota2dir + "/data/test_scripts"
sys.path.append(iota2_script)
sys.path.append(iota2_script_tests)

from Common.Tools import RandomInSituByTile
from Sampling import VectorSampler
from Common import FileUtils as fu
import test_genGrid as test_genGrid
from Sampling import TileEnvelope
from gdalconst import *
from osgeo import gdal
from config import Config
import numpy as np
import otbApplication as otb
import argparse
from Common import ServiceConfigFile as SCF
from Common import ServiceLogger as sLog
from Common import IOTA2Directory
from Sensors import Sensors
from Common import Utils

from VectorTools.AddField import addField
from VectorTools.DeleteField import deleteField


#python -m unittest discover ./ -p "*Tests*.py"
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
    from Common.Utils import run

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


def random_update(vect_file, table_name, field, value, nb_update):
    """
    use in test_split_selection Test
    """
    import sqlite3 as lite

    sql_clause = "UPDATE {} SET {}='{}' WHERE ogc_fid in (SELECT ogc_fid FROM {} ORDER BY RANDOM() LIMIT {})".format(table_name, field, value, table_name ,nb_update)

    conn = lite.connect(vect_file)
    cursor = conn.cursor()
    cursor.execute(sql_clause)
    conn.commit()


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


def arrayToRaster(inArray, outRaster, output_format="int"):
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
    if output_format=='int':
        outRaster = driver.Create(outRaster, cols, rows, 1, gdal.GDT_UInt16)
    elif output_format=='float':
        outRaster = driver.Create(outRaster, cols, rows, 1, gdal.GDT_Float32)
    if not outRaster:
        raise Exception("can not create : "+outRaster)
    outRaster.SetGeoTransform((originX, pixSize, 0, originY, 0, pixSize))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(inArray)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromEPSG(2154)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()

def compareVectorFile(vect_1, vect_2, mode='table', typegeom = 'point', drivername = "SQLite"):

        '''
        compare SQLite, table mode is faster but does not work with 
        connected OTB applications.

        return true if vectors are the same
        '''

        def getFieldValue(feat,fields):
                return dict([(currentField,feat.GetField(currentField)) for currentField in fields])
        def priority(item):
                return (item[0],item[1])
        def getValuesSortedByCoordinates(vector):
                values = []
                driver = ogr.GetDriverByName(drivername)
                ds = driver.Open(vector,0)
                lyr = ds.GetLayer()
                fields = fu.getAllFieldsInShape(vector, drivername)
                for feature in lyr:
                    if typegeom == "point":
                        x,y= feature.GetGeometryRef().GetX(),feature.GetGeometryRef().GetY()
                    elif typegeom == "polygon":
                        x,y= feature.GetGeometryRef().Centroid().GetX(),feature.GetGeometryRef().Centroid().GetY()
                    fields_val = getFieldValue(feature,fields)
                    values.append((x,y,fields_val))

                values = sorted(values,key=priority)
                return values

        fields_1 = fu.getAllFieldsInShape(vect_1, drivername) 
        fields_2 = fu.getAllFieldsInShape(vect_2, drivername)

        if len(fields_1) != len(fields_2): return False
        elif cmp(fields_1,fields_2) != 0 : return False
        
        if mode == 'table':
                connection_1 = lite.connect(vect_1)
                df_1 = pad.read_sql_query("SELECT * FROM output", connection_1)

                connection_2 = lite.connect(vect_2)
                df_2 = pad.read_sql_query("SELECT * FROM output", connection_2)

                try: 
                        table = (df_1 != df_2).any(1)
                        if True in table.tolist():return False
                        else:return True
                except ValueError:
                        return False

        elif mode == 'coordinates':
                values_1 = getValuesSortedByCoordinates(vect_1)
                values_2 = getValuesSortedByCoordinates(vect_2)
                sameFeat = [cmp(val_1,val_2) == 0 for val_1,val_2 in zip(values_1,values_2)]
                if False in sameFeat:return False
                return True
        else:
                raise Exception("mode parameter must be 'table' or 'coordinates'")    


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
    from Common.Utils import run
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
            os.mkdir(os.path.join(testPath, "features"))
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

        from Common import ServiceConfigFile as SCF
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
        
        VectorSampler.generateSamples({"usually":self.referenceShape_test}, None, self.config, sampleSelection=self.selection_test)
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
        VectorSampler.generateSamples({"usually":self.referenceShape_test}, None, self.config, sampleSelection=self.selection_test)
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
        VectorSampler.generateSamples({"usually":self.referenceShape_test}, wD, self.config, sampleSelection=self.selection_test)
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
        VectorSampler.generateSamples({"usually":self.referenceShape_test}, wD, self.config, sampleSelection=self.selection_test)

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
        VectorSampler.generateSamples({"usually":self.referenceShape_test}, wD, self.config, sampleSelection=self.selection_test)

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

        from Common.Tools.Iota2TestsFeaturesLabels import prepareAnnualFeatures

        def prepareTestsFolder(workingDirectory=False):

            testPath = self.test_vector+"/cropMixSampler_bindings/"
            if os.path.exists(testPath):
                shutil.rmtree(testPath)
            os.mkdir(testPath)
            os.mkdir(os.path.join(testPath, "features"))

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
            cfg.chain.userFeatPath = 'None'
            cfg.GlobChain.annualClassesExtractionSource = 'False'
            cfg.GlobChain.useAdditionalFeatures = False
            cfg.save(file(annual_config_path, 'w'))
            featuresPath = os.path.join(cfg.chain.outputPath, "features")
            if not os.path.exists(featuresPath):
                os.mkdir(featuresPath)

            return annual_config_path

        from Common import ServiceConfigFile as SCF

        featuresPath = iota2_dataTest+"/references/features/"
        sensorData = iota2_dataTest+"/L8_50x50"
        reference = iota2_dataTest+"/references/sampler/D0005H0002_polygons_To_Sample_Samples_CropMix_bindings.sqlite"

        #prepare outputs test folders
        testPath, features_NA_Outputs, features_A_Outputs, wD = prepareTestsFolder(True)
        annualFeaturesPath = testPath+"/annualFeatures"

        #prepare annual configuration file
        annual_config_path = generate_annual_config(wD, annualFeaturesPath, features_A_Outputs)

        testPath, features_NA_Outputs, features_A_Outputs, wD = prepareTestsFolder(True)

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
        self.config.setParam('chain', 'L8Path', L8_rasters_non_annual)
        self.config.setParam('chain', 'userFeatPath', 'None')
        self.config.setParam('argTrain', 'cropMix', True)
        self.config.setParam('argTrain', 'prevFeatures', annual_config_path)
        self.config.setParam('argTrain', 'outputPrevFeatures', features_A_Outputs)
        self.config.setParam('argTrain', 'samplesClassifMix', False)
        self.config.setParam('GlobChain', 'useAdditionalFeatures', False)
        self.config.setParam('GlobChain', 'writeOutputs', True)

        #Launch sampler
        VectorSampler.generateSamples({"usually":self.referenceShape_test}, None,
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
        VectorSampler.generateSamples({"usually":self.referenceShape_test}, wD, self.config, sampleSelection=self.selection_test)

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
        vectorTest = VectorSampler.generateSamples({"usually":self.referenceShape_test}, None,
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
        VectorSampler.generateSamples({"usually":self.referenceShape_test}, None, self.config, sampleSelection=self.selection_test)

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
        from Common import ServiceConfigFile as SCF
        from Sampling import TileEnvelope as env
        from Sampling import TileArea as area
        from Common.Tools import CreateRegionsByTiles as RT

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
        IOTA2Directory.GenerateDirectories(self.config)

        #shapes genereation
        fu.getCommonMasks("D0005H0002", self.config, None)
        env.GenerateShapeTile(["D0005H0002"], wD, testPath + "/envelope", None, self.config)
        shapeRegion = os.path.join(wD, "MyFakeRegion.shp")
        area.generateRegionShape(testPath + "/envelope", "", shapeRegion, "region", self.config, None)
        RT.createRegionsByTiles(shapeRegion, "region", testPath + "/envelope", testPath + "/shapeRegion/", None)

        #launch sampling
        addField(vector, "region", "1", str)
        VectorSampler.generateSamples({"usually":vector}, wD, self.config, sampleSelection=self.selection_test)
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
        IOTA2Directory.GenerateDirectories(self.config)

        #shapes genereation
        vector = shapeReferenceVector(self.referenceShape, "D0005H0002")
        fu.getCommonMasks("D0005H0002", self.config, None)
        env.GenerateShapeTile(["D0005H0002"], wD, testPath + "/envelope", None, self.config)
        shapeRegion = os.path.join(wD, "MyFakeRegion.shp")
        area.generateRegionShape(testPath + "/envelope", "", shapeRegion, "region", self.config, None)
        RT.createRegionsByTiles(shapeRegion, "region", testPath + "/envelope", testPath + "/shapeRegion/", None)

        addField(vector, "region", "1", str)
        VectorSampler.generateSamples({"usually":vector}, wD, self.config, sampleSelection=self.selection_test)

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
        IOTA2Directory.GenerateDirectories(self.config)

        #shapes genereation
        vector = shapeReferenceVector(self.referenceShape, "D0005H0002")
        fu.getCommonMasks("D0005H0002", self.config, None)
        env.GenerateShapeTile(["D0005H0002"], wD, testPath + "/envelope", None, self.config)
        shapeRegion = os.path.join(wD, "MyFakeRegion.shp")
        area.generateRegionShape(testPath + "/envelope", "", shapeRegion, "region", self.config, None)
        RT.createRegionsByTiles(shapeRegion, "region", testPath + "/envelope", testPath + "/shapeRegion/", None)

        addField(vector, "region", "1", str)
        VectorSampler.generateSamples({"usually":vector}, None, self.config, sampleSelection=self.selection_test)

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
        IOTA2Directory.GenerateDirectories(self.config)

        #shapes genereation
        vector = shapeReferenceVector(self.referenceShape, "D0005H0002")
        fu.getCommonMasks("D0005H0002", self.config, None)
        env.GenerateShapeTile(["D0005H0002"], wD, testPath + "/envelope", None, self.config)
        shapeRegion = os.path.join(wD, "MyFakeRegion.shp")
        area.generateRegionShape(testPath + "/envelope", "", shapeRegion, "region", self.config, None)
        RT.createRegionsByTiles(shapeRegion, "region", testPath + "/envelope", testPath + "/shapeRegion/", None)

        addField(vector, "region", "1", str)
        VectorSampler.generateSamples({"usually":vector}, None, self.config, sampleSelection=self.selection_test)

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
        from Common import FileUtils as fut
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

        ObjListTile = [TileEnvelope.Tile(currentTile, currentTile.split("/")[-1].split(".")[0].split("_")[0]) for currentTile in tilesPath]
        ObjListTile_sort = sorted(ObjListTile, key=TileEnvelope.priorityKey)

        TileEnvelope.genTileEnvPrio(ObjListTile_sort, self.priorityEnvelope_test,
                                    self.priorityEnvelope_test, self.epsg)

        envRef = fu.fileSearchRegEx(self.priorityEnvelope_ref+"/*.shp")

        comp = []
        for eRef in envRef:
            tile_number = os.path.split(eRef)[-1].split("_")[1]
            comp.append(fut.FileSearch_AND(self.priorityEnvelope_test, True, "Tile"+tile_number+"_PRIO.shp")[0])


        cmpEnv = [checkSameEnvelope(currentRef, test_env) for currentRef,test_env in zip(envRef,comp)]
        self.assertTrue(all(cmpEnv))

    def test_regionsByTile(self):
        from Common.Tools import CreateRegionsByTiles as RT
        self.test_regionsByTiles = iota2_dataTest+"/test_vector/test_regionsByTiles"
        if os.path.exists(self.test_regionsByTiles):
            shutil.rmtree(self.test_regionsByTiles)
        os.mkdir(self.test_regionsByTiles)

        RT.createRegionsByTiles(self.typeShape,
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


    @classmethod
    def setUpClass(self):
        self.iota2_directory = os.environ.get('IOTA2DIR')
        #the configuration file tested must be the one in /config.
        self.fichierConfig = os.path.join(self.iota2_directory, "config", "Config_4Tuiles_Multi_FUS_Confidence.cfg")
        self.fichierConfigBad1 = iota2_dataTest+"/config/test_config_serviceConfigFileBad1.cfg"
        self.fichierConfigBad2 = iota2_dataTest+"/config/test_config_serviceConfigFileBad2.cfg"
        self.fichierConfigBad3 = iota2_dataTest+"/config/test_config_serviceConfigFileBad3.cfg"

    def test_initConfigFile(self):
        from Common import ServiceError as sErr
        # the class is instantiated with self.fichierConfig config file
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'runs', 2)
        cfg.setParam('chain', 'regionPath', '../../../data/references/region_need_To_env.shp')
        cfg.setParam('chain', 'regionField', 'DN_char')
        cfg.setParam('argClassification', 'classifMode', 'separate')

        # we check the config file
        self.assertTrue(cfg.checkConfigParameters())

        # we get outputPath variable
        self.assertEqual(cfg.getParam('chain', 'outputPath'), '../../../data/tmp/')

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
        from Sampling import TileEnvelope as env

        #Test de création des enveloppes
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        IOTA2_dir = cfg.getParam("chain", "outputPath")
        featuresPath = os.path.join(IOTA2_dir, "features")

        masks_references = '../../../data/references/features'
        if os.path.exists(featuresPath):
            shutil.rmtree(featuresPath)

        shutil.copytree(masks_references, featuresPath)

        #Test de création des enveloppes
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)

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
        shutil.rmtree(featuresPath)
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
        from Sampling import TileArea as area

        print "pathEnvelope: " + self.pathEnvelope
        print "model: " + self.model
        print "shapeRegion: " + self.shapeRegion
        print "field_Region: " + self.field_Region
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)

        area.generateRegionShape(self.pathEnvelope, self.model,
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
        from Learning import TrainingCmd as TC
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        dataField = 'CODE'
        N = 1
        cfg.setParam('chain', 'outputPath', self.pathOut)
        cfg.setParam('chain', 'regionField', "region")

        TC.launchTraining(cfg, dataField, self.pathStats, N, self.cmdPath + "/train", self.pathModels,
                          None)

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
        from Classification import ClassificationCmd as CC
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'outputPath', self.pathOut)
        field_Region = cfg.getParam('chain', 'regionField')
        N = 1
        CC.launchClassification(self.pathModels, cfg, self.pathStats,
                      self.pathTileRegion, self.pathTilesFeat,
                      self.shapeRegion, field_Region,
                      N, self.cmdPath+"/cla", self.pathClassif, 128, None)

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
        from Sampling import VectorSamplesMerge as VSM
        from Sampling import VectorSampler as vs
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
        from Classification import Fusion as FUS
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'outputPath', self.pathOut)
        cfg.setParam('argClassification', 'classifMode', 'fusion')

        field_Region = cfg.getParam('chain', 'regionField')
        N = 1

        cmdFus = FUS.fusion(self.pathClassif, cfg, None)



class iota_testNoData(unittest.TestCase):

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
        from Classification import NoData as ND
        from Classification import Fusion as FUS
        from Common.Utils import run
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
        from Validation import ClassificationShaping as CS
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'outputPath', self.pathOut)
        cfg.setParam('chain', 'listTile', "D0005H0002")
        cfg.setParam('argClassification', 'classifMode', "separate")

        features_ref = "../../../data/references/features"
        features_ref_test = os.path.join(self.pathOut, "features")
        os.mkdir(features_ref_test)
        shutil.copytree(features_ref+"/D0005H0002", features_ref_test + "/D0005H0002")
        shutil.copytree(features_ref+"/D0005H0003", features_ref_test + "/D0005H0003")

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
            nbDiff = serviceCompareImageFile.gdalFileCompare(File1, referenceFile1)
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
        from Validation import GenConfusionMatrix as GCM
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
        from Validation import ConfusionFusion as confFus
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
        from Learning import ModelStat as MS
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'outputPath', self.pathOut)
        cfg.setParam('argTrain', 'classifier', 'svm')

        MS.generateStatModel(self.pathAppVal, self.pathTilesFeat, self.pathStats,
                             self.cmdPath+"/stats", None, cfg)

        # file comparison to ref file
        File1 = self.cmdPath + "/stats/stats.txt"
        self.assertTrue(os.path.getsize(File1) > 0)


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


class iota_testGetModel(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        '''
        We test every function in the file getModel.py'
        '''
        self.pathInput = iota2_dataTest + 'references/getModel/Input/'
        self.pathTestRunning = iota2_dataTest + 'test_vector/test_getModel/'

        if not os.path.exists(self.pathTestRunning):
            os.mkdir(self.pathTestRunning)

        shutil.copyfile(self.pathInput + 'tile0_0_learn_seed0.shp', self.pathTestRunning + 'tile0_0_learn_seed0.shp')
        shutil.copyfile(self.pathInput + 'tile0_1_learn_seed0.shp', self.pathTestRunning + 'tile0_1_learn_seed0.shp')
        shutil.copyfile(self.pathInput + 'tile0_2_learn_seed0.shp', self.pathTestRunning + 'tile0_2_learn_seed0.shp')
        shutil.copyfile(self.pathInput + 'tile0_3_learn_seed0.shp', self.pathTestRunning + 'tile0_3_learn_seed0.shp')
        shutil.copyfile(self.pathInput + 'tile1_2_learn_seed0.shp', self.pathTestRunning + 'tile1_2_learn_seed0.shp')
        shutil.copyfile(self.pathInput + 'tile1_3_learn_seed0.shp', self.pathTestRunning + 'tile1_3_learn_seed0.shp')
        shutil.copyfile(self.pathInput + 'tile2_2_learn_seed0.shp', self.pathTestRunning + 'tile2_2_learn_seed0.shp')
        shutil.copyfile(self.pathInput + 'tile3_2_learn_seed0.shp', self.pathTestRunning + 'tile3_2_learn_seed0.shp')
        shutil.copyfile(self.pathInput + 'tile4_1_learn_seed0.shp', self.pathTestRunning + 'tile4_1_learn_seed0.shp')
        shutil.copyfile(self.pathInput + 'tile4_2_learn_seed0.shp', self.pathTestRunning + 'tile4_2_learn_seed0.shp')
        shutil.copyfile(self.pathInput + 'tile6_3_learn_seed0.shp', self.pathTestRunning + 'tile6_3_learn_seed0.shp')
        self.tileForRegionNumber = [[0, ['tile0']], [1, ['tile0', 'tile4']], [2, ['tile0', 'tile1', 'tile2', 'tile3', 'tile4']], [3, ['tile0', 'tile1', 'tile6']]]

    def test_getModel(self):
        '''
        We check we have the expected files in the output
        '''
        from Learning import GetModel

        # We execute the function getModel()
        outputStr = GetModel.getModel(self.pathTestRunning)

        # the function produces a list of regions and its tiles
        # We check if we have all the expected element in the list
        for element in outputStr:
            # We get the region number and all the tiles for the region number
            region = int(element[0])
            tiles = element[1]

            # We check if we have this region number in the list tileForRegionNumber
            iRN = -1
            for l in range(len(self.tileForRegionNumber)):
                if region == self.tileForRegionNumber[l][0]:
                    iRN = l
            self.assertEqual(iRN, region)

            # for each tile for this region, we check if we have this value in the list of the expected values
            for tile in tiles:
                iTFRN = self.tileForRegionNumber[iRN][1].index(tile)
                self.assertEqual(tile, self.tileForRegionNumber[iRN][1][iTFRN])

        # We delete all temporary files from the test folder
        os.remove(self.pathTestRunning + 'tile0_0_learn_seed0.shp')
        os.remove(self.pathTestRunning + 'tile0_1_learn_seed0.shp')
        os.remove(self.pathTestRunning + 'tile0_2_learn_seed0.shp')
        os.remove(self.pathTestRunning + 'tile0_3_learn_seed0.shp')
        os.remove(self.pathTestRunning + 'tile1_2_learn_seed0.shp')
        os.remove(self.pathTestRunning + 'tile1_3_learn_seed0.shp')
        os.remove(self.pathTestRunning + 'tile2_2_learn_seed0.shp')
        os.remove(self.pathTestRunning + 'tile3_2_learn_seed0.shp')
        os.remove(self.pathTestRunning + 'tile4_1_learn_seed0.shp')
        os.remove(self.pathTestRunning + 'tile4_2_learn_seed0.shp')
        os.remove(self.pathTestRunning + 'tile6_3_learn_seed0.shp')


class iota_testMergeOutStats(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        '''
        In this function, we initialize the configuration file used by the function mergeOutStats()
        We will change the value for the output path for our output folder
        '''
        # We create a test_folder
        if not os.path.exists(iota2_dataTest + 'test_vector/test_mergeOutStats'):
            os.mkdir(iota2_dataTest + 'test_vector/test_mergeOutStats')

        # We copy the configuration file in the test folder
        if os.path.exists(iota2_dataTest + 'test_vector/test_mergeOutStats/config.cfg'):
            os.remove(iota2_dataTest + 'test_vector/test_mergeOutStats/config.cfg')
        shutil.copyfile(iota2_dataTest + 'references/mergeOutStats/Input/config.cfg',\
                        iota2_dataTest + 'test_vector/test_mergeOutStats/config.cfg')

        # We copy the folder and its files in the test folder from the reference folder
        if os.path.exists(iota2_dataTest + 'test_vector/test_mergeOutStats/final'):
            shutil.rmtree(iota2_dataTest + 'test_vector/test_mergeOutStats/final')
        shutil.copytree(iota2_dataTest + 'references/mergeOutStats/Input/final',\
                        iota2_dataTest + 'test_vector/test_mergeOutStats/final')

        # We modify some parameters of the configuration file for this test
        self.cfg = SCF.serviceConfigFile(iota2_dataTest + 'test_vector/test_mergeOutStats/config.cfg')
        self.cfg.setParam('chain', 'outputPath', iota2_dataTest + 'test_vector/test_mergeOutStats/')
        self.cfg.setParam('chain', 'runs', 1)
        self.cfg.setParam('chain', 'listTile', 'T31TCJ')

    def test_mergeOutStats(self):
        '''
        We test the function mergeOutStats()
        This is more a non-regression test than a unit test
        '''
        from Validation import MergeOutStats

        # We delete each file in the output directory
        if os.path.exists(iota2_dataTest + 'test_vector/mergeOutStats/Output/final/Stats_LNOK.txt'):
            os.remove(iota2_dataTest + 'test_vector/mergeOutStats/Output/final/Stats_LNOK.txt')
        if os.path.exists(iota2_dataTest + 'test_vector/mergeOutStats/Output/final/Stats_LOK.txt'):
            os.remove(iota2_dataTest + 'test_vector/mergeOutStats/Output/final/Stats_LOK.txt')
        if os.path.exists(iota2_dataTest + 'test_vector/mergeOutStats/Output/final/Stats_LOK_LNOK.png'):
            os.remove(iota2_dataTest + 'test_vector/mergeOutStats/Output/final/Stats_LOK_LNOK.png')
        if os.path.exists(iota2_dataTest + 'test_vector/mergeOutStats/Output/final/Stats_VNOK.txt'):
            os.remove(iota2_dataTest + 'test_vector/mergeOutStats/Output/final/Stats_VNOK.txt')
        if os.path.exists(iota2_dataTest + 'test_vector/mergeOutStats/Output/final/Stats_VOK.txt'):
            os.remove(iota2_dataTest + 'test_vector/mergeOutStats/Output/final/Stats_VOK.txt')
        if os.path.exists(iota2_dataTest + 'test_vector/mergeOutStats/Output/final/Stats_VOK_VNOK.png'):
            os.remove(iota2_dataTest + 'test_vector/mergeOutStats/Output/final/Stats_VOK_VNOK.png')
        if os.path.exists(iota2_dataTest + 'test_vector/mergeOutStats/Output/final/Validity.txt'):
            os.remove(iota2_dataTest + 'test_vector/mergeOutStats/Output/final/Validity.txt')
        if os.path.exists(iota2_dataTest + 'test_vector/mergeOutStats/Output/final/Validity.png'):
            os.remove(iota2_dataTest + 'test_vector/mergeOutStats/Output/final/Validity.png')

        # We execute mergeOutStats()
        MergeOutStats.mergeOutStats(self.cfg)

        # We check the produced value with the expected value
        # we should have 0 as result of the difference between the expected value and the produced value
        self.assertEqual(0, os.system('diff ' + iota2_dataTest + '/references/mergeOutStats/Output/Stats_LNOK.txt '
                                      + iota2_dataTest + '/test_vector/test_mergeOutStats/final/Stats_LNOK.txt'))
        self.assertEqual(0, os.system('diff ' + iota2_dataTest + '/references/mergeOutStats/Output/Stats_LOK.txt '
                                      + iota2_dataTest + '/test_vector/test_mergeOutStats/final/Stats_LOK.txt'))
        #self.assertEqual(0, os.system('diff ' + iota2_dataTest + '/references/mergeOutStats/Output/Stats_LOK_LNOK.png '
        #                              + iota2_dataTest + '/test_vector/test_mergeOutStats/final/Stats_LOK_LNOK.png'))
        self.assertEqual(0, os.system('diff ' + iota2_dataTest + '/references/mergeOutStats/Output/Stats_VNOK.txt '
                                      + iota2_dataTest + '/test_vector/test_mergeOutStats/final/Stats_VNOK.txt'))
        self.assertEqual(0, os.system('diff ' + iota2_dataTest + '/references/mergeOutStats/Output/Stats_VOK.txt '
                                      + iota2_dataTest + '/test_vector/test_mergeOutStats/final/Stats_VOK.txt'))
        #self.assertEqual(0, os.system('diff ' + iota2_dataTest + '/references/mergeOutStats/Output/Stats_VOK_VNOK.png '
        #                              + iota2_dataTest + '/references/test_mergeOutStats/final/Stats_VOK_VNOK.png'))

        # We delete every file from test_vector/test_mergeOutStats
        shutil.rmtree(iota2_dataTest + 'test_vector/test_mergeOutStats/final')
        os.remove(iota2_dataTest + 'test_vector/test_mergeOutStats/config.cfg')

class iota_testGenResults(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        '''
        In this function we will initialize the required parameters for the function
        '''
        # We create a test folder
        if not os.path.exists(iota2_dataTest + 'test_vector/test_genResults'):
            os.mkdir(iota2_dataTest + 'test_vector/test_genResults')

        # We copy every file from the input directory
        if os.path.exists(iota2_dataTest + 'test_vector/test_genResults'):
            shutil.rmtree(iota2_dataTest + 'test_vector/test_genResults')
        shutil.copytree(iota2_dataTest + 'references/genResults/Input',
                        iota2_dataTest + 'test_vector/test_genResults')

        # We initialize parameters for the configuration file
        self.classifFinal = iota2_dataTest + 'test_vector/test_genResults/final'
        self.nomenclaturePath = iota2_dataTest + 'test_vector/test_genResults/nomenclature.txt'

        # We remove the file RESULTS.txt
        if os.path.exists(iota2_dataTest + 'test_vector/test_genResults/final/RESULTS.txt'):
            os.remove(iota2_dataTest + 'test_vector/test_genResults/final/RESULTS.txt')

        if os.path.exists(iota2_dataTest + 'test_vector/test_genResults/final/TMP/Classif_Seed_1_sq.csv'):
            os.remove(iota2_dataTest + 'test_vector/test_genResults/final/TMP/Classif_Seed_1_sq.csv')
        if os.path.exists(iota2_dataTest + 'test_vector/test_genResults/final/TMP/Classif_Seed_0_sq.csv'):
            os.remove(iota2_dataTest + 'test_vector/test_genResults/final/TMP/Classif_Seed_0_sq.csv')

    def test_GenResults(self):
        '''
        '''
        from Validation import GenResults as GR

        # we execute the function genResults()
        GR.genResults(self.classifFinal, self.nomenclaturePath)

        # We check we have the same produced file that the expected file
        self.assertEqual(0, os.system('diff ' + iota2_dataTest + 'references/genResults/Output/RESULTS.txt '
                                      + iota2_dataTest + 'test_vector/test_genResults/final/RESULTS.txt'))


    def test_ResultsUtils(self):
        """
        """
        from Validation import ResultsUtils as resU
        import numpy as np

        conf_mat_array = np.array([[1, 2, 3],
                                   [4, 5, 6],
                                   [7, 8, 9]])

        norm_ref_ref = np.array([[0.16666667, 0.33333333, 0.5],
                                 [0.26666667, 0.33333333, 0.4],
                                 [0.29166667, 0.33333333, 0.375]])

        norm_prod_ref = np.array([[0.08333333, 0.13333333, 0.16666667],
                                  [0.33333333, 0.33333333, 0.33333333],
                                  [0.58333333, 0.53333333, 0.5]])

        norm_ref_test = resU.normalize_conf(conf_mat_array, norm="ref")
        self.assertTrue(np.allclose(norm_ref_ref, norm_ref_test),
                        msg="problem with the normalization by ref")

        norm_prod_test = resU.normalize_conf(conf_mat_array, norm="prod")
        self.assertTrue(np.allclose(norm_prod_ref, norm_prod_test),
                        msg="problem with the normalization by prod")


    def test_getCoeff(self):
        """
        test confusion matrix coefficients computation
        """
        from Validation import ResultsUtils as resU
        from collections import OrderedDict

        # construct input
        confusion_matrix = OrderedDict([(1, OrderedDict([(1, 50.0), (2, 78.0), (3, 41.0)])),
                                        (2, OrderedDict([(1, 20.0), (2, 52.0), (3, 31.0)])),
                                        (3, OrderedDict([(1, 27.0), (2, 72.0), (3, 98.0)]))])
        K_ref = 0.15482474945066724
        OA_ref = 0.42643923240938164
        P_ref = OrderedDict([(1, 0.5154639175257731), (2, 0.25742574257425743), (3, 0.5764705882352941)])
        R_ref = OrderedDict([(1, 0.2958579881656805), (2, 0.5048543689320388), (3, 0.49746192893401014)])
        F_ref = OrderedDict([(1, 0.3759398496240602), (2, 0.3409836065573771), (3, 0.5340599455040872)])

        K_test, OA_test, P_test, R_test, F_test = resU.get_coeff(confusion_matrix)

        self.assertTrue(K_ref == K_test,
                        msg="Kappa computation is broken")
        self.assertTrue(OA_test == OA_ref,
                        msg="Overall accuracy computation is broken")
        self.assertTrue(P_test == P_ref,
                        msg="Precision computation is broken")
        self.assertTrue(R_test == R_ref,
                        msg="Recall computation is broken")
        self.assertTrue(F_test == F_ref,
                        msg="F-Score computation is broken")


class iota_testPlotCor(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        '''
        We test the file plotCor.py
        We define every parameter the function requires
        '''
        import math
        # We initialize the test folder
        if os.path.exists(iota2_dataTest + 'test_vector/test_plotCor'):
            shutil.rmtree(iota2_dataTest + 'test_vector/test_plotCor')
        os.mkdir(iota2_dataTest + 'test_vector/test_plotCor')

        self.outpath = iota2_dataTest + 'test_vector/test_plotCor/correlatedTemperature'
        self.xLabel = ''
        self.yLabel = 'Temperature (K)'
        self.x = [x for x in range(5, 654)]
        self.y = map(lambda x: 16+14*math.cos(x*2*math.pi/17), self.x)

    def test_PlotCor(self):
        '''
        We test the function plotCorrelation()
        '''
        from Validation import PlotCor

        # We initialize the class Parametres from plotCor.py
        param = PlotCor.Parametres()
        param.xlims = [5, 654]
        param.ylims = [2, 31]

        # We execute the function plotCorrelation
        PlotCor.plotCorrelation(self.x, self.y, self.xLabel, self.yLabel, self.outpath, param)


class iota_testMergeSamples(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # We initialize the expected mergeSamples for the function get_models()
        self.expectedOutputGetModels = [('1', ['T31TCJ'], 0), ('1', ['T31TCJ'], 1)]

        # Copy and remove files in the test folder
        if os.path.exists(iota2_dataTest + 'test_vector/test_mergeSamples'):
            shutil.rmtree(iota2_dataTest + 'test_vector/test_mergeSamples')
        shutil.copytree(iota2_dataTest + 'references/mergeSamples/Input', iota2_dataTest + 'test_vector/test_mergeSamples')

        if not os.path.exists(iota2_dataTest + 'test_vector/test_mergeSamples/samples_merge/samplesSelection/'):
            os.mkdir(iota2_dataTest + 'test_vector/test_mergeSamples/samples_merge/samplesSelection/')

        # We define several parameters for the configuration file
        self.cfg = SCF.serviceConfigFile(iota2_dataTest + 'test_vector/test_mergeSamples/config.cfg')
        self.cfg.setParam('chain', 'outputPath', iota2_dataTest + 'test_vector/test_mergeSamples/samples_merge')
        self.cfg.setParam('chain', 'regionField', 'region')



    def test_getModels(self):
        from Sampling import SamplesMerge

        # We execute the function : get_models()
        output = SamplesMerge.get_models(iota2_dataTest + 'test_vector/test_mergeSamples/get_models/formattingVectors', 'region', 2)

        # We check the output values with the expected values
        self.assertEqual(self.expectedOutputGetModels[0][0], output[0][0])
        self.assertEqual(self.expectedOutputGetModels[0][1][0], output[0][1][0])
        self.assertEqual(self.expectedOutputGetModels[0][2], output[0][2])
        self.assertEqual(self.expectedOutputGetModels[1][0], output[1][0])
        self.assertEqual(self.expectedOutputGetModels[1][1][0], output[1][1][0])
        self.assertEqual(self.expectedOutputGetModels[1][2], output[1][2])


    def test_samplesMerge(self):
        from Sampling import SamplesMerge

        # We execute the function: samples_merge()
        output = SamplesMerge.get_models(iota2_dataTest + 'test_vector/test_mergeSamples/get_models/formattingVectors', 'region', 2)
        SamplesMerge.samples_merge(output[0], self.cfg, None)

        # We check the produced files
        self.assertEqual(0, os.system('diff ' + iota2_dataTest + 'references/mergeSamples/Output/samples_region_1_seed_0.shp '\
                                      + iota2_dataTest + 'test_vector/test_mergeSamples/samples_merge/samplesSelection/samples_region_1_seed_0.shp'))
        self.assertEqual(0, os.system('diff ' + iota2_dataTest + 'references/mergeSamples/Output/samples_region_1_seed_0.prj '\
                                      + iota2_dataTest + 'test_vector/test_mergeSamples/samples_merge/samplesSelection/samples_region_1_seed_0.prj'))
        self.assertEqual(0, os.system('diff ' + iota2_dataTest + 'references/mergeSamples/Output/samples_region_1_seed_0.shx '\
                                      + iota2_dataTest + 'test_vector/test_mergeSamples/samples_merge/samplesSelection/samples_region_1_seed_0.shx'))
        # dbf file are database file we cannot binary compare them
        #self.assertEqual(0, os.system('diff ' + iota2_dataTest + 'references/mergeSamples/Output/samples_region_1_seed_0.dbf '\
        #                              + iota2_dataTest + 'test_vector/test_mergeSamples/samples_merge/samplesSelection/samples_region_1_seed_0.dbf'))


class iota_testMergeSamples(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # We initialize the expected mergeSamples for the function get_models()
        self.expectedOutputGetModels = [('1', ['T31TCJ'], 0), ('1', ['T31TCJ'], 1)]

        # Copy and remove files in the test folder
        if os.path.exists(iota2_dataTest + 'test_vector/test_mergeSamples'):
            shutil.rmtree(iota2_dataTest + 'test_vector/test_mergeSamples')
        shutil.copytree(iota2_dataTest + 'references/mergeSamples/Input', iota2_dataTest + 'test_vector/test_mergeSamples')
        os.mkdir(iota2_dataTest + 'test_vector/test_mergeSamples/samples_merge/samplesSelection/')
        # We define several parameters for the configuration file
        self.cfg = SCF.serviceConfigFile(iota2_dataTest + 'test_vector/test_mergeSamples/config.cfg')
        self.cfg.setParam('chain', 'outputPath', iota2_dataTest + 'test_vector/test_mergeSamples/samples_merge')
        self.cfg.setParam('chain', 'regionField', 'region')



    def test_getModels(self):
        from Sampling import SamplesMerge

        # We execute the function : get_models()
        output = SamplesMerge.get_models(iota2_dataTest + 'test_vector/test_mergeSamples/get_models/formattingVectors', 'region', 2)

        # We check the output values with the expected values
        self.assertEqual(self.expectedOutputGetModels[0][0], output[0][0])
        self.assertEqual(self.expectedOutputGetModels[0][1][0], output[0][1][0])
        self.assertEqual(self.expectedOutputGetModels[0][2], output[0][2])
        self.assertEqual(self.expectedOutputGetModels[1][0], output[1][0])
        self.assertEqual(self.expectedOutputGetModels[1][1][0], output[1][1][0])
        self.assertEqual(self.expectedOutputGetModels[1][2], output[1][2])


class iota_testSplitSamples(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # We remove every file present in the test folder
        if os.path.exists(iota2_dataTest + 'test_vector/test_SplitSamples/'):
            shutil.rmtree(iota2_dataTest + 'test_vector/test_SplitSamples/')
        #os.mkdir(iota2_dataTest + 'test_vector/test_SplitSamples')

        # We copy every file from the input folder
        shutil.copytree(iota2_dataTest + 'references/splitSamples/Input',\
                      iota2_dataTest + 'test_vector/test_SplitSamples')

        # We define the configuration file
        self.cfg = SCF.serviceConfigFile(iota2_dataTest + 'test_vector/test_SplitSamples/config.cfg')

        # We forced several parameters for this test
        self.cfg.setParam('chain', 'outputPath', iota2_dataTest + 'test_vector/test_SplitSamples/')
        self.cfg.setParam('chain', 'dataField', 'CODE')
        self.cfg.setParam('chain', 'mode_outside_RegionSplit', '0.0098')
        self.cfg.setParam('chain', 'regionField', 'region')
        self.cfg.setParam('GlobChain', 'proj', 'EPSG:2154')
        self.cfg.setParam('chain', 'runs', '2')
        self.cfg.setParam('chain', 'ratio', '0.5')

        # We define several output
        self.formattingVectorDir = os.path.abspath(iota2_dataTest + 'test_vector/test_SplitSamples/formattingVectors')
        self.shapeRegionDir = os.path.abspath(iota2_dataTest + 'test_vector/test_SplitSamples/shapeRegion')
        self.vectors = os.path.abspath(iota2_dataTest + 'test_vector/test_SplitSamples/formattingVectors/T31TCJ.shp')
        self.shapesRegion = os.path.abspath(iota2_dataTest + 'test_vector/test_SplitSamples/shapeRegion/Myregion_region_1_T31TCJ.shp')
        self.regions = '1'
        self.areas = 12399.173485632864
        self.regionTiles = os.path.abspath(iota2_dataTest + '/test_vector/test_SplitSamples/formattingVectors/T31TCJ.sqlite')
        self.dataToRm = os.path.abspath(iota2_dataTest + 'test_vector/test_SplitSamples/formattingVectors/T31TCJ.sqlite')
        self.regionsSplit = 2
        self.updatedVector = os.path.abspath(iota2_dataTest + '/test_vector/test_SplitSamples/formattingVectors/T31TCJ.sqlite')
        self.newRegionShape = os.path.abspath(iota2_dataTest + 'test_vector/test_SplitSamples/formattingVectors/T31TCJ.shp')
        self.dataAppValDir = os.path.abspath(iota2_dataTest + 'test_vector/test_SplitSamples/dataAppVal')

    def test_SplitSamples(self):
        from Sampling import SplitSamples

        # We execute several functions of this file
        outputPath = self.cfg.getParam('chain', 'outputPath')
        dataField = self.cfg.getParam('chain', 'dataField')
        region_threshold = float(self.cfg.getParam('chain', 'mode_outside_RegionSplit'))
        region_field = (self.cfg.getParam('chain', 'regionField')).lower()
        regions_pos = -2

        formatting_vectors_dir = os.path.join(outputPath, "formattingVectors")
        # We check we have the correct file
        self.assertEqual(self.formattingVectorDir, os.path.abspath(formatting_vectors_dir))

        shape_region_dir = os.path.join(outputPath, "shapeRegion")
        # We check we have the correct file
        self.assertEqual(self.shapeRegionDir, os.path.abspath(shape_region_dir))

        ratio = float(self.cfg.getParam('chain', 'ratio'))
        seeds = int(self.cfg.getParam('chain', 'runs'))
        epsg = int((self.cfg.getParam('GlobChain', 'proj')).split(":")[-1])

        vectors = fu.FileSearch_AND(formatting_vectors_dir, True, ".shp")
        # We check we have the correct file
        self.assertEqual(self.vectors, os.path.abspath(vectors[0]))

        shapes_region = fu.FileSearch_AND(shape_region_dir, True, ".shp")
        # We check we have the correct file
        self.assertEqual(self.shapesRegion, os.path.abspath(shapes_region[0]))

        regions = list(set([os.path.split(shape)[-1].split("_")[regions_pos] for shape in shapes_region]))
        # We check we have the correct value
        self.assertEqual(self.regions, regions[0])

        areas, regions_tiles, data_to_rm = SplitSamples.get_regions_area(vectors, regions,
                                                            formatting_vectors_dir,
                                                            None,
                                                            region_field)
        # We check we have the correct values
        self.assertAlmostEqual(self.areas, areas['1'], 9e-3)
        self.assertEqual(self.regionTiles, os.path.abspath(regions_tiles['1'][0]))
        self.assertEqual(self.dataToRm, os.path.abspath(data_to_rm[0]))

        regions_split = SplitSamples.get_splits_regions(areas, region_threshold)
        # We check we have the correct value
        self.assertEqual(self.regionsSplit, regions_split['1'])

        updated_vectors = SplitSamples.split(regions_split, regions_tiles, dataField, region_field)

        # We check we have the correct file
        self.assertEqual(self.updatedVector, os.path.abspath(updated_vectors[0]))

        new_regions_shapes = SplitSamples.transform_to_shape(updated_vectors, formatting_vectors_dir)
        # We check we have the correct file
        self.assertEqual(self.newRegionShape, os.path.abspath(new_regions_shapes[0]))

        for data in data_to_rm:
            os.remove(data)

        dataAppVal_dir = os.path.join(outputPath, "dataAppVal")
        self.assertEqual(self.dataAppValDir, os.path.abspath(dataAppVal_dir))
        enableCrossValidation = False
        SplitSamples.update_learningValination_sets(new_regions_shapes, dataAppVal_dir, dataField,
                                                    region_field, ratio, seeds, epsg, enableCrossValidation)


class iota_testVectorSplits(unittest.TestCase):
    @classmethod

    def setUpClass(self):
        # We create the test folder
        if os.path.exists(iota2_dataTest + 'test_vector/test_VectorSplits'):
            shutil.rmtree(iota2_dataTest + 'test_vector/test_VectorSplits')
        shutil.copytree(iota2_dataTest + 'references/vector_splits/Input', iota2_dataTest + 'test_vector/test_VectorSplits')

        self.cfg = SCF.serviceConfigFile(iota2_dataTest + 'test_vector/test_VectorSplits/config.cfg')
        self.outputEMVS = iota2_dataTest + 'test_vector/test_VectorSplits/T31TCJ.shp'
        self.new_regions_shapes = [iota2_dataTest + 'test_vector/test_VectorSplits/formattingVectors/T31TCJ.shp']
        self.dataAppVal_dir = iota2_dataTest + 'test_vector/test_VectorSplits/dataAppVal'
        self.dataField = 'CODE'
        self.regionField = 'region'
        self.ratio = 0.5
        self.seeds = 2
        self.epsg = 2154

        # Output files for references
        self.refSplitDbf = iota2_dataTest + 'references/vector_splits/Output/splitInSubSets/T31TCJ.dbf'
        self.refSplitPrj = iota2_dataTest + 'references/vector_splits/Output/splitInSubSets/T31TCJ.prj'
        self.refSplitShp = iota2_dataTest + 'references/vector_splits/Output/splitInSubSets/T31TCJ.shp'
        self.refSplitShx = iota2_dataTest + 'references/vector_splits/Output/splitInSubSets/T31TCJ.shx'

        # Output files
        self.outSplitDbf = iota2_dataTest + 'test_vector/test_VectorSplits/formattingVectors/T31TCJ.dbf'
        self.outSplitPrj = iota2_dataTest + 'test_vector/test_VectorSplits/formattingVectors/T31TCJ.prj'
        self.outSplitShp = iota2_dataTest + 'test_vector/test_VectorSplits/formattingVectors/T31TCJ.shp'
        self.outSplitShx = iota2_dataTest + 'test_vector/test_VectorSplits/formattingVectors/T31TCJ.shx'

    def test_vectorSplits(self):
        from Sampling import SplitInSubSets as VS
        # We execute the function splitInSubSets()
        for new_region_shape in self.new_regions_shapes:
            tile_name = os.path.splitext(os.path.basename(new_region_shape))[0]
            vectors_to_rm = fu.FileSearch_AND(self.dataAppVal_dir, True, tile_name)
            for vect in vectors_to_rm:
                os.remove(vect)
            VS.splitInSubSets(new_region_shape, self.dataField, self.regionField, self.ratio, self.seeds, "ESRI Shapefile")
            print new_region_shape
        # We check the output
        self.assertEqual(0, os.system('diff ' + self.refSplitPrj + ' ' + self.outSplitPrj))
        self.assertEqual(0, os.system('diff ' + self.refSplitShp + ' ' + self.outSplitShp))
        self.assertEqual(0, os.system('diff ' + self.refSplitShx + ' ' + self.outSplitShx))
        #self.assertEqual(0, os.system('diff ' + self.refSplitDbf + ' ' + self.outSplitDbf))

    def test_vectorSplitsCrossValidation(self):
        from Sampling import SplitInSubSets as VS
        from Common import FileUtils as fut
        # We execute the function splitInSubSets()
        new_region_shape = self.new_regions_shapes[0]
        tile_name = os.path.splitext(os.path.basename(new_region_shape))[0]
        VS.splitInSubSets(new_region_shape, self.dataField,
                          self.regionField, self.ratio, self.seeds,
                          "ESRI Shapefile", crossValidation=True)

        seed0 = fut.getFieldElement(new_region_shape, driverName="ESRI Shapefile",
                                    field="seed_0", mode="all",elemType="str")
        seed1 = fut.getFieldElement(new_region_shape, driverName="ESRI Shapefile",
                                    field="seed_1", mode="all",elemType="str")
                                    
        for elem in seed0:
            self.assertTrue(elem in ["unused", "learn"],
                            msg="flag not in ['unused', 'learn']")
        for elem in seed1:
            self.assertTrue(elem in ["unused", "validation"],
                            msg="flag not in ['unused', 'validation']")

    def test_vectorSplitsNoSplits(self):
        from Sampling import SplitInSubSets as VS
        from Common import FileUtils as fut

        new_region_shape = self.new_regions_shapes[0]
        tile_name = os.path.splitext(os.path.basename(new_region_shape))[0]
        VS.splitInSubSets(new_region_shape, self.dataField,
                          self.regionField, self.ratio, 1,
                          "ESRI Shapefile", crossValidation=False,
                          splitGroundTruth=False)
        seed0 = fut.getFieldElement(new_region_shape, driverName="ESRI Shapefile",
                                    field="seed_0", mode="all",elemType="str")
                                    
        for elem in seed0:
            self.assertTrue(elem in ["learn"],
                            msg="flag not in ['learn']")

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

