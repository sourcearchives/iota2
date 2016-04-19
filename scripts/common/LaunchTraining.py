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
import fileUtils as fu


def launchTraining(pathShapes,pathConf,pathToTiles,dataField,stat,N,pathToCmdTrain,out,pathWd,pathlog):

	"""
	OUT : les commandes pour l'app
	"""
	cmd_out = []

	f = file(pathConf)
	cfg = Config(f)
	classif = cfg.argTrain.classifier
	options = cfg.argTrain.options

	listIndices = cfg.GlobChain.features
	if len(listIndices)>1:
		listIndices = list(listIndices)
		listIndices = sorted(listIndices)
		listFeat = "_".join(listIndices)
	else:
		listFeat = listIndices[0]

	Stack_ind = "SL_MultiTempGapF_"+listFeat+"__.tif"

	for seed in range(N):
		pathAppVal = fu.FileSearch_AND(pathShapes,True,"seed"+str(seed),".shp","learn")

		#training cmd generation
		sort = []
		for path in pathAppVal:
			sort.append((int(path.split("/")[-1].split("_")[-3]),path))
	
		d = defaultdict(list)
		for k, v in sort:
   			d[k].append(v)
		sort = list(d.items())#[(RegionNumber,[shp1,shp2,...]),(...),...]

		#get tiles by model
		names = []
		for r,paths in sort:
			tmp = ""
			for i in range(len(paths)):
				if i <len(paths)-1:
					tmp = tmp+paths[i].split("/")[-1].split("_")[0]+"_"
				else :
					tmp = tmp+paths[i].split("/")[-1].split("_")[0]
			names.append(tmp)
		cpt = 0
		for r,paths in sort:
			cmd = "otbcli_TrainImagesClassifier -io.il "
			for path in paths:
				if path.count("learn")!=0:
					tile = path.split("/")[-1].split("_")[0]
					pathToFeat = pathToTiles+"/"+tile+"/Final/"+"SL_MultiTempGapF_"+listFeat+"__.tif"
					cmd = cmd+pathToFeat+" " 

			cmd = cmd+"-io.vd"
			for path in paths:
				if path.count("learn")!=0:
					cmd = cmd +" "+path

			cmd = cmd+" -classifier "+classif+" "+options+" -sample.vfn "+dataField
			#if pathWd != None:
			#	out="$TMPDIR"
			cmd = cmd+" -io.out "+out+"/model_"+str(r)+"_"+names[cpt]+"_seed_"+str(seed)+".txt"

			if ("svm" in classif)or("rf" in classif):
				cmd = cmd + " -io.imstat "+stat+"/Model_"+str(r)+".xml"

			if pathlog != None:
				cmd = cmd +" > "+pathlog+"/LOG_model_"+str(r)+"_seed_"+str(seed)+".out"
			cmd_out.append(cmd)
			cpt+=1

	fu.writeCmds(pathToCmdTrain+"/train.txt",cmd_out)

	return cmd_out

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you to create a training command for a classifieur according to a configuration file")
	parser.add_argument("-shapesIn",help ="path to the folder which ONLY contains shapes for the classification (learning and validation) (mandatory)",dest = "pathShapes",required=True)
	parser.add_argument("-conf",help ="path to the configuration file which describe the learning method (mandatory)",dest = "pathConf",required=True)
	parser.add_argument("-tiles.path",dest = "pathToTiles",help ="path where tiles are stored (mandatory)",required=True)
	parser.add_argument("-data.field",dest = "dataField",help ="data field into data shape (mandatory)",required=True)
	parser.add_argument("-N",dest = "N",type = int,help ="number of random sample(mandatory)",required=True)
	parser.add_argument("--stat",dest = "stat",help ="statistics for classification",required=False)
	parser.add_argument("-train.out.cmd",dest = "pathToCmdTrain",help ="path where all training cmd will be stored in a text file(mandatory)",required=True)	
	parser.add_argument("-out",dest = "out",help ="path where all models will be stored(mandatory)",required=True)
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
	parser.add_argument("--path.log",dest = "pathlog",help ="path to the log file",default=None,required=False)
	args = parser.parse_args()

	launchTraining(args.pathShapes,args.pathConf,args.pathToTiles,args.dataField,args.stat,args.N,args.pathToCmdTrain,args.out,args.pathWd,args.pathlog)


























































