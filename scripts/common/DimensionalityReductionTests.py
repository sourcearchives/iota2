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
import fileUtils as fu

iota2dir = os.environ.get('IOTA2DIR')
iota2_script = iota2dir + "/scripts/common"
iota2_dataTest = iota2dir + "/data/"

class DimensionalityReductionTests(unittest.TestCase):
 
    def setUp(self):
        self.inputSampleFileName = iota2_dataTest+'dim_red_samples.sqlite'
        self.numberOfMetaDataFields = 3
        self.targetDimension = 6
        self.flDate = ['sentinel2_b2_20151230', 'sentinel2_b3_20151230', 
                       'sentinel2_b4_20151230', 'sentinel2_b5_20151230', 
                       'sentinel2_b6_20151230', 'sentinel2_b7_20151230', 
                       'sentinel2_b8_20151230', 'sentinel2_b8a_20151230', 
                       'sentinel2_b11_20151230', 'sentinel2_b12_20151230', 
                       'sentinel2_ndvi_20151230', 'sentinel2_ndwi_20151230', 
                       'sentinel2_brightness_20151230']
        self.statsFile = iota2_dataTest+'dim_red_stats.xml'
        self.testStatsFile = '/tmp/stats.xml'
        self.outputModelFileName = iota2_dataTest+'/model.pca'
        self.testOutputModelFileName = '/tmp/model.pca'
        self.reducedOutputFileName = iota2_dataTest+'/reduced.sqlite'
        self.testReducedOutputFileName = '/tmp/reduced.sqlite'
        self.testJointReducedFile = '/tmp/joint.sqlite'
        self.jointReducedFile = iota2_dataTest+'/joint.sqlite'
        self.outputSampleFileName = iota2_dataTest+'/reduced_output_samples.sqlite'
        self.testOutputSampleFileName = '/tmp/reduced_output_samples.sqlite'

    def test_GetAvailableFeatures(self):

        expected = '20151230'
        feats = DR.GetAvailableFeatures(self.inputSampleFileName, 
                                        self.numberOfMetaDataFields)
        self.assertEqual(feats['sentinel2']['brightness'][0], expected)

        expected = 'b2'
        feats = DR.GetAvailableFeatures(self.inputSampleFileName, 
                                        self.numberOfMetaDataFields,
                                        'date', 'sensor')
        self.assertEqual(feats['20160428']['sentinel2'][0], expected)

        expected = 'sentinel2'
        feats = DR.GetAvailableFeatures(self.inputSampleFileName, 
                                        self.numberOfMetaDataFields,
                                        'date', 'band')
        self.assertEqual(feats['20160428']['b2'][0], expected)


    def test_GenerateFeatureListGlobal(self):
        expected = ['s1aasc_vv_20160113', 's1aasc_vh_20160113', 
                    's1basc_vv_20170630', 's1basc_vh_20170630', 
                    'sentinel2_b2_20151230', 'sentinel2_b3_20151230', 
                    'sentinel2_b4_20151230', 'sentinel2_b5_20151230', 
                    'sentinel2_b6_20151230', 'sentinel2_b7_20151230', 
                    'sentinel2_b8_20151230', 'sentinel2_b8a_20151230', 
                    'sentinel2_b11_20151230', 'sentinel2_b12_20151230', 
                    'sentinel2_b2_20160109', 'sentinel2_b3_20160109']
        fl = DR.BuildFeaturesLists(self.inputSampleFileName, 
                                   self.numberOfMetaDataFields,'global')
        self.assertEqual(expected, fl[:len(expected)])

    def test_GenerateFeatureListDate(self):
        fl = DR.BuildFeaturesLists(self.inputSampleFileName, 
                                   self.numberOfMetaDataFields,'date')
        self.assertEqual(self.flDate, fl[0])

    def test_GenerateFeatureListBand(self):
        # second spectral band
        expected = ['sentinel2_b12_20151230', 'sentinel2_b12_20160109', 
                    'sentinel2_b12_20160119', 'sentinel2_b12_20160129', 
                    'sentinel2_b12_20160208', 'sentinel2_b12_20160218', 
                    'sentinel2_b12_20160228', 'sentinel2_b12_20160309', 
                    'sentinel2_b12_20160319', 'sentinel2_b12_20160329', 
                    'sentinel2_b12_20160408', 'sentinel2_b12_20160418', 
                    'sentinel2_b12_20160428', 'sentinel2_b12_20160508', 
                    'sentinel2_b12_20160518', 'sentinel2_b12_20160528', 
                    'sentinel2_b12_20160607', 'sentinel2_b12_20160617', 
                    'sentinel2_b12_20160627', 'sentinel2_b12_20160707', 
                    'sentinel2_b12_20160710']

        fl = DR.BuildFeaturesLists(self.inputSampleFileName, 
                                   self.numberOfMetaDataFields,'band')
        self.assertEqual(expected, fl[1])


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
        inputDimensions = len(fu.getAllFieldsInShape(self.inputSampleFileName, 
                                                 'SQLite')[self.numberOfMetaDataFields:])
        DR.ApplyDimensionalityReduction(self.inputSampleFileName, 
                                        self.testReducedOutputFileName,
                                        self.outputModelFileName, self.flDate, 
                                        outputFeatures, inputDimensions,
                                        statsFile = self.statsFile, 
                                        pcaDimension = len(outputFeatures), 
                                        writingMode = 'overwrite')
        self.assertTrue(filecmp.cmp(self.testReducedOutputFileName, 
                                    self.reducedOutputFileName, 
                                    shallow=False), msg="Reduced files don't match")

    def test_JoinReducedSampleFiles(self):
        fl = [self.reducedOutputFileName, self.reducedOutputFileName]
        outputFeatures = ['pc_'+str(x+1) for x in range(5)]
        DR.JoinReducedSampleFiles(fl, self.testJointReducedFile, outputFeatures)
        self.assertTrue(filecmp.cmp(self.testJointReducedFile, 
                                    self.jointReducedFile, 
                                    shallow=False), msg="Joined files don't match")

    def test_SampleFilePCAReduction(self):
        DR.SampleFilePCAReduction(self.inputSampleFileName,
                                  self.testOutputSampleFileName, 'date',
                                  self.targetDimension,
                                  self.numberOfMetaDataFields)
        self.assertTrue(filecmp.cmp(self.testOutputSampleFileName, 
                                    self.outputSampleFileName, 
                                    shallow=False), msg="Output sample files don't match")

if __name__ == '__main__':
    unittest.main()
