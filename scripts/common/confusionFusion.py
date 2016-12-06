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

from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from osgeo.gdalconst import *
import os
import numpy as np
import argparse
from config import Config
import fileUtils as fu

def computeKappa(confMat):

	nbrGood = confMat.trace()
	nbrSample = confMat.sum()

	overallAccuracy  = float(nbrGood) / float(nbrSample)

	## the lucky rate.
	luckyRate = 0.
	for i in range(0, confMat.shape[0]):
		sum_ij = 0.
       		sum_ji = 0.
        	for j in range(0, confMat.shape[0]):
         		sum_ij += confMat[i][j]
                	sum_ji += confMat[j][i]
        	luckyRate += sum_ij * sum_ji

	# Kappa.
	if float((nbrSample*nbrSample)-luckyRate) != 0:
		kappa = float((overallAccuracy*nbrSample*nbrSample)-luckyRate)/float((nbrSample*nbrSample)-luckyRate)
	else :
		kappa = 1000

	return kappa

def computePreByClass(confMat,AllClass):

	Pre = []#[(class,Pre),(...),()...()]

	for i in range(len(AllClass)):
		denom = 0
		for j in range(len(AllClass)):
			denom += confMat[j][i]
			if i == j:
				nom = confMat[j][i]
		if denom != 0:
			currentPre = float(nom)/float(denom)
		else :
			currentPre = 0.
		Pre.append((AllClass[i],currentPre))
	return Pre

def computeRecByClass(confMat,AllClass):
	Rec = []#[(class,rec),(...),()...()]
	for i in range(len(AllClass)):
		denom = 0
		for j in range(len(AllClass)):
			denom += confMat[i][j]
			if i == j:
				nom = confMat[i][j]
		if denom != 0 :
			currentRec = float(nom)/float(denom)
		else:
			currentRec = 0.
		Rec.append((AllClass[i],currentRec))
	return Rec

def computeFsByClass(Pre,Rec,AllClass):
	Fs = []
	for i in range(len(AllClass)):
		if float(Rec[i][1]+Pre[i][1]) != 0:
			Fs.append((AllClass[i],float(2*Rec[i][1]*Pre[i][1])/float(Rec[i][1]+Pre[i][1])))
		else:
			Fs.append((AllClass[i],0.0))
	return Fs

def writeCSV(confMat,AllClass,pathOut):

	allC = ""
	for i in range(len(AllClass)):
		if i<len(AllClass)-1:
			allC = allC+str(AllClass[i])+","
		else:
			allC = allC+str(AllClass[i])
	csvFile = open(pathOut,"w")
	csvFile.write("#Reference labels (rows):"+allC+"\n")
	csvFile.write("#Produced labels (columns):"+allC+"\n")
	for i in range(len(confMat)):
		for j in range(len(confMat[i])):
			if j < len(confMat[i])-1:
				csvFile.write(str(confMat[i][j])+",")
			else:
				csvFile.write(str(confMat[i][j])+"\n")
	csvFile.close()

def writeResults(Fs,Rec,Pre,kappa,overallAccuracy,AllClass,pathOut):

	resFile = open(pathOut,"w")
	resFile.write("#Reference labels (rows):")
	for i in range(len(AllClass)):
		if i < len(AllClass)-1:
			resFile.write(str(AllClass[i])+",")
		else:
			resFile.write(str(AllClass[i])+"\n")
	resFile.write("#Produced labels (columns):")
	for i in range(len(AllClass)):
		if i < len(AllClass)-1:
			resFile.write(str(AllClass[i])+",")
		else:
			resFile.write(str(AllClass[i])+"\n\n")

	for i in range(len(AllClass)):
		resFile.write("Precision of class ["+str(AllClass[i])+"] vs all: "+str(Pre[i][1])+"\n")
		resFile.write("Recall of class ["+str(AllClass[i])+"] vs all: "+str(Rec[i][1])+"\n")
		resFile.write("F-score of class ["+str(AllClass[i])+"] vs all: "+str(Fs[i][1])+"\n\n")

	resFile.write("Precision of the different classes: [")
	for i in range(len(AllClass)):
		if i < len(AllClass)-1:
			resFile.write(str(Pre[i][1])+",")
		else:
			resFile.write(str(Pre[i][1])+"]\n")
	resFile.write("Recall of the different classes: [")
	for i in range(len(AllClass)):
		if i < len(AllClass)-1:
			resFile.write(str(Rec[i][1])+",")
		else:
			resFile.write(str(Rec[i][1])+"]\n")
	resFile.write("F-score of the different classes: [")
	for i in range(len(AllClass)):
		if i < len(AllClass)-1:
			resFile.write(str(Fs[i][1])+",")
		else:
			resFile.write(str(Fs[i][1])+"]\n\n")
	resFile.write("Kappa index: "+str(kappa)+"\n")
	resFile.write("Overall accuracy index: "+str(overallAccuracy))

	resFile.close()

def replaceAnnualCropInConfMat(confMat,AllClass,annualCrop,labelReplacement):

	"""
	IN :
		confMat [np.array of np.array] : confusion matrix
		AllClass [list of integer] : ordinates integer class label
		annualCrop : [list of string] : list of class number (string)
		labelReplacement : [string] : label replacement
	OUT :
		outMatrix [np.array of np.array] : new confusion matrix
		AllClassAC [list of integer] : new ordinates integer class label
	Exemple :

		AllClass = [1,2,3,4]
		confMat = [[1 2 3 4] [5 6 7 8] [9 10 11 12] [13 14 15 16]]

		confMat.csv
		#ref label rows : 1,2,3,4
		#prod label col : 1,2,3,4
		1,2,3,4
		5,6,7,8
		9,10,11,12
		13,14,15,16 

		annualCrop = ['1','2']
		labelReplacement = '0'

		outMatrix,outAllClass = replaceAnnualCropInConfMat(confMat,AllClass,annualCrop,labelReplacement)

		outAllClass = [0,3,4]
		confMat = [[14 10 12] [19 11 12] [27 15 16]]
	"""
	allIndex = []
	outMatrix = []

	for currentClass in annualCrop:
		try:
			ind = AllClass.index(int(currentClass))
			allIndex.append(ind)
		except ValueError:
			raise Exception("Class : "+currentClass+" doesn't exists")
	
	AllClassAC = AllClass[:]
	for labelAcrop in annualCrop:
		AllClassAC.remove(int(labelAcrop))
	AllClassAC.append(int(labelReplacement))
	AllClassAC.sort()
	indexAC = AllClassAC.index(labelReplacement)
	
	#replace ref labels in confusion matrix
	matrix = []
	for y in range(len(AllClass)):
		if y not in allIndex:
			 matrix.append(confMat[y])
	tmpY = [0]*len(AllClass)
	for y in allIndex:
		tmpY = tmpY+confMat[y,:]
	matrix.insert(indexAC,tmpY)

	#replace produced labels in confusion matrix
	for y in range(len(matrix)):
		tmpX = []
		buff = 0
		for x in range(len(matrix[0])):
			if x not in allIndex:
				tmpX.append(matrix[y][x])
			else:
				buff += matrix[y][x]
		tmpX.insert(indexAC,buff)
		outMatrix.append(tmpX)
	return np.asarray(outMatrix),AllClassAC

def confFusion(shapeIn,dataField,csv_out,txt_out,csvPath,pathConf):

	f = file(pathConf)
	cfg = Config(f)

	N = int(cfg.chain.runs)
	cropMix = Config(file(pathConf)).argTrain.cropMix
	annualCrop = Config(file(pathConf)).argTrain.annualCrop
	labelReplacement,labelName = Config(file(pathConf)).argTrain.ACropLabelReplacement
	labelReplacement = int(labelReplacement)

	for seed in range(N):
		#Recherche de toute les classes possible
		AllClass = []
		AllClass = getFieldElement(shapeIn,driverName="ESRI Shapefile",dataField,mode = "unique")
		AllClass = sorted(AllClass)
		#Initialisation de la matrice finale
		AllConf = fu.FileSearch_AND(csvPath,True,"seed_"+str(seed)+".csv")
		csv = fu.confCoordinatesCSV(AllConf)
		csv_f = fu.sortByFirstElem(csv)

		confMat = fu.gen_confusionMatrix(csv_f,AllClass)
		if cropMix == 'True':
			writeCSV(confMat,AllClass,csv_out+"/MatrixBeforeClassMerge_"+str(seed)+".csv")		
			confMat,AllClass = replaceAnnualCropInConfMat(confMat,AllClass,annualCrop,labelReplacement)
			writeCSV(confMat,AllClass,csv_out+"/Classif_Seed_"+str(seed)+".csv")
		else:
			writeCSV(confMat,AllClass,csv_out+"/Classif_Seed_"+str(seed)+".csv")

		nbrGood = confMat.trace()
		nbrSample = confMat.sum()

		overallAccuracy  = float(nbrGood) / float(nbrSample)
		kappa = computeKappa(confMat)
		Pre = computePreByClass(confMat,AllClass)
		Rec = computeRecByClass(confMat,AllClass)
		Fs = computeFsByClass(Pre,Rec,AllClass)	

		writeResults(Fs,Rec,Pre,kappa,overallAccuracy,AllClass,txt_out+"/ClassificationResults_seed_"+str(seed)+".txt")
		

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function merge confusionMatrix.csv from different tiles")
	parser.add_argument("-path.shapeIn",help ="path to the entire ground truth (mandatory)",dest = "shapeIn",required=True)
	parser.add_argument("-dataField",help ="data's field inside the ground truth shape (mandatory)",dest = "dataField",required=True)
	parser.add_argument("-path.csv.out",help ="csv out (mandatory)",dest = "csv_out",required=True)
	parser.add_argument("-path.txt.out",help ="results out (mandatory)",dest = "txt_out",required=True)
	parser.add_argument("-path.csv",help ="where are stored all csv files by tiles (mandatory)",dest = "csvPath",required=True)					
	parser.add_argument("-conf",help ="path to the configuration file which describe the classification (mandatory)",dest = "pathConf",required=False)	
	args = parser.parse_args()

	confFusion(args.shapeIn,args.dataField,args.csv_out,args.txt_out,args.csvPath,args.pathConf)
















