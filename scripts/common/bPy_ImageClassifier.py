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
import prepareStack
        
def filterOTB_output(raster,mask,output,outputType=otb.ImagePixelType_uint8):
        
        bandMathFilter = otb.Registry.CreateApplication("BandMath")
        bandMathFilter.SetParameterString("exp","im2b1==1?im1b1:0")
        bandMathFilter.SetParameterStringList("il",[raster,mask])
        bandMathFilter.SetParameterString("ram","10000")
        bandMathFilter.SetParameterString("out",output,"?&streaming:type=stripped&streaming:sizemode=nbsplits&streaming:sizevalue=10")
        if outputType : bandMathFilter.SetParameterOutputImagePixelType("out",outputType)
        bandMathFilter.ExecuteAndWriteOutput()

def gapFilling(pathConf,tile,wMode,featuresPath=None,workingDirectory=None,testMode=False,testSensorData=None):

    outFeatures = Config(file(pathConf)).GlobChain.features
    userFeatPath = Config(file(pathConf)).chain.userFeatPath
    if userFeatPath == "None" : userFeatPath = None
    extractBands = Config(file(pathConf)).iota2FeatureExtraction.extractBands
    if extractBands == "False" : extractBands = None
       
    ipathL5=Config(file(pathConf)).chain.L5Path
    if ipathL5 == "None" : ipathL5=None
    ipathL8=Config(file(pathConf)).chain.L8Path
    if ipathL8 == "None" : ipathL8=None
    ipathS2=Config(file(pathConf)).chain.S2Path
    if ipathS2 == "None" : ipathS2=None
    autoDate = ast.literal_eval(Config(file(pathConf)).GlobChain.autoDate)
    gapL5=Config(file(pathConf)).Landsat5.temporalResolution
    gapL8=Config(file(pathConf)).Landsat8.temporalResolution
    gapS2=Config(file(pathConf)).Sentinel_2.temporalResolution
    tiles=(Config(file(pathConf)).chain.listTile).split()
        
    if testMode : ipathL8 = testSensorData
    dateB_L5=dateE_L5=dateB_L8=dateE_L8=dateB_S2=dateE_S2 = None
    if ipathL5 :
        dateB_L5,dateE_L5=fu.getDateL5(ipathL5,tiles)
    if not autoDate : 
        dateB_L5 = Config(file(pathConf)).Landsat5.startDate
        dateE_L5 = Config(file(pathConf)).Landsat5.endDate
    if ipathL8 :
        dateB_L8,dateE_L8=fu.getDateL8(ipathL8,tiles)
        if not autoDate : 
            dateB_L8 = Config(file(pathConf)).Landsat8.startDate
            dateE_L8 = Config(file(pathConf)).Landsat8.endDate
    if ipathS2 :
        dateB_S2,dateE_S2=fu.getDateS2(ipathS2,tiles)
        if not autoDate : 
            dateB_S2 = Config(file(pathConf)).Sentinel_2.startDate
            dateE_S2 = Config(file(pathConf)).Sentinel_2.endDate

    S2 = Sensors.Sentinel_2("",Opath("",create = False),pathConf,"",createFolder = None)
    L8 = Sensors.Landsat8("",Opath("",create = False),pathConf,"",createFolder = None)
    L5 = Sensors.Landsat5("",Opath("",create = False),pathConf,"",createFolder = None)
    SensorsList = [S2,L8,L5]
    workingDirectoryFeatures = workingDirectory+"/"+tile
    if not os.path.exists(workingDirectoryFeatures):os.mkdir(workingDirectoryFeatures)
    AllRefl,AllMask,datesInterp,realDates = prepareStack.generateStack(tile,pathConf,\
                                                                       featuresPath,ipathL5=ipathL5,ipathL8=ipathL8,\
                                                                       ipathS2=ipathS2,dateB_L5=dateB_L5,dateE_L5=dateE_L5,\
                                                                       dateB_L8=dateB_L8,dateE_L8=dateE_L8,dateB_S2=dateB_S2,\
                                                                       dateE_S2=dateE_S2,gapL5=gapL5,gapL8=gapL8,\
                                                                       gapS2=gapS2,writeOutput=wMode,\
                                                                       workingDirectory=workingDirectoryFeatures)

    AllgapFill = []
    reflectanceOutput = [currentRefl.GetParameterValue("out") for currentRefl in AllRefl]
    masksOutput = [currentMask[0].GetParameterValue("out") for currentMask in AllMask]
    datesInterpOutput = [currentDateInterp for currentDateInterp in datesInterp]
    datesRealOutput = [currentDateReal for currentDateReal in realDates]

    print "\n****** gapFilling to sample script ******"
    print "Reflectances used  : "+" ".join(reflectanceOutput)
    print "masks used : "+" ".join(masksOutput)
    print "interpolation dates : "+" ".join(datesInterpOutput)
    print "real dates : "+" ".join(datesRealOutput)
    print "*****************************************\n"

    features = []
    concatSensors= otb.Registry.CreateApplication("ConcatenateImages")
    for refl,mask,currentDatesInterp,currentRealDates in zip(AllRefl,AllMask,datesInterp,realDates):
        if wMode :
            refl.ExecuteAndWriteOutput()
            mask[0].ExecuteAndWriteOutput()
        else :
            refl.Execute()
            mask[0].Execute()

        currentSensor = fu.getCurrentSensor(SensorsList,refl.GetParameterValue("out"))
        reflDirectory,reflName =  os.path.split(refl.GetParameterValue("out"))
        outGapFilling=reflDirectory+"/"+reflName.replace(".tif","_GAP.tif")
        outFeatures=outGapFilling.replace(".tif","_Features.tif")

        nbDate = fu.getNbDateInTile(currentRealDates)
        gapFill = otb.Registry.CreateApplication("ImageTimeSeriesGapFilling")
        comp = len(currentSensor.bands['BANDS'])

        gapFill.SetParameterInputImage("mask",mask[0].GetParameterOutputImage("out"))
        gapFill.SetParameterString("it","linear")
        gapFill.SetParameterString("id",currentRealDates)
        gapFill.SetParameterString("od",currentDatesInterp)
        gapFill.SetParameterString("out",outGapFilling)
        gapFill.SetParameterOutputImagePixelType("out",fu.commonPixTypeToOTB('int16'))

        if extractBands :
            bandsToKeep = [bandNumber for bandNumber,bandName in currentSensor.keepBands]
            extract = fu.ExtractInterestBands(refl,nbDate,bandsToKeep,comp,ram = 10000)
            comp = len(bandsToKeep)
            gapFill.SetParameterInputImage("in",extract.GetParameterOutputImage("out"))

        else : gapFill.SetParameterInputImage("in",refl.GetParameterOutputImage("out"))   
        gapFill.SetParameterString("comp",str(comp))
        AllgapFill.append(gapFill)

    return AllgapFill,AllRefl,AllMask,datesInterp,realDates

def computeFeatures(pathConf,*ApplicationList):

    userFeatPath = Config(file(pathConf)).chain.userFeatPath
    if userFeatPath == "None" : userFeatPath = None
    extractBands = ast.literal_eval(Config(file(pathConf)).iota2FeatureExtraction.extractBands)
    featuresFlag = Config(file(pathConf)).GlobChain.features
    if not featuresFlag and userFeatpath == None : return ApplicationList

    S2 = Sensors.Sentinel_2("",Opath("",create = False),pathConf,"",createFolder = None)
    L8 = Sensors.Landsat8("",Opath("",create = False),pathConf,"",createFolder = None)
    L5 = Sensors.Landsat5("",Opath("",create = False),pathConf,"",createFolder = None)
    SensorsList = [S2,L8,L5]

    AllGapFilling = ApplicationList[0]
    AllFeatures = []
    for gapFilling in AllGapFilling:
        outFeatures=gapFilling.GetParameterValue("out")
        outFeatures=outFeatures.replace(".tif","_Features.tif")
        featExtr = otb.Registry.CreateApplication("iota2FeatureExtraction")
        currentSensor = fu.getCurrentSensor(SensorsList,gapFilling.GetParameterValue("out"))

        comp = len(currentSensor.bands['BANDS'])
        if extractBands :
            bandsToKeep = [bandNumber for bandNumber,bandName in currentSensor.keepBands]
            comp = len(bandsToKeep)

        featExtr.SetParameterInputImage("in",gapFilling.GetParameterOutputImage("out"))
        featExtr.SetParameterString("comp",str(comp))
        red = str(currentSensor.bands["BANDS"]["red"])
        nir = str(currentSensor.bands["BANDS"]["NIR"])
        swir = str(currentSensor.bands["BANDS"]["SWIR"])
        if extractBands : 
            red = str(fu.getIndex(currentSensor.keepBands,"red"))
            nir = str(fu.getIndex(currentSensor.keepBands,"NIR"))
            swir = str(fu.getIndex(currentSensor.keepBands,"SWIR"))

        featExtr.SetParameterString("red",red)
        featExtr.SetParameterString("nir",nir)
        featExtr.SetParameterString("swir",swir)
        featExtr.SetParameterString("out",outFeatures)
        featExtr.SetParameterOutputImagePixelType("out",fu.commonPixTypeToOTB('int16'))
        fu.iota2FeatureExtractionParameter(featExtr,pathConf)
        if featuresFlag : AllFeatures.append(featExtr)

    allTiles = (Config(file(pathConf)).chain.listTile).split()
    tile = fu.findCurrentTileInString(AllGapFilling[0].GetParameterValue("out"),allTiles)
    if userFeatPath :
        print "Add user features"
        userFeat_arbo = Config(file(pathConf)).userFeat.arbo
        userFeat_pattern = (Config(file(pathConf)).userFeat.patterns).split(",")
        userFeatures = fu.getUserFeatInTile(userFeatPath,tile,userFeat_arbo,userFeat_pattern)
        concatUserFeatures.Execute()
            
        concatUserFeatures = fu.CreateConcatenateImagesApplication(imagesList=userFeatures,\
                                                                   ram='4000',pixType="int16",wMode=False,output="")
        concatUserFeatures.Execute()
        AllFeatures.append(concatUserFeatures)

    if len(AllFeatures)>1:
        featuresConcatenation = fu.CreateConcatenateImagesApplication(imagesList=AllFeatures,\
                                                                   ram='4000',pixType="int16",wMode=False,output="")
        outputFeatures = featuresConcatenation
    else : outputFeatures = AllFeatures[0]
       

        
    return outputFeatures,ApplicationList
        
def computeClasifications(pathConf,model,outputClassif,confmap,MaximizeCPU,Classifmask,stats,AllFeatures,*ApplicationList):
        """
        if len(AllFeatures)>=1:
            inputStack = fu.CreateConcatenateImagesApplication(imagesList=AllFeatures,ram='4000',pixType="int16",wMode=False,output="")
            inputStack.Execute()
        else : 
            inputStack = AllFeatures[0]
        """
        classifier = otb.Registry.CreateApplication("ImageClassifier")
        classifier.SetParameterInputImage("in",AllFeatures.GetParameterOutputImage("out"))
        classifier.SetParameterString("out",outputClassif)
	classifier.SetParameterOutputImagePixelType("out",otb.ImagePixelType_uint8)
        classifier.SetParameterString("confmap",confmap)
        classifier.SetParameterString("model",model)
        if not MaximizeCPU : classifier.SetParameterString("mask",Classifmask)
	if stats : classifier.SetParameterString("imstat",stats)
	classifier.SetParameterString("ram","5000")
        return classifier,AllFeatures
        

def launchClassification(tempFolderSerie,Classifmask,model,stats,outputClassif,confmap,pathWd,pathConf,pixType,MaximizeCPU="False"):

	tiles=(Config(file(pathConf)).chain.listTile).split()
        tile = fu.findCurrentTileInString(Classifmask,tiles)
        wMode =  ast.literal_eval(Config(file(pathConf)).GlobChain.writeOutputs)
        featuresPath=Config(file(pathConf)).chain.featuresPath
        outputPath = Config(file(pathConf)).chain.outputPath

        AllGapFill,AllRefl,AllMask,datesInterp,realDates = gapFilling(pathConf,tile,wMode=wMode,featuresPath=None,workingDirectory=pathWd)
        if wMode:
                for currentGapFillSensor in AllGapFill : currentGapFillSensor.ExecuteAndWriteOutput()
        else:
                for currentGapFillSensor in AllGapFill : currentGapFillSensor.Execute()
        AllFeatures,ApplicationList = computeFeatures(pathConf,AllGapFill,AllRefl,AllMask,datesInterp,realDates)
        if wMode:
                AllFeatures.ExecuteAndWriteOutput()
        else:
                AllFeatures.Execute()
        
        classifier,inputStack = computeClasifications(pathConf,model,outputClassif,\
                                                      confmap,MaximizeCPU,Classifmask,\
                                                      stats,AllFeatures,\
                                                      AllGapFill,AllRefl,AllMask,\
                                                      datesInterp,realDates,\
                                                      AllFeatures,ApplicationList)
        classifier.ExecuteAndWriteOutput()
        if MaximizeCPU :
            filterOTB_output(outputClassif,Classifmask,outputClassif)
            filterOTB_output(confmap,Classifmask,confmap)

        if pathWd : shutil.copy(outputClassif,outputPath+"/classif")
	if pathWd : shutil.copy(confmap,outputPath+"/classif")
        '''
	os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = "5"
	featuresPath = Config(file(pathConf)).chain.featuresPath
	outputPath = Config(file(pathConf)).chain.outputPath
	outFeatures = Config(file(pathConf)).GlobChain.features
	tile = outputClassif.split("/")[-1].split("_")[1]
	userFeatPath = Config(file(pathConf)).chain.userFeatPath
  	if userFeatPath == "None" : userFeatPath = None
	extractBands = Config(file(pathConf)).iota2FeatureExtraction.extractBands
    	if extractBands == "False" : extractBands = None
        if MaximizeCPU == "True": 
                MaximizeCPU = True
        else :
                MaximizeCPU = False

	AllRefl = sorted(fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"REFL.tif"))
        AllMask = sorted(fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"MASK.tif"))
        datesInterp = sorted(fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"DatesInterp"))
        realDates = sorted(fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"imagesDate"))

	tmpFolder = outputPath+"/TMPFOLDER_"+tile
   	S2 = Sensors.Sentinel_2("",Opath(tmpFolder,create = False),pathConf,"",createFolder = None)
    	L8 = Sensors.Landsat8("",Opath(tmpFolder,create = False),pathConf,"",createFolder = None)
    	L5 = Sensors.Landsat5("",Opath(tmpFolder,create = False),pathConf,"",createFolder = None)

    	SensorsList = [S2,L8,L5]
        #gapFill + feat
        features = []
        concatSensors= otb.Registry.CreateApplication("ConcatenateImages")
        for refl,mask,datesInterp,realDates in zip(AllRefl,AllMask,datesInterp,realDates):

	    currentSensor = fu.getCurrentSensor(SensorsList,refl)

	    nbDate = fu.getNbDateInTile(realDates)
	    gapFill = otb.Registry.CreateApplication("ImageTimeSeriesGapFilling")
	    nbReflBands = fu.getRasterNbands(refl)
            comp = int(nbReflBands)/int(nbDate)
	    print datesInterp
            if not isinstance( comp, int ):
                raise Exception("unvalid component by date (not integer) : "+comp)
            
            gapFill.SetParameterString("mask",mask)
            gapFill.SetParameterString("it","linear")
            gapFill.SetParameterString("id",realDates)
            gapFill.SetParameterString("od",datesInterp)
	    
	    if extractBands :
		bandsToKeep = [bandNumber for bandNumber,bandName in currentSensor.keepBands]
	    	extract = fu.ExtractInterestBands(refl,nbDate,bandsToKeep,comp,ram = 10000)
		comp = len(bandsToKeep)
		gapFill.SetParameterInputImage("in",extract.GetParameterOutputImage("out"))
	    else : gapFill.SetParameterString("in",refl)
	    gapFill.SetParameterString("comp",str(comp))
            gapFill.Execute()

            featExtr = otb.Registry.CreateApplication("iota2FeatureExtraction")
            featExtr.SetParameterInputImage("in",gapFill.GetParameterOutputImage("out"))
            featExtr.SetParameterString("comp",str(comp))

	    red = str(currentSensor.bands["BANDS"]["red"])
	    nir = str(currentSensor.bands["BANDS"]["NIR"])
	    swir = str(currentSensor.bands["BANDS"]["SWIR"])
	    if extractBands : 
		red = str(fu.getIndex(currentSensor.keepBands,"red"))
		nir = str(fu.getIndex(currentSensor.keepBands,"NIR"))
		swir = str(fu.getIndex(currentSensor.keepBands,"SWIR"))

            featExtr.SetParameterString("red",red)
            featExtr.SetParameterString("nir",nir)
            featExtr.SetParameterString("swir",swir)
	    featExtr.SetParameterString("ram","256")
	    fu.iota2FeatureExtractionParameter(featExtr,pathConf)
	    if not outFeatures :
		print "without Features"
	    	concatSensors.AddImageToParameterInputImageList("il",gapFill.GetParameterOutputImage("out"))
		features.append(gapFill)
	    else:
		print "with Features"
		featExtr.Execute()
		features.append(featExtr)
	    	concatSensors.AddImageToParameterInputImageList("il",featExtr.GetParameterOutputImage("out"))
            
	classifier = otb.Registry.CreateApplication("ImageClassifier")
	if not MaximizeCPU : classifier.SetParameterString("mask",Classifmask)
	if stats : classifier.SetParameterString("imstat",stats)
	classifier.SetParameterString("model",model)
	classifier.SetParameterString("ram","5120")
	print "AllRefl"
	print AllRefl
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
        classifier.SetParameterString("out",outputClassif)
	classifier.SetParameterOutputImagePixelType("out",otb.ImagePixelType_uint8)
        classifier.SetParameterString("confmap",confmap)
        classifier.ExecuteAndWriteOutput()

        if MaximizeCPU :
                filterOTB_output(outputClassif,Classifmask,outputClassif)
                filterOTB_output(confmap,Classifmask,confmap)

	if pathWd : shutil.copy(outputClassif,outputPath+"/classif")
	if pathWd : shutil.copy(confmap,outputPath+"/classif")
        '''
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

	launchClassification(args.tempFolderSerie,args.mask,args.model,args.stats,args.outputClassif,\
                             args.confmap,args.pathWd,args.pathConf,args.pixType,args.MaximizeCPU)







