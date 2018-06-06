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


"""
This test script is dedicated to launch all possible IOTA2 scenarios and check
if they reach the end.
"""

import unittest
import os
import shutil
import traceback
from Common import ServiceConfigFile as SCF

#TODO add tests using different sensors ?

#export IOTA2DIR=/mnt/data/home/vincenta/IOTA2/theia_oso
#python -m unittest iota2tests_runs

class iota2_run(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        
        
        #class const variables
        self.iota2_directory = os.environ.get('IOTA2DIR')
        self.config_path = os.path.join(self.iota2_directory, "config",
                                        "Config_4Tuiles_Multi_FUS_Confidence.cfg")
        self.config_path_test = None
        self.iota2_tests_directory = os.path.join(self.iota2_directory, "data",
                                                  "test_IOTA2_scenarios")
        if os.path.exists(self.iota2_tests_directory):
            shutil.rmtree(self.iota2_tests_directory)
        os.mkdir(self.iota2_tests_directory)

    @classmethod
    def tearDownClass(self):
        print "end of iota2_run tests"

    def setUp(self):
        """
        create test environement (directories)
        """
        #clear configuration object
        SCF.clearConfig()
        
        #create directories
        test_name = self.id().split(".")[-1]
        self.test_working_directory = os.path.join(self.iota2_tests_directory, test_name)
        self.test_working_directory_tmp = os.path.join(self.iota2_tests_directory, test_name + "_TMP")
        if os.path.exists(self.test_working_directory):
            shutil.rmtree(self.test_working_directory)
        if not os.path.exists(self.test_working_directory_tmp):
            os.mkdir(self.test_working_directory_tmp)
        self.config_path_test = os.path.join(self.test_working_directory_tmp, test_name + ".cfg")
        shutil.copy(self.config_path, self.config_path_test)

    def tearDown(self):
        result = getattr(self, '_outcomeForDoCleanups', self._resultForDoCleanups)
        error = self.list2reason(result.errors)
        failure = self.list2reason(result.failures)
        ok = not error and not failure
        
        if ok:
            shutil.rmtree(self.test_working_directory)
            shutil.rmtree(self.test_working_directory_tmp)
        
    def list2reason(self, exc_list):
        if exc_list and exc_list[-1][0] is self:
            return exc_list[-1][1]

    def test_scenario_1(self):
        
        #Test one region mode
        #L8 sensor
        
        from config import Config
        
        #prepare configuration file
        cfg = Config(file(self.config_path_test))
        cfg.chain.outputPath = self.test_working_directory
        cfg.chain.listTile = 'D0005H0002'
        cfg.chain.L8Path = os.path.join(self.iota2_directory, "data/L8_50x50")
        cfg.chain.featuresPath = self.test_working_directory_tmp
        cfg.chain.userFeatPath = 'None'
        cfg.chain.regionPath = os.path.join(self.test_working_directory_tmp, "MyTestRegion.shp")
        cfg.chain.mode = 'one_region'
        cfg.chain.groundTruth = os.path.join(self.iota2_directory,
                                             "data/references/sampler/D0005H0002_polygons_To_Sample.shp")
        cfg.chain.nomenclaturePath = os.path.join(self.iota2_directory,
                                                  "data/references/nomenclature.txt")
        cfg.chain.runs = 1
        cfg.chain.ratio = 0.5
        cfg.chain.cloud_threshold = 1
        cfg.chain.spatialResolution = 30
        cfg.chain.colorTable = os.path.join(self.iota2_directory,
                                            "data/references/color.txt")
        cfg.argTrain.samplesOptions = '-sampler random -strategy all'
        cfg.argTrain.options = ' -classifier.rf.min 5 -classifier.rf.max 25 '
        cfg.argTrain.cropMix = False
        cfg.argClassification.classifMode = 'separate'
        cfg.Landsat8.keepBands = []
        cfg.GlobChain.useAdditionalFeatures = False
        cfg.save(file(self.config_path_test, 'w'))

        import launchChain
        try:
            launchChain.launchChain(self.config_path_test)
        except Exception as e:
            print (e)
            traceback.print_exc()
            
            #should something else
            self.assertTrue(False)

if __name__ == '__main__':
    unittest.main()
