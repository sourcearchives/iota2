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
import matplotlib
matplotlib.use("AGG")
import matplotlib.pyplot as plt

def getValidOK(configStats):

	histoValidOK = Config(file(configStats)).ValidOK.histogram
	bins = Config(file(configStats)).ValidOK.bins
	
	histoValidOK_s = histoValidOK.split(" ")
	histoValidOK = [int(currentVal) for currentVal in histoValidOK_s]
	bins = bins.split(" ")
	bins_ = [int(currentVal) for currentVal in bins]
	
	return histoValidOK,bins_

def getValidNOK(configStats):

	histoValidNOK = Config(file(configStats)).ValidNOK.histogram
	bins = Config(file(configStats)).ValidNOK.bins
	
	histoValidNOK_s = histoValidNOK.split(" ")
	histoValidNOK = [int(currentVal) for currentVal in histoValidNOK_s]
	bins = bins.split(" ")
	bins_ = [int(currentVal) for currentVal in bins]
	
	return histoValidNOK,bins_

def getAppOK(configStats):

	histoAppOK = Config(file(configStats)).AppOK.histogram
	bins = Config(file(configStats)).AppOK.bins
	
	histoAppOK_s = histoAppOK.split(" ")
	histoAppOK = [int(currentVal) for currentVal in histoAppOK_s]
	bins = bins.split(" ")
	bins_ = [int(currentVal) for currentVal in bins]
	
	return histoAppOK,bins_

def getAppNOK(configStats):

	histoAppNOK = Config(file(configStats)).AppNOK.histogram
	bins = Config(file(configStats)).AppNOK.bins
	
	histoAppNOK_s = histoAppNOK.split(" ")
	histoAppNOK = [int(currentVal) for currentVal in histoAppNOK_s]
	bins = bins.split(" ")
	bins_ = [int(currentVal) for currentVal in bins]
	
	return histoAppNOK,bins_

def getValidity(configStats):

	histoValidity = Config(file(configStats)).TileValidity.histogram
	bins = Config(file(configStats)).TileValidity.bins
	
	histoValidity_s = histoValidity.split(" ")
	histoValidity = [int(currentVal) for currentVal in histoValidity_s]
	bins = bins.split(" ")
	bins_ = [int(currentVal) for currentVal in bins]
	
	return histoValidity,bins_

def SumInList(histoList):
	histoSum = [0]*len(histoList[0])
	for i in range(len(histoList)):#current Tile
		for j in range(len(histoList[i])):#current bin
			histoSum[j]+=histoList[i][j]
	return histoSum

def saveHisto(savePath,histo,bins):
	
	saveHistog = " ".join([str(currentVal) for currentVal in histo])
	saveBins = " ".join([str(currentVal) for currentVal in bins])
	with open(savePath,"w") as saveFile:
		saveFile.write("Pixels validity\nBins:"+saveBins+"\nHistogram:"+saveHistog)

def mergeOutStats(config):
	Testpath = Config(file(config)).chain.outputPath	
	Nruns = int(Config(file(config)).chain.runs)
	AllTiles = Config(file(config)).chain.listTile
	
	for seed in range(Nruns):
		seedStats = fu.fileSearchRegEx(Testpath+"/final/TMP/*_stats_seed_"+str(seed)+".cfg")
		AllDiffTest = Config(file(seedStats[0])).AllDiffStats
		AllDiffTest = AllDiffTest.split(",")
		VOK_buff = []
		VNOK_buff = []
		AOK_buff = []
		ANOK_buff = []
		Validity_buff = []
		for currentTileStats in seedStats:

			histoVOK,binsVOK = getValidOK(currentTileStats)
			histoVNOK,binsVNOK = getValidNOK(currentTileStats)
			histoAOK,binsAOK = getAppOK(currentTileStats)
			histoANOK,binsANOK = getAppNOK(currentTileStats)
			histoValidity,binsValidity = getValidity(currentTileStats)

			VOK_buff.append(histoVOK)
			VNOK_buff.append(histoVNOK)
			AOK_buff.append(histoAOK)
			ANOK_buff.append(histoANOK)
			Validity_buff.append(histoValidity)

		SumVOK = SumInList(VOK_buff)
		SumVNOK = SumInList(VNOK_buff)
		SumAOK = SumInList(AOK_buff)
		SumANOK = SumInList(ANOK_buff)
		SumValidity = SumInList(Validity_buff)

		plt.plot(binsVOK,SumVOK,label= "Validation OK",color="green")
		plt.plot(binsVNOK,SumVNOK,label= "Validation NOK",color="red")
		plt.ylabel("Nb pix")
		plt.xlabel("Confidence")
		plt.legend()
		plt.title('Histogram')
		plt.savefig(Testpath+"/final/Stats_VOK_VNOK.png")
		saveHisto(Testpath+"/final/Stats_VNOK.txt",SumVNOK,binsVNOK)
		saveHisto(Testpath+"/final/Stats_VOK.txt",SumVOK,binsVOK)

		plt.figure()
		plt.plot(binsAOK,SumAOK,label= "Learning OK",color="yellow")
		plt.plot(binsANOK,SumANOK,label= "Learning NOK",color="blue")
		plt.ylabel("Nb pix")
		plt.xlabel("Confidence")
		plt.legend()
		plt.title('Histogram')
		plt.savefig(Testpath+"/final/Stats_LOK_LNOK.png")
		saveHisto(Testpath+"/final/Stats_LNOK.txt",SumANOK,binsANOK)
		saveHisto(Testpath+"/final/Stats_LOK.txt",SumAOK,binsAOK)

		plt.figure()
		plt.bar(binsValidity,SumValidity,label= "pixels validity",color="red",align="center")
		plt.ylabel("Nb pix")
		plt.xlabel("Validity")
		plt.gca().yaxis.grid(True)
		plt.legend()
		plt.title('Histogram')
		plt.xticks(binsValidity, binsValidity)
		plt.xlim((0,max(binsValidity)+1))
		plt.savefig(Testpath+"/final/Validity.png")
		saveHisto(Testpath+"/final/Validity.txt",SumValidity,binsValidity)
			
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function merges tile's statistics")
	parser.add_argument("-conf",dest = "config",help ="path to configuration file",required=True)
	args = parser.parse_args()

	mergeOutStats(args.config)


