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
import sys
import shutil
import filecmp

iota2dir = os.environ.get('IOTA2DIR')
iota2_script = iota2dir + "/scripts"
sys.path.append(iota2_script)

from Common import FileUtils as fu
from Sampling import DimensionalityReduction as DR
iota2_dataTest = iota2dir + "/data/"


class DimensionalityReductionTests(unittest.TestCase):
 
    def setUp(self):
        self.inputSampleFileName = iota2_dataTest+'dim_red_samples.sqlite'
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
        self.configFile = os.path.join(iota2dir, "config", "Config_4Tuiles_Multi_FUS_Confidence.cfg")
    def test_GetAvailableFeatures(self):

        expected = '20140118'
        (feats, metaDataFields) = DR.GetAvailableFeatures(self.inputSampleFileName)
        self.assertEqual(feats['landsat8']['brightness'][0], expected)

        expected = 'b1'
        (feats, metaDataFields) = DR.GetAvailableFeatures(self.inputSampleFileName, 
                                        'date', 'sensor')
        self.assertEqual(feats['20141017']['landsat8'][0], expected)

        expected = 'landsat8'
        (feats, metaDataFields) = DR.GetAvailableFeatures(self.inputSampleFileName, 
                                                                  'date', 'band')
        self.assertEqual(feats['20141118']['b2'][0], expected)

    def test_GenerateFeatureListGlobal(self):
        expected = [['landsat8_b1_20140118', 
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
                    'landsat8_b6_20140323', 'landsat8_b7_20140323']]

        (fl, metaDataFields) = DR.BuildFeaturesLists(self.inputSampleFileName, 
                                                             'global')
        self.assertEqual(expected[0], fl[0][:len(expected[0])])

    def test_GenerateFeatureListDate(self):
        (fl, metaDataFields) = DR.BuildFeaturesLists(self.inputSampleFileName, 
                                                             'date')
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
        (fl, metaDataFields) = DR.BuildFeaturesLists(self.inputSampleFileName, 
                                                             'band')
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
        outputFeatures = ['reduced_'+str(x+1) for x in range(5)]
        (dummy, metaDataFields) = DR.BuildFeaturesLists(self.inputSampleFileName)
        numberOfMetaDataFields = len(metaDataFields)
        inputDimensions = len(fu.getAllFieldsInShape(self.inputSampleFileName, 
                                                 'SQLite')[numberOfMetaDataFields:])
        DR.ApplyDimensionalityReduction(self.inputSampleFileName, 
                                        self.testReducedOutputFileName,
                                        self.outputModelFileName, self.flDate, 
                                        outputFeatures, inputDimensions,
                                        statsFile = self.statsFile, 
                                        writingMode = 'overwrite')
        self.assertTrue(filecmp.cmp(self.testReducedOutputFileName, 
                                    self.reducedOutputFileName, 
                                    shallow=False), msg="Reduced files don't match")

    def test_JoinReducedSampleFiles(self):
        
        from Iota2Tests import compareSQLite

        fl = [self.reducedOutputFileName, self.reducedOutputFileName]
        outputFeatures = ['reduced_'+str(x+1) for x in range(5)]
        DR.JoinReducedSampleFiles(fl, self.testJointReducedFile, outputFeatures)

        self.assertTrue(compareSQLite(self.testJointReducedFile,
                                      self.jointReducedFile,
                                      CmpMode="coordinates"),
                        msg="Joined files don't match")


        #self.assertTrue(filecmp.cmp(self.testJointReducedFile, 
        #                            self.jointReducedFile, 
        #                            shallow=False), msg="Joined files don't match")

    def test_SampleFilePCAReduction(self):
        from Iota2Tests import compareSQLite

        test_testOutputSampleFileName = iota2_dataTest + "/" + self.testOutputSampleFileName

        DR.SampleFilePCAReduction(self.inputSampleFileName, 
                                  test_testOutputSampleFileName, 'date',
                                  self.targetDimension, tmpDir=os.path.join(iota2_dataTest, "tmp"))

        self.assertTrue(compareSQLite(test_testOutputSampleFileName,
                                      self.outputSampleFileName,
                                      CmpMode="coordinates"),
                        msg="Output sample files don't match")

        #~ self.assertTrue(filecmp.cmp(test_testOutputSampleFileName, 
                                    #~ self.outputSampleFileName, 
                                    #~ shallow=False), msg="Output sample files don't match")

    # """
    # def test_SampleFileDimensionalityReduction(self):
    #     outpath = iota2_dataTest = iota2dir + "/data/tmp/learningSamples/reduced"
    #     if not os.path.exists(outpath):
    #         os.makedirs(outpath)
    #     basename = os.path.basename(self.inputSampleFileName)
    #     ifile = iota2dir+"/data/tmp/learningSamples/"+basename
    #     shutil.copyfile(self.inputSampleFileName, ifile) 
    #     ofile = outpath+'/reduced_output_samples.sqlite'
    #     DR.SampleFileDimensionalityReduction(ifile, ofile,
    #                                          self.configFile)
    #     self.assertTrue(filecmp.cmp(ofile, 
    #                                 self.outputSampleFileName, 
    #                                 shallow=False), msg="Output sample files don't match")
    # """

    def test_BuildChannelGroups(self):
        cg = DR.BuildChannelGroups(self.configFile)
        expected = [['Channel1', 'Channel2', 'Channel3', 'Channel4', 'Channel5', 'Channel6', 'Channel7', 'Channel162', 'Channel185', 'Channel208'],
                    ['Channel8', 'Channel9', 'Channel10', 'Channel11', 'Channel12', 'Channel13', 'Channel14', 'Channel163', 'Channel186', 'Channel209'],
                    ['Channel15', 'Channel16', 'Channel17', 'Channel18', 'Channel19', 'Channel20', 'Channel21', 'Channel164', 'Channel187', 'Channel210'],
                    ['Channel22', 'Channel23', 'Channel24', 'Channel25', 'Channel26', 'Channel27', 'Channel28', 'Channel165', 'Channel188', 'Channel211'],
                    ['Channel29', 'Channel30', 'Channel31', 'Channel32', 'Channel33', 'Channel34', 'Channel35', 'Channel166', 'Channel189', 'Channel212'],
                    ['Channel36', 'Channel37', 'Channel38', 'Channel39', 'Channel40', 'Channel41', 'Channel42', 'Channel167', 'Channel190', 'Channel213'],
                    ['Channel43', 'Channel44', 'Channel45', 'Channel46', 'Channel47', 'Channel48', 'Channel49', 'Channel168', 'Channel191', 'Channel214'],
                    ['Channel50', 'Channel51', 'Channel52', 'Channel53', 'Channel54', 'Channel55', 'Channel56', 'Channel169', 'Channel192', 'Channel215'],
                    ['Channel57', 'Channel58', 'Channel59', 'Channel60', 'Channel61', 'Channel62', 'Channel63', 'Channel170', 'Channel193', 'Channel216'],
                    ['Channel64', 'Channel65', 'Channel66', 'Channel67', 'Channel68', 'Channel69', 'Channel70', 'Channel171', 'Channel194', 'Channel217'],
                    ['Channel71', 'Channel72', 'Channel73', 'Channel74', 'Channel75', 'Channel76', 'Channel77', 'Channel172', 'Channel195', 'Channel218'],
                    ['Channel78', 'Channel79', 'Channel80', 'Channel81', 'Channel82', 'Channel83', 'Channel84', 'Channel173', 'Channel196', 'Channel219'],
                    ['Channel85', 'Channel86', 'Channel87', 'Channel88', 'Channel89', 'Channel90', 'Channel91', 'Channel174', 'Channel197', 'Channel220'],
                    ['Channel92', 'Channel93', 'Channel94', 'Channel95', 'Channel96', 'Channel97', 'Channel98', 'Channel175', 'Channel198', 'Channel221'],
                    ['Channel99', 'Channel100', 'Channel101', 'Channel102', 'Channel103', 'Channel104', 'Channel105', 'Channel176', 'Channel199', 'Channel222'],
                    ['Channel106', 'Channel107', 'Channel108', 'Channel109', 'Channel110', 'Channel111', 'Channel112', 'Channel177', 'Channel200', 'Channel223'],
                    ['Channel113', 'Channel114', 'Channel115', 'Channel116', 'Channel117', 'Channel118', 'Channel119', 'Channel178', 'Channel201', 'Channel224'],
                    ['Channel120', 'Channel121', 'Channel122', 'Channel123', 'Channel124', 'Channel125', 'Channel126', 'Channel179', 'Channel202', 'Channel225'],
                    ['Channel127', 'Channel128', 'Channel129', 'Channel130', 'Channel131', 'Channel132', 'Channel133', 'Channel180', 'Channel203', 'Channel226'],
                    ['Channel134', 'Channel135', 'Channel136', 'Channel137', 'Channel138', 'Channel139', 'Channel140', 'Channel181', 'Channel204', 'Channel227'],
                    ['Channel141', 'Channel142', 'Channel143', 'Channel144', 'Channel145', 'Channel146', 'Channel147', 'Channel182', 'Channel205', 'Channel228'],
                    ['Channel148', 'Channel149', 'Channel150', 'Channel151', 'Channel152', 'Channel153', 'Channel154', 'Channel183', 'Channel206', 'Channel229'],
                    ['Channel155', 'Channel156', 'Channel157', 'Channel158', 'Channel159', 'Channel160', 'Channel161', 'Channel184', 'Channel207', 'Channel230']]
        self.assertEqual(expected, cg)
        
    def test_ApplyDimensionalityReductionToFeatureStack(self):
        imageStack = iota2_dataTest+'/230feats.tif'
        modelList = [self.outputModelFileName]*len(DR.BuildChannelGroups(self.configFile))
        print "Models", modelList
        (app, other) = DR.ApplyDimensionalityReductionToFeatureStack(self.configFile, imageStack, 
                                                                     modelList)
        app.SetParameterString("out","/tmp/reducedStack.tif")
        app.ExecuteAndWriteOutput()

    def test_ApplyDimensionalityReductionToFeatureStackPipeline(self):
        inimage = iota2_dataTest+'/230feats.tif'
        import otbApplication as otb
        app = otb.Registry.CreateApplication("ExtractROI")
        app.SetParameterString("in", inimage)
        app.Execute()
        modelList = [self.outputModelFileName]*len(DR.BuildChannelGroups(self.configFile))
        (appdr, other) = DR.ApplyDimensionalityReductionToFeatureStack(self.configFile, app, 
                                                                     modelList)
        appdr.SetParameterString("out","/tmp/reducedStackPipeline.tif")
        appdr.ExecuteAndWriteOutput()

if __name__ == '__main__':
    unittest.main()
