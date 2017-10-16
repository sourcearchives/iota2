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

import argparse
import fileUtils as fu
import serviceConfigFile as SCF
import otbApplication as otb

def CheckFieldCoherency(inputSampleFileName, numberOfDates, numberOfBandsPerDate, 
                        numberOfIndices, numberOfMetaDataFields):
    """

    Verify that the input sample file contains the right number of
    fields according to the number of dates, bands, indices and
    metadata fields.

    """
    nbFields = len(fu.getAllFieldsInShape(inputSampleFileName, 'SQLite'))
    if nbFields != (numberOfDates*(numberOfBandsPerDate+numberOfIndices)+
                    numberOfMetaDataFields):
        raise RuntimeError("The number of fields ("+str(nbFields)+
                           ") in "+inputSampleFileName+" does not match")

def BuildFeaturesLists(inputSampleFileName, numberOfDates, numberOfBandsPerDate, 
                       numberOfIndices, numberOfMetaDataFields, 
                       reductionMode='global'):
    """
    Build a list of lists of the features containing the features to be
    used for each reduction.

    'global' reduction mode selects all the features
    'band' reduction mode selects all the dates for each feature
    'date' reduction mode selects all the features for each date
    """
    allFeatures = fu.getAllFieldsInShape(inputSampleFileName, 
                                         'SQLite')[numberOfMetaDataFields:]
    if reductionMode == 'global':
        return list(allFeatures)
    if reductionMode == 'band':
        fl = list()
        for b in range(numberOfBandsPerDate):
            lb = list()
            for d in range(numberOfDates):
                lb.append('value_'+str(numberOfBandsPerDate*d+b))
            fl.append(lb)
        for i in range(numberOfIndices):
            li = list()
            for d in range(numberOfDates):
                li.append('value_'+str(numberOfDates*numberOfBandsPerDate+
                                       numberOfDates*i+d))
            fl.append(li)
        return fl
    if reductionMode == 'date':
        fl = list()
        for d in range(numberOfDates):
            ld = list()
            for b in range(numberOfBandsPerDate):
                ld.append('value_'+str(d*numberOfBandsPerDate+b))
            for i in range(numberOfIndices):
                ld.append('value_'+str(numberOfDates*numberOfBandsPerDate+
                                       numberOfDates*i+d))
            fl.append(ld)
        return fl
    else:
        raise RuntimeError("Unknown reduction mode")

def ComputeFeatureStatistics(inputSampleFileName, outputStatsFile, featureList):
    """Computes the mean and the standard deviation of a set of features
    of a file of samples. It will be used for the dimensionality
    reduction training and reduction applications.
    """
    CStats = otb.Registry.CreateApplication("ComputeOGRLayersFeaturesStatistics")
    CStats.SetParameterString("inshp", inputSampleFileName)
    CStats.SetParameterString("outstats", outputStatsFile)
    CStats.UpdateParameters()
    CStats.SetParameterStringList("feat", featureList)
    CStats.ExecuteAndWriteOutput()


def TrainDimensionalityReduction(inputSampleFileName, outputModelFileName, 
                                 featureList, targetDimension, statsFile = None):

    DRTrain = otb.Registry.CreateApplication("TrainDimensionalityReduction")
    DRTrain.SetParameterString("io.vd",inputSampleFileName)
    DRTrain.SetParameterStringList("feat",featureList)
    if statsFile is not None:
	DRTrain.SetParameterString("io.stats",statsFile)
    DRTrain.SetParameterString("io.out", outputModelFileName)
    DRTrain.SetParameterString("algorithm","pca")
    DRTrain.SetParameterInt("algorithm.pca.dim", targetDimension)
    DRTrain.ExecuteAndWriteOutput()

def SampleFilePCAReduction(inputSampleFileName, outputSampleFileName, 
                           reductionMode, targetDimension, numberOfDates, 
                           numberOfBandsPerDate, numberOfIndices, 
                           numberOfMetaDataFields):
    """usage : Apply a PCA reduction 

    IN:
    inputSampleFileName [string] : path to a vector file containing training samples
    reductionMode [string] : 'date', 'band', 'global' modes of PCA application
    numberOfDates [int] : number of dates in the time series
    numberOfBandsPerDate [int]
    numberOfIndices [int] : additional features added at the end
    numberOfMetaDataFields [int] : initial attributes like area, land cover type, etc.

    the fields of each sample are supposed to follow this pattern
    (assuming N metadata fields, K bands, L dates and M additional
    features:

    meta1, ..., metaN d1b1 d1b2 ... d1bK d2b1 ... dLbK f1d1 ... f1dK f2d1 ... fMdK

    OUT:
    outputSampleFileName [string] : name of the resulting reduced sample file

    """

    CheckFieldCoherency(inputSampleFileName, numberOfDates, numberOfBandsPerDate, 
                        numberOfIndices, numberOfMetaDataFields)
    featureList = BuildFeaturesLists(inputSampleFileName, numberOfDates, 
                                     numberOfBandsPerDate, numberOfIndices, 
                                     numberOfMetaDataFields, reductionMode)
    feats_and_stats = list()
    fl_counter = 0
    for fl in featureList:
        statsFile = 'stats_'+str(fl_counter)
        modelFile = 'model_'+str(fl_counter)
        reducedSampleFile = 'reduced_'+str(fl_counter)
        fl_counter += 1
        feats_and_stats.append((fl, statsFile, reducedSampleFile))
        ComputeFeatureStatistics(inputSampleFileName, statsFile, fl)
        TrainDimensionalityReduction(inputSampleFileName, modelFile, fl, 
                                     targetDimension, statsFile)
        ApplyDimensionalityReduction(inputSampleFileName, reducedSampleFile, 
                                     modelFile, fl, statsFile)
    JoinReducedSampleFiles(feats_and_stats, outputSampleFileName)
        
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=
                                     "Apply dimensionality reduction to a sample file")
    parser.add_argument("-in", dest="inSampleFile", 
                        help="path to the input sample file",
                        default=None, required=True)
    parser.add_argument("-out", dest="outSampleFile", 
                        help="path to the output sample file",
                        default=None, required=True)
    parser.add_argument("-conf", help="path to the configuration file (mandatory)",
                        dest="pathConf", required=True)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)

    SampleFilePCAReduction(inSampleFile, outSampleFile)
