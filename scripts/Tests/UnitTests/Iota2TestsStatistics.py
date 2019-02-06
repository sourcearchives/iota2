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

# python -m unittest Iota2TestsStatistics

import os
import sys
import shutil
import filecmp
import numpy as np
import unittest

IOTA2DIR = os.environ.get('IOTA2DIR')

if IOTA2DIR is None:
    raise Exception ("IOTA2DIR environment variable must be set")

# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True

iota2_script = IOTA2DIR + "/scripts"
sys.path.append(iota2_script)

from Common import FileUtils as fut
from Tests.UnitTests import Iota2Tests as testutils
from simplification import ZonalStats as zs
from simplification import computeStats as cs

class iota_testZonalStats(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.group_test_name = "iota_testZonalStats"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data", self.group_test_name)
        self.all_tests_ok = []

        # Tests directory
        self.test_working_directory = None
        if os.path.exists(self.iota2_tests_directory):
            shutil.rmtree(self.iota2_tests_directory)
        os.mkdir(self.iota2_tests_directory)

        self.wd = os.path.join(self.iota2_tests_directory, "wd/")
        self.out = os.path.join(self.iota2_tests_directory, "out/")
        self.classif = os.path.join(IOTA2DIR, "data", "references/sampler/final/Classif_Seed_0.tif")
        self.validity = os.path.join(IOTA2DIR, "data", "references/sampler/final/PixelsValidity.tif")
        self.confid = os.path.join(IOTA2DIR, "data", "references/sampler/final/PixelsValidity.tif")
        self.vector = os.path.join(IOTA2DIR, "data", "references/posttreat/vectors/")
        self.nomenclature = os.path.join(IOTA2DIR, "data", "references/posttreat/nomenclature.txt")
        self.vectorfile = os.path.join(self.vector, "classif.shp")
        self.outfilestats = os.path.join(IOTA2DIR, "data", "references/posttreat/stats_classif")
        self.outfilevector = os.path.join(self.iota2_tests_directory, self.wd, "final.shp")
        self.outfilevectorref = os.path.join(self.vector, "classifjoin.shp")        
        self.outzip = os.path.join(self.iota2_tests_directory, self.wd, "classif.zip")       
        self.outzipref = os.path.join(self.vector, "classif.zip")
        self.gdallib = os.environ.get('GDAL224DIR')

        if self.gdallib is None:
            raise Exception("GDAL224DIR not initialized (Version of gdal greater or equal to 2.2.4")


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

        if os.path.exists(self.wd):
            shutil.rmtree(self.wd, ignore_errors=True)
            os.mkdir(self.wd)
        else:
            os.mkdir(self.wd)

        if os.path.exists(self.out):
            shutil.rmtree(self.out, ignore_errors=True)
            os.mkdir(self.out)
        else:
            os.mkdir(self.out)   

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
    def test_iota2_Statistics(self):
        """Test how many samples must be add to the sample set
        """
        
        # Statistics test
        zs.computZonalStats(self.wd, [self.classif, self.confid, self.validity], self.vector, self.wd, self.gdallib)
        self.assertTrue(filecmp.cmp(self.outfilestats, os.path.join(self.wd, "stats_classif")), "Generated shapefile vector does not fit with shapefile reference file")

        for ext in ['.shp', '.dbf', '.shx', '.prj']:
            shutil.copy(os.path.splitext(self.vectorfile)[0] + ext, self.wd)

        # Final integration test
        #cs.computeStats(self.wd, os.path.join(self.wd, "stats_classif"), self.nomenclature, self.wd, self.outfilevector, True)
        cs.computeStats(self.wd, os.path.join(self.wd, "stats_classif"), self.wd, self.outfilevector, True)        
        os.system("unzip %s -d %s"%(self.outzipref, self.wd))
        os.system("unzip %s -d %s"%(self.outzip, self.out))
        self.assertTrue(testutils.compareVectorFile(self.outfilevectorref, os.path.join(self.wd, "classif.shp"), 'coordinates', 'polygon', "ESRI Shapefile"), \
                        "Generated shapefile vector does not fit with shapefile reference file")

        # remove temporary folders
        if os.path.exists(self.wd):shutil.rmtree(self.wd, ignore_errors=True)
        if os.path.exists(self.out):shutil.rmtree(self.out, ignore_errors=True)
