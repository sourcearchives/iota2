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
import argparse,shutil,os,Sensors,ast
from config import Config
import otbApplication as otb
import fileUtils as fu
from Utils import Opath
import prepareStack,otbAppli
import serviceConfigFile as SCF 

def filterOTB_output(raster,mask,output,outputType=otb.ImagePixelType_uint8):
        
    bandMathFilter = otb.Registry.CreateApplication("BandMath")
    bandMathFilter.SetParameterString("exp","im2b1>=1?im1b1:0")
    bandMathFilter.SetParameterStringList("il",[raster,mask])
    bandMathFilter.SetParameterString("ram","10000")
    bandMathFilter.SetParameterString("out",output+"?&streaming:type=stripped&streaming:sizemode=nbsplits&streaming:sizevalue=10")
    if outputType: 
        bandMathFilter.SetParameterOutputImagePixelType("out",outputType)
    bandMathFilter.ExecuteAndWriteOutput()
        
def computeClasifications(model,outputClassif,confmap,MaximizeCPU,Classifmask,stats,AllFeatures,*ApplicationList):
    
    classifier = otb.Registry.CreateApplication("ImageClassifier")
    classifier.SetParameterInputImage("in",AllFeatures.GetParameterOutputImage("out"))
    classifier.SetParameterString("out",outputClassif)
    classifier.SetParameterOutputImagePixelType("out",otb.ImagePixelType_uint8)
    classifier.SetParameterString("confmap",confmap)
    classifier.SetParameterString("model",model)
    if not MaximizeCPU: 
        classifier.SetParameterString("mask",Classifmask)
    if stats: 
        classifier.SetParameterString("imstat",stats)
    classifier.SetParameterString("ram","5000")
    return classifier,AllFeatures
        

def launchClassification(tempFolderSerie,Classifmask,model,stats,
                         outputClassif,confmap,pathWd,cfg,pixType,
                         MaximizeCPU=True):

    if not isinstance(cfg,SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    tiles = (cfg.getParam('chain', 'listTile')).split()
    tile = fu.findCurrentTileInString(Classifmask,tiles)
    wMode = ast.literal_eval(cfg.getParam('GlobChain', 'writeOutputs'))
    featuresPath = cfg.getParam('chain', 'featuresPath')
    outputPath = cfg.getParam('chain', 'outputPath')
    wd = pathWd
    if not pathWd: 
        wd = featuresPath
        os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = "5"
    AllGapFill,AllRefl,AllMask,datesInterp,realDates,dep = otbAppli.gapFilling(cfg,tile,wMode=wMode,\
                                                            featuresPath=None,workingDirectory=wd)
    if wMode:
        for currentGapFillSensor in AllGapFill:
            currentGapFillSensor.ExecuteAndWriteOutput()
    else:
        for currentGapFillSensor in AllGapFill: 
            currentGapFillSensor.Execute()
    nbDates = [fu.getNbDateInTile(currentDateFile) for currentDateFile in datesInterp]

    AllFeatures,ApplicationList,a,b,c,d,e = otbAppli.computeFeatures(cfg, nbDates,tile,
                                                                     AllGapFill,AllRefl,
                                                                     AllMask,datesInterp,realDates)
    if wMode:
        AllFeatures.ExecuteAndWriteOutput()
    else:
        AllFeatures.Execute()
    classifier,inputStack = computeClasifications(model,outputClassif,
                                                  confmap,MaximizeCPU,Classifmask,
                                                  stats,AllFeatures,
                                                  AllGapFill,AllRefl,AllMask,
                                                  datesInterp,realDates,
                                                  AllFeatures,ApplicationList)
    classifier.ExecuteAndWriteOutput()
    if MaximizeCPU:
        filterOTB_output(outputClassif,Classifmask,outputClassif)
        filterOTB_output(confmap,Classifmask,confmap)

    if pathWd: 
        shutil.copy(outputClassif,outputPath+"/classif")
    if pathWd: 
        shutil.copy(confmap,outputPath+"/classif")
 
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "Performs a classification of the input image (compute in RAM) according to a model file, ")
    parser.add_argument("-in",dest = "tempFolderSerie",help ="path to the folder which contains temporal series",default=None,required=True)
    parser.add_argument("-mask",dest = "mask",help ="path to classification's mask",default=None,required=True)
    parser.add_argument("-pixType",dest = "pixType",help ="pixel format",default=None,required=True)
    parser.add_argument("-model",dest = "model",help ="path to the model",default=None,required=True)
    parser.add_argument("-imstat",dest = "stats",help ="path to statistics",default=None,required=False)
    parser.add_argument("-out",dest = "outputClassif",help ="output classification's path",default=None,required=True)
    parser.add_argument("-confmap",dest = "confmap",help ="output classification confidence map",default=None,required=True)
    parser.add_argument("-ram",dest = "ram",help ="pipeline's size",default=128,required=False) 
    parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
    parser.add_argument("-conf",help ="path to the configuration file (mandatory)",dest = "pathConf",required=True)
    parser.add_argument("-maxCPU",help ="True : Class all the image and after apply mask",\
                            dest = "MaximizeCPU",default = "False",choices = ["True","False"],required=False)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)
    
    launchClassification(args.tempFolderSerie,args.mask,args.model,args.stats,args.outputClassif,\
                         args.confmap,args.pathWd, cfg,args.pixType,args.MaximizeCPU)







