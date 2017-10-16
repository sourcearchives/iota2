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
import filecmp
import DimensionalityReduction as DR

iota2dir = os.environ.get('IOTA2DIR')
iota2_script = iota2dir + "/scripts/common"
iota2_dataTest = iota2dir + "/data/"

class DimensionalityReductionTests(unittest.TestCase):
 
    def setUp(self):
        self.inputSampleFileName = iota2_dataTest+'dim_red_samples.sqlite'
        self.numberOfDates = 21
        self.numberOfBandsPerDate= 6
        self.numberOfIndices = 3
        self.numberOfMetaDataFields = 5
        self.statsFile = iota2_dataTest+'dim_red_stats.xml'
        self.testStatsFile = '/tmp/stats.xml'
 
    def test_checkFieldCoherency(self): 
        DR.CheckFieldCoherency(self.inputSampleFileName, self.numberOfDates,
                               self.numberOfBandsPerDate, self.numberOfIndices,
                               self.numberOfMetaDataFields)

    def test_GenerateFeatureListGlobal(self):
        expected = ['value_'+str(x) for x in
                    range(self.numberOfDates*(self.numberOfBandsPerDate+
                                              self.numberOfIndices))]
        fl = DR.BuildFeaturesLists(self.inputSampleFileName, self.numberOfDates, 
                                   self.numberOfBandsPerDate, self.numberOfIndices,
                                   self.numberOfMetaDataFields,'global')
        self.assertEqual(list(expected), fl)

    def test_GenerateFeatureListDate(self):
        expected = ['value_6', 'value_7', 'value_8', 'value_9', 'value_10', 
                    'value_11', 'value_127', 'value_148', 'value_169']

        fl = DR.BuildFeaturesLists(self.inputSampleFileName, self.numberOfDates, 
                                   self.numberOfBandsPerDate, self.numberOfIndices,
                                   self.numberOfMetaDataFields,'date')
        self.assertEqual(expected, fl[1])

    def test_GenerateFeatureListBand(self):
        # second spectral band
        expected = ['value_'+str(x*self.numberOfBandsPerDate+1) 
                    for x in range(self.numberOfDates)]

        fl = DR.BuildFeaturesLists(self.inputSampleFileName, self.numberOfDates, 
                                   self.numberOfBandsPerDate, self.numberOfIndices,
                                   self.numberOfMetaDataFields,'band')
        self.assertEqual(expected, fl[1])

        # first feature
        expected = ['value_'+str(x+self.numberOfDates*self.numberOfBandsPerDate) 
                    for x in range(self.numberOfDates)]
        fl = DR.BuildFeaturesLists(self.inputSampleFileName, self.numberOfDates, 
                                   self.numberOfBandsPerDate, self.numberOfIndices,
                                   self.numberOfMetaDataFields,'band')
        self.assertEqual(expected, fl[self.numberOfBandsPerDate])

    def test_ComputeFeatureStatistics(self):
        fl = DR.BuildFeaturesLists(self.inputSampleFileName, self.numberOfDates, 
                                   self.numberOfBandsPerDate, self.numberOfIndices,
                                   self.numberOfMetaDataFields,'date')[0]
        DR.ComputeFeatureStatistics(self.inputSampleFileName, self.testStatsFile, 
                                    fl)
        self.assertTrue(filecmp.cmp(self.testStatsFile, self.statsFile, 
                                    shallow=False), msg="Stats files don't match")

if __name__ == '__main__':
    unittest.main()
