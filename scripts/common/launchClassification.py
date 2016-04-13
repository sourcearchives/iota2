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
from config import Config
from collections import defaultdict
from osgeo import gdal, ogr,osr
import fileUtils as fu

def launchClassification(model,pathConf,stat,pathToRT,pathToImg,pathToRegion,fieldRegion,N,pathToCmdClassif,pathOut,pathWd):

	f = file(pathConf)
	
	cfg = Config(f)
	classif = cfg.argTrain.classifier
	mode = cfg.chain.mode

	classifMode = cfg.argClassification.classifMode
	pixType = cfg.argClassification.pixType
	listIndices = cfg.GlobChain.features
	if len(listIndices)>1:
		listIndices = list(listIndices)
		listIndices = sorted(listIndices)
		listFeat = "_".join(listIndices)
	else:
		listFeat = listIndices[0]

	AllCmd = []

	allTiles_s = cfg.chain.listTile
	allTiles = allTiles_s.split(" ")

	if classifMode.count("separate")!=0:
		maskFiles = pathOut+"/MASK"
		if not os.path.exists(maskFiles):
			os.system("mkdir "+maskFiles)
		
		shpRName = pathToRegion.split("/")[-1].replace(".shp","")

		AllModel = fu.FileSearch_AND(model,"model",".txt")

		for path in AllModel :
			tiles = path.replace(".txt","").split("/")[-1].split("_")[2:len(path.split("/")[-1].split("_"))-2]
			model = path.split("/")[-1].split("_")[1]
			seed = path.split("/")[-1].split("_")[-1].replace(".txt","")
		
			#construction du string de sortie
			for tile in tiles:
				pathToFeat = pathToImg+"/"+tile+"/Final/"+"SL_MultiTempGapF_"+listFeat+"__.tif"
				maskSHP = pathToRT+"/"+shpRName+"_region_"+model+"_"+tile+".shp"
				maskTif = shpRName+"_region_"+model+"_"+tile+".tif"
				maskClassif = "MASK_Classif_"+shpRName+"_region_"+model+"_"+tile+".tif"
				#Création du mask cas cluster
				if not os.path.exists(maskFiles+"/"+maskTif):
					
					#cas cluster
					if pathWd != None:

						nameOut = fu.ClipVectorData(maskSHP,pathToImg+"/"+tile+"/MaskCommunSL.shp", pathWd,maskTif.replace(".tif",""))
						cmdRaster = "otbcli_Rasterization -in "+nameOut+" -mode attribute -mode.attribute.field "+fieldRegion+" -im "+pathToFeat+" -out "+pathWd+"/"+maskTif
						print cmdRaster
						os.system(cmdRaster)
						os.system("cp "+pathWd+"/"+maskTif+" "+maskFiles)

					else:
						nameOut = fu.ClipVectorData(maskSHP,pathToImg+"/"+tile+"/tmp/MaskCommunSL.shp", maskFiles,maskTif.replace(".tif",""))
						cmdRaster = "otbcli_Rasterization -in "+nameOut+" -mode attribute -mode.attribute.field "+fieldRegion+" -im "+pathToFeat+" -out "+maskFiles+"/"+maskTif
						print cmdRaster
						os.system(cmdRaster)

				if pathWd == None:
					out = pathOut+"/Classif_"+tile+"_model_"+model+"_seed_"+seed+".tif"
				#hpc case
				else :
					out = "$TMPDIR/Classif_"+tile+"_model_"+model+"_seed_"+seed+".tif"

				cmd = "otbcli_ImageClassifier -in "+pathToFeat+" -model "+path+" -mask "+maskFiles+"/"+maskTif+" -out "+out+" "+pixType+" -ram 128"


                                #Ajout des stats lors de la phase de classification
				if classif == "svm" or "rf":
					cmd = cmd+" -imstat "+stat+"/Model_"+str(model)+".xml"
				AllCmd.append(cmd)

	elif classifMode.count("fusion")!=0:

		maskFiles = pathOut+"/MASK"
		if not os.path.exists(maskFiles):
			os.system("mkdir "+maskFiles)
		pathToEnvelope = pathOut.replace("classif","envelope")
		shpRName = pathToRegion.split("/")[-1].replace(".shp","")

		AllModel = fu.FileSearch_AND(model,"model",".txt")

		for path in AllModel :
			tiles = path.replace(".txt","").split("/")[-1].split("_")[2:len(path.split("/")[-1].split("_"))-2]
			model = path.split("/")[-1].split("_")[1]
			seed = path.split("/")[-1].split("_")[-1].replace(".txt","")
		
			#construction du string de sortie
			for tile in allTiles:
				pathToFeat = pathToImg+"/"+tile+"/Final/SL_MultiTempGapF_"+listFeat+"__.tif"
				maskSHP = pathToEnvelope+"/"+tile+".shp"
				maskTif = shpRName+"_region_"+model+"_"+tile+".tif"
				maskClassif = "MASK_Classif_"+shpRName+"_region_"+model+"_"+tile+".tif"
				#Création du mask
				if not os.path.exists(maskFiles+"/"+maskTif):
					#cas cluster
					if pathWd != None:
						nameOut = fu.ClipVectorData(pathToImg+"/"+tile+"/MaskCommunSL.shp", maskSHP, pathWd,maskTif.replace(".tif",""))
						cmdRaster = "otbcli_Rasterization -in "+nameOut+" -mode binary -mode.binary.foreground 1 -im "+pathToFeat+" -out "+pathWd+"/"+maskTif
						print cmdRaster
						os.system(cmdRaster)
						os.system("cp "+pathWd+"/"+maskTif+" "+maskFiles)
						
					else:
						nameOut = fu.ClipVectorData(pathToImg+"/"+tile+"/tmp/MaskCommunSL.shp", maskSHP, maskFiles,maskTif.replace(".tif",""))


						cmdRaster = "otbcli_Rasterization -in "+nameOut+" -mode binary -mode.binary.foreground 1 -im "+pathToFeat+" -out "+maskFiles+"/"+maskTif
						print cmdRaster
						os.system(cmdRaster)
			
				if pathWd == None:
					out = pathOut+"/Classif_"+tile+"_model_"+model+"_seed_"+seed+".tif"
				#hpc case
				else :
					out = "$TMPDIR/Classif_"+tile+"_model_"+model+"_seed_"+seed+".tif"

				cmd = "otbcli_ImageClassifier -in "+pathToFeat+" -model "+path+" -mask "+maskFiles+"/"+maskTif+" -out "+out+" "+pixType+" -ram 128"

				# ajout des statistiques dans le cas RF (car NDWI,NDVI*1000)
				if classif == "svm" or classif == "rf":
					cmd = cmd+" -imstat "+stat+"/Model_"+str(model)+".xml"
				AllCmd.append(cmd)

	#écriture du fichier de cmd
	if pathWd ==  None:
		cmdFile = open(pathToCmdClassif+"/class.txt","w")
		for i in range(len(AllCmd)):
			if i == 0:
				cmdFile.write("%s"%(AllCmd[i]))
			else:
				cmdFile.write("\n%s"%(AllCmd[i]))
		cmdFile.close()
	#hpc case
	else:
		cmdFile = open(pathWd+"/class.txt","w")
		for i in range(len(AllCmd)):
			if i == 0:
				cmdFile.write("%s"%(AllCmd[i]))
			else:
				cmdFile.write("\n%s"%(AllCmd[i]))
		cmdFile.close()
		os.system("cp "+pathWd+"/class.txt "+pathToCmdClassif)

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
































