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

# python -m unittest SamplesSelectionsTests

import os
import sys
import shutil
import unittest

IOTA2DIR = os.environ.get('IOTA2DIR')

# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True

iota2_script = IOTA2DIR + "/scripts"
sys.path.append(iota2_script)

from Common import FileUtils as fut

class iota_testSamplesSelection(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.group_test_name = "iota_testSamplesSelection"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data", self.group_test_name)
        self.all_tests_ok = []

        # References
        self.in_shape = os.path.join(IOTA2DIR, "data", "references", "mergeSamples",
                                     "Input", "samples_merge", "formattingVectors",
                                     "T31TCJ.shp")
        self.in_xml = os.path.join(IOTA2DIR, "data", "references",
                                   "selectionSamples", "Input",
                                   "samplesSelection", "samples_region_1_seed_0.xml")
        # Tests directory
        self.test_working_directory = None
        if os.path.exists(self.iota2_tests_directory):
            shutil.rmtree(self.iota2_tests_directory)
        os.mkdir(self.iota2_tests_directory)

    # after launching all tests
    @classmethod
    def tearDownClass(self):
        print "{} ended".format(self.group_test_name)
        if RM_IF_ALL_OK and all(self.all_tests_ok):
            shutil.rmtree(self.iota2_tests_directory)

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


    def list2reason(self, exc_list):
        if exc_list and exc_list[-1][0] is self:
            return exc_list[-1][1]

    # after launching a test, remove test's data if test succeed
    def tearDown(self):
        result = getattr(self, '_outcomeForDoCleanups', self._resultForDoCleanups)
        error = self.list2reason(result.errors)
        failure = self.list2reason(result.failures)
        ok = not error and not failure
        self.all_tests_ok.append(ok)
        if ok:
            shutil.rmtree(self.test_working_directory)

    # Tests definitions
    def test_write_xml(self):
        """
        """
        from Sampling.SamplesSelection import write_xml
        import collections
        import filecmp

        samples_per_class = collections.OrderedDict([("11", 5), ("12", 6), ("211", 5),
                                                     ("32", 3), ("31", 4), ("51", 8),
                                                     ("34", 5), ("41", 9), ("222", 4),
                                                     ("221", 4)])
        samples_per_vector = collections.OrderedDict([("1", 4), ("0", 5), ("3", 4),
                                                      ("2", 4), ("5", 6), ("4", 5),
                                                      ("7", 9), ("6", 8), ("9", 5),
                                                      ("8", 3)])
    
        xml_test = os.path.join(self.test_working_directory, "test.xml")
        write_xml(samples_per_class, samples_per_vector, xml_test)
        
        self.assertTrue(filecmp.cmp(self.in_xml, xml_test), msg="")


