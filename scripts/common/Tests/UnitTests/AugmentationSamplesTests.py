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

IOTA2DIR = os.environ.get('IOTA2DIR')
RM_IF_ALL_OK = True

iota2_script = IOTA2DIR + "/scripts/common"
sys.path.append(iota2_script)

from Sampling.DataAugmentation import AugmentationSamples
import fileUtils as fut

class iota_testSamplesAugmentation(unittest.TestCase):
    #before launching tests
    @classmethod
    def setUpClass(self):

        # definition of local variables
        self.group_test_name = "iota_testSamplesAugmentation"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data", self.group_test_name)
        self.vector = os.path.join(IOTA2DIR, "data", "references", "sampler",
                                   "D0005H0002_polygons_To_Sample_Samples_ref_bindings.sqlite")
        self.csvFile = os.path.join(IOTA2DIR, "data", "references", "sampleAugmentation.csv")
        self.all_tests_ok = []
        self.test_working_directory = None
        if os.path.exists(self.iota2_tests_directory):
            shutil.rmtree(self.iota2_tests_directory)
        os.mkdir(self.iota2_tests_directory)


    #after launching tests
    @classmethod
    def tearDownClass(self):
        print "{} ended".format(self.group_test_name)
        if RM_IF_ALL_OK and all(self.all_tests_ok):
            shutil.rmtree(self.iota2_tests_directory)

    #before launching a test
    def setUp(self):
        """
        create test environement (directories)
        """
        #create directories
        test_name = self.id().split(".")[-1]
        self.test_working_directory = os.path.join(self.iota2_tests_directory, test_name)
        if os.path.exists(self.test_working_directory):
            shutil.rmtree(self.test_working_directory)
        os.mkdir(self.test_working_directory)

    def list2reason(self, exc_list):
        if exc_list and exc_list[-1][0] is self:
            return exc_list[-1][1]

    #after launching a test, remove test's data if test succeed
    def tearDown(self):
        result = getattr(self, '_outcomeForDoCleanups', self._resultForDoCleanups)
        error = self.list2reason(result.errors)
        failure = self.list2reason(result.failures)
        ok = not error and not failure
        self.all_tests_ok.append(ok)
        if ok:
            shutil.rmtree(self.test_working_directory)

    #Tests definitions
    def test_iota2_augmentation_counter(self):
        """Test how many samples must be add to the sample set
        
        test the 3 differents strategies
        """
        from collections import Counter
        self.test_working_directory
        class_count = {51: 147, 11: 76, 12: 37, 42: 19}
        balance_expected = {42: 128, 11: 71, 12: 110}
        atLeast_expected = {42: 101, 11: 44, 12: 83}
        byClass_expected = {42: 11, 51: 33, 12: 1}
        class_augmentation_balance = AugmentationSamples.SamplesAugmentationCounter(class_count, mode="balance",
                                                                                    atleast_num=None,
                                                                                    byclass=None)
        self.assertEqual(cmp(class_augmentation_balance, balance_expected), 0)
        
        class_augmentation_atLeast = AugmentationSamples.SamplesAugmentationCounter(class_count, mode="atLeast",
                                                                                    atleast_num=120,
                                                                                    byclass=None)
        self.assertEqual(cmp(class_augmentation_atLeast, atLeast_expected), 0)
        
        class_augmentation_byClass = AugmentationSamples.SamplesAugmentationCounter(class_count, mode="byClass",
                                                                                    atleast_num=None,
                                                                                    byclass=self.csvFile)
        self.assertEqual(cmp(class_augmentation_byClass, byClass_expected), 0)