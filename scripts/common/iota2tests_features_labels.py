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
import serviceConfigFile as SCF

#export IOTA2DIR=/mnt/data/home/vincenta/IOTA2/theia_oso
#python -m unittest iota2tests_features_labels


class iota_test_Basic(unittest.TestCase):

    """
    this tests group check feature's labels with basic runs
    parameters are set as follow :

    copyinput:'True'
    relrefl:'False'
    keepduplicates:'False'
    extractBands:'False'
    """
    #currenResult = None
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
        os.mkdir(self.test_working_directory)
        os.mkdir(self.test_working_directory_tmp)

    #call after each tests
    '''
    def tearDown(self):
        """
        ok = self.currentResult.wasSuccessful()
        errors = self.currentResult.errors
        failures = self.currentResult.failures
        
        print ok
        print errors
        print failures
        """
        shutil.rmtree(self.test_working_directory)
        shutil.rmtree(self.test_working_directory_tmp)
    '''

    def test_Basic(self):
        """
        this test verify if features labels generated are similar to a reference
        produce thanks to a specific configuration file
        """
        import vectorSampler
        import oso_directory
        import fileUtils as fut
        
        #expected output
        ref_path = os.path.join(self.iota2_directory, "data", "references",
                                "iota2tests_features_labels_test_Basic.txt")
        
        #test inputs
        vector_file = os.path.join(self.iota2_directory, "data", "references",
                                   "sampler", "D0005H0002_polygons_To_Sample.shp")
        L8_rasters = os.path.join(self.iota2_directory, "data", "L8_50x50")

        #generate IOTA output directory
        oso_directory.GenerateDirectories(self.test_working_directory)
        
        #fill up configuration file
        self.config.setParam('chain', 'outputPath', self.test_working_directory)
        self.config.setParam('chain', 'listTile', "D0005H0002")
        self.config.setParam('chain', 'featuresPath', self.test_working_directory_tmp)
        self.config.setParam('chain', 'L8Path', L8_rasters)
        self.config.setParam('chain', 'userFeatPath', 'None')
        self.config.setParam('argTrain', 'samplesOptions', '-sampler random -strategy all')
        self.config.setParam('argTrain', 'cropMix', 'False')
        self.config.setParam('argTrain', 'samplesClassifMix', 'False')
        self.config.setParam('GlobChain', 'useAdditionalFeatures', 'False')

        vectorSampler.generateSamples(vector_file, None, self.config)

        test_vector = fut.fileSearchRegEx(self.test_working_directory + "/learningSamples/*sqlite")[0]
        test_field_list = fut.getAllFieldsInShape(test_vector,driver='SQLite')
        
        with open(ref_path, 'r') as f:
            ref_field_list = [line.rstrip() for line in f]

        self.assertTrue(ref_field_list == test_field_list)


