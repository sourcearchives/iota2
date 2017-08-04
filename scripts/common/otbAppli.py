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
from __future__ import absolute_import

import re
import numpy as np
import os,Sensors
from Utils import Opath
import otbApplication as otb
import fileUtils as fut
from config import Config
import ast
    
def getInputParameterOutput(otbObj):

    listParam = otbObj.GetParametersKeys()
    #check out
    if "out" in listParam : return "out"
    #check io.out
    elif "io.out" in listParam : return "io.out"
    #check mode.raster.out
    elif "mode.raster.out" in listParam : return "mode.raster.out"
    else : raise Exception("out parameter not recognize")
    
def unPackFirst(someListOfList):

    for values in someListOfList:
        if isinstance(values,list) or isinstance(values,tuple):yield values[0]
        else : yield values

def CreateBinaryMorphologicalOperation(inImg, ram="2000", pixType='uint8', filter="opening", ballxradius = '5', ballyradius = '5', outImg = ""):

    morphoMath = otb.Registry.CreateApplication("BinaryMorphologicalOperation")
    if morphoMath is None:
        raise Exception("Not possible to create 'Binary Morphological Operation' application, check if OTB is well configured / installed")
    
    if isinstance(inImg,str):morphoMath.SetParameterString("in", inImg)
    elif type(inImg)==otb.Application:
        inOutParam = getInputParameterOutput(inImg)
        morphoMath.SetParameterInputImage("in", inImg.GetParameterOutputImage(inOutParam))
    elif isinstance(inImg,tuple):morphoMath.SetParameterInputImage("in", inImg[0].GetParameterOutputImage("out"))
    else : raise Exception("input image not recognize")
    morphoMath.SetParameterString("filter", filter)    
    morphoMath.SetParameterString("structype", "ball")
    morphoMath.SetParameterString("structype.ball.xradius", str(ballxradius))
    morphoMath.SetParameterString("structype.ball.yradius", str(ballyradius))
    morphoMath.SetParameterString("out", outImg)
    morphoMath.SetParameterOutputImagePixelType("out", fut.commonPixTypeToOTB(pixType))

    return morphoMath
    
def CreateClumpApplication(stack, exp, ram='128', pixType="uint8", output=""):

    seg = otb.Registry.CreateApplication("Segmentation")
    if seg is None:
        raise Exception("Not possible to create 'Segmentation' application, check if OTB is well configured / installed")
    if not stack : 
        raise Exception("no input image detected")
    if isinstance(stack, str):seg.SetParameterString("in", stack)
    elif type(stack) == otb.Application:
        inOutParam = getInputParameterOutput(stack)
        seg.SetParameterInputImage("in", stack.GetParameterOutputImage(inOutParam))
    else:
        raise Exception(type(stack)+" not available to CreateClumpApplication function")

    seg.SetParameterString("mode","raster")
    seg.SetParameterString("filter","cc")
    seg.SetParameterString("filter.cc.expr", exp)
    seg.SetParameterString("mode.raster.out", output)
    seg.SetParameterOutputImagePixelType("mode.raster.out", fut.commonPixTypeToOTB(pixType))

    return seg
    
def CreateConcatenateImagesApplication(imagesList=None,ram='128',pixType="uint8",output=""):

    if not isinstance(imagesList,list):imagesList=[imagesList]

    concatenate = otb.Registry.CreateApplication("ConcatenateImages")
    if concatenate is None:
        raise Exception("Not possible to create 'Concatenation' application, check if OTB is well configured / installed")
    
    if isinstance(imagesList[0],str):
	concatenate.SetParameterStringList("il",imagesList)
    elif type(imagesList[0])==otb.Application:
        for currentObj in imagesList:
			inOutParam = getInputParameterOutput(currentObj)
			concatenate.AddImageToParameterInputImageList("il",currentObj.GetParameterOutputImage(inOutParam))
    elif isinstance(imagesList[0],tuple):
        for currentObj in unPackFirst(imagesList):
            inOutParam = getInputParameterOutput(currentObj)
            concatenate.AddImageToParameterInputImageList("il",currentObj.GetParameterOutputImage(inOutParam))

    concatenate.SetParameterString("out",output)
    concatenate.SetParameterOutputImagePixelType("out", fut.commonPixTypeToOTB(pixType))

    return concatenate

def CreateBandMathApplication(imagesList=None,exp=None,ram='128',pixType="uint8",output=""):

    if not isinstance(imagesList,list):imagesList=[imagesList]

    bandMath = otb.Registry.CreateApplication("BandMath")
    if bandMath is None:
        raise Exception("Not possible to create 'BandMath' application, check if OTB is well configured / installed")
    
    bandMath.SetParameterString("exp",exp)

    if isinstance(imagesList[0],str):bandMath.SetParameterStringList("il",imagesList)
    elif type(imagesList[0])==otb.Application:
	for currentObj in imagesList:
		inOutParam = getInputParameterOutput(currentObj)
		bandMath.AddImageToParameterInputImageList("il",currentObj.GetParameterOutputImage(inOutParam))
    elif isinstance(imagesList[0],tuple):
        for currentObj in unPackFirst(imagesList):
            inOutParam = getInputParameterOutput(currentObj)
            bandMath.AddImageToParameterInputImageList("il",currentObj.GetParameterOutputImage(inOutParam))
    else : 
	raise Exception(type(imageList[0])+" not available to CreateBandMathApplication function")
    bandMath.SetParameterString("ram",str(ram))
    bandMath.SetParameterString("out",output)
    bandMath.SetParameterOutputImagePixelType("out",fut.commonPixTypeToOTB(pixType))
    return bandMath

    
def CreateSuperimposeApplication(inImg1, inImg2, ram="2000", pixType='uint8', lms = "4", outImg = "", interpolator = "nn"):

    siApp = otb.Registry.CreateApplication("Superimpose")
    if siApp  is None:
        raise Exception("Not possible to create 'Superimpose' application, check if OTB is well configured / installed")    
    
    # First image input
    if isinstance(inImg1, str):siApp.SetParameterString("inr", inImg1)
    elif type(inImg1) == otb.Application:
        inOutParam = getInputParameterOutput(inImg1)
        siApp.SetParameterInputImage("inr", inImg1.GetParameterOutputImage(inOutParam))
    elif isinstance(inImg1, tuple):siApp.SetParameterInputImage("inr", inImg1[0].GetParameterOutputImage("out"))
    else : raise Exception("reference input image not recognize")
    
    # Second image input
    if isinstance(inImg2, str):siApp.SetParameterString("inm", inImg2)
    elif type(inImg2) == otb.Application:
        inOutParam = getInputParameterOutput(inImg2)
        siApp.SetParameterInputImage("inm", inImg2.GetParameterOutputImage(inOutParam))
    elif isinstance(inImg2, tuple):siApp.SetParameterInputImage("inm", inImg2[0].GetParameterOutputImage("out"))
    else : raise Exception("Image to reproject not recognize")

    siApp.SetParameterString("ram", str(ram))
    siApp.SetParameterString("interpolator", interpolator)
    siApp.SetParameterString("lms", str(lms))
    siApp.SetParameterString("out", outImg)
    siApp.SetParameterOutputImagePixelType("out", fut.commonPixTypeToOTB(pixType))

    return siApp

def CreateExtractROIApplication(inImg, startx, starty, sizex, sizey, ram="2000", pixType='uint8', outImg = ""):

    erApp = otb.Registry.CreateApplication("ExtractROI")
    if erApp is None:
        raise Exception("Not possible to create 'ExtractROI' application, check if OTB is well configured / installed")
    
    if isinstance(inImg, str):erApp.SetParameterString("in", inImg)
    elif type(inImg) == otb.Application:
        inOutParam = getInputParameterOutput(inImg)
        erApp.SetParameterInputImage("in", inImg.GetParameterOutputImage(inOutParam))
    elif isinstance(inImg, tuple):erApp.SetParameterInputImage("in", inImg[0].GetParameterOutputImage("out"))
    else : raise Exception("input image not recognize")

    erApp.SetParameterString("ram", str(ram))
    erApp.SetParameterString("startx", str(startx))
    erApp.SetParameterString("starty", str(starty))
    erApp.SetParameterString("sizex", str(sizex))
    erApp.SetParameterString("sizey", str(sizey))    
    erApp.SetParameterString("out", outImg)
    erApp.SetParameterOutputImagePixelType("out", fut.commonPixTypeToOTB(pixType))
    
    return erApp

def CreatePolygonClassStatisticsApplication(inImg, inVect, field, outxml, ram='128', split=""):

    statsApp = otb.Registry.CreateApplication("PolygonClassStatistics")
    if statsApp is None:
        raise Exception("Not possible to create 'PolygonClassStatistics' application, check if OTB is well configured / installed")

    if isinstance(inImg, str):statsApp.SetParameterString("in", inImg)
    elif type(inImg) == otb.Application:
        inOutParam = getInputParameterOutput(inImg)
        statsApp.SetParameterInputImage("in", inImg.GetParameterOutputImage(inOutParam))
    elif isinstance(inImg, tuple):statsApp.SetParameterInputImage("in", inImg[0].GetParameterOutputImage("out"))
    else : raise Exception("input image not recognize")

    statsApp.SetParameterString("vec", inVect)    
    statsApp.SetParameterString("ram", str(ram))
    statsApp.SetParameterString("out", os.path.splitext(str(outxml))[0] + split + os.path.splitext(str(outxml))[1]) 
    statsApp.UpdateParameters()
    statsApp.SetParameterString("field", field)    

    return statsApp

def CreateSampleSelectionApplication(inImg, inVect, field, stats, outsqlite, ram='128', split="", mask="", strategy = "all", sampler = "random"):

    sampleApp = otb.Registry.CreateApplication("SampleSelection")
    if sampleApp is None:
        raise Exception("Not possible to create 'SampleSelection' application, check if OTB is well configured / installed")    

    if isinstance(inImg, str):sampleApp.SetParameterString("in", inImg)
    elif type(inImg) == otb.Application:
        inOutParam = getInputParameterOutput(inImg)
        sampleApp.SetParameterInputImage("in", inImg.GetParameterOutputImage(inOutParam))
    elif isinstance(inImg, tuple):sampleApp.SetParameterInputImage("in", inImg[0].GetParameterOutputImage("out"))
    else : raise Exception("input image not recognize")

    sampleApp.SetParameterString("vec", inVect)    
    sampleApp.SetParameterString("instats", stats)
    sampleApp.UpdateParameters()
    sampleApp.SetParameterString("field", field)
    sampleApp.SetParameterString("ram", str(ram))        
    sampleApp.SetParameterString("sampler", sampler)
    sampleApp.SetParameterString("strategy", strategy)
    sampleApp.SetParameterString("out", outsqlite) 

    return sampleApp

def CreateSampleExtractionApplication(inImg, inVect, field, outsqlite, ram='128', split=""):

    extractApp = otb.Registry.CreateApplication("SampleExtraction")
    if extractApp is None:
        raise Exception("Not possible to create 'SampleExtraction' application, check if OTB is well configured / installed")    

    if isinstance(inImg, str):extractApp.SetParameterString("in", inImg)
    elif type(inImg) == otb.Application:
        inOutParam = getInputParameterOutput(inImg)
        extractApp.SetParameterInputImage("in", inImg.GetParameterOutputImage(inOutParam))
    elif isinstance(inImg, tuple):extractApp.SetParameterInputImage("in", inImg[0].GetParameterOutputImage("out"))
    else : raise Exception("input image not recognize")

    extractApp.SetParameterString("vec", inVect)    
    extractApp.UpdateParameters()  
    extractApp.SetParameterString("field", field)
    extractApp.SetParameterString("ram", str(ram))                
    extractApp.SetParameterString("out", os.path.splitext(str(outsqlite))[0] + split + os.path.splitext(str(outsqlite))[1]) 


    return extractApp

def CreateRasterizationApplication(inVect, inRefImg, background, outImg=""):

    rasterApp = otb.Registry.CreateApplication("Rasterization")
    if rasterApp is None:
        raise Exception("Not possible to create 'Rasterization' application, check if OTB is well configured / installed")    

    rasterApp.SetParameterString("in", inVect)
    rasterApp.SetParameterString("out", outImg)
    rasterApp.SetParameterString("im", inRefImg)
    rasterApp.SetParameterString("background", str(background))            
    mode.attribute.field
    
    return rasterApp

def computeUserFeatures(stack,nbDates,nbComponent,expressions): 

    def transformExprToListString(expr):
        """
	Example : 
	expr = "(b1+b2)/(b3+b10+b1)"
	print transformExprToListString(expr)
	>> ['(', 'b1', '+', 'b2', ')', '/', '(', 'b3', '+', 'b10', '+', 'b1', ')']
	"""
	container = []
	cpt=0
	while cpt < len(expr):
		currentChar = expr[cpt]
		if currentChar != "b" : container.append(currentChar)
		else:
			stringDigit = "b"
			for j in range(cpt+1,len(expr)):
                            try :
                                digit = int(expr[j])
                                cpt+=1
                                stringDigit+=expr[j]
                                if cpt == len(expr)-1: container.append(stringDigit)
                            except :
                                container.append(stringDigit)
                                break
		cpt+=1
	return container
    def checkBands(allBands,nbComp):
        """
        usage : check coherence between allBands in expression and number of component

        IN :
        allBands [set of all bands requested for expression] : example set(['b1', 'b2'])
        nbComp [int] : number of possible bands

        OUT
        ok [bool]
        """
        integerBands = [int(currentBand.split("b")[-1]) for currentBand in allBands]
        if max(integerBands)<=nbComp : return True
        else : return False

    def computeExpressionDates(expr,nbDate,nbComp):

        """
        from an "bandMath like" expression return bandMath expressions to each dates : 
        
        IN :
        expr [string] : bandMath - like expression
        nbDate [int] : number of dates (in a raster stack)
        nbComp [int] : number of components by dates 

        OUT : 
        allExpression [list of strings] : bandMath expression by dates

        Example:
        nbDate = 3
        nbComp = 10
        expr = "(b1+b2)/(b3+b10+b1)"
        print computeExpressionDates(expr,nbDate,nbComp)
        >> ['(im1b1+im1b2)/(im1b3+im1b10+im1b1)', '(im1b11+im1b12)/(im1b13+im1b20+im1b11)', '(im1b21+im1b22)/(im1b23+im1b30+im1b21)']
        """
        allBands = set([ currentDec for currentDec in re.findall(r'[b]\d+',expr)])
        expressionValid = checkBands(allBands,nbComp)
        if not expressionValid : raise Exception("User features expression : '"+expr+\
                                                  "' is not consistent with sensor's component number : "+str(nbComp))
        expression = transformExprToListString(expr)
        allExpression = []
        for date in range(nbDate):
            expressionDate = [currentChar for currentChar in expression]
            for currentBand in allBands : 
                indices = list(np.where(np.array(expression) == currentBand)[0])
                if not indices:
                    raise Exception("Problem in parsing expression : band "+currentBand+" not recognize")
                for ind in indices :
                    bandNumber = expressionDate[ind]
                    bandDate = int(bandNumber.split("b")[-1])+nbComp*date
                    expressionDate[ind] = "b"+str(bandDate)
            allExpression.append(("".join(expressionDate)).replace("b","im1b"))
	
        return allExpression

    expressionDate = [computeExpressionDates(currentExpression,nbDates,nbComponent) for currentExpression in expressions]
    flatExprDate = [currentExp for currentDate in expressionDate for currentExp in currentDate]
    
    userFeatureDate = []
    for expression in flatExprDate:
        bandMathApp = CreateBandMathApplication(imagesList=stack,exp=expression,\
                                                ram='2000',pixType="int16",\
                                                output="None")
        bandMathApp.Execute()
        userFeatureDate.append(bandMathApp)
    UserFeatures = CreateConcatenateImagesApplication(imagesList=userFeatureDate,ram='2000',\
                                                      pixType="int16",output="")

    return UserFeatures,userFeatureDate,stack

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
        dateB_L5,dateE_L5=fut.getDateL5(ipathL5,tiles)
    if not autoDate : 
        dateB_L5 = Config(file(pathConf)).Landsat5.startDate
        dateE_L5 = Config(file(pathConf)).Landsat5.endDate
    if ipathL8 :
        dateB_L8,dateE_L8=fut.getDateL8(ipathL8,tiles)
        if not autoDate : 
            dateB_L8 = Config(file(pathConf)).Landsat8.startDate
            dateE_L8 = Config(file(pathConf)).Landsat8.endDate
    if ipathS2 :
        dateB_S2,dateE_S2=fut.getDateS2(ipathS2,tiles)
        if not autoDate : 
            dateB_S2 = Config(file(pathConf)).Sentinel_2.startDate
            dateE_S2 = Config(file(pathConf)).Sentinel_2.endDate

    S2 = Sensors.Sentinel_2("",Opath("",create = False),pathConf,"",createFolder = None)
    L8 = Sensors.Landsat8("",Opath("",create = False),pathConf,"",createFolder = None)
    L5 = Sensors.Landsat5("",Opath("",create = False),pathConf,"",createFolder = None)
    SensorsList = [S2,L8,L5]

    workingDirectoryFeatures = workingDirectory+"/"+tile
    if not os.path.exists(workingDirectoryFeatures):os.mkdir(workingDirectoryFeatures)
    import prepareStack
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

        currentSensor = fut.getCurrentSensor(SensorsList,refl.GetParameterValue("out"))
        reflDirectory,reflName =  os.path.split(refl.GetParameterValue("out"))
        outGapFilling=reflDirectory+"/"+reflName.replace(".tif","_GAP.tif")
        outFeatures=outGapFilling.replace(".tif","_Features.tif")

        nbDate = fut.getNbDateInTile(currentRealDates)
        gapFill = otb.Registry.CreateApplication("ImageTimeSeriesGapFilling")
        comp = len(currentSensor.bands['BANDS'])

        gapFill.SetParameterInputImage("mask",mask[0].GetParameterOutputImage("out"))
        gapFill.SetParameterString("it","linear")
        gapFill.SetParameterString("id",currentRealDates)
        gapFill.SetParameterString("od",currentDatesInterp)
        gapFill.SetParameterString("out",outGapFilling)
        gapFill.SetParameterOutputImagePixelType("out",fut.commonPixTypeToOTB('int16'))

        if extractBands :
            bandsToKeep = [bandNumber for bandNumber,bandName in currentSensor.keepBands]
            extract = fut.ExtractInterestBands(refl,nbDate,bandsToKeep,comp,ram = 10000)
            comp = len(bandsToKeep)
            gapFill.SetParameterInputImage("in",extract.GetParameterOutputImage("out"))

        else : gapFill.SetParameterInputImage("in",refl.GetParameterOutputImage("out"))   
        gapFill.SetParameterString("comp",str(comp))
        AllgapFill.append(gapFill)

    return AllgapFill,AllRefl,AllMask,datesInterp,realDates

def computeFeatures(pathConf,nbDates,*ApplicationList,**testVariables):
    """
    IN:
    pathConf [string] : path to the configuration file
    *ApplicationList [list of list of OTB's application] : only first content of list is used to produce features
    nbDates [list of int] : number of component by stack (ApplicationList[0])
    
    OUT:
    """
    testMode = testVariables.get('testMode')
    testUserFeatures = testVariables.get('testUserFeatures')
    userFeatPath = Config(file(pathConf)).chain.userFeatPath
    if testMode : userFeatPath = testUserFeatures
    if userFeatPath == "None" : userFeatPath = None
    useAddFeat = ast.literal_eval(Config(file(pathConf)).GlobChain.useAdditionalFeatures)
    extractBands = ast.literal_eval(Config(file(pathConf)).iota2FeatureExtraction.extractBands)
    featuresFlag = Config(file(pathConf)).GlobChain.features
    if not featuresFlag and userFeatpath == None : return ApplicationList

    S2 = Sensors.Sentinel_2("",Opath("",create = False),pathConf,"",createFolder = None)
    L8 = Sensors.Landsat8("",Opath("",create = False),pathConf,"",createFolder = None)
    L5 = Sensors.Landsat5("",Opath("",create = False),pathConf,"",createFolder = None)
    SensorsList = [S2,L8,L5]

    AllGapFilling = ApplicationList[0]
    AllFeatures = []
    for gapFilling,dates in zip(AllGapFilling,nbDates):
        outFeatures=gapFilling.GetParameterValue("out")
        outFeatures=outFeatures.replace(".tif","_Features.tif")
        featExtr = otb.Registry.CreateApplication("iota2FeatureExtraction")
        currentSensor = fut.getCurrentSensor(SensorsList,gapFilling.GetParameterValue("out"))
        comp = len(currentSensor.bands['BANDS'])
       
        if extractBands :
            bandsToKeep = [bandNumber for bandNumber,bandName in currentSensor.keepBands]
            comp = len(bandsToKeep)
        if useAddFeat : 
            userDateFeatures,a,b = computeUserFeatures(gapFilling,dates,comp,currentSensor.addFeatures)
            userDateFeatures.Execute()
        else :
            userDateFeatures=a=b=None

        featExtr.SetParameterInputImage("in",gapFilling.GetParameterOutputImage("out"))
        featExtr.SetParameterString("comp",str(comp))
        red = str(currentSensor.bands["BANDS"]["red"])
        nir = str(currentSensor.bands["BANDS"]["NIR"])
        swir = str(currentSensor.bands["BANDS"]["SWIR"])
        if extractBands : 
            red = str(fut.getIndex(currentSensor.keepBands,"red"))
            nir = str(fut.getIndex(currentSensor.keepBands,"NIR"))
            swir = str(fut.getIndex(currentSensor.keepBands,"SWIR"))

        featExtr.SetParameterString("red",red)
        featExtr.SetParameterString("nir",nir)
        featExtr.SetParameterString("swir",swir)
        featExtr.SetParameterString("out",outFeatures)
        featExtr.SetParameterOutputImagePixelType("out",fut.commonPixTypeToOTB('int16'))
        fut.iota2FeatureExtractionParameter(featExtr,pathConf)
        if featuresFlag : AllFeatures.append(featExtr)
        if useAddFeat : AllFeatures.append(userDateFeatures)

    allTiles = (Config(file(pathConf)).chain.listTile).split()
    tile = fut.findCurrentTileInString(AllGapFilling[0].GetParameterValue("out"),allTiles)
    if userFeatPath :
        print "Add user features"
        userFeat_arbo = Config(file(pathConf)).userFeat.arbo
        userFeat_pattern = (Config(file(pathConf)).userFeat.patterns).split(",")
        userFeatures = fut.getUserFeatInTile(userFeatPath,tile,userFeat_arbo,userFeat_pattern)
            
        concatUserFeatures = CreateConcatenateImagesApplication(imagesList=userFeatures,\
                                                                   ram='4000',pixType="int16",output="")
        concatUserFeatures.Execute()
        AllFeatures.append(concatUserFeatures)
    if len(AllFeatures)>1:
        for currentFeat in AllFeatures : currentFeat.Execute()
        outFeatures=outFeatures.replace(".tif","_USERFEAT.tif")
        featuresConcatenation = CreateConcatenateImagesApplication(imagesList=AllFeatures,\
                                                                      ram='4000',pixType="int16",output=outFeatures)
        outputFeatures = featuresConcatenation
        
    else : 
        outputFeatures = AllFeatures[0]

    return outputFeatures,ApplicationList,userDateFeatures,a,b,AllFeatures
