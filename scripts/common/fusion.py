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
import fileUtils as fu

def fusion(pathClassif,pathConf,pathWd):
	
	f = file(pathConf)
	cfg = Config(f)
	classifMode = cfg.argClassification.classifMode
	N = int(cfg.chain.runs)
	allTiles = cfg.chain.listTile.split(" ")
	fusionOptions = cfg.argClassification.fusionOptions
	mode = cfg.chain.mode

	if mode == "outside":
		AllClassif = fu.fileSearchRegEx(pathClassif+"/Classif_*_model_*f*_seed_*.tif")
		allTiles = []
		models = []
		for classif in AllClassif:
			mod = classif.split("/")[-1].split("_")[3].split("f")[0]
			tile = classif.split("/")[-1].split("_")[1]
			if not mod in models:
				models.append(mod)
			if not tile in allTiles:
				allTiles.append(tile)
	AllCmd = []
	for seed in range(N):
		for tile in allTiles:
			directoryOut = pathClassif
			if pathWd != None :
					directoryOut = "$TMPDIR"

			if mode != "outside":
				classifPath = fu.FileSearch_AND(pathClassif,True,"Classif_"+tile,"seed_"+str(seed)+".tif")
				allPathFusion = " ".join(classifPath)
				cmd = "otbcli_FusionOfClassifications -il "+allPathFusion+" "+fusionOptions+" -out "+directoryOut+"/"+tile+"_FUSION_seed_"+str(seed)+".tif"
				AllCmd.append(cmd)
			else:
				for mod in models:
					classifPath = fu.fileSearchRegEx(pathClassif+"/Classif_"+tile+"_model_"+mod+"f*_seed_"+str(seed)+".tif")
					if len(classifPath)!=0:
						allPathFusion = " ".join(classifPath)
						cmd = "otbcli_FusionOfClassifications -il "+allPathFusion+" "+fusionOptions+" -out "+directoryOut+"/"+tile+"_FUSION_model_"+mod+"_seed_"+str(seed)+".tif"
						AllCmd.append(cmd)

	tmp = pathClassif.split("/")
	if pathClassif[-1]=="/":
		del tmp[-1]
	tmp[-1]="cmd/fusion"
	pathToCmdFusion = "/".join(tmp)

	#pathToCmdFusion = pathClassif.replace("classif","cmd/fusion")
	fu.writeCmds(pathToCmdFusion+"/fusion.txt",AllCmd)

	return AllCmd

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you launch oso chain according to a configuration file")
	parser.add_argument("-path.classif",help ="path to the folder which ONLY contains classification images (mandatory)",dest = "pathClassif",required=True)
	parser.add_argument("-conf",help ="path to the configuration file which describe the classification (mandatory)",dest = "pathConf",required=False)
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
	args = parser.parse_args()

	fusion(args.pathClassif,args.pathConf,args.pathWd)















