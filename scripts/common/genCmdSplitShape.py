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

def getAreaByRegion(allShape):
	"""
	IN :
		allShape [list] : list of path to ground truth shapeFile
	OUT :
		allArea [list] list of ground truth's area by regions in meter square
	"""
	shapeSort = []
	for shape in allShape:
		region = shape.split("_")[-2]
		shapeSort.append([region,shape])

	d = defaultdict(list)
	for k, v in shapeSort:
   		 d[k].append(v)
	shapeSort = list(d.items())
	allArea = []
	for region, shapesRegion in shapeSort:
		area = 0
		for shapeF in shapesRegion:
			area+= rs.getShapeSurface(shapeF)
		allArea.append([region,area])
	return allArea

def genCmdSplitShape(config):

	f = file(config)
	cfg = Config(f)
	maxArea = float(cfg.chain.mode_outside_RegionSplit)
	Nfold = int(cfg.chain.mode_outside_Nfold)
	outputpath = cfg.chain.outputPath
	dataField = cfg.chain.dataField
	allShape = fu.fileSearchRegEx(outputpath+"/dataRegion/*.shp")
	allArea = getAreaByRegion(allShape)
	print "all area [square meter]:"
	print allArea
	shapeToSplit = []
	TooBigRegions = [region for region,Rarea in allArea if Rarea/1e6 > maxArea]
	print TooBigRegions
	
	for bigR in TooBigRegions:
		tmp = fu.fileSearchRegEx(outputpath+"/dataAppVal/*_region_"+bigR+"*.shp")
		for shapeTmp in tmp:
			shapeToSplit.append(shapeTmp)
	print shapeToSplit
	
	#write cmds
	AllCmd = []
	for currentShape in shapeToSplit:
		cmd = "python splitShape.py -config "+config+" --wd $TMPDIR -path.shape "+currentShape+" -Nsplit "+str(Nfold)
		AllCmd.append(cmd)

	fu.writeCmds(outputpath+"/cmd/splitShape/splitShape.txt",AllCmd)
	return AllCmd
	

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "this function allow you to split a shape regarding a region shape")
	parser.add_argument("-config",dest = "config",help ="path to configuration file",required=True)
	args = parser.parse_args()

	genCmdSplitShape(args.config)










