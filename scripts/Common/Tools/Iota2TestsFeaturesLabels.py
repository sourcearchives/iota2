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

import unittest
import os
import shutil
from Common import ServiceConfigFile as SCF
from Common import FileUtils as fut

#export IOTA2DIR=/mnt/data/home/vincenta/IOTA2/theia_oso
#python -m unittest iota2tests_features_labels


def prepareAnnualFeatures(workingDirectory, referenceDirectory,
                          pattern, rename=None):
    """
    double all rasters's pixels
    rename must be a tuple
    """

    for dirname, dirnames, filenames in os.walk(referenceDirectory):
        # print path to all subdirectories first.
        for subdirname in dirnames:
            os.mkdir(os.path.join(dirname, subdirname).replace(referenceDirectory, workingDirectory).replace(rename[0], rename[1]))

        # print path to all filenames.
        for filename in filenames:
            shutil.copy(os.path.join(dirname, filename), os.path.join(dirname, filename).replace(referenceDirectory, workingDirectory).replace(rename[0], rename[1]))

    rastersPath = fut.FileSearch_AND(workingDirectory, True, pattern)
    for raster in rastersPath:
        cmd = 'otbcli_BandMathX -il ' + raster + ' -out ' + raster + ' -exp "im1+im1"'
        print cmd
        os.system(cmd)

    if rename:
        all_content = []
        for dirname, dirnames, filenames in os.walk(workingDirectory):
            # print path to all subdirectories first.
            for subdirname in dirnames:
                all_content.append(os.path.join(dirname, subdirname))

            # print path to all filenames.
            for filename in filenames:
                all_content.append(os.path.join(dirname, filename))


class iota_test_Basic(unittest.TestCase):

    """
    this tests group check feature's labels with basic runs
    parameters are set as follow :

    copyinput:True
    relrefl:False
    keepduplicates:False
    extractBands:False
    """
    currenResult = None

    @classmethod
    def setUpClass(self):

        #class variables
        self.iota2_directory = os.environ.get('IOTA2DIR')
        self.iota2_tests_directory = os.path.join(self.iota2_directory, "data",
                                                  "test_features_labels")
        self.test_working_directory = None
        self.test_working_directory_tmp = None
        config_path = os.path.join(self.iota2_directory, "config",
                                   "Config_4Tuiles_Multi_FUS_Confidence.cfg")
        self.config = SCF.serviceConfigFile(config_path)

        if os.path.exists(self.iota2_tests_directory):
            shutil.rmtree(self.iota2_tests_directory, ignore_errors=False)

        os.mkdir(self.iota2_tests_directory)

    '''
    @classmethod
    def tearDownClass(self):
        shutil.rmtree(self.iota2_tests_directory)
    '''
    #call before each tests
    def setUp(self):
        test_name = self.id().split(".")[-1]
        SCF.clearConfig()
        self.test_working_directory = os.path.join(self.iota2_tests_directory, test_name)
        self.test_working_directory_tmp = os.path.join(self.iota2_tests_directory, "FEATURES")
        if not os.path.exists(self.test_working_directory):
            os.mkdir(self.test_working_directory)
        if not os.path.exists(self.test_working_directory_tmp):
            os.mkdir(self.test_working_directory_tmp)

    #call after each tests
    def tearDown(self):
        pass


    def test_Basic(self):
        """
        this test verify if features labels generated are similar to a reference
        produce thanks to a specific configuration file
        """
        from Sampling.DataExtraction import VectorSampler
        from Common import IOTA2Directory

        #expected output
        ref_path = os.path.join(self.iota2_directory, "data", "references",
                                "iota2tests_features_labels_test_Basic.txt")

        #test inputs
        vector_file = os.path.join(self.iota2_directory, "data", "references",
                                   "sampler", "D0005H0002_polygons_To_Sample.shp")
        L8_rasters = os.path.join(self.iota2_directory, "data", "L8_50x50")

        #generate IOTA output directory
        IOTA2Directory.GenerateDirectories(self.test_working_directory)

        #fill up configuration file
        self.config.setParam('chain', 'outputPath', self.test_working_directory)
        self.config.setParam('chain', 'listTile', "D0005H0002")
        self.config.setParam('chain', 'featuresPath', self.test_working_directory_tmp)
        self.config.setParam('chain', 'L8Path', L8_rasters)
        self.config.setParam('chain', 'userFeatPath', 'None')
        self.config.setParam('argTrain', 'samplesOptions', '-sampler random -strategy all')
        self.config.setParam('argTrain', 'cropMix', False)
        self.config.setParam('argTrain', 'samplesClassifMix', False)
        self.config.setParam('GlobChain', 'useAdditionalFeatures', False)

        #Launch sampling
        VectorSampler.generateSamples(vector_file, None, self.config)

        test_vector = fut.fileSearchRegEx(self.test_working_directory + "/learningSamples/*sqlite")[0]
        test_field_list = fut.getAllFieldsInShape(test_vector, driver='SQLite')

        with open(ref_path, 'r') as f:
            ref_field_list = [line.rstrip() for line in f]

        #check outputs
        self.assertTrue(ref_field_list == test_field_list)

    def test_Basic_CropMix(self):
        """
        this test verify if features labels generated are similar to a reference
        produce thanks to a specific configuration file (cropMix 1 mode)
        """
        from Sampling.DataExtraction import VectorSampler
        from Common import IOTA2Directory
        from config import Config

        #expected output
        ref_path = os.path.join(self.iota2_directory, "data", "references",
                                "iota2tests_features_labels_test_Basic.txt")
        non_annual_features = os.path.join(self.test_working_directory_tmp, "non_annual_features")
        annual_features = os.path.join(self.test_working_directory_tmp, "annual_features")
        os.mkdir(annual_features)

        #test inputs
        vector_file = os.path.join(self.iota2_directory, "data", "references",
                                   "sampler", "D0005H0002_polygons_To_Sample.shp")
        L8_rasters_non_annual = os.path.join(self.iota2_directory, "data", "L8_50x50")
        L8_rasters_annual = os.path.join(self.test_working_directory_tmp, "annualData")
        os.mkdir(L8_rasters_annual)

        #annual sensor data generation (pix annual = 2 * pix non_annual)
        prepareAnnualFeatures(L8_rasters_annual, L8_rasters_non_annual, "CORR_PENTE",
                              rename=("2016", "2015"))

        #prepare annual configuration file
        annual_config_path = os.path.join(self.test_working_directory_tmp, "AnnualConfig.cfg")
        shutil.copy(self.config.pathConf, annual_config_path)

        cfg = Config(file(annual_config_path))
        cfg.chain.listTile = 'D0005H0002'
        cfg.chain.L8Path = L8_rasters_annual
        cfg.chain.featuresPath = annual_features
        cfg.chain.userFeatPath = 'None'
        cfg.argTrain.samplesOptions = '-sampler random -strategy all'
        cfg.GlobChain.useAdditionalFeatures = False
        cfg.save(file(annual_config_path, 'w'))

        #generate IOTA output directory
        IOTA2Directory.GenerateDirectories(self.test_working_directory)

        #fill up configuration file
        self.config.setParam('chain', 'outputPath', self.test_working_directory)
        self.config.setParam('chain', 'listTile', "D0005H0002")
        self.config.setParam('chain', 'featuresPath', non_annual_features)
        self.config.setParam('chain', 'L8Path', L8_rasters_non_annual)
        self.config.setParam('chain', 'userFeatPath', 'None')
        self.config.setParam('argTrain', 'samplesOptions', '-sampler random -strategy all')
        self.config.setParam('argTrain', 'cropMix', True)
        self.config.setParam('argTrain', 'prevFeatures', annual_config_path)
        self.config.setParam('argTrain', 'outputPrevFeatures', annual_features)
        self.config.setParam('argTrain', 'samplesClassifMix', False)
        self.config.setParam('GlobChain', 'useAdditionalFeatures', False)

        #Launch sampling
        VectorSampler.generateSamples(vector_file, None, self.config)

        test_vector = fut.fileSearchRegEx(self.test_working_directory + "/learningSamples/*sqlite")[0]
        test_field_list = fut.getAllFieldsInShape(test_vector, driver='SQLite')

        with open(ref_path, 'r') as f:
            ref_field_list = [line.rstrip() for line in f]

        #check outputs
        self.assertTrue(ref_field_list == test_field_list)
        
    def test_Basic_CropMix_classif(self):
        """
        this test verify if features labels generated are similar to a reference
        produce thanks to a specific configuration file (cropMix 2 mode)
        """
        from Sampling.DataExtraction import VectorSampler
        import tileEnvelope as env
        from Sampling import TileArea as area
        from Common.Tools import CreateRegionsByTiles as RT
        
        #expected output
        ref_path = os.path.join(self.iota2_directory, "data", "references",
                                "iota2tests_features_labels_test_Basic.txt")
        #test inputs
        vector_file = os.path.join(self.iota2_directory, "data", "references",
                                   "sampler", "D0005H0002_polygons_To_Sample.shp")
        L8_rasters = os.path.join(self.iota2_directory, "data", "L8_50x50")
        classifications_path = os.path.join(self.iota2_directory, "data",
                                            "references", "sampler")
        #rename reference shape
        test_vector = os.path.join(self.test_working_directory_tmp,
                                   "D0005H0002_polygons_1_Sample.shp")
        fut.cpShapeFile(vector_file.replace(".shp", ""), test_vector.replace(".shp", ""), [".prj", ".shp", ".dbf", ".shx"])

        #generate IOTA output directory
        IOTA2Directory.GenerateDirectories(self.test_working_directory)

        #fill up configuration file
        self.config.setParam('chain', 'outputPath', self.test_working_directory)
        self.config.setParam('chain', 'listTile', "D0005H0002")
        self.config.setParam('chain', 'featuresPath', self.test_working_directory_tmp)
        self.config.setParam('chain', 'L8Path', L8_rasters)
        self.config.setParam('chain', 'userFeatPath', 'None')
        self.config.setParam('argTrain', 'samplesOptions', '-sampler random -strategy all')
        self.config.setParam('argTrain', 'cropMix', True)
        self.config.setParam('argTrain', 'samplesClassifMix', True)
        self.config.setParam('argTrain', 'annualClassesExtractionSource', classifications_path)
        self.config.setParam('GlobChain', 'useAdditionalFeatures', False)

        #shapes genereation
        fut.getCommonMasks("D0005H0002", self.config, None)
        env.GenerateShapeTile(["D0005H0002"], self.test_working_directory_tmp, self.test_working_directory + "/envelope", None, self.config)
        shapeRegion = os.path.join(self.test_working_directory_tmp, "MyFakeRegion.shp")
        area.generateRegionShape("one_region", self.test_working_directory + "/envelope", "", shapeRegion, "region", self.config, None)
        RT.createRegionsByTiles(shapeRegion, "region", self.test_working_directory + "/envelope", self.test_working_directory + "/shapeRegion/", None)

        #Launch sampling
        VectorSampler.generateSamples(test_vector, None, self.config)

        test_vector = fut.fileSearchRegEx(self.test_working_directory + "/learningSamples/*sqlite")[0]
        test_field_list = fut.getAllFieldsInShape(test_vector, driver='SQLite')

        with open(ref_path, 'r') as f:
            ref_field_list = [line.rstrip() for line in f]


        #check outputs
        #condition : the difference between ref_field_list and test_field_list must be 'originfid'
        condition = len(set(ref_field_list) - set(test_field_list)) == 1 and list(set(ref_field_list) - set(test_field_list))[0] == "originfid"
        self.assertTrue(condition)
