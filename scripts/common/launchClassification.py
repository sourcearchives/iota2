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

import argparse,os,re
from config import Config
from osgeo import gdal, ogr,osr
import fileUtils as fu

def launchClassification(model,pathConf,stat,pathToRT,pathToImg,pathToRegion,fieldRegion,N,pathToCmdClassif,pathOut,pathWd):

	f = file(pathConf)
	
	cfg = Config(f)
	classif = cfg.argTrain.classifier
	mode = cfg.chain.mode
	outputPath = cfg.chain.outputPath
	classifMode = cfg.argClassification.classifMode
	regionMode = cfg.chain.mode
	pixType = cfg.argClassification.pixType
	bindingPy = cfg.GlobChain.bindingPython

	Stack_ind = fu.getFeatStackName(pathConf)
	
	AllCmd = []

	allTiles_s = cfg.chain.listTile
	allTiles = allTiles_s.split(" ")

	maskFiles = pathOut+"/MASK"
	if not os.path.exists(maskFiles):
		os.system("mkdir "+maskFiles)
		
	shpRName = pathToRegion.split("/")[-1].replace(".shp","")

	AllModel_tmp = fu.FileSearch_AND(model,True,"model",".txt")
	AllModel = fu.fileSearchRegEx(model+"/*model*.txt")
	
	for currentFile in AllModel_tmp:
		if not currentFile in AllModel:
			os.remove(currentFile)

	for path in AllModel :
		model = path.split("/")[-1].split("_")[1]
		tiles = fu.getListTileFromModel(model,outputPath+"/config_model/configModel.cfg")

		model_Mask = model
		if re.search('model_.*f.*_', path.split("/")[-1]):
			model_Mask = path.split("/")[-1].split("_")[1].split("f")[0]
		seed = path.split("/")[-1].split("_")[-1].replace(".txt","")
		tilesToEvaluate = tiles
		if ("fusion" in classifMode and regionMode != "outside" ) or (regionMode == "one_region"):
			tilesToEvaluate = allTiles
		#construction du string de sortie
		for tile in tilesToEvaluate:
			pathToFeat = pathToImg+"/"+tile+"/Final/"+Stack_ind
			if bindingPy == "True":
				pathToFeat = fu.FileSearch_AND(pathToImg+"/"+tile+"/tmp/",True,".tif")[0]
			maskSHP = pathToRT+"/"+shpRName+"_region_"+model_Mask+"_"+tile+".shp"
			maskTif = shpRName+"_region_"+model_Mask+"_"+tile+".tif"

			CmdConfidenceMap = ""
			confidenceMap = ""
			if "fusion" in classifMode:
				if mode!= "outside":
					tmp = pathOut.split("/")
					if pathOut[-1]=="/":
						del tmp[-1]
					tmp[-1]="envelope"
					pathToEnvelope = "/".join(tmp)
					maskSHP = pathToEnvelope+"/"+tile+".shp"
			confidenceMap = tile+"_model_"+model+"_confidence_seed_"+seed+".tif"
			CmdConfidenceMap = " -confmap "+pathOut+"/"+confidenceMap

			if not os.path.exists(maskFiles+"/"+maskTif):
				pathToMaskCommun = pathToImg+"/"+tile+"/tmp/MaskCommunSL.shp"
				#cas cluster
				if pathWd != None:
					pathToMaskCommun = pathToImg+"/"+tile+"/MaskCommunSL.shp"
					maskFiles = pathWd
			
				nameOut = fu.ClipVectorData(maskSHP,pathToMaskCommun, maskFiles,maskTif.replace(".tif",""))
				cmdRaster = "otbcli_Rasterization -in "+nameOut+" -mode attribute -mode.attribute.field "+fieldRegion+" -im "+pathToFeat+" -out "+maskFiles+"/"+maskTif
				if "fusion" in classifMode:
					cmdRaster = "otbcli_Rasterization -in "+nameOut+" -mode binary -mode.binary.foreground 1 -im "+pathToFeat+" -out "+maskFiles+"/"+maskTif
				print cmdRaster
				os.system(cmdRaster)
				if pathWd != None:
					os.system("cp "+pathWd+"/"+maskTif+" "+pathOut+"/MASK")
					os.remove(pathWd+"/"+maskTif)

			out = pathOut+"/Classif_"+tile+"_model_"+model+"_seed_"+seed+".tif"
			
			cmdcpy = ""
			#hpc case
			if pathWd != None:
				out = "$TMPDIR/Classif_"+tile+"_model_"+model+"_seed_"+seed+".tif"
				CmdConfidenceMap = " -confmap $TMPDIR/"+confidenceMap
				cmdcpy = " && cp $TMPDIR/*.tif "+outputPath+"/classif/"

			appli = "otbcli_ImageClassifier "
			pixType_cmd = pixType
			if bindingPy == "True":
				appli = "python bPy_ImageClassifier.py -conf "+pathConf+" "
				pixType_cmd = " -pixType "+pixType
				cmdcpy = ""
				if pathWd != None:pixType_cmd=pixType_cmd+" --wd $TMPDIR "

			cmdcpy = ""
			cmd = appli+" -in "+pathToFeat+" -model "+path+" -mask "+pathOut+"/MASK/"+maskTif+" -out "+out+" "+pixType_cmd+" -ram 128 "+CmdConfidenceMap+" "+cmdcpy

                        #Ajout des stats lors de la phase de classification
			if classif == "svm":
				cmd = cmd+" -imstat "+stat+"/Model_"+str(model)+".xml"
			AllCmd.append(cmd)

	fu.writeCmds(pathToCmdClassif+"/class.txt",AllCmd)

	return AllCmd

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you to create all classification command")
	parser.add_argument("-path.model",help ="path to the folder which ONLY contains models for the classification(mandatory)",dest = "model",required=True)
	parser.add_argument("-conf",help ="path to the configuration file which describe the learning method (mandatory)",dest = "pathConf",required=True)
	parser.add_argument("--stat",dest = "stat",help ="statistics for classification",required=False)
	parser.add_argument("-path.region.tile",dest = "pathToRT",help ="path to the folder which contains all region shapefile by tiles (mandatory)",required=True)
	parser.add_argument("-path.img",dest = "pathToImg",help ="path where all images are stored",required=True)
	parser.add_argument("-path.region",dest = "pathToRegion",help ="path to the global region shape",required=True)
	parser.add_argument("-region.field",dest = "fieldRegion",help ="region field into region shape",required=True)
	parser.add_argument("-N",dest = "N",help ="number of random sample(mandatory)",required=True)
	parser.add_argument("-classif.out.cmd",dest = "pathToCmdClassif",help ="path where all classification cmd will be stored in a text file(mandatory)",required=True)	
	parser.add_argument("-out",dest = "pathOut",help ="path where to stock all classifications",required=True)
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)

	args = parser.parse_args()

	launchClassification(args.model,args.pathConf,args.stat,args.pathToRT,args.pathToImg,args.pathToRegion,args.fieldRegion,args.N,args.pathToCmdClassif,args.pathOut,args.pathWd)
































