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

# python -m unittest Iota2TestsVectorTools

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
from VectorTools import AddFieldArea as afa
from VectorTools import AddFieldID as afi
from VectorTools import AddFieldPerimeter as afp
from VectorTools import BufferOgr as bfo
from VectorTools import ChangeNameField as cnf
from VectorTools import ConditionalFieldRecode as cfr
from VectorTools import DeleteField as df
from VectorTools import vector_functions as vf
from VectorTools import spatialOperations as so
from VectorTools import checkGeometryAreaThreshField as check
from VectorTools import splitByArea as sba
from VectorTools import MergeFiles as mf

class iota_testVectortools(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.group_test_name = "iota_testVectortools"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data", self.group_test_name)
        self.all_tests_ok = []

        # Tests directory
        self.test_working_directory = None
        if os.path.exists(self.iota2_tests_directory):
            shutil.rmtree(self.iota2_tests_directory)
        os.mkdir(self.iota2_tests_directory)

        self.wd = os.path.join(self.iota2_tests_directory, "wd/")
        self.out = os.path.join(self.iota2_tests_directory, "out/")
        self.classif = os.path.join(IOTA2DIR, "data", "references/vectortools/classif.shp")
        self.inter = os.path.join(IOTA2DIR, "data", "references/vectortools/region.shp")
        self.classifwd = os.path.join(self.out, "classif.shp")
        self.classifout = os.path.join(IOTA2DIR, "data", "references/vectortools/classifout.shp")
        self.outinter = os.path.join(self.wd, "inter.shp")       

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
    def test_iota2_vectortools(self):
        """Test how many samples must be add to the sample set
        """

        # Add Field
        for ext in ['.shp', '.dbf', '.shx', '.prj']:
            shutil.copyfile(os.path.splitext(self.classif)[0] + ext, os.path.splitext(self.classifwd)[0] + ext)

        afp.addFieldPerimeter(self.classifwd)
        tmpbuff = os.path.join(self.wd, "tmpbuff.shp")
        bfo.bufferPoly(self.classifwd, tmpbuff, -10)
        for ext in ['.shp', '.dbf', '.shx', '.prj']:
            shutil.copyfile(os.path.splitext(tmpbuff)[0] + ext, os.path.splitext(self.classifwd)[0] + ext)
            
        cnf.changeName(self.classifwd, "Classe", "class")
        self.assertEqual(vf.getNbFeat(self.classifwd), 144, "Number of features does not fit")
        self.assertEqual(vf.getFields(self.classifwd), ['Validmean', 'Validstd', 'Confidence', 'Hiver', 'Ete', \
                                                        'Feuillus', 'Coniferes', 'Pelouse', 'Landes', 'UrbainDens', 'UrbainDiff', \
                                                        'ZoneIndCom', 'Route', 'PlageDune', 'SurfMin', 'Eau', 'GlaceNeige', 'Prairie', \
                                                        'Vergers', 'Vignes', 'Perimeter', 'class'], "List of fields does not fit") 
        self.assertEqual(vf.ListValueFields(self.classifwd, "class"), ['211', '31', '11', '42', '36', '32', '43', '12', '51', '222'], \
                        "Values of field 'class' do not fit")
        self.assertEqual(vf.getFieldType(self.classifwd, "class"), str, \
                         "Type of field 'class' (%s) do not fit, 'str' expected"%(vf.getFieldType(self.classifwd, "class")))        
       
        cfr.conFieldRecode(self.classifwd, "class", "mask", 11, 0)
        so.intersectSqlites(self.classifwd, self.inter, self.wd, self.outinter, 2154, "intersection", ['class', 'Validmean', 'Validstd', 'Confidence','ID', 'Perimeter', 'Aire', "mask"])
        check.checkGeometryAreaThreshField(self.outinter, 100, 1, self.classifwd)
        self.assertEqual(vf.getNbFeat(self.classifwd), 102, "Number of features does not fit")

        sba.extractFeatureFromShape(self.classifwd, 3, "mask", self.wd)
        mf.mergeVectors([os.path.join(self.wd, "classif00.shp"), os.path.join(self.wd, "classif01.shp"), os.path.join(self.wd, "classif02.shp")], self.classifwd)
        self.assertEqual(vf.getFirstLayer(self.classifwd), 'classif', "Layer does not exist in this shapefile")

        self.assertTrue(testutils.compareVectorFile(self.classifwd, self.classifout, 'coordinates', 'polygon', "ESRI Shapefile"), \
                        "Generated shapefile vector does not fit with shapefile reference file")
