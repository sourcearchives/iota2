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

iota2_script = IOTA2DIR + "/scripts"
sys.path.append(iota2_script)

from Sampling import DataAugmentation


class iota_testSamplesAugmentationUser(unittest.TestCase):
    #before launching tests
    @classmethod
    def setUpClass(self):

        # definition of local variables
        self.group_test_name = "iota_testSamplesAugmentationUser"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data", self.group_test_name)
        self.vector = os.path.join(IOTA2DIR, "data", "references", "sampler",
                                   "D0005H0002_polygons_To_Sample_Samples_ref_bindings.sqlite")
        self.all_tests_ok = []
        self.test_working_directory = None
        if os.path.exists(self.iota2_tests_directory):
            shutil.rmtree(self.iota2_tests_directory)
        os.mkdir(self.iota2_tests_directory)
        self.csv_path = os.path.join(IOTA2DIR, "data", "references", "dataAugmentation.csv")

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

        #Create test data
        self.vector_1 = os.path.join(self.test_working_directory, "vector_TEST_1_seed0.sqlite")
        if os.path.exists(self.vector_1):
            os.remove(self.vector_1)
        shutil.copy(self.vector, self.vector_1)

        self.vector_2 = os.path.join(self.test_working_directory, "vector_TEST_2_seed0.sqlite")
        if os.path.exists(self.vector_2):
            os.remove(self.vector_2)
        shutil.copy(self.vector, self.vector_2)

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
    def test_iota2_dataAugmentationByCopy(self):
        """ TEST the function DataAugmentationByCopy

        test if the function AugmentationSamplesUser.samples_management_csv
        works as expected.
        """
        expected = [152, 42, 24, 152]

        DataAugmentation.DataAugmentationByCopy("CODE", self.csv_path, [self.vector_1, self.vector_2])
        count = [DataAugmentation.countClassInSQLite(self.vector_2, "CODE", "11"),
                 DataAugmentation.countClassInSQLite(self.vector_2, "CODE", "12"),
                 DataAugmentation.countClassInSQLite(self.vector_2, "CODE", "42"),
                 DataAugmentation.countClassInSQLite(self.vector_2, "CODE", "51")]

        self.assertTrue(all([ex == co for ex, co in zip(expected, count)]))

    def test_parse_csv(self):
        """ TEST
        """
        expected = [['1', '2', '11', '-1'],
                    ['1', '2', '12', '5'],
                    ['1', '2', '42', '5'],
                    ['1', '2', '51', '5']]
        csv_test = DataAugmentation.getUserSamplesManagement(self.csv_path)
        self.assertTrue(expected == csv_test)

    def test_count(self):
        """ TEST AugmentationSamplesUser.countClassInSQLite
        """
        expected = [76, 37, 19, 147]
        count = [DataAugmentation.countClassInSQLite(self.vector, "CODE", "11"),
                 DataAugmentation.countClassInSQLite(self.vector, "CODE", "12"),
                 DataAugmentation.countClassInSQLite(self.vector, "CODE", "42"),
                 DataAugmentation.countClassInSQLite(self.vector, "CODE", "51")]
        self.assertTrue(all([ex == co for ex, co in zip(expected, count)]))
