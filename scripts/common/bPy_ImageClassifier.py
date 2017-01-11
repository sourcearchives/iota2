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
import argparse,shutil,os,Sensors
from config import Config
import otbApplication as otb
import fileUtils as fu
from Utils import Opath

def launchClassification(tempFolderSerie,Classifmask,model,stats,outputClassif,confmap,pathWd,pathConf,pixType):
	
	outputClassif=outputClassif.replace(".tif","_TMP.tif")
	confmap=confmap.replace(".tif","_TMP.tif")
	os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = "5"
	featuresPath = Config(file(pathConf)).chain.featuresPath
	outputPath = Config(file(pathConf)).chain.outputPath
	tile = outputClassif.split("/")[-1].split("_")[1]

	AllRefl = sorted(fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"REFL.tif"))
        AllMask = sorted(fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"MASK.tif"))
        datesInterp = sorted(fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"DatesInterp"))
        realDates = sorted(fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"imagesDate"))

	tmpFolder = outputPath+"/TMPFOLDER_"+tile
    	if not os.path.exists(tmpFolder):
    		os.mkdir(tmpFolder)
   	#Sensors
   	S2 = Sensors.Sentinel_2("",Opath(tmpFolder),pathConf,"")
    	L8 = Sensors.Landsat8("",Opath(tmpFolder),pathConf,"")
    	L5 = Sensors.Landsat5("",Opath(tmpFolder),pathConf,"")
	#shutil.rmtree(tmpFolder, ignore_errors=True)

    	SensorsList = [S2,L8,L5]
        #gapFill + feat
        features = []
        concatSensors= otb.Registry.CreateApplication("ConcatenateImages")
        for refl,mask,datesInterp,realDates in zip(AllRefl,AllMask,datesInterp,realDates):
            gapFill = otb.Registry.CreateApplication("ImageTimeSeriesGapFilling")
            nbDate = fu.getNbDateInTile(realDates)
            nbReflBands = fu.getRasterNbands(refl)
            comp = int(nbReflBands)/int(nbDate)
            if not isinstance( comp, int ):
                raise Exception("unvalid component by date (not integer) : "+comp)
            gapFill.SetParameterString("in",refl)
            gapFill.SetParameterString("mask",mask)
            gapFill.SetParameterString("comp",str(comp))
            gapFill.SetParameterString("it","linear")
            gapFill.SetParameterString("id",realDates)
            gapFill.SetParameterString("od",datesInterp)
	    #gapFill.SetParameterString("ram","1024")
            gapFill.Execute()

            #featExtr = otb.Registry.CreateApplication("iota2FeatureExtraction")
            #featExtr.SetParameterInputImage("in",gapFill.GetParameterOutputImage("out"))
            #featExtr.SetParameterString("comp",str(comp))
	    #for currentSensor in SensorsList:
            #    if currentSensor.name in refl:
	    #	    red = str(currentSensor.bands["BANDS"]["red"])
	    #	    nir = str(currentSensor.bands["BANDS"]["NIR"])
	    #	    swir = str(currentSensor.bands["BANDS"]["SWIR"])
            #featExtr.SetParameterString("red",red)
            #featExtr.SetParameterString("nir",nir)
            #featExtr.SetParameterString("swir",swir)
            #featExtr.Execute()

            #features.append(featExtr)
	    concatSensors.AddImageToParameterInputImageList("il",gapFill.GetParameterOutputImage("out"))
	    features.append(gapFill)
            
	classifier = otb.Registry.CreateApplication("ImageClassifier")
	classifier.SetParameterString("mask",Classifmask)
	if stats : classifier.SetParameterString("imstat",stats)
	classifier.SetParameterString("out",outputClassif)
	classifier.SetParameterString("model",model)
	classifier.SetParameterString("confmap",confmap)
	classifier.SetParameterString("ram","512")
	print "AllRefl"
	print AllRefl
	#if len(AllRefl) >1:
	#	concatSensors.Execute()
	#	classifier.SetParameterInputImage("in",concatSensors.GetParameterOutputImage("out"))
	#else:	
	#	classifier.SetParameterInputImage("in",features[0].GetParameterOutputImage("out"))
	#classifier.ExecuteAndWriteOutput()
	if len(AllRefl) > 1:
		concatSensors.Execute()
		allFeatures = concatSensors.GetParameterOutputImage("out")
	else : allFeatures = features[0].GetParameterOutputImage("out")

	if userFeatPath :
		print "Add user features"
		userFeat_arbo = Config(file(pathConf)).userFeat.arbo
		userFeat_pattern = (Config(file(pathConf)).userFeat.patterns).split(",")
		concatFeatures = otb.Registry.CreateApplication("ConcatenateImages")
		userFeatures = fu.getUserFeatInTile(userFeatPath,tile,userFeat_arbo,userFeat_pattern)
		concatFeatures.SetParameterStringList("il",userFeatures)
		concatFeatures.Execute()

		concatAllFeatures = otb.Registry.CreateApplication("ConcatenateImages")
		concatAllFeatures.AddImageToParameterInputImageList("il",allFeatures)
		concatAllFeatures.AddImageToParameterInputImageList("il",concatFeatures.GetParameterOutputImage("out"))
		concatAllFeatures.Execute()

		allFeatures = concatAllFeatures.GetParameterOutputImage("out")

	classifier.SetParameterInputImage("in",allFeatures)
        classifier.ExecuteAndWriteOutput()

	expr = "im2b1>=1?im1b1:0"
	cmd = 'otbcli_BandMath -il '+outputClassif+' '+Classifmask+' -out '+outputClassif.replace("_TMP.tif",".tif")+' -exp "'+expr+'"'
	print cmd 
	os.system(cmd)

	cmd = 'otbcli_BandMath -il '+confmap+' '+Classifmask+' -out '+confmap.replace("_TMP.tif",".tif")+' -exp "'+expr+'"'
	print cmd 
	os.system(cmd)

	if pathWd : shutil.copy(outputClassif.replace("_TMP.tif",".tif"),outputPath+"/classif")
	if pathWd : shutil.copy(confmap.replace("_TMP.tif",".tif"),outputPath+"/classif")
	os.remove(outputClassif)
	os.remove(confmap)
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
	args = parser.parse_args()

	launchClassification(args.tempFolderSerie,args.mask,args.model,args.stats,args.outputClassif,args.confmap,args.pathWd,args.pathConf,args.pixType)







