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
        self.datadir = "../../../data/references/CoRegister/sensor_data/"

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
    	expected = ['20170203','20170223']
    	output = [CoRegister.fitnessDateScore("20170216",os.path.join(self.datadir,"T38KPD"),'S2'),
    				CoRegister.fitnessDateScore("20170216",os.path.join(self.datadir,"T38KPE"),'S2')]

    	self.assertTrue(all([ex == out for ex, out in zip(expected, output)]))

    def test_launch_CoRegister(self):
    	"""
    	TEST
    	"""
    	stackFiles = glob.glob(os.path.join(self.datadir,"T38KPD","*","*STACK*.tif"))
    	for file in stackFiles:
    		shutil.copy(file, os.path.join(os.path.dirname(file),"temp.tif"))
    	CoRegister.launch_coregister("T38KPD",self.config_test,None)
    	dateFolders = glob.glob(os.path.join(self.datadir,"T38KPD","*"))
    	geomsFiles = glob.glob(os.path.join(self.datadir,"T38KPD","*","*.geom"))
    	self.assertTrue(len(dateFolders) == len(geomsFiles))
    	for file in geomsFiles:
    		os.remove(file)
    	stackFiles = glob.glob(os.path.join(self.datadir,"T38KPD","*","*STACK*.tif"))
    	for file in stackFiles:
    		shutil.move(os.path.join(os.path.dirname(file),"temp.tif"), file)

    	stackFiles = glob.glob(os.path.join(self.datadir,"T38KPE","*","*STACK*.tif"))
    	for file in stackFiles:
    		shutil.copy(file, os.path.join(os.path.dirname(file),"temp.tif"))
    	CoRegister.launch_coregister("T38KPE",self.config_test,None)
    	dateFolders = glob.glob(os.path.join(self.datadir,"T38KPE","*"))
    	geomsFiles = glob.glob(os.path.join(self.datadir,"T38KPE","*","*.geom"))
    	self.assertTrue(len(dateFolders) == len(geomsFiles))
    	for file in geomsFiles:
    		os.remove(file)
    	stackFiles = glob.glob(os.path.join(self.datadir,"T38KPE","*","*STACK*.tif"))
    	for file in stackFiles:
    		shutil.move(os.path.join(os.path.dirname(file),"temp.tif"), file)
