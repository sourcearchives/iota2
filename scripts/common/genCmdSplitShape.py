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
import sys,os,random
from osgeo import gdal, ogr,osr
from random import randrange
from collections import defaultdict
import repInShape as rs
from config import Config
import fileUtils as fu

def genCmdSplitShape(config):

	f = file(config)
	cfg = Config(f)
	Nregions = int(cfg.chain.mode_outside_RegionSplit)
	Nfold = int(cfg.chain.mode_outside_Nfold)
	shape = cfg.chain.regionPath
	regionField = cfg.chain.regionField
	outputpath = cfg.chain.outputPath
	dataField = cfg.chain.dataField

	repartition = rs.repartitionInShape(shape,regionField,None)

	bigestRegion = []
	for i in range(Nregions):
		bigestRegion.append(repartition[-1-i][0])

	allshape = []
	for region in bigestRegion:
		allshape_tmp = fu.FileSearch_AND(outputpath+"/dataAppVal",True,"region_"+str(region),".shp")
		for currentShape in allshape_tmp:
			allshape.append(currentShape)

	#write cmds
	AllCmd = []
	for currentShape in allshape:
		cmd = "python splitShape.py -config "+config+" --wd $TMPDIR -path.shape "+currentShape+" -Nsplit "+str(Nfold)
		AllCmd.append(cmd)

	fu.writeCmds(outputpath+"/cmd/splitShape/splitShape.txt",AllCmd)
	return AllCmd

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "this function allow you to split a shape regarding a region shape")
	parser.add_argument("-config",dest = "config",help ="path to configuration file",required=True)
	args = parser.parse_args()

	genCmdSplitShape(args.config)










