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
from config import Config

def generateSamples(trainShape,pathWd,pathConf):

	TestPath = Config(file(pathConf)).chain.outputPath
	dataField = Config(file(pathConf)).chain.dataField
	featuresPath = Config(file(pathConf)).chain.featuresPath
	samplesOptions = Config(file(pathConf)).argTrain.samplesOptions

	folderSample = TestPath+"/learningSamples"
	if not os.path.exists(folderSample):
		os.system("mkdir "+folderSample)

	workingDirectory = folderSample
	if pathWd:
		workingDirectory = pathWd
	
	stats = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_stats.xml")
	tile = trainShape.split("/")[-1].split("_")[0]
	stack = fu.getFeatStackName(pathConf)
	feat = featuresPath+"/"+tile+"/Final/"+stack
	cmd = "otbcli_PolygonClassStatistics -in "+feat+" -vec "+trainShape+" -out "+stats+" -field "+dataField
	print cmd
	os.system(cmd)	
	sampleSelection = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_SampleSel.shp")
	cmd = "otbcli_SampleSelection -out "+sampleSelection+" "+samplesOptions+" -field "+dataField+" -in "+feat+" -vec "+trainShape+" -instats "+stats
	print cmd
	os.system(cmd)
	samples = workingDirectory+"/"+trainShape.split("/")[-1].replace(".shp","_Samples.shp")
	cmd = "otbcli_SampleExtraction -field "+dataField+" -out "+samples+" -vec "+sampleSelection+" -in "+feat
	print cmd
	os.system(cmd)

	if pathWd:
		#shutil.copy(stats,folderSample)
		#fu.cpShapeFile(sampleSelection.replace(".shp",""),folderSample,[".prj",".shp",".dbf",".shx"],spe=True)
		fu.cpShapeFile(samples.replace(".shp",""),folderSample,[".prj",".shp",".dbf",".shx"],spe=True)

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function generates samples a shapeFile")
	parser.add_argument("-shape",dest = "shape",help ="path to the shapeFile to sampled",default=None,required=True)
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
	parser.add_argument("-conf",help ="path to the configuration file (mandatory)",dest = "pathConf",required=True)
	args = parser.parse_args()

	generateSamples(args.shape,args.pathWd,args.pathConf)

















