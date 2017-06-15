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
import sys,os,random,shutil,Sensors,osr
import fileUtils as fu
from osgeo import ogr
from config import Config
import otbApplication as otb
from Utils import Opath
import genAnnualSamples as genAS

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

def gapFillingToSample(sampleSelection,samples,dataField,featuresPath,tile,pathConf):
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

        S2 = Sensors.Sentinel_2("",Opath("",create = False),pathConf,"",createFolder = None)
        L8 = Sensors.Landsat8("",Opath("",create = False),pathConf,"",createFolder = None)
        L5 = Sensors.Landsat5("",Opath("",create = False),pathConf,"",createFolder = None)
        SensorsList = [S2,L8,L5]
  
        AllRefl = sorted(fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"REFL.tif"))
        AllMask = sorted(fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"MASK.tif"))
        datesInterp = sorted(fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"DatesInterp"))
        realDates = sorted(fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"imagesDate"))

        print "\n****** gapFilling to sample script ******"
	print "Reflectances used  : "+" ".join(AllRefl)
	print "masks used : "+" ".join(AllMask)
	print "interpolation dates : "+" ".join(datesInterp)
	print "real dates : "+" ".join(realDates)
        print "*****************************************\n"

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
	    if not outFeatures:
		print "without Features"
	    	concatSensors.AddImageToParameterInputImageList("il",gapFill.GetParameterOutputImage("out"))
		features.append(gapFill)
	    else:
		print "with Features"
		featExtr.Execute()
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

        return sampleExtr,featExtr,concatAllFeatures,concatFeatures,gapFill,concatSensors

def generateSamples_simple(folderSample,workingDirectory,trainShape,pathWd,featuresPath,samplesOptions,\
                           pathConf,dataField,testMode=False,testFeatures=None,testFeaturePath=None):
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
    if testMode and testFeaturePath : featuresPath = testFeaturePath
    bindingPython = Config(file(pathConf)).GlobChain.bindingPython
    dataField = Config(file(pathConf)).chain.dataField
    outputPath = Config(file(pathConf)).chain.outputPath
    userFeatPath = Config(file(pathConf)).chain.userFeatPath
    outFeatures = Config(file(pathConf)).GlobChain.features
    if userFeatPath == "None" : userFeatPath = None

    extractBands = Config(file(pathConf)).iota2FeatureExtraction.extractBands
    if extractBands == "False" : extractBands = None

    tmpFolder = outputPath+"/TMPFOLDER"

    #Sensors
    S2 = Sensors.Sentinel_2("",Opath(tmpFolder,create = False),pathConf,"",createFolder = None)
    L8 = Sensors.Landsat8("",Opath(tmpFolder,create = False),pathConf,"",createFolder = None)
    L5 = Sensors.Landsat5("",Opath(tmpFolder,create = False),pathConf,"",createFolder = None)
  
    SensorsList = [S2,L8,L5]
    stats = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_stats.xml")
    tile = trainShape.split("/")[-1].split("_")[0]
    stack = fu.getFeatStackName(pathConf)
    feat = featuresPath+"/"+tile+"/Final/"+stack
    if bindingPython == "True":
        feat = fu.FileSearch_AND(featuresPath+"/"+tile+"/tmp/",True,"ST_MASK")[0]
    if testFeatures : feat = testFeatures
    os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = "1"
    cmd = "otbcli_PolygonClassStatistics -in "+feat+" -vec "+trainShape+" -out "+stats+" -field "+dataField
    print cmd
    os.system(cmd)
    verifPolyStats(stats)
    sampleSelection = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_SampleSel.sqlite")
    cmd = "otbcli_SampleSelection -out "+sampleSelection+" "+samplesOptions+" -field "+\
          dataField+" -in "+feat+" -vec "+trainShape+" -instats "+stats
    print cmd
    os.system(cmd)

    os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = "5"
    samples = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite")
    
    if bindingPython == "True":
        sampleExtr,a,b,c,d,e = gapFillingToSample(sampleSelection,samples,dataField,featuresPath,tile,pathConf)
        sampleExtr.ExecuteAndWriteOutput()
    else:
        cmd = "otbcli_SampleExtraction -field "+dataField.lower()+" -out "+samples+" -vec "+sampleSelection+" -in "+feat
        print cmd
        os.system(cmd)
    if pathWd and not testMode:shutil.copy(samples,folderSample+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite"))
    os.remove(sampleSelection)
    os.remove(stats)
    if testMode : return samples

def generateSamples_cropMix(folderSample,workingDirectory,trainShape,pathWd,featuresPath,samplesOptions,\
                            prevFeatures,annualCrop,AllClass,dataField,pathConf,testMode=False,testFeatures=None,\
                            testFeaturePath=None,testAnnualFeaturePath=None):
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
    if testMode and testFeaturePath : 
        featuresPath = testFeaturePath
        prevFeatures = testAnnualFeaturePath

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

    S2 = Sensors.Sentinel_2("",Opath("",create = False),pathConf,"",createFolder = None)
    L8 = Sensors.Landsat8("",Opath("",create = False),pathConf,"",createFolder = None)
    L5 = Sensors.Landsat5("",Opath("",create = False),pathConf,"",createFolder = None)
    SensorsList = [S2,L8,L5]

    stack = "/Final/"+fu.getFeatStackName(pathConf)
    NA_img = featuresPath+"/"+currentTile+"/"+stack
    A_img = prevFeatures+"/"+currentTile+"/"+stack
    if bindingPy == "True":
        NA_img = fu.FileSearch_AND(featuresPath+"/"+currentTile+"/tmp/",True,"ST_MASK")[0]
	A_img = fu.FileSearch_AND(prevFeatures+"/"+currentTile+"/tmp/",True,"ST_MASK")[0]
    #Step 1 : filter trainShape in order to keep non-annual class
    nameNonAnnual = trainShape.split("/")[-1].replace(".shp","_NonAnnu.shp")
    nonAnnualShape = workingDirectory+"/"+nameNonAnnual
    nonAnnualCropFind = filterShpByClass(dataField,nonAnnualShape,AllClass,trainShape)

    #Step 2 : filter trainShape in order to keep annual class
    nameAnnual = trainShape.split("/")[-1].replace(".shp","_Annu.shp")
    annualShape = workingDirectory+"/"+nameAnnual
    annualCropFind = filterShpByClass(dataField,annualShape,annualCrop,trainShape)

    #Step 3 : nonAnnual stats
    stats_NA= workingDirectory+"/"+nameNonAnnual.replace(".shp","_STATS.xml")
    cmd = "otbcli_PolygonClassStatistics -in "+NA_img+" -vec "+nonAnnualShape+" -field "+dataField+" -out "+stats_NA
    if nonAnnualCropFind:
	print cmd
    	os.system(cmd)
    	verifPolyStats(stats_NA)

    #Step 4 : Annual stats
    stats_A= workingDirectory+"/"+nameAnnual.replace(".shp","_STATS.xml")
    cmd = "otbcli_PolygonClassStatistics -in "+A_img+" -vec "+annualShape+" -field "+dataField+" -out "+stats_A
    if annualCropFind:
        print cmd
        os.system(cmd)
   	verifPolyStats(stats_A)

    #Step 5 : Sample Selection NonAnnual
    SampleSel_NA = workingDirectory+"/"+nameNonAnnual.replace(".shp","_SampleSel_NA.sqlite")
    cmd = "otbcli_SampleSelection -in "+NA_img+" -vec "+nonAnnualShape+" -field "+\
          dataField+" -instats "+stats_NA+" -out "+SampleSel_NA+" "+samplesOptions
    if nonAnnualCropFind:
    	print cmd
    	os.system(cmd)
	featuresFind_NA = fu.getFieldElement(SampleSel_NA,driverName="SQLite",field = dataField.lower(),\
                                             mode = "all",elemType = "int")#check non-empty sampleSel

    #Step 6 : Sample Selection Annual
    SampleSel_A = workingDirectory+"/"+nameAnnual.replace(".shp","_SampleSel_A.sqlite")
    cmd = "otbcli_SampleSelection -in "+A_img+" -vec "+annualShape+" -field "+dataField+" -instats "+\
          stats_A+" -out "+SampleSel_A+" "+samplesOptions
    if annualCropFind:
        print cmd
        os.system(cmd)
	featuresFind_A = fu.getFieldElement(SampleSel_A,driverName="SQLite",field = dataField.lower(),\
                                            mode = "all",elemType = "int")#check non-empty sampleSel

    SampleExtr_NA = workingDirectory+"/"+nameNonAnnual.replace(".shp","_SampleExtr_NA.sqlite")
    SampleExtr_A = workingDirectory+"/"+nameAnnual.replace(".shp","_SampleExtr_A.sqlite")
    if bindingPy == "False":
	    #Step 7 : Sample extraction NonAnnual
	    cmd = "otbcli_SampleExtraction -in "+NA_img+" -vec "+SampleSel_NA+" -field "+dataField.lower()+" -out "+SampleExtr_NA
	    if nonAnnualCropFind and featuresFind_NA:
	    	print cmd
	    	os.system(cmd)

	    #Step 8 : Sample extraction Annual
	    cmd = "otbcli_SampleExtraction -in "+A_img+" -vec "+SampleSel_A+" -field "+dataField.lower()+" -out "+SampleExtr_A
	    if annualCropFind and featuresFind_A:
		print cmd
		os.system(cmd)
    else:
            #Step 7 : Sample extraction NonAnnual
            sampleExtr,a,b,c,d,e = gapFillingToSample(SampleSel_NA,SampleExtr_NA,dataField,featuresPath,currentTile,pathConf)
	    if nonAnnualCropFind and featuresFind_NA: sampleExtr.ExecuteAndWriteOutput()
            
            #Step 8 : Sample extraction Annual
            sampleExtra,a,b,c,d,e = gapFillingToSample(SampleSel_A,SampleExtr_A,dataField,prevFeatures,currentTile,pathConf)
            if annualCropFind and featuresFind_A:sampleExtra.ExecuteAndWriteOutput()

    #Step 9 : Merge
    MergeName = trainShape.split("/")[-1].replace(".shp","_Samples")

    #fu.mergeSQLite(MergeName, workingDirectory,listToMerge)
    if (nonAnnualCropFind and featuresFind_NA) and (annualCropFind and featuresFind_A):
	fu.mergeSQLite(MergeName, workingDirectory,[SampleExtr_NA,SampleExtr_A])
    elif (nonAnnualCropFind and featuresFind_NA) and not (annualCropFind and featuresFind_A):
	shutil.copyfile(SampleExtr_NA, workingDirectory+"/"+MergeName+".sqlite")
    elif not (nonAnnualCropFind and featuresFind_NA) and (annualCropFind and featuresFind_A):
 	shutil.copyfile(SampleExtr_A, workingDirectory+"/"+MergeName+".sqlite")

    samples = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite")

    if nonAnnualCropFind and featuresFind_NA:
    	os.remove(stats_NA)
    	os.remove(SampleSel_NA)
    	os.remove(SampleExtr_NA)
    	fu.removeShape(nonAnnualShape.replace(".shp",""),[".prj",".shp",".dbf",".shx"])

    if annualCropFind and featuresFind_A:
        os.remove(stats_A)
        os.remove(SampleSel_A)
        os.remove(SampleExtr_A)
        fu.removeShape(annualShape.replace(".shp",""),[".prj",".shp",".dbf",".shx"])

    if testMode : return samples
    if pathWd and os.path.exists(samples):
        shutil.copy(samples,folderSample+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite"))

def extractROI(raster,currentTile,pathConf,pathWd,name,testMode=None,testFeaturesPath=None):
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
	rasterROI = workingDirectory+"/"+currentTile+"_"+name+".tif"
        if testMode : featuresPath = testFeaturesPath
	currentTile_raster = fu.FileSearch_AND(featuresPath+"/"+currentTile,True,".tif")[0]

	minX,maxX,minY,maxY = fu.getRasterExtent(currentTile_raster)
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

def getRegionModelInTile(currentTile,currentRegion,pathWd,pathConf,refImg,testMode,testPath):
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
	
	if testMode : maskSHP = testPath
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

def generateSamples_classifMix(folderSample,workingDirectory,trainShape,pathWd,featuresPath,samplesOptions,\
                               annualCrop,AllClass,dataField,pathConf,configPrevClassif,testMode=None,testFeatures=None,\
                               testPrevClassif=None,testPrevConfig=None,testShapeRegion=None,testFeaturePath=None):
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
	if testMode : configPrevClassif = testPrevConfig

	corseTiles = ["T32TMN","T32TNN","T32TMM","T32TNM","T32TNL"]
	currentTile, bindingPy = trainShape.split("/")[-1].split("_")[0],Config(file(pathConf)).GlobChain.bindingPython
	if currentTile in corseTiles:
		generateSamples_simple(folderSample,workingDirectory,trainShape,pathWd,featuresPath,samplesOptions,pathConf,dataField)
		return 0
	targetResolution  = Config(file(pathConf)).chain.spatialResolution
        validityThreshold = Config(file(pathConf)).argTrain.validityThreshold
	previousClassifPath, projOut = Config(file(configPrevClassif)).chain.outputPath,Config(file(configPrevClassif)).GlobChain.proj
	projOut = int(projOut.split(":")[-1])
        stack = "/Final/"+fu.getFeatStackName(pathConf)
	userFeatPath = Config(file(pathConf)).chain.userFeatPath
	outFeatures = Config(file(pathConf)).GlobChain.features
	coeff = Config(file(pathConf)).argTrain.coeffSampleSelection
	extractBands = Config(file(pathConf)).iota2FeatureExtraction.extractBands

   	if extractBands == "False" : extractBands = None
        if userFeatPath == "None" : userFeatPath = None

	seed = trainShape.split("_")[-2]
        featImg = featuresPath+"/"+currentTile+"/"+stack
        if bindingPy == "True":
            featImg = fu.FileSearch_AND(featuresPath+"/"+currentTile+"/tmp/",True,"ST_MASK")[0]

	if testMode :
             featImg = testFeatures
             previousClassifPath = testPrevClassif
	if testMode and testFeaturePath:
             featuresPath = testFeaturePath

	nameNonAnnual = trainShape.split("/")[-1].replace(".shp","_NonAnnu.shp")
    	nonAnnualShape = workingDirectory+"/"+nameNonAnnual

	nameAnnual = trainShape.split("/")[-1].replace(".shp","_Annu.shp")
    	AnnualShape = workingDirectory+"/"+nameAnnual

    	nonAnnualCropFind = filterShpByClass(dataField,nonAnnualShape,AllClass,trainShape)
	annualCropFind = filterShpByClass(dataField,AnnualShape,annualCrop,trainShape)
	
	gdalDriver = "SQLite"
	SampleSel_NA = workingDirectory+"/"+nameNonAnnual.replace(".shp","_SampleSel_NA.sqlite")
	stats_NA= workingDirectory+"/"+nameNonAnnual.replace(".shp","_STATS.xml")
	if nonAnnualCropFind:
		cmd = "otbcli_PolygonClassStatistics -in "+featImg+" -vec "+nonAnnualShape+" -field "+dataField+" -out "+stats_NA
		print cmd
		os.system(cmd)
		verifPolyStats(stats_NA)
		cmd = "otbcli_SampleSelection -in "+featImg+" -vec "+nonAnnualShape+" -field "+\
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
                                          currentTile,pathConf,pathWd,"Classif",testMode,
                                          testFeaturePath)
	validityRaster = extractROI(previousClassifPath+"/final/PixelsValidity.tif",
                                    currentTile,pathConf,pathWd,"Cloud",testMode,
                                    testFeaturePath)

	maskFolder = previousClassifPath+"/classif/MASK"
	currentRegion = trainShape.split("/")[-1].split("_")[2].split("f")[0]
	mask = getRegionModelInTile(currentTile,currentRegion,pathWd,pathConf,classificationRaster,testMode,testShapeRegion)	
		
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
	if bindingPy == "False":
	    folderSample+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite")
	    if not os.path.exists(folderSample+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite"))\
               and os.path.exists(sampleSelection):
		cmd = "otbcli_SampleExtraction -in "+featImg+" -vec "+sampleSelection+" -field "+dataField.lower()+" -out "+samples
	    	print cmd
	    	os.system(cmd)
	else:
            sampleExtr,a,b,c,d,e = gapFillingToSample(sampleSelection,samples,dataField,featuresPath,currentTile,pathConf)
            sampleExtr.ExecuteAndWriteOutput()
	if os.path.exists(samples) and pathWd and not testMode:
		shutil.copy(samples,folderSample+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite"))
	if os.path.exists(SampleSel_NA) :os.remove(SampleSel_NA)
	if os.path.exists(sampleSelection) :os.remove(sampleSelection)
	if os.path.exists(stats_NA) :os.remove(stats_NA)

	if testMode : return samples

def generateSamples(trainShape,pathWd,pathConf,testMode=False,features=None,testFeaturePath=None,\
                    testAnnualFeaturePath=None,testPrevConfig=None,testShapeRegion=None):
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
    TestPath = Config(file(pathConf)).chain.outputPath
    dataField = Config(file(pathConf)).chain.dataField
    featuresPath = Config(file(pathConf)).chain.featuresPath
    samplesOptions = Config(file(pathConf)).argTrain.samplesOptions
    cropMix = Config(file(pathConf)).argTrain.cropMix
    samplesClassifMix = Config(file(pathConf)).argTrain.samplesClassifMix

    prevFeatures = Config(file(pathConf)).argTrain.prevFeatures
    annualCrop = Config(file(pathConf)).argTrain.annualCrop
    AllClass = fu.getFieldElement(trainShape,"ESRI Shapefile",dataField,mode = "unique",elemType = "str")
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
        samples = generateSamples_simple(folderSample,workingDirectory,trainShape,pathWd,featuresPath,\
                                         samplesOptions,pathConf,dataField,testMode,features,testFeaturePath)
    elif cropMix == 'True' and samplesClassifMix == "False":
        samples = generateSamples_cropMix(folderSample,workingDirectory,trainShape,pathWd,featuresPath,\
                                          samplesOptions,prevFeatures,annualCrop,AllClass,dataField,pathConf,\
                                          testMode,features,testFeaturePath,testAnnualFeaturePath)
    elif cropMix == 'True' and samplesClassifMix == "True":
	configPrevClassif = Config(file(pathConf)).argTrain.configClassif
	samples = generateSamples_classifMix(folderSample,workingDirectory,trainShape,pathWd,featuresPath,samplesOptions,\
                                   annualCrop,AllClass,dataField,pathConf,configPrevClassif,testMode,features,\
                                   testAnnualFeaturePath,testPrevConfig,testShapeRegion,testFeaturePath)

    if testMode : return samples

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "This function sample a shapeFile")
    parser.add_argument("-shape",dest = "shape",help ="path to the shapeFile to sampled",default=None,required=True)
    parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
    parser.add_argument("-conf",help ="path to the configuration file (mandatory)",dest = "pathConf",required=True)
    args = parser.parse_args()

    generateSamples(args.shape,args.pathWd,args.pathConf)

















