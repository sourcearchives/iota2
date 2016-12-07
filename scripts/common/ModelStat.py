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
import getModel as GM
from config import Config
import fileUtils as fu

def generateStatModel(pathShapes,pathToTiles,pathToStats,pathToCmdStats,pathWd,pathConf):

	AllCmd = []
	modTiles = GM.getModel(pathShapes)
	cfg = Config(pathConf)
	Stack_ind = fu.getFeatStackName(pathConf)
	
	for mod, Tiles in modTiles:
		allpath = ""
		for tile in Tiles:
			pathToFeat = pathToTiles+"/"+tile+"/Final/"+Stack_ind
			allpath = allpath+" "+pathToFeat+" "
		#hpc case
		if pathWd != None:
			pathToStats = "$TMPDIR"
		cmd = "otbcli_ComputeImagesStatistics -il "+allpath+" -out "+pathToStats+"/Model_"+str(mod)+".xml"

		AllCmd.append(cmd)

	fu.writeCmds(pathToCmdStats+"/stats.txt",AllCmd)

	return AllCmd

if __name__ == "__main__":
	
	parser = argparse.ArgumentParser(description = "This function compute the statistics for a model compose by N tiles")

	parser.add_argument("-shapesIn",help ="path to the folder which ONLY contains shapes for the classification (learning and validation) (mandatory)",dest = "pathShapes",required=True)
	parser.add_argument("-tiles.path",dest = "pathToTiles",help ="path where tiles are stored (mandatory)",required=True)
	parser.add_argument("-Stats.out",dest = "pathToStats",help ="path where all statistics will be stored (mandatory)",required=True)
	parser.add_argument("-Stat.out.cmd",dest = "pathToCmdStats",help ="path where all statistics cmd will be stored in a text file(mandatory)",required=True)	
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
	parser.add_argument("-conf",help ="path to the configuration file which describe the learning method (mandatory)",dest = "pathConf",required=True)
	args = parser.parse_args()
	generateStatModel(args.pathShapes,args.pathToTiles,args.pathToStats,args.pathToCmdStats,args.pathWd,args.pathConf)






































