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

# python -m unittest Iota2TestsSerialisation

import os
import sys
import shutil
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
from simplification import searchCrownTile as sct
from simplification import buildCrownRaster as bcr
from simplification import GridGenerator as gridg
from simplification import MergeTileRasters as mtr


class iota_testSerialisation(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.group_test_name = "iota_testSerialisation"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data", self.group_test_name)
        self.all_tests_ok = []

        # Tests directory
        self.test_working_directory = None
        if os.path.exists(self.iota2_tests_directory):
            shutil.rmtree(self.iota2_tests_directory)
        os.mkdir(self.iota2_tests_directory)

        self.rasterclump = os.path.join(os.path.join(IOTA2DIR, "data", "references/posttreat/clump32bits.tif"))
        self.raster = os.path.join(os.path.join(IOTA2DIR, "data", "references/posttreat/classif_clump.tif"))        
        self.wd = os.path.join(self.iota2_tests_directory, "wd")
        self.out = os.path.join(self.iota2_tests_directory, "out")
        self.outpathtile = os.path.join(self.iota2_tests_directory, self.out, "tiles")
        self.outfile = os.path.join(self.iota2_tests_directory, self.out, "grid.shp")
        self.outfileref = os.path.join(os.path.join(IOTA2DIR, "data", "references/posttreat/grid.shp"))
        self.outseria = os.path.join(self.iota2_tests_directory, self.out, "tiles/crown_0.tif")
        self.outtile = os.path.join(self.iota2_tests_directory, self.out, "tiles/tile_0.tif")
        self.outseriaref = os.path.join(os.path.join(IOTA2DIR, "data", "references/posttreat/tiles/crown_0.tif"))
        self.outtileref = os.path.join(os.path.join(IOTA2DIR, "data", "references/posttreat/tiles/tile_0.tif"))        
        self.outfilevect = os.path.join(self.iota2_tests_directory, self.out, "classif.shp")
        self.outfilevectname = os.path.join(self.iota2_tests_directory, self.out, "classifmontagne.shp")        
        self.vector = os.path.join(os.path.join(IOTA2DIR, "data", "references/posttreat/classifmontagne.shp"))
        self.clipfile = os.path.join(os.path.join(IOTA2DIR, "data", "references/posttreat/region.shp"))
        self.grasslib = os.environ.get('GRASSDIR')

        if self.grasslib is None:
            raise Exception("GRASSDIR not initialized")

        if not os.path.exists(os.path.join(self.grasslib, 'bin')):
            raise Exception("GRASSDIR '%s' not well initialized"%(self.grasslib))


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

        if os.path.exists(self.outpathtile):
            shutil.rmtree(self.outpathtile, ignore_errors=True)
            os.mkdir(self.outpathtile)
        else:
            os.mkdir(self.outpathtile)   

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
    def test_iota2_regularisation(self):
        """Test how many samples must be add to the sample set
        """

        # Grid generation test
        gridg.grid_generate(self.outfile, 2, 2154, self.rasterclump)
        self.assertTrue(testutils.compareVectorFile(self.outfile, self.outfileref, 'coordinates', 'polygon', "ESRI Shapefile"), \
                        "Generated grid shapefile vector does not fit with reference file")

        # Crown entities test
        sct.searchCrownTile(self.wd, self.raster, self.rasterclump, 128, self.outfileref, self.outpathtile, 1, 0)

        outtest = testutils.rasterToArray(self.outseria)
        outref = testutils.rasterToArray(self.outseriaref)        
        self.assertTrue(np.array_equal(outtest, outref))        

        # Crown building test        
        bcr.manageBlocks(self.outpathtile, 0, 20, self.wd, self.outpathtile, 128)
        
        outtest = testutils.rasterToArray(self.outtile)
        outtileref = testutils.rasterToArray(self.outtileref)
        self.assertTrue(np.array_equal(outtest, outtileref))

        # Vectorisation test
        mtr.tilesRastersMergeVectSimp(self.wd, self.outfileref, self.outfilevect, self.grasslib, 1000, \
                                      "class", self.clipfile, "region", "montagne", "FID", "tile_", self.outpathtile, \
                                      10, 10, True)

        self.assertTrue(testutils.compareVectorFile(self.vector, self.outfilevectname, 'coordinates', 'polygon', "ESRI Shapefile"), \
                        "Generated shapefile vector does not fit with shapefile reference file")

        # remove temporary folders
        if os.path.exists(self.wd):shutil.rmtree(self.wd, ignore_errors=True)
        if os.path.exists(self.out):shutil.rmtree(self.out, ignore_errors=True)


