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

import argparse,prepareStack,ast
import sys,os,random,shutil,Sensors,osr
import fileUtils as fu
from osgeo import ogr
from config import Config
import otbApplication as otb
from Utils import Opath
import genAnnualSamples as genAS
from distutils.dir_util import copy_tree


def verifPolyStats(inXML):
	"""
	due to OTB error, use this parser to check '0 values' in class sampling and remove them
	IN : xml polygons statistics
	OUT : same xml without 0 values
	"""
	flag = False
	buff = ""
	with open(inXML,"r") as xml:
		for inLine in xml:
			buff+=inLine
			if 'name="samplesPerClass"' in inLine.rstrip('\n\r'):
				for inLine2 in xml:
					if 'value="0" />' in inLine2:
						flag = True
						continue
					else:buff+=inLine2
					if 'name="samplesPerVector"' in inLine2:break
	if flag :
		os.remove(inXML)
		output = open(inXML,"w")
		output.write(buff)
		output.close()
	return flag

def createSamplePoint(nonAnnual,annual,dataField,output,projOut):
	"""
        IN:
        nonAnnual [string] : path to vector shape containing non annual points 
        annual [string] : path to vector shape containing annual points
        dataField [string] : dataField in vector shape
        output [string] : output path
        projOut [int] : output EPSG code

        OUT :
        fusion of two vector shape in 'output' parameter
	"""
	outDriver = ogr.GetDriverByName("SQLite")
	if os.path.exists(output):outDriver.DeleteDataSource(output)
	outDataSource = outDriver.CreateDataSource(output)
	out_lyr_name = os.path.splitext(os.path.split(output)[1])[0]
	srs = osr.SpatialReference()
	srs.ImportFromEPSG(projOut)
	outLayer = outDataSource.CreateLayer(out_lyr_name, srs, ogr.wkbPoint)
	field_name = ogr.FieldDefn(dataField, ogr.OFTInteger)
	outLayer.CreateField(field_name)

	driverNonAnnual = ogr.GetDriverByName("SQLite")
	dataSourceNonAnnual = driverNonAnnual.Open(nonAnnual, 0)
	layerNonAnnual = dataSourceNonAnnual.GetLayer()

	driverAnnual = ogr.GetDriverByName("SQLite")
	dataSourceAnnual = driverAnnual.Open(annual, 0)
	layerAnnual = dataSourceAnnual.GetLayer()

	for feature in layerNonAnnual:
		geom = feature.GetGeometryRef()
		currentClass = feature.GetField(dataField)
		wkt = geom.Centroid().ExportToWkt()
		outFeat = ogr.Feature(outLayer.GetLayerDefn())
		outFeat.SetField(dataField, int(currentClass))
		outFeat.SetGeometry(ogr.CreateGeometryFromWkt(wkt))
		outLayer.CreateFeature(outFeat)
		outFeat.Destroy()
	
	for feature in layerAnnual:
		geom = feature.GetGeometryRef()
		currentClass = feature.GetField(dataField)
		wkt = geom.Centroid().ExportToWkt()
		outFeat = ogr.Feature(outLayer.GetLayerDefn())
		outFeat.SetField(dataField, int(currentClass))
		outFeat.SetGeometry(ogr.CreateGeometryFromWkt(wkt))
		outLayer.CreateFeature(outFeat)
		outFeat.Destroy()
	
	outDataSource.Destroy()

def getPointsCoordInShape(inShape,gdalDriver):
	"""
        IN:
        inShape [string] : path to the vector shape containing points
        gdalDriver [string] : gdalDriver of inShape

        OUT:
        allCoord [list of tuple] : coord X and Y of points
        """
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
    Filter a shape by class allow in keepClass
    IN :
    shape [string] : path to input vector shape
    datafield [string] : data's field'
    keepClass [list of string] : class to keep
    shapeFiltered [string] : output path to filtered shape
    """
    if not keepClass:return False
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(shape, 0)
    layer = dataSource.GetLayer()

    AllFields = []
    layerDefinition = layer.GetLayerDefn()

    for i in range(layerDefinition.GetFieldCount()):
            currentField = layerDefinition.GetFieldDefn(i).GetName()
            AllFields.append(currentField)

    exp = " OR ".join(datafield+" = '"+str(currentClass)+"'" for currentClass in keepClass)
    layer.SetAttributeFilter(exp)
    if layer.GetFeatureCount() == 0:
        return False
    fu.CreateNewLayer(layer, shapeFiltered,AllFields)
    return True

def prepareSelection(ref,trainShape,dataField,samplesOptions,workingDirectory):

        stats=sampleSelection = None
	if not os.path.exists(workingDirectory):os.mkdir(workingDirectory)
        os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = "1"
        stats = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_stats.xml")
        cmd = "otbcli_PolygonClassStatistics -in "+ref+" -vec "+trainShape+" -out "+stats+" -field "+dataField
        print cmd
        os.system(cmd)
        verifPolyStats(stats)

        sampleSelection = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_SampleSel.sqlite")
        cmd = "otbcli_SampleSelection -out "+sampleSelection+" "+samplesOptions+" -field "+\
              dataField+" -in "+ref+" -vec "+trainShape+" -instats "+stats
        nbFeatures = len(fu.getFieldElement(trainShape,driverName="ESRI Shapefile",field=dataField))
        if nbFeatures >= 1 :
                print cmd
                os.system(cmd)
                return stats, sampleSelection

def gapFillingToSample(trainShape,samplesOptions,workingDirectory,samples,dataField,featuresPath,tile,pathConf,\
                       wMode=False,inputSelection=False,testMode=False,testSensorData=None,onlyMaskComm=False):
        """
        usage : compute from a stack of data -> gapFilling -> features computation -> sampleExtractions
        thanks to OTB's applications'

        IN:
        sampleSelection [string] : path to a vector shape containing points (SampleSelection output)
        samples [string] : output path
        dataField [string] : data's field'
        featuresPath [string] : path to all stack (/featuresPath/tile/tmp/*.tif)
        tile [string] : actual tile to compute. (ex : T31TCJ)
        pathConf [string] : path to configuation file

        OUT:
        sampleExtr [SampleExtraction OTB's object]: 
        """
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

        ref = fu.FileSearch_AND(workingDirectory,True,"MaskCommunSL.tif")[0]
        if onlyMaskComm : return ref
        sampleSelectionDirectory = workingDirectory+"/SampleSelection"
        if inputSelection == False :
            stats,sampleSelection = prepareSelection(ref,trainShape,dataField,samplesOptions,sampleSelectionDirectory)
        else : sampleSelection = inputSelection

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
            if wMode == False : gapFill.Execute()
            else : gapFill.ExecuteAndWriteOutput()

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
            featExtr.SetParameterString("out",outFeatures)
            featExtr.SetParameterOutputImagePixelType("out",fu.commonPixTypeToOTB('int16'))

	    fu.iota2FeatureExtractionParameter(featExtr,pathConf)
	    if not outFeatures:
		print "without Features"
	    	concatSensors.AddImageToParameterInputImageList("il",gapFill.GetParameterOutputImage("out"))
		features.append(gapFill)
	    else:
		print "with Features"
		if wMode == False : featExtr.Execute()
                else : featExtr.ExecuteAndWriteOutput()
		features.append(featExtr)
	    	concatSensors.AddImageToParameterInputImageList("il",featExtr.GetParameterOutputImage("out"))

        #sensors Concatenation + sampleExtraction
        sampleExtr = otb.Registry.CreateApplication("SampleExtraction")
	sampleExtr.SetParameterString("ram","1024")
        sampleExtr.SetParameterString("vec",sampleSelection)
	sampleExtr.SetParameterString("out",samples)
	sampleExtr.UpdateParameters()
        sampleExtr.SetParameterStringList("field",[dataField.lower()])
	
	if len(AllRefl) > 1:
		concatSensors.Execute()
		allFeatures = concatSensors.GetParameterOutputImage("out")
	else : allFeatures = features[0].GetParameterOutputImage("out")
        
        concatFeatures = otb.Registry.CreateApplication("ConcatenateImages")
        concatAllFeatures = otb.Registry.CreateApplication("ConcatenateImages")

	if userFeatPath :
		print "Add user features"
		userFeat_arbo = Config(file(pathConf)).userFeat.arbo
		userFeat_pattern = (Config(file(pathConf)).userFeat.patterns).split(",")
		userFeatures = fu.getUserFeatInTile(userFeatPath,tile,userFeat_arbo,userFeat_pattern)
		concatFeatures.SetParameterStringList("il",userFeatures)
		concatFeatures.Execute()

		concatAllFeatures.AddImageToParameterInputImageList("il",allFeatures)
		concatAllFeatures.AddImageToParameterInputImageList("il",concatFeatures.GetParameterOutputImage("out"))
		concatAllFeatures.Execute()

		allFeatures = concatAllFeatures.GetParameterOutputImage("out")

	sampleExtr.SetParameterInputImage("in",allFeatures)
        return sampleExtr,featExtr,concatAllFeatures,concatFeatures,gapFill,concatSensors,AllRefl,AllMask,sampleSelectionDirectory

import errno

def copyanything(src, dst):
    try:
        shutil.copytree(src, dst)
    except OSError as exc: # python >2.5
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else: raise

def generateSamples_simple(folderSample,workingDirectory,trainShape,pathWd,\
                           featuresPath,samplesOptions,pathConf,dataField,\
                           wMode=False,folderFeatures=None,testMode=False,\
                           testSensorData=None,testFeaturePath=None):
    """
    usage : from a strack of data generate samples containing points with features

    IN:
    folderSample [string] : output folder
    workingDirectory [string] : computation folder
    trainShape [string] : vector shape (polygons) to sample
    pathWd [string] : if different from None, enable HPC mode (copy at ending)
    featuresPath [string] : path to all stack
    samplesOptions [string] : sampling strategy according to OTB SampleSelection application
    pathConf [string] : path to configuration file
    dataField [string] : data's field into vector shape
    testMode [bool] : enable testMode -> iota2tests.py
    testFeatures [string] : path to features allready compute (refl + NDVI ...)
    testFeaturePath [string] : path to the stack of data, without features

    OUT:
    samples [string] : vector shape containing points
    """
    tile = trainShape.split("/")[-1].split("_")[0]    
    bindingPython = Config(file(pathConf)).GlobChain.bindingPython
    dataField = Config(file(pathConf)).chain.dataField
    outputPath = Config(file(pathConf)).chain.outputPath
    userFeatPath = Config(file(pathConf)).chain.userFeatPath
    outFeatures = Config(file(pathConf)).GlobChain.features
    if userFeatPath == "None" : userFeatPath = None

    extractBands = Config(file(pathConf)).iota2FeatureExtraction.extractBands
    if extractBands == "False" : extractBands = None

    os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = "5"
    samples = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite")
    sampleExtr,a,b,c,d,e,f,g,sampleSel = gapFillingToSample(trainShape,samplesOptions,\
                                                            workingDirectory,samples,\
                                                            dataField,featuresPath,tile,\
                                                            pathConf,wMode,False,testMode,\
                                                            testSensorData)
    sampleExtr.ExecuteAndWriteOutput()
    shutil.rmtree(sampleSel)
    if pathWd :
        shutil.copy(samples,folderSample+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite"))
        if wMode :
            if os.path.exists(folderFeatures+"/"+tile):shutil.rmtree(folderFeatures+"/"+tile)
            copyanything(workingDirectory+"/"+tile,folderFeatures+"/"+tile)

    if testMode : return samples

def generateSamples_cropMix(folderSample,workingDirectory,trainShape,pathWd,nonAnnualData,samplesOptions,\
                            annualData,annualCrop,AllClass,dataField,pathConf,\
                            folderFeature,folderFeaturesAnnual,wMode=False,testMode=False):
    """
    usage : from stracks A and B, generate samples containing points where annual crop are compute with A
    and non annual crop with B.

    IN:
    folderSample [string] : output folder
    workingDirectory [string] : computation folder
    trainShape [string] : vector shape (polygons) to sample
    pathWd [string] : if different from None, enable HPC mode (copy at ending)
    featuresPath [string] : path to all stack
    samplesOptions [string] : sampling strategy according to OTB SampleSelection application
    prevFeatures [string] : path to the configuration file which compute features A
    annualCrop [list of string/int] : list containing annual crops ex : [11,12]
    AllClass [list of string/int] : list containing all classes in vector shape ex : [11,12,51..]
    pathConf [string] : path to configuration file
    dataField [string] : data's field into vector shape
    testMode [bool] : enable testMode -> iota2tests.py
    testFeatures [string] : path to features allready compute (refl + NDVI ...)
    testFeaturePath [string] : path to the stack of data, without features dedicated to non 
                               annual crops
    testAnnualFeaturePath [string] : path to the stack of data, without features dedicated to
                                     annual crops

    OUT:
    samples [string] : vector shape containing points
    """
    currentTile = trainShape.split("/")[-1].split("_")[0]
    corseTiles = ["T32TMN","T32TNN","T32TMM","T32TNM","T32TNL"]
    if currentTile in corseTiles:
    	generateSamples_simple(folderSample,workingDirectory,trainShape,pathWd,featuresPath,samplesOptions,pathConf,dataField)
    	return 0
    bindingPy = Config(file(pathConf)).GlobChain.bindingPython
    samplesClassifMix = Config(file(pathConf)).argTrain.samplesClassifMix
    outFeatures = Config(file(pathConf)).GlobChain.features
    featuresFind_NA = ""
    featuresFind_A = ""
    userFeatPath = Config(file(pathConf)).chain.userFeatPath
    if userFeatPath == "None" : userFeatPath = None

    extractBands = Config(file(pathConf)).iota2FeatureExtraction.extractBands
    if extractBands == "False" : extractBands = None
    
    #filter shape file
    nameNonAnnual = trainShape.split("/")[-1].replace(".shp","_NonAnnu.shp")
    nonAnnualShape = workingDirectory+"/"+nameNonAnnual
    nonAnnualCropFind = filterShpByClass(dataField,nonAnnualShape,AllClass,trainShape)
    nameAnnual = trainShape.split("/")[-1].replace(".shp","_Annu.shp")
    annualShape = workingDirectory+"/"+nameAnnual
    annualCropFind = filterShpByClass(dataField,annualShape,annualCrop,trainShape)

    SampleExtr_NA_name = nameNonAnnual.replace(".shp","_SampleExtr_NA.sqlite")
    SampleExtr_A_name = nameAnnual.replace(".shp","_SampleExtr_A.sqlite")
    SampleExtr_NA = workingDirectory+"/"+SampleExtr_NA_name
    SampleExtr_A = workingDirectory+"/"+SampleExtr_A_name

    sampleSel_A=sampleSel_NA=None
    if nonAnnualCropFind :
        Na_workingDirectory = workingDirectory+"/"+currentTile+"_nonAnnual"
        if not os.path.exists(Na_workingDirectory):os.mkdir(Na_workingDirectory)
        sampleExtr_NA,a,b,c,d,e,f,g,sampleSel_NA = gapFillingToSample(nonAnnualShape,samplesOptions,\
                                                                      Na_workingDirectory,SampleExtr_NA,\
                                                                      dataField,nonAnnualData,currentTile,\
                                                                      pathConf,wMode,False,testMode,\
                                                                      nonAnnualData)
        sampleExtr_NA.ExecuteAndWriteOutput()
    if annualCropFind:
        A_workingDirectory = workingDirectory+"/"+currentTile+"_annual"
        if not os.path.exists(A_workingDirectory):os.mkdir(A_workingDirectory)
        sampleExtr_A,a,b,c,d,e,f,g,sampleSel_A = gapFillingToSample(annualShape,samplesOptions,\
                                                                    A_workingDirectory,SampleExtr_A,\
                                                                    dataField,annualData,currentTile,\
                                                                    pathConf,wMode,False,testMode,\
                                                                    annualData)
        sampleExtr_A.ExecuteAndWriteOutput()

    #Merge samples
    MergeName = trainShape.split("/")[-1].replace(".shp","_Samples")

    if (nonAnnualCropFind and sampleSel_NA) and (annualCropFind and sampleSel_A):
	fu.mergeSQLite(MergeName, workingDirectory,[SampleExtr_NA,SampleExtr_A])
    elif (nonAnnualCropFind and sampleSel_NA) and not (annualCropFind and sampleSel_A):
	shutil.copyfile(SampleExtr_NA, workingDirectory+"/"+MergeName+".sqlite")
    elif not (nonAnnualCropFind and sampleSel_NA) and (annualCropFind and sampleSel_A):
 	shutil.copyfile(SampleExtr_A, workingDirectory+"/"+MergeName+".sqlite")

    samples = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite")

    if nonAnnualCropFind and sampleSel_NA:
        if os.path.exists(sampleSel_NA):shutil.rmtree(sampleSel_NA)
    	os.remove(SampleExtr_NA)
    	fu.removeShape(nonAnnualShape.replace(".shp",""),[".prj",".shp",".dbf",".shx"])

    if annualCropFind and sampleSel_A:
        if os.path.exists(sampleSel_A):shutil.rmtree(sampleSel_A)
        os.remove(SampleExtr_A)
        fu.removeShape(annualShape.replace(".shp",""),[".prj",".shp",".dbf",".shx"])

    if wMode :
        targetDirectory = folderFeature+"/"+currentTile
        if not os.path.exists(targetDirectory) : 
            copyanything(workingDirectory+"/"+currentTile+"_nonAnnual/"+currentTile,targetDirectory)
        
        targetDirectory = folderFeaturesAnnual+"/"+currentTile
        if not os.path.exists(targetDirectory) :
            copyanything(workingDirectory+"/"+currentTile+"_annual/"+currentTile,targetDirectory)

    if testMode : return samples
    if pathWd and os.path.exists(samples):
        shutil.copy(samples,folderSample+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite"))

def extractROI(raster,currentTile,pathConf,pathWd,name,ref,testMode=None,testOutput=None):
	"""
        usage : extract ROI in raster

        IN:
        raster [string] : path to the input raster
        currentTile [string] : current tile
        pathConf [string] : path to the configuration file
        pathWd [string] : path to the working directory
        name [string] : output name

        OUT:
        raterROI [string] : path to the extracted raster.
        """
	outputPath = Config(file(pathConf)).chain.outputPath
	featuresPath = Config(file(pathConf)).chain.featuresPath

	workingDirectory = outputPath+"/learningSamples/"
	if pathWd : workingDirectory = pathWd
	
        if testMode :
            #currentTile_raster=testFeaturesPath
            workingDirectory=testOutput
        #else:currentTile_raster = fu.FileSearch_AND(featuresPath+"/"+currentTile,True,".tif")[0]
        currentTile_raster = ref
	minX,maxX,minY,maxY = fu.getRasterExtent(currentTile_raster)
        rasterROI = workingDirectory+"/"+currentTile+"_"+name+".tif"
	cmd = "gdalwarp -of GTiff -te "+str(minX)+" "+str(minY)+" "+str(maxX)+" "+str(maxY)+" -ot Byte "+raster+" "+rasterROI
	"""
	if not os.path.exists(outputPath+"/learningSamples/"+currentTile+"_"+name+".tif"):
		print cmd
		os.system(cmd)
		if pathWd : shutil.copy(workingDirectory+"/"+currentTile+"_"+name+".tif",outputPath+"/learningSamples/")
	"""
	print cmd
	os.system(cmd)
	return rasterROI

def getRegionModelInTile(currentTile,currentRegion,pathWd,pathConf,refImg,\
                         testMode,testPath,testOutputFolder):
        """
        usage : rasterize region shape.
        
        IN:
        currentTile [string] : tile to compute
        currentRegion [string] : current region in tile
        pathWd [string] : working directory
        pathConf [string] : path to the configuration file
        refImg [string] : reference image
        testMode [bool] : flag to enable test mode
        testPath [string] : path to the vector shape

        OUT:
        rasterMask [string] : path to the output raster
        """
        outputPath = Config(file(pathConf)).chain.outputPath
	fieldRegion = Config(file(pathConf)).chain.regionField

	workingDirectory = outputPath+"/learningSamples/"
	if pathWd : workingDirectory = pathWd
	nameOut = "Mask_region_"+currentRegion+"_"+currentTile+".tif"
	
	if testMode : 
            maskSHP = testPath
            workingDirectory = testOutputFolder
	else : maskSHP = fu.FileSearch_AND(outputPath+"/shapeRegion/",True,currentTile,"region_"+currentRegion,".shp")[0]

	rasterMask = workingDirectory+"/"+nameOut
	cmdRaster = "otbcli_Rasterization -in "+maskSHP+" -mode attribute -mode.attribute.field "+\
                    fieldRegion+" -im "+refImg+" -out "+rasterMask
	"""
	if not os.path.exists(outputPath+"/learningSamples/"+nameOut):
		print cmdRaster
		os.system(cmdRaster)
		if pathWd : shutil.copy(workingDirectory+"/"+nameOut,outputPath+"/learningSamples/")
	return outputPath+"/learningSamples/"+nameOut
	"""
	print cmdRaster
	os.system(cmdRaster)
	return rasterMask

def generateSamples_classifMix(folderSample,workingDirectory,trainShape,pathWd,samplesOptions,\
                               annualCrop,AllClass,dataField,pathConf,configPrevClassif,folderFeatures=None,\
                               wMode=False,\
                               testMode=None,\
                               testSensorData=None,\
                               testPrevClassif=None,\
                               testShapeRegion=None):
	"""
        usage : from one classification, chose randomly annual sample merge with non annual sample and extract features.

        IN:
        folderSample [string] : output folder
        workingDirectory [string] : computation folder
        trainShape [string] : vector shape (polygons) to sample
        pathWd [string] : if different from None, enable HPC mode (copy at ending)
        featuresPath [string] : path to all stack
        samplesOptions [string] : sampling strategy according to OTB SampleSelection application
        annualCrop [list of string/int] : list containing annual crops ex : [11,12]
        AllClass [list of string/int] : list containing all classes in vector shape ex : [11,12,51..]
        pathConf [string] : path to configuration file
        configPrevClassif [string] : path to the configuration file which generate previous classification
        dataField [string] : data's field into vector shape
        testMode [bool] : enable testMode -> iota2tests.py
        testFeatures [string] : path to features allready compute (refl + NDVI ...)
        testPrevClassif [string] : path to the classification
        testPrevConfig [string] : path to the configuration file which generate previous classification
        testShapeRegion [string] : path to the shapefile representing region in the tile.
        testFeaturePath [string] : path to the stack of data

        OUT:
        samples [string] : vector shape containing points
        """
	corseTiles = ["T32TMN","T32TNN","T32TMM","T32TNM","T32TNL"]
	currentTile, bindingPy = trainShape.split("/")[-1].split("_")[0],Config(file(pathConf)).GlobChain.bindingPython
	if currentTile in corseTiles:
		generateSamples_simple(folderSample,workingDirectory,trainShape,pathWd,featuresPath,samplesOptions,pathConf,dataField)
		return 0
	targetResolution  = Config(file(pathConf)).chain.spatialResolution
        validityThreshold = Config(file(pathConf)).argTrain.validityThreshold
	previousClassifPath, projOut = Config(file(configPrevClassif)).chain.outputPath,Config(file(configPrevClassif)).GlobChain.proj
	projOut = int(projOut.split(":")[-1])
	userFeatPath = Config(file(pathConf)).chain.userFeatPath
	outFeatures = Config(file(pathConf)).GlobChain.features
	coeff = Config(file(pathConf)).argTrain.coeffSampleSelection
	extractBands = Config(file(pathConf)).iota2FeatureExtraction.extractBands

   	if extractBands == "False" : extractBands = None
        if userFeatPath == "None" : userFeatPath = None

	seed = trainShape.split("_")[-2]
   
	if testMode:previousClassifPath = testPrevClassif

	nameNonAnnual = trainShape.split("/")[-1].replace(".shp","_NonAnnu.shp")
    	nonAnnualShape = workingDirectory+"/"+nameNonAnnual
	nameAnnual = trainShape.split("/")[-1].replace(".shp","_Annu.shp")
    	AnnualShape = workingDirectory+"/"+nameAnnual

    	nonAnnualCropFind = filterShpByClass(dataField,nonAnnualShape,AllClass,trainShape)
	annualCropFind = filterShpByClass(dataField,AnnualShape,annualCrop,trainShape)
	
	gdalDriver = "SQLite"
	SampleSel_NA = workingDirectory+"/"+nameNonAnnual.replace(".shp","_SampleSel_NA.sqlite")
	stats_NA= workingDirectory+"/"+nameNonAnnual.replace(".shp","_STATS.xml")

        communDirectory = workingDirectory+"/commun"
        if not os.path.exists(communDirectory) : os.mkdir(communDirectory)
        ref = gapFillingToSample(nonAnnualShape,samplesOptions,\
                                 communDirectory,"",\
                                 dataField,"",currentTile,\
                                 pathConf,wMode,False,testMode,\
                                 testSensorData,onlyMaskComm=True)
	if nonAnnualCropFind:
		cmd = "otbcli_PolygonClassStatistics -in "+ref+" -vec "+nonAnnualShape+" -field "+dataField+" -out "+stats_NA
		print cmd
		os.system(cmd)
		verifPolyStats(stats_NA)
		cmd = "otbcli_SampleSelection -in "+ref+" -vec "+nonAnnualShape+" -field "+\
                      dataField+" -instats "+stats_NA+" -out "+SampleSel_NA+" "+samplesOptions
		print cmd
		os.system(cmd)		
		allCoord = getPointsCoordInShape(SampleSel_NA,gdalDriver)
		featuresFind_NA = fu.getFieldElement(SampleSel_NA,driverName="SQLite",\
                                                     field = dataField.lower(),mode = "all",elemType = "int")
	else :allCoord=[0]
        
	nameAnnual = trainShape.split("/")[-1].replace(".shp","_Annu.sqlite")
	annualShape = workingDirectory+"/"+nameAnnual

	classificationRaster = extractROI(previousClassifPath+"/final/Classif_Seed_0.tif",
                                          currentTile,pathConf,pathWd,"Classif",
                                          ref,testMode,testOutput=folderSample)
	validityRaster = extractROI(previousClassifPath+"/final/PixelsValidity.tif",
                                    currentTile,pathConf,pathWd,"Cloud",\
                                    ref,testMode,testOutput=folderSample)
        shutil.rmtree(communDirectory)

	currentRegion = trainShape.split("/")[-1].split("_")[2].split("f")[0]
	mask = getRegionModelInTile(currentTile,currentRegion,pathWd,pathConf,classificationRaster,\
                                    testMode,testShapeRegion,testOutputFolder=folderSample)

	if annualCropFind : annualPoints = genAS.genAnnualShapePoints(allCoord,gdalDriver,workingDirectory,\
                                                                      targetResolution,annualCrop,dataField,\
                                                                      currentTile,validityThreshold,validityRaster,\
                                                                      classificationRaster,mask,trainShape,annualShape,coeff,projOut)
	MergeName = trainShape.split("/")[-1].replace(".shp","_selectionMerge")
	sampleSelection = workingDirectory+"/"+MergeName+".sqlite"

	if (nonAnnualCropFind and featuresFind_NA) and (annualCropFind and annualPoints): 
		createSamplePoint(SampleSel_NA,annualShape,dataField,sampleSelection,projOut)
	elif (nonAnnualCropFind and featuresFind_NA) and not (annualCropFind and annualPoints) :
		shutil.copy(SampleSel_NA,sampleSelection)
	elif not (nonAnnualCropFind and featuresFind_NA) and (annualCropFind and annualPoints) : 
		shutil.copy(annualShape,sampleSelection)
	samples = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite")
        
        sampleExtr,a,b,c,d,e,f,g,h = gapFillingToSample("","",workingDirectory,samples,\
                                                        dataField,folderFeatures,currentTile,\
                                                        pathConf,wMode,sampleSelection,\
                                                        testMode,\
                                                        testSensorData)
        sampleExtr.ExecuteAndWriteOutput()
        finalSamples = folderSample+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite")
	if os.path.exists(samples) and pathWd :
            shutil.copy(samples,finalSamples)
	if os.path.exists(SampleSel_NA) :os.remove(SampleSel_NA)
	if os.path.exists(sampleSelection) :os.remove(sampleSelection)
	if os.path.exists(stats_NA) :os.remove(stats_NA)

        if wMode : 
            targetDirectory=folderFeatures+"/"+currentTile
            if not os.path.exists(targetDirectory) : 
                copyanything(workingDirectory+"/"+currentTile,targetDirectory)

	if testMode : return finalSamples

def generateSamples(trainShape,pathWd,pathConf,wMode=False,folderFeatures=None,\
                    folderAnnualFeatures=None,\
                    testMode=False,testSensorData=None,testNonAnnualData=None,\
                    testAnnualData=None,testPrevConfig=None,testShapeRegion=None,\
                    testTestPath=None,testPrevClassif=None):
    """
    usage :

    IN:
    trainShape [string] : path to a shapeFile
    pathWd [string] : working directory
    pathConf [string] : path to the configuration file

    testMode [bool] : enable test
    features [string] : path to features allready compute (refl + NDVI ...)
    testFeaturePath [string] : path to stack of data without features 
    testAnnualFeaturePath [string] : path to stack of data without features 
    testPrevConfig [string] : path to a configuration file
    testShapeRegion [string] : path to a vector shapeFile, representing region in tile

    OUT:
    samples [string] : path to output vector shape
    """
    featuresPath = testNonAnnualData
    TestPath = testTestPath
    dataField = Config(file(pathConf)).chain.dataField
    configPrevClassif = testPrevConfig
    
    samplesOptions = Config(file(pathConf)).argTrain.samplesOptions
    cropMix = Config(file(pathConf)).argTrain.cropMix
    samplesClassifMix = Config(file(pathConf)).argTrain.samplesClassifMix

    prevFeatures = testAnnualData
    annualCrop = Config(file(pathConf)).argTrain.annualCrop
    AllClass = fu.getFieldElement(trainShape,"ESRI Shapefile",dataField,mode = "unique",elemType = "str")
    folderFeaturesAnnual = folderAnnualFeatures
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
    
    if testMode==False :
            featuresPath = Config(file(pathConf)).chain.featuresPath
            wMode = Config(file(pathConf)).GlobChain.writeOutputs
            folderFeatures = Config(file(pathConf)).chain.featuresPath
            folderFeaturesAnnual = Config(file(pathConf)).argTrain.outputPrevFeatures
            TestPath = Config(file(pathConf)).chain.outputPath
            prevFeatures = Config(file(pathConf)).argTrain.prevFeatures
            configPrevClassif = Config(file(pathConf)).argTrain.configClassif

    folderSample = TestPath+"/learningSamples"
    if not os.path.exists(folderSample):
        os.system("mkdir "+folderSample)

    workingDirectory = folderSample
    if pathWd:
        workingDirectory = pathWd

    if not cropMix == 'True':
        samples = generateSamples_simple(folderSample,workingDirectory,trainShape,pathWd,featuresPath,\
                                         samplesOptions,pathConf,dataField,wMode,folderFeatures,\
                                         testMode,testSensorData,testNonAnnualData)
    elif cropMix == 'True' and samplesClassifMix == "False":
        samples = generateSamples_cropMix(folderSample,workingDirectory,trainShape,pathWd,featuresPath,\
                                          samplesOptions,prevFeatures,annualCrop,AllClass,dataField,pathConf,\
                                          folderFeatures,folderFeaturesAnnual,wMode,testMode)
    elif cropMix == 'True' and samplesClassifMix == "True":
	samples = generateSamples_classifMix(folderSample,workingDirectory,trainShape,pathWd,samplesOptions,\
                                             annualCrop,AllClass,dataField,pathConf,configPrevClassif,folderFeatures,
                                             wMode,\
                                             testMode,\
                                             testSensorData,\
                                             testPrevClassif,\
                                             testShapeRegion)
    if testMode : return samples

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "This function sample a shapeFile")
    parser.add_argument("-shape",dest = "shape",help ="path to the shapeFile to sampled",default=None,required=True)
    parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
    parser.add_argument("-conf",help ="path to the configuration file (mandatory)",dest = "pathConf",required=True)
    args = parser.parse_args()

    generateSamples(args.shape,args.pathWd,args.pathConf)

















