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
import sys
import shutil
import unittest
import glob

IOTA2DIR = os.environ.get('IOTA2DIR')
RM_IF_ALL_OK = True

iota2_script = IOTA2DIR + "/scripts"
sys.path.append(iota2_script)

from Common.Tools import CoRegister

class iota_testCoRegistration(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.group_test_name = "iota_testCoRegistration"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data", self.group_test_name)
        self.all_tests_ok = []

        # References
        self.config_test = os.path.join(IOTA2DIR, "data", "config", "test_config_coregister.cfg")
        self.datadir = os.path.join(IOTA2DIR, "/data/references/CoRegister/sensor_data/")

        # Tests directory
        self.test_working_directory = None
        if os.path.exists(self.iota2_tests_directory):
            shutil.rmtree(self.iota2_tests_directory)
        os.mkdir(self.iota2_tests_directory)
    
    # before launching a test
    def setUp(self):
        """
        create test environement (directories)
        """
        # self.test_working_directory is the diretory dedicated to each tests
        # it changes for each tests

        test_name = self.id().split(".")[-1]
        self.test_working_directory = os.path.join(self.iota2_tests_directory, test_name)
        if os.path.exists(self.test_working_directory):
            shutil.rmtree(self.test_working_directory)
        os.mkdir(self.test_working_directory)

    # after launching all tests
    @classmethod
    def tearDownClass(self):
        print "{} ended".format(self.group_test_name)

    def list2reason(self, exc_list):
        if exc_list and exc_list[-1][0] is self:
            return exc_list[-1][1]

    # after launching a test, remove test's data if test succeed
    def tearDown(self):
        result = getattr(self, '_outcomeForDoCleanups', self._resultForDoCleanups)
        error = self.list2reason(result.errors)
        failure = self.list2reason(result.failures)
        test_ok = not error and not failure
        self.all_tests_ok.append(test_ok)

    def test_fitnessScore_Coregister(self):
    	"""
    	TEST 
    	"""
    	expected = ['20170203', '20170223']
    	output = [CoRegister.fitnessDateScore("20170216", os.path.join(self.datadir, "T38KPD"), 'S2'),
                  CoRegister.fitnessDateScore("20170216", os.path.join(self.datadir, "T38KPE"), 'S2')]

    	self.assertTrue(all([ex == out for ex, out in zip(expected, output)]))

    def test_launch_CoRegister(self):
    	"""
    	TEST
    	"""
        from config import Config
        from Common.FileUtils import ensure_dir

    	stackFiles = glob.glob(os.path.join(self.datadir, "T38KPD", "*", "*STACK*.tif"))
    	for current_file in stackFiles:
    		shutil.copy(current_file, os.path.join(os.path.dirname(current_file), "temp.tif"))
        test_config = os.path.join(self.test_working_directory, os.path.basename(self.config_test))
        shutil.copy(self.config_test, test_config)

        # prepare test's inputs
        cfg_coregister = Config(file(test_config))
        cfg_coregister.chain.outputPath = self.test_working_directory
        cfg_coregister.save(file(test_config, 'w'))
        ensure_dir(os.path.join(self.test_working_directory, "features", "T38KPD"))

        # launch function
    	CoRegister.launch_coregister("T38KPD", test_config, None, False)
    	dateFolders = glob.glob(os.path.join(self.datadir, "T38KPD", "*"))
    	geomsFiles = glob.glob(os.path.join(self.datadir, "T38KPD", "*", "*.geom"))

        # assert
    	self.assertTrue(len(dateFolders)==len(geomsFiles))
        
        # cleaning
    	for current_file in geomsFiles:
    		os.remove(current_file)
    	stackFiles = glob.glob(os.path.join(self.datadir, "T38KPD", "*", "*STACK*.tif"))
    	for current_file in stackFiles:
    		shutil.move(os.path.join(os.path.dirname(current_file), "temp.tif"), current_file)
    	stackFiles = glob.glob(os.path.join(self.datadir,"T38KPE", "*", "*STACK*.tif"))
    	for current_file in stackFiles:
    		shutil.copy(current_file, os.path.join(os.path.dirname(current_file), "temp.tif"))
        ensure_dir(os.path.join(self.test_working_directory, "features", "T38KPE"))
        # launch function
    	CoRegister.launch_coregister("T38KPE", test_config, None, False)

        # assert
    	dateFolders = glob.glob(os.path.join(self.datadir, "T38KPE", "*"))
    	geomsFiles = glob.glob(os.path.join(self.datadir, "T38KPE", "*", "*.geom"))        
    	self.assertTrue(len(dateFolders)==len(geomsFiles))
        # cleaning
    	for current_file in geomsFiles:
    		os.remove(current_file)
    	stackFiles = glob.glob(os.path.join(self.datadir, "T38KPE", "*", "*STACK*.tif"))
    	for current_file in stackFiles:
    		shutil.move(os.path.join(os.path.dirname(current_file), "temp.tif"), current_file)
