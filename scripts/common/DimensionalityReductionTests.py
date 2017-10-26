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
        self.numberOfInputDimensions = (self.numberOfDates*(
                                            self.numberOfBandsPerDate+
                                            self.numberOfIndices))
        self.targetDimension = 6
        self.flDate = ['value_0', 'value_1', 'value_2', 'value_3', 'value_4', 
                       'value_5', 'value_126', 'value_147', 'value_168']
        self.statsFile = iota2_dataTest+'dim_red_stats.xml'
        self.testStatsFile = '/tmp/stats.xml'
        self.outputModelFileName = iota2_dataTest+'/model.pca'
        self.testOutputModelFileName = '/tmp/model.pca'
        self.reducedOutputFileName = iota2_dataTest+'/reduced.sqlite'
        self.testReducedOutputFileName = '/tmp/reduced.sqlite'
        self.testJointReducedFiles = '/tmp/joint.sqlite'
 
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
        DR.ComputeFeatureStatistics(self.inputSampleFileName, self.testStatsFile, 
                                    self.flDate)
        self.assertTrue(filecmp.cmp(self.testStatsFile, self.statsFile, 
                                    shallow=False), msg="Stats files don't match")

    def test_TrainDimensionalityReduction(self):
        DR.TrainDimensionalityReduction(self.inputSampleFileName, 
                                        self.testOutputModelFileName, self.flDate, 
                                        self.targetDimension, self.statsFile)
        self.assertTrue(filecmp.cmp(self.testOutputModelFileName, 
                                    self.outputModelFileName, 
                                    shallow=False), msg="Model files don't match")
    def test_ApplyDimensionalityReduction(self):
        outputFeatures = ['pc_'+str(x+1) for x in range(5)]
        DR.ApplyDimensionalityReduction(self.inputSampleFileName, 
                                        self.testReducedOutputFileName,
                                        self.outputModelFileName, self.flDate, 
                                        outputFeatures, 
                                        self.numberOfInputDimensions,
                                        statsFile = self.statsFile, 
                                        pcaDimension = len(outputFeatures), 
                                        writingMode = 'overwrite')
        self.assertTrue(filecmp.cmp(self.testReducedOutputFileName, 
                                    self.reducedOutputFileName, 
                                    shallow=False), msg="Reduced files don't match")

    def test_JoinReducedSampleFiles(self):
        fl = [self.reducedOutputFileName, self.reducedOutputFileName]
        DR.JoinReducedSampleFiles(fl, self.testJointReducedFiles)
if __name__ == '__main__':
    unittest.main()
