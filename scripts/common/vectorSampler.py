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
import sys,os,random,shutil,Sensors
import fileUtils as fu
from osgeo import ogr
from config import Config
import otbApplication as otb
from Utils import Opath
import genAnnualSamples as genAS

def getPointsCoordInShape(inShape,gdalDriver):
	
	driver = ogr.GetDriverByName(gdalDriver)
	dataSource = driver.Open(inShape, 0)
	layer = dataSource.GetLayer()

	allCoord = []
	for feature in layer:
    		geom = feature.GetGeometryRef()
		allCoord.append((geom.GetX(),geom.GetY()))
	return allCoord

def filterShpByClass(datafield,shapeFiltered,keepClass,shape):
    """
    Filter a shape by class allow in configPath
    IN :
        configPath [string] : path to the configuration file
        newShapeFile [string] : path to the output shape
    """

    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(shape, 0)
    layer = dataSource.GetLayer()

    AllFields = []
    layerDefinition = layer.GetLayerDefn()

    for i in range(layerDefinition.GetFieldCount()):
            currentField = layerDefinition.GetFieldDefn(i).GetName()
            AllFields.append(currentField)

    exp = " OR ".join(datafield+" = '"+currentClass+"'" for currentClass in keepClass)
    layer.SetAttributeFilter(exp)
    if layer.GetFeatureCount() == 0:
        return False
    fu.CreateNewLayer(layer, shapeFiltered,AllFields)
    return True

def generateSamples_simple(folderSample,workingDirectory,trainShape,pathWd,featuresPath,samplesOptions,pathConf,dataField):
    
    bindingPython = Config(file(pathConf)).GlobChain.bindingPython
    dataField = Config(file(pathConf)).chain.dataField
    outputPath = Config(file(pathConf)).chain.outputPath
    tmpFolder = outputPath+"/TMPFOLDER"
    if not os.path.exists(tmpFolder):
    	os.mkdir(tmpFolder)
    #Sensors
    S2 = Sensors.Sentinel_2("",Opath(tmpFolder),pathConf,"")
    L8 = Sensors.Landsat8("",Opath(tmpFolder),pathConf,"")
    L5 = Sensors.Landsat5("",Opath(tmpFolder),pathConf,"")
    #shutil.rmtree(tmpFolder, ignore_errors=True)
    SensorsList = [S2,L8,L5]
    stats = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_stats.xml")
    tile = trainShape.split("/")[-1].split("_")[0]
    stack = fu.getFeatStackName(pathConf)
    feat = featuresPath+"/"+tile+"/Final/"+stack
    if bindingPython == "True":
        feat = fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"ST_MASK")[0]

    os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = "1"
    cmd = "otbcli_PolygonClassStatistics -in "+feat+" -vec "+trainShape+" -out "+stats+" -field "+dataField
    print cmd
    os.system(cmd)
    sampleSelection = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_SampleSel.sqlite")
    cmd = "otbcli_SampleSelection -out "+sampleSelection+" "+samplesOptions+" -field "+dataField+" -in "+feat+" -vec "+trainShape+" -instats "+stats
    print cmd
    os.system(cmd)

    #if pathWd:shutil.copy(sampleSelection,folderSample)

    os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = "5"
 
    samples = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite")
    sampleExtr = otb.Registry.CreateApplication("SampleExtraction")
    sampleExtr.SetParameterString("vec",sampleSelection)
    sampleExtr.SetParameterString("field",dataField)
    sampleExtr.SetParameterString("out",samples)
    if bindingPython == "True":
        AllRefl = sorted(fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"REFL.tif"))
        AllMask = sorted(fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"MASK.tif"))
        datesInterp = sorted(fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"DatesInterp"))
        realDates = sorted(fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"imagesDate"))

	print AllRefl
	print AllMask
	print datesInterp
	print realDates
        #gapFill + feat
        features = []
        concatSensors= otb.Registry.CreateApplication("ConcatenateImages")
        for refl,mask,datesInterp,realDates in zip(AllRefl,AllMask,datesInterp,realDates):
            gapFill = otb.Registry.CreateApplication("ImageTimeSeriesGapFilling")
            nbDate = fu.getNbDateInTile(realDates)
            nbReflBands = fu.getRasterNbands(refl)
            comp = int(nbReflBands)/int(nbDate)
	    print datesInterp
            if not isinstance( comp, int ):
                raise Exception("unvalid component by date (not integer) : "+comp)
            gapFill.SetParameterString("in",refl)
            gapFill.SetParameterString("mask",mask)
            gapFill.SetParameterString("comp",str(comp))
            gapFill.SetParameterString("it","linear")
            gapFill.SetParameterString("id",realDates)
            gapFill.SetParameterString("od",datesInterp)
            gapFill.Execute()

	    #gapFill.SetParameterString("out","/ptmp/vincenta/tmp/TestGapFill.tif")
	    #gapFill.ExecuteAndWriteOutput()
	    #pause = raw_input("Pause1")

            #featExtr = otb.Registry.CreateApplication("iota2FeatureExtraction")
            #featExtr.SetParameterInputImage("in",gapFill.GetParameterOutputImage("out"))
            #featExtr.SetParameterString("comp",str(comp))
            #for currentSensor in SensorsList:
            #    if currentSensor.name in refl:
	    #		red = str(currentSensor.bands["BANDS"]["red"])
	    #		nir = str(currentSensor.bands["BANDS"]["NIR"])
	    #		swir = str(currentSensor.bands["BANDS"]["SWIR"])
            #featExtr.SetParameterString("red",red)
            #featExtr.SetParameterString("nir",nir)
            #featExtr.SetParameterString("swir",swir)
	    #featExtr.SetParameterString("ram","256")
	    #featExtr.Execute()
            #features.append(featExtr)
	    concatSensors.AddImageToParameterInputImageList("il",gapFill.GetParameterOutputImage("out"))
	    features.append(gapFill)

        #sensors Concatenation + sampleExtraction
        sampleExtr = otb.Registry.CreateApplication("SampleExtraction")
	sampleExtr.SetParameterString("ram","1024")
        sampleExtr.SetParameterString("vec",sampleSelection)
        sampleExtr.SetParameterString("field",dataField)
        sampleExtr.SetParameterString("out",samples)
	print "-----------------------"
	print samples
	print "-----------------------"
	
        if len(AllRefl) > 1:
            concatSensors.Execute()
            sampleExtr.SetParameterInputImage("in",concatSensors.GetParameterOutputImage("out"))
        else:
            sampleExtr.SetParameterInputImage("in",features[0].GetParameterOutputImage("out"))
        sampleExtr.ExecuteAndWriteOutput()

	#cmd = "otbcli_SampleExtraction -field "+dataField+" -out "+samples+" -vec "+sampleSelection+" -in /ptmp/vincenta/tmp/TestGapFill.tif"
        #print cmd
	#pause = raw_input("Pause")
        #os.system(cmd)
    else:
        cmd = "otbcli_SampleExtraction -field "+dataField+" -out "+samples+" -vec "+sampleSelection+" -in "+feat
        print cmd
        os.system(cmd)
    if pathWd:shutil.copy(samples,folderSample+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite"))
        

def generateSamples_cropMix(folderSample,workingDirectory,trainShape,pathWd,featuresPath,samplesOptions,prevFeatures,annualCrop,AllClass,dataField,pathConf):

    currentTile = trainShape.split("/")[-1].split("_")[0]
    bindingPy = Config(file(pathConf)).GlobChain.bindingPython
    samplesClassifMix = Config(file(pathConf)).argTrain.samplesClassifMix

    stack = "/Final/"+fu.getFeatStackName(pathConf)
    NA_img = featuresPath+"/"+currentTile+"/"+stack
    A_img = prevFeatures+"/"+currentTile+"/"+stack
    if bindingPy == "True":
        NA_img = fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"ST_MASK")[0]
	A_img = fu.FileSearch_AND(prevFeatures+"/"+tile+"/tmp/",True,"ST_MASK")[0]
    #Step 1 : filter trainShape in order to keep non-annual class
    nameNonAnnual = trainShape.split("/")[-1].replace(".shp","_NonAnnu.shp")
    nonAnnualShape = workingDirectory+"/"+nameNonAnnual
    filterShpByClass(dataField,nonAnnualShape,AllClass,trainShape)

    #Step 2 : filter trainShape in order to keep annual class
    nameAnnual = trainShape.split("/")[-1].replace(".shp","_Annu.shp")
    annualShape = workingDirectory+"/"+nameAnnual
    annualCropFind = filterShpByClass(dataField,annualShape,annualCrop,trainShape)

    #Step 3 : nonAnnual stats
    stats_NA= workingDirectory+"/"+nameNonAnnual.replace(".shp","_STATS.xml")
    cmd = "otbcli_PolygonClassStatistics -in "+NA_img+" -vec "+nonAnnualShape+" -field "+dataField+" -out "+stats_NA
    print cmd
    os.system(cmd)

    #Step 4 : Annual stats
    stats_A= workingDirectory+"/"+nameAnnual.replace(".shp","_STATS.xml")
    cmd = "otbcli_PolygonClassStatistics -in "+A_img+" -vec "+annualShape+" -field "+dataField+" -out "+stats_A
    if annualCropFind:
        print cmd
        os.system(cmd)

    #Step 5 : Sample Selection NonAnnual
    SampleSel_NA = workingDirectory+"/"+nameNonAnnual.replace(".shp","_SampleSel_NA.sqlite")
    cmd = "otbcli_SampleSelection -in "+NA_img+" -vec "+nonAnnualShape+" -field "+dataField+" -instats "+stats_NA+" -out "+SampleSel_NA+" "+samplesOptions
    print cmd
    os.system(cmd)

    #Step 6 : Sample Selection Annual
    SampleSel_A = workingDirectory+"/"+nameAnnual.replace(".shp","_SampleSel_A.sqlite")
    cmd = "otbcli_SampleSelection -in "+A_img+" -vec "+annualShape+" -field "+dataField+" -instats "+stats_A+" -out "+SampleSel_A+" "+samplesOptions
    if annualCropFind:
        print cmd
        os.system(cmd)
    SampleExtr_NA = workingDirectory+"/"+nameNonAnnual.replace(".shp","_SampleExtr_NA.sqlite")
    SampleExtr_A = workingDirectory+"/"+nameAnnual.replace(".shp","_SampleExtr_A.sqlite")
    if bindingPy == "False":
	    #Step 7 : Sample extraction NonAnnual
	    cmd = "otbcli_SampleExtraction -in "+NA_img+" -vec "+SampleSel_NA+" -field "+dataField+" -out "+SampleExtr_NA
	    print cmd
	    os.system(cmd)

	    #Step 8 : Sample extraction Annual
	    cmd = "otbcli_SampleExtraction -in "+A_img+" -vec "+SampleSel_A+" -field "+dataField+" -out "+SampleExtr_A
	    if annualCropFind:
		print cmd
		os.system(cmd)
    else:
	    #Step 7 : Sample extraction NonAnnual
    	    concatSensors= otb.Registry.CreateApplication("ConcatenateImages")
	    AllRefl = sorted(fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"REFL.tif"))
      	    AllMask = sorted(fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"MASK.tif"))
            datesInterp = sorted(fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"DatesInterp"))
            realDates = sorted(fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"imagesDate"))
            features = []
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
		concatSensors.AddImageToParameterInputImageList("il",gapFill.GetParameterOutputImage("out"))
		features.append(gapFill)

	    sampleExtr = otb.Registry.CreateApplication("SampleExtraction")
	    sampleExtr.SetParameterString("ram","128")
            sampleExtr.SetParameterString("vec",SampleSel_NA)
            sampleExtr.SetParameterString("field",dataField)
            sampleExtr.SetParameterString("out",SampleExtr_NA)
	    if len(AllRefl) > 1:
                concatSensors.Execute()
                sampleExtr.SetParameterInputImage("in",concatSensors.GetParameterOutputImage("out"))
            else:
                sampleExtr.SetParameterInputImage("in",features[0].GetParameterOutputImage("out"))
            sampleExtr.ExecuteAndWriteOutput()

            #Step 8 : Sample extraction Annual
    	    concatSensors= otb.Registry.CreateApplication("ConcatenateImages")
	    AllRefl = sorted(fu.FileSearch_AND(prevFeatures+"/"+tile+"/tmp/",True,"REFL.tif"))
      	    AllMask = sorted(fu.FileSearch_AND(prevFeatures+"/"+tile+"/tmp/",True,"MASK.tif"))
            datesInterp = sorted(fu.FileSearch_AND(prevFeatures+"/"+tile+"/tmp/",True,"DatesInterp"))
            realDates = sorted(fu.FileSearch_AND(prevFeatures+"/"+tile+"/tmp/",True,"imagesDate"))
            features = []
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
		concatSensors.AddImageToParameterInputImageList("il",gapFill.GetParameterOutputImage("out"))
		features.append(gapFill)

	    sampleExtr = otb.Registry.CreateApplication("SampleExtraction")
	    sampleExtr.SetParameterString("ram","128")
            sampleExtr.SetParameterString("vec",SampleSel_A)
            sampleExtr.SetParameterString("field",dataField)
            sampleExtr.SetParameterString("out",SampleExtr_A)
	    if len(AllRefl) > 1:
                concatSensors.Execute()
                sampleExtr.SetParameterInputImage("in",concatSensors.GetParameterOutputImage("out"))
            else:
                sampleExtr.SetParameterInputImage("in",features[0].GetParameterOutputImage("out"))
            if annualCropFind:sampleExtr.ExecuteAndWriteOutput()

    #Step 9 : Merge
    MergeName = trainShape.split("/")[-1].replace(".shp","_Samples")
    listToMerge = [SampleExtr_NA]
    if annualCropFind:
        #listToMerge = [SampleExtr_A,SampleExtr_NA]
	listToMerge = [SampleExtr_NA,SampleExtr_A]
    fu.mergeSQLite(MergeName, workingDirectory,listToMerge)
    samples = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite")

    os.remove(stats_NA)
    os.remove(SampleSel_NA)
    os.remove(SampleExtr_NA)
    fu.removeShape(nonAnnualShape.replace(".shp",""),[".prj",".shp",".dbf",".shx"])

    if annualCropFind:
        os.remove(stats_A)
        os.remove(SampleSel_A)
        os.remove(SampleExtr_A)
        fu.removeShape(annualShape.replace(".shp",""),[".prj",".shp",".dbf",".shx"])

    if pathWd:
        shutil.copy(samples,folderSample+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite"))

def generateSamples_classifMix(folderSample,workingDirectory,trainShape,pathWd,featuresPath,samplesOptions,annualCrop,AllClass,dataField,pathConf,configPrevClassif):
	
	currentTile = trainShape.split("/")[-1].split("_")[0]
        bindingPy = Config(file(pathConf)).GlobChain.bindingPython
	targetResolution = Config(file(pathConf)).chain.spatialResolution
	validityThreshold = Config(file(pathConf)).argTrain.validityThreshold
        stack = "/Final/"+fu.getFeatStackName(pathConf)
	
	previousClassifPath = Config(file(configPrevClassif)).chain.outputPath
        featImg = featuresPath+"/"+currentTile+"/"+stack
        if bindingPy == "True":
            featImg = fu.FileSearch_AND(featuresPath+"/"+currentTile+"/tmp/",True,"ST_MASK")[0]

        nameNonAnnual = trainShape.split("/")[-1].replace(".shp","_NonAnnu.shp")
    	nonAnnualShape = workingDirectory+"/"+nameNonAnnual
    	filterShpByClass(dataField,nonAnnualShape,AllClass,trainShape)

	stats_NA= workingDirectory+"/"+nameNonAnnual.replace(".shp","_STATS.xml")
	cmd = "otbcli_PolygonClassStatistics -in "+featImg+" -vec "+nonAnnualShape+" -field "+dataField+" -out "+stats_NA
	print cmd
	os.system(cmd)

	SampleSel_NA = workingDirectory+"/"+nameNonAnnual.replace(".shp","_SampleSel_NA.sqlite")
	cmd = "otbcli_SampleSelection -in "+featImg+" -vec "+nonAnnualShape+" -field "+dataField+" -instats "+stats_NA+" -out "+SampleSel_NA+" "+samplesOptions
	print cmd
	os.system(cmd)

	gdalDriver = "SQLite"
	allCoord = getPointsCoordInShape(SampleSel_NA,gdalDriver)
	nameAnnual = trainShape.split("/")[-1].replace(".shp","_Annu.shp")
	annualShape = workingDirectory+"/"+nameAnnual
	validityRaster = fu.FileSearch_AND(previousClassifPath+"/final/TMP",True,currentTile,"Cloud",".tif")[0]
	classificationRaster = fu.FileSearch_AND(previousClassifPath+"/final/TMP",True,currentTile+"_seed_0.tif")[0]
	maskFolder = previousClassifPath+"/classif/MASK"
	genAS.genAnnualShapePoints(allCoord,gdalDriver,workingDirectory,targetResolution,annualCrop,dataField,currentTile,validityThreshold,validityRaster,classificationRaster,maskFolder,trainShape,annualShape)

	MergeName = trainShape.split("/")[-1].replace(".shp","_selectionMerge")
   	listToMerge = [SampleSel_NA,annualShape]
	fu.mergeSQLite(MergeName, workingDirectory,listToMerge)
	sampleSelection = workingDirectory+"/"+MergeName+".sqlite"

	samples = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite")
	if bindingPy == "False":
	    cmd = "otbcli_SampleExtraction -in "+featImg+" -vec "+selectionMerge+" -field "+dataField+" -out "+samples
	    print cmd
	    os.system(cmd)
	else:
	    AllRefl = sorted(fu.FileSearch_AND(featuresPath+"/"+currentTile+"/tmp/",True,"REFL.tif"))
            AllMask = sorted(fu.FileSearch_AND(featuresPath+"/"+currentTile+"/tmp/",True,"MASK.tif"))
            datesInterp = sorted(fu.FileSearch_AND(featuresPath+"/"+currentTile+"/tmp/",True,"DatesInterp"))
            realDates = sorted(fu.FileSearch_AND(featuresPath+"/"+currentTile+"/tmp/",True,"imagesDate"))

	    print AllRefl
	    print AllMask
	    print datesInterp
	    print realDates
            #gapFill + feat
            features = []
            concatSensors= otb.Registry.CreateApplication("ConcatenateImages")
            for refl,mask,datesInterp,realDates in zip(AllRefl,AllMask,datesInterp,realDates):
                gapFill = otb.Registry.CreateApplication("ImageTimeSeriesGapFilling")
                nbDate = fu.getNbDateInTile(realDates)
                nbReflBands = fu.getRasterNbands(refl)
                comp = int(nbReflBands)/int(nbDate)
	        print datesInterp
                if not isinstance( comp, int ):
                    raise Exception("unvalid component by date (not integer) : "+comp)
                gapFill.SetParameterString("in",refl)
                gapFill.SetParameterString("mask",mask)
                gapFill.SetParameterString("comp",str(comp))
                gapFill.SetParameterString("it","linear")
                gapFill.SetParameterString("id",realDates)
                gapFill.SetParameterString("od",datesInterp)
                gapFill.Execute()
	        concatSensors.AddImageToParameterInputImageList("il",gapFill.GetParameterOutputImage("out"))
	        features.append(gapFill)

            #sensors Concatenation + sampleExtraction
            sampleExtr = otb.Registry.CreateApplication("SampleExtraction")
	    sampleExtr.SetParameterString("ram","128")
            sampleExtr.SetParameterString("vec",sampleSelection)
            sampleExtr.SetParameterString("field",dataField)
            sampleExtr.SetParameterString("out",samples)
            if len(AllRefl) > 1:
                concatSensors.Execute()
                sampleExtr.SetParameterInputImage("in",concatSensors.GetParameterOutputImage("out"))
            else:
                sampleExtr.SetParameterInputImage("in",features[0].GetParameterOutputImage("out"))
            sampleExtr.ExecuteAndWriteOutput()
        if pathWd:shutil.copy(samples,folderSample+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite"))
	

def generateSamples(trainShape,pathWd,pathConf):

    TestPath = Config(file(pathConf)).chain.outputPath
    dataField = Config(file(pathConf)).chain.dataField
    featuresPath = Config(file(pathConf)).chain.featuresPath
    samplesOptions = Config(file(pathConf)).argTrain.samplesOptions
    cropMix = Config(file(pathConf)).argTrain.cropMix
    samplesClassifMix = Config(file(pathConf)).argTrain.samplesClassifMix

    prevFeatures = Config(file(pathConf)).argTrain.prevFeatures
    annualCrop = Config(file(pathConf)).argTrain.annualCrop
    AllClass = fu.getAllClassInShape(trainShape,dataField)

    for CurrentClass in annualCrop:
        try:
            AllClass.remove(str(CurrentClass))
        except ValueError:
            print CurrentClass+" doesn't exist in "+trainShape
            print "All Class : "
            print AllClass
    print trainShape
    print AllClass
    print annualCrop

    folderSample = TestPath+"/learningSamples"
    if not os.path.exists(folderSample):
        os.system("mkdir "+folderSample)

    workingDirectory = folderSample
    if pathWd:
        workingDirectory = pathWd

    if not cropMix == 'True':
        generateSamples_simple(folderSample,workingDirectory,trainShape,pathWd,featuresPath,samplesOptions,pathConf,dataField)
    elif cropMix == 'True' and samplesClassifMix == "False":
        generateSamples_cropMix(folderSample,workingDirectory,trainShape,pathWd,featuresPath,samplesOptions,prevFeatures,annualCrop,AllClass,dataField,pathConf)
    elif cropMix == 'True' and samplesClassifMix == "True":
	configPrevClassif = Config(file(pathConf)).argTrain.configClassif
	generateSamples_classifMix(folderSample,workingDirectory,trainShape,pathWd,featuresPath,samplesOptions,annualCrop,AllClass,dataField,pathConf,configPrevClassif)
	

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "This function generates samples a shapeFile")
    parser.add_argument("-shape",dest = "shape",help ="path to the shapeFile to sampled",default=None,required=True)
    parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
    parser.add_argument("-conf",help ="path to the configuration file (mandatory)",dest = "pathConf",required=True)
    args = parser.parse_args()

    generateSamples(args.shape,args.pathWd,args.pathConf)

















