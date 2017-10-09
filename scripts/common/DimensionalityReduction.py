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

def CheckFieldCoherency(inputSampleFileName, numberOfDates, numberOfBandsPerDate, numberOfIndices, numberOfMetaDataFields):
    """
    Verify that the input sample file contains the right number of fields according to the number of dates, bands, indices and metadata fields.
    """
    nbFields = fu.getAllFieldsInShape(inputSampleFileName, 'SQLite')
    if nbFields != numberOfDates*(numberOfBandsPerDate+numberOfIndices)+numberOfMetaDataFields:
        raise RuntimeError("The number of fields in "+inputSampleFileName+" does not match")

def BuildFeaturesLists(inputSampleFileName, numberOfDates, numberOfBandsPerDate, numberOfIndices, numberOfMetaDataFields, reductionMode):
    """
    Build a list of lists of the features containing the features to be used for each reduction.
    """
    allFeatures = ["band_"+str(x) for x in range(numberOfDates*(numberOfBandsPerDate+numberOfIndices)+numberOfMetaDataFields)]	
    if reductionMode == 'global':
        return list(allFeatures)
    if reductionMode == 'band':
        raise RuntimeError("band reduction mode not implemented")
    if reductionMode == 'date':
        raise RuntimeError("date reduction mode not implemented")
    else:
        raise RuntimeError("Unknown reduction mode")

    
def TrainDimensionalityReduction(param, Model_file):
	feat = ["band_"+str(x) for x in param['bands']]	
	DRTrain = otb.Registry.CreateApplication("CbDimensionalityReductionTrainer")
	DRTrain.SetParameterString("io.vd",param['Training Sample'])
	DRTrain.SetParameterStringList("feat",feat)
	if param['Image Stats'] is not None:
		print param['Image Stats']
		DRTrain.SetParameterString("io.stats",param['Image Stats'])
	DRTrain.SetParameterString("io.out",Model_file )
	DRTrain.SetParameterString("model","pca")
	DRTrain.SetParameterString("model.pca.dim",param['Dimension'])
	DRTrain.ExecuteAndWriteOutput()

def SampleFilePCAReduction(inputSampleFileName, outputSampleFileName, reductionMode, numberOfDates, numberOfBandsPerDate, numberOfIndices, numberOfMetaDataFields):
    """
    usage : Apply a PCA reduction 

    IN:
    inputSampleFileName [string] : path to a vector file containing training samples
    reductionMode [string] : 'date', 'band', 'global' modes of PCA application
    numberOfDates [int] : number of dates in the time series
    numberOfBandsPerDate [int]
    numberOfIndices [int] : additional features added at the end
    numberOfMetaDataFields [int] : initial attributes like area, land cover type, etc.

    the fields of each sample are supposed to follow this pattern (assuming N metadata fields, K bands, L dates and M additional features:

    meta1, ..., metaN d1b1 d1b2 ... d1bK d2b1 ... dLbK f1d1 ... f1dK f2d1 ... fMdK

    OUT:
    outputSampleFileName [string] : name of the resulting reduced sample file
    """

    CheckFieldCoherency(inputSampleFileName, numberOfDates, numberOfBandsPerDate, numberOfIndices, numberOfMetaDataFields)
    featureList = BuildFeaturesLists(inputSampleFileName, numberOfDates, numberOfBandsPerDate, numberOfIndices, numberOfMetaDataFields, reductionMode)
    for l in featureList:
        TrainDimensionalityReduction(inputSampleFileName)
        
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Apply dimensionality reduction to a sample file")
    parser.add_argument("-in", dest="inSampleFile", help="path to the input sample file",
                        default=None, required=True)
    parser.add_argument("-out", dest="outSampleFile", help="path to the output sample file",
                        default=None, required=True)
    parser.add_argument("-conf", help="path to the configuration file (mandatory)",
                        dest="pathConf", required=True)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)

    SampleFilePCAReduction(inSampleFile, outSampleFile)
