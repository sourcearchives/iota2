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
from osgeo import gdal
from osgeo.gdalconst import *
from osgeo import ogr
import fileUtils as fu
import numpy as np

def raster2array(rasterfn):
    raster = gdal.Open(rasterfn)
    band = raster.GetRasterBand(1)
    return band.ReadAsArray()

def getDiffHisto(confMin,confMax,confStep,confidence,difference):

	diff = [[],[],[],[],[],[],[]]
	for currentConf in np.arange(confMin,confMax+1,confStep):
		x,y = np.where(confidence==currentConf)
		coord = [(currentX,currentY) for currentX,currentY in zip(x,y)]
	
		for currentX,currentY in coord:
			diff[difference[currentX][currentY]].append(currentConf)
	return diff

def genStatsDiff(pathToConfigstats,StatsName,histo,bins):
	stats = open(pathToConfigstats,"a")
	stats.write(StatsName+":\n{\n\thistogram:'"+histo+"'\n\tbins:'"+bins+"'\n}\n\n")
	stats.close()

def histo(array,bins):
	hist = []
	for currentBin in bins:
		indexes = np.where(array==currentBin)
		hist.append(len(indexes[0]))
	return hist,bins

def outStats(config,tile,sample,workingDirectory):

	Testpath = Config(file(config)).chain.outputPath
	Nruns = int(Config(file(config)).chain.runs)
	featuresPath = Config(file(config)).chain.featuresPath
	stackName = fu.getFeatStackName(config)
	statsName=["ValidOK","ValidNOK","AppOK","AppNOK"]
	
	"""
	1 valid NOK
	2 valid OK
	3 app NOK
	4 app OK
	"""

	confStep = 1
	confMin = 1
	confMax = 100
	
	cloudAllTile = Testpath+"/final/PixelsValidity.tif"
	src_ds = gdal.Open(cloudAllTile)
	if src_ds is None:
        	print 'Unable to open %s'%cloudAllTile
        	sys.exit(1)

       	srcband = src_ds.GetRasterBand(1).ReadAsArray()
	maxView = np.amax(srcband)
	Cloud = raster2array(Testpath+"/final/TMP/"+tile+"_Cloud.tif")
	for seed in range(Nruns):
		Classif = raster2array(Testpath+"/final/TMP/"+tile+"_seed_"+str(seed)+".tif")
		confidence = raster2array(Testpath+"/final/TMP/"+tile+"_GlobalConfidence_seed_"+str(seed)+".tif")
		difference = raster2array(Testpath+"/final/TMP/"+tile+"_seed_"+str(seed)+"_CompRef.tif")
		diffHisto = getDiffHisto(confMin,confMax,confStep,confidence,difference)

		statsTile = Testpath+"/final/TMP/"+tile+"_stats_seed_"+str(seed)+".cfg"
		stats = open(statsTile,"a")
		stats.write("AllDiffStats:'"+",".join(statsName)+"'\n")
		stats.close()
		for i in range(len(statsName)):
			hist, bin_edges = histo(diffHisto[i+1],bins=np.arange(confMin,confMax+1,confStep))
			hist_str = " ".join([str(currentVal) for currentVal in hist])
			bin_edges_str = " ".join([str(currentVal) for currentVal in bin_edges])
			genStatsDiff(statsTile,statsName[i],hist_str,bin_edges_str)

		histNView, binsNview = histo(Cloud,bins=np.arange(0,maxView+1,1))
		hist_str = " ".join([str(currentVal) for currentVal in histNView])
		bin_edges_str = " ".join([str(currentVal) for currentVal in binsNview])
		genStatsDiff(statsTile,"TileValidity",hist_str,bin_edges_str)
			
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allows you launch the chain according to a configuration file")
	parser.add_argument("-conf",dest = "config",help ="path to configuration file",required=True)
	parser.add_argument("-tile",dest = "tile",help ="Tile to extract statistics",required=True)
	parser.add_argument("--sample",dest = "sample",help ="path to configuration file",required=False,default = None)
	parser.add_argument("--wd",dest = "workingDirectory",help ="path to the working directory",required=False,default = None)
	args = parser.parse_args()

	outStats(args.config,args.tile,args.sample,args.workingDirectory)


