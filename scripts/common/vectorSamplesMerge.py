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

import argparse,os
import fileUtils as fu
from config import Config

def getAllModelsFromShape(PathLearningSamples):
	#AllSample = fu.fileSearchRegEx(PathLearningSamples+"/*.shp")
	AllSample = fu.fileSearchRegEx(PathLearningSamples+"/*.sqlite")
	AllModels = []
	for currentSample in AllSample:
		try:
			model = currentSample.split("/")[-1].split("_")[-4]
			ind = AllModels.index(model)
		except ValueError:
			AllModels.append(model)
	return AllModels

def vectorSamplesMerge(pathConf):
	
	f = file(pathConf)
	cfg = Config(f)
	outputPath = cfg.chain.outputPath
	runs = int(cfg.chain.runs)

	AllModels = getAllModelsFromShape(outputPath+"/learningSamples")
	
	for seed in range(runs):
		for currentModel in AllModels:
			#learningShapes = fu.fileSearchRegEx(outputPath+"/learningSamples/*_region_"+currentModel+"_seed"+str(seed)+"*.shp")
			learningShapes = fu.fileSearchRegEx(outputPath+"/learningSamples/*_region_"+currentModel+"_seed"+str(seed)+"*.sqlite")
			shapeOut = "Samples_region_"+currentModel+"_seed"+str(seed)+"_learn"
			folderOut = outputPath+"/learningSamples"
			#fu.mergeVectors(shapeOut, folderOut,learningShapes,ext="sqlite")
			fu.mergeSQLite(shapeOut, folderOut,learningShapes)
			for currentShape in learningShapes:
				#fu.removeShape(currentShape.replace(".shp",""),[".prj",".shp",".dbf",".shx"])
				os.remove(currentShape)

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function creates the jobArray.pbs for training")	
	parser.add_argument("-conf",help ="path to the configuration file (mandatory)",dest = "pathConf",required=True)	
	args = parser.parse_args()

	vectorSamplesMerge(args.pathConf)
