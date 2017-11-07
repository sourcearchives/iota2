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
        self.numberOfMetaDataFields = 5
        self.targetDimension = 6
        self.flDate = ['landsat8_b1_20140118', 'landsat8_b2_20140118',
                       'landsat8_b3_20140118', 'landsat8_b4_20140118',
                       'landsat8_b5_20140118', 'landsat8_b6_20140118',
                       'landsat8_b7_20140118', 'landsat8_ndvi_20140118',
                       'landsat8_ndwi_20140118', 'landsat8_brightness_20140118']
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
        self.configFile = iota2_dataTest+'/config/test_config_serviceConfigFile.cfg'

    def test_GetAvailableFeatures(self):

        expected = '20140118'
        feats = DR.GetAvailableFeatures(self.inputSampleFileName, 
                                        self.numberOfMetaDataFields)
        self.assertEqual(feats['landsat8']['brightness'][0], expected)

        expected = 'b1'
        feats = DR.GetAvailableFeatures(self.inputSampleFileName, 
                                        self.numberOfMetaDataFields,
                                        'date', 'sensor')
        self.assertEqual(feats['20141017']['landsat8'][0], expected)

        expected = 'landsat8'
        feats = DR.GetAvailableFeatures(self.inputSampleFileName, 
                                        self.numberOfMetaDataFields,
                                        'date', 'band')
        self.assertEqual(feats['20141118']['b2'][0], expected)

    def test_GenerateFeatureListGlobal(self):
        expected = ['landsat8_b1_20140118', 
                    'landsat8_b2_20140118', 'landsat8_b3_20140118', 
                    'landsat8_b4_20140118', 'landsat8_b5_20140118', 
                    'landsat8_b6_20140118', 'landsat8_b7_20140118', 
                    'landsat8_b1_20140203', 'landsat8_b2_20140203', 
                    'landsat8_b3_20140203', 'landsat8_b4_20140203', 
                    'landsat8_b5_20140203', 'landsat8_b6_20140203', 
                    'landsat8_b7_20140203', 'landsat8_b1_20140219', 
                    'landsat8_b2_20140219', 'landsat8_b3_20140219', 
                    'landsat8_b4_20140219', 'landsat8_b5_20140219', 
                    'landsat8_b6_20140219', 'landsat8_b7_20140219', 
                    'landsat8_b1_20140307', 'landsat8_b2_20140307', 
                    'landsat8_b3_20140307', 'landsat8_b4_20140307', 
                    'landsat8_b5_20140307', 'landsat8_b6_20140307', 
                    'landsat8_b7_20140307', 'landsat8_b1_20140323', 
                    'landsat8_b2_20140323', 'landsat8_b3_20140323', 
                    'landsat8_b4_20140323', 'landsat8_b5_20140323', 
                    'landsat8_b6_20140323', 'landsat8_b7_20140323']
        fl = DR.BuildFeaturesLists(self.inputSampleFileName, 
                                   self.numberOfMetaDataFields,'global')
        self.assertEqual(expected, fl[:len(expected)])

    def test_GenerateFeatureListDate(self):
        fl = DR.BuildFeaturesLists(self.inputSampleFileName, 
                                   self.numberOfMetaDataFields,'date')
        self.assertEqual(self.flDate, fl[0])

    def test_GenerateFeatureListBand(self):
        # second spectral band
        expected = ['landsat8_b2_20140118', 'landsat8_b2_20140203', 
                    'landsat8_b2_20140219', 'landsat8_b2_20140307', 
                    'landsat8_b2_20140323', 'landsat8_b2_20140408', 
                    'landsat8_b2_20140424', 'landsat8_b2_20140510', 
                    'landsat8_b2_20140526', 'landsat8_b2_20140611', 
                    'landsat8_b2_20140627', 'landsat8_b2_20140713', 
                    'landsat8_b2_20140729', 'landsat8_b2_20140814', 
                    'landsat8_b2_20140830', 'landsat8_b2_20140915', 
                    'landsat8_b2_20141001', 'landsat8_b2_20141017', 
                    'landsat8_b2_20141102', 'landsat8_b2_20141118', 
                    'landsat8_b2_20141204', 'landsat8_b2_20141220', 
                    'landsat8_b2_20141229']
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

    def test_SampleFileDimensionalityReduction(self):
        DR.SampleFileDimensionalityReduction(self.inputSampleFileName,
                                             self.testOutputSampleFileName,
                                             self.configFile)
        self.assertTrue(filecmp.cmp(self.testOutputSampleFileName, 
                                    self.outputSampleFileName, 
                                    shallow=False), msg="Output sample files don't match")

if __name__ == '__main__':
    unittest.main()
