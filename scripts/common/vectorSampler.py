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
import sys,os,random,shutil
import fileUtils as fu
from osgeo import ogr
from config import Config

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

	stats = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_stats.xml")
	tile = trainShape.split("/")[-1].split("_")[0]
	stack = fu.getFeatStackName(pathConf)
	feat = featuresPath+"/"+tile+"/Final/"+stack
	cmd = "otbcli_PolygonClassStatistics -in "+feat+" -vec "+trainShape+" -out "+stats+" -field "+dataField
	print cmd
	os.system(cmd)	
	#sampleSelection = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_SampleSel.shp")
	sampleSelection = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_SampleSel.sqlite")
	cmd = "otbcli_SampleSelection -out "+sampleSelection+" "+samplesOptions+" -field "+dataField+" -in "+feat+" -vec "+trainShape+" -instats "+stats
	print cmd
	os.system(cmd)
	#samples = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.shp")
	samples = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite")
	cmd = "otbcli_SampleExtraction -field "+dataField+" -out "+samples+" -vec "+sampleSelection+" -in "+feat
	print cmd
	os.system(cmd)

	if pathWd:
		#fu.cpShapeFile(samples.replace(".shp",""),folderSample,[".prj",".shp",".dbf",".shx"],spe=True)
		shutil.copy(samples,folderSample+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite"))

def generateSamples_cropMix(folderSample,workingDirectory,trainShape,pathWd,featuresPath,samplesOptions,prevFeatures,annualCrop,AllClass,dataField,pathConf):
	
	currentTile = trainShape.split("/")[-1].split("_")[0]
	stack = fu.getFeatStackName(pathConf)

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
	NA_img = featuresPath+"/"+currentTile+"/Final/"+stack
	cmd = "otbcli_PolygonClassStatistics -in "+NA_img+" -vec "+nonAnnualShape+" -field "+dataField+" -out "+stats_NA
	print cmd
	os.system(cmd)

	#Step 4 : Annual stats
	stats_A= workingDirectory+"/"+nameAnnual.replace(".shp","_STATS.xml")
	A_img = prevFeatures+"/"+currentTile+"/Final/"+stack
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

	#Step 7 : Sample extraction NonAnnual
	SampleExtr_NA = workingDirectory+"/"+nameNonAnnual.replace(".shp","_SampleExtr_NA.sqlite")
	cmd = "otbcli_SampleExtraction -in "+NA_img+" -vec "+SampleSel_NA+" -field "+dataField+" -out "+SampleExtr_NA
	print cmd
	os.system(cmd)

	#Step 8 : Sample extraction Annual
	SampleExtr_A = workingDirectory+"/"+nameAnnual.replace(".shp","_SampleExtr_A.sqlite")
	cmd = "otbcli_SampleExtraction -in "+A_img+" -vec "+SampleSel_A+" -field "+dataField+" -out "+SampleExtr_A
	if annualCropFind:
		print cmd
		os.system(cmd)

	#Step 9 : Merge
	MergeName = trainShape.split("/")[-1].replace(".shp","_Samples")
	listToMerge = [SampleExtr_NA]
	if annualCropFind:
		listToMerge = [SampleExtr_A,SampleExtr_NA]
	print "----------------------------------"
	print listToMerge
	print type(listToMerge)
	print "----------------------------------"
	fu.mergeSQLite(MergeName, workingDirectory,listToMerge)
	#fu.mergeVectors(MergeName, workingDirectory,listToMerge,ext="sqlite")
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
		#fu.cpShapeFile(samples.replace(".shp",""),folderSample,[".prj",".shp",".dbf",".shx"],spe=True)
		shutil.copy(samples,folderSample+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.sqlite"))
	
def generateSamples(trainShape,pathWd,pathConf):

	TestPath = Config(file(pathConf)).chain.outputPath
	dataField = Config(file(pathConf)).chain.dataField
	featuresPath = Config(file(pathConf)).chain.featuresPath
	samplesOptions = Config(file(pathConf)).argTrain.samplesOptions
	cropMix = Config(file(pathConf)).argTrain.cropMix
	
	folderSample = TestPath+"/learningSamples"
	if not os.path.exists(folderSample):
		os.system("mkdir "+folderSample)

	workingDirectory = folderSample
	if pathWd:
		workingDirectory = pathWd
	
	if not cropMix == 'True':
		generateSamples_simple(folderSample,workingDirectory,trainShape,pathWd,featuresPath,samplesOptions,pathConf,dataField)

	else:
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
		generateSamples_cropMix(folderSample,workingDirectory,trainShape,pathWd,featuresPath,samplesOptions,prevFeatures,annualCrop,AllClass,dataField,pathConf)

	

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function generates samples a shapeFile")
	parser.add_argument("-shape",dest = "shape",help ="path to the shapeFile to sampled",default=None,required=True)
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
	parser.add_argument("-conf",help ="path to the configuration file (mandatory)",dest = "pathConf",required=True)
	args = parser.parse_args()

	generateSamples(args.shape,args.pathWd,args.pathConf)

















