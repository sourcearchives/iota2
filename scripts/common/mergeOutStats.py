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

import argparse,os,math
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

def computeMeanStd(histo,bins):
	
	#Mean
	meanNom = 0.0
	for currentVal,currentBin in zip(histo,bins):
		meanNom += (currentVal*currentBin)
	mean = meanNom/(np.sum(histo))
	
	#Var
	varNom = 0.0
	for currentVal,currentBin in zip(histo,bins):
		varNom+=currentVal*(currentBin-mean)**2
	var = varNom/(np.sum(histo))
	return mean,math.sqrt(var)

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

		meanVOK,stdVOK = computeMeanStd(SumVOK,binsVOK)
		meanVNOK,stdVNOK = computeMeanStd(SumVNOK,binsVNOK)
		plt.plot(binsVOK,SumVOK,label= "Valid OK\nmean: "+"{0:.2f}".format(meanVOK)+"\nstd: "+"{0:.2f}".format(stdVOK)+"\n",color="green")
		plt.plot(binsVNOK,SumVNOK,label= "Valid NOK\nmean: "+"{0:.2f}".format(meanVNOK)+"\nstd: "+"{0:.2f}".format(stdVNOK)+"\n",color="red")
		plt.ylabel("Nb pix")
		plt.xlabel("Confidence")
		lgd = plt.legend(loc = "center left",bbox_to_anchor = (1, 0.8),numpoints = 1)
		plt.title('Histogram')
		plt.savefig(Testpath+"/final/Stats_VOK_VNOK.png",bbox_extra_artists=(lgd,),bbox_inches='tight')
		saveHisto(Testpath+"/final/Stats_VNOK.txt",SumVNOK,binsVNOK)
		saveHisto(Testpath+"/final/Stats_VOK.txt",SumVOK,binsVOK)

		plt.figure()
		meanAOK,stdAOK = computeMeanStd(SumAOK,binsAOK)
		meanANOK,stdANOK = computeMeanStd(SumANOK,binsANOK)
		plt.plot(binsAOK,SumAOK,label= "Learning OK\nmean: "+"{0:.2f}".format(meanAOK)+"\nstd: "+"{0:.2f}".format(stdAOK)+"\n",color="yellow")
		plt.plot(binsANOK,SumANOK,label= "Learning NOK\nmean: "+"{0:.2f}".format(meanANOK)+"\nstd: "+"{0:.2f}".format(stdANOK),color="blue")
		plt.ylabel("Nb pix")
		plt.xlabel("Confidence")
		lgd = plt.legend(loc = "center left",bbox_to_anchor = (1, 0.8),numpoints = 1)
		plt.title('Histogram')
		plt.savefig(Testpath+"/final/Stats_LOK_LNOK.png",bbox_extra_artists=(lgd,),bbox_inches='tight')
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
		plt.savefig(Testpath+"/final/Validity.png", bbox_extra_artists=(lgd,), bbox_inches='tight')
		saveHisto(Testpath+"/final/Validity.txt",SumValidity,binsValidity)

	#AllTif = fu.fileSearchRegEx(Testpath+"/final/TMP/*.tif")
	#for currentTif in AllTif:
	#	os.remove(currentTif)
		
			
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function merges tile's statistics")
	parser.add_argument("-conf",dest = "config",help ="path to configuration file",required=True)
	args = parser.parse_args()

	mergeOutStats(args.config)


