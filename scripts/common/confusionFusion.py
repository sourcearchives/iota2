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

from collections import defaultdict
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from osgeo.gdalconst import *
import os
import numpy as np
import argparse
from config import Config
import fileUtils as fu

def confCoordinatesCSV(csvPaths):
	"""
	IN :
		csvPaths [string] : list of path to csv files
			ex : ["/path/to/file1.csv","/path/to/file2.csv"]
	OUT : 
		out [list of lists] : containing csv's coordinates

		ex : file1.csv
			#Reference labels (rows):11
			#Produced labels (columns):11,12
			14258,52

		     file2.csv
			#Reference labels (rows):12
			#Produced labels (columns):11,12
			38,9372

		out = [[12,[11,38]],[12,[12,9372]],[11,[11,14258]],[11,[12,52]]]
	"""
	out = []
	for csvPath in csvPaths:
		cpty = 0
		FileMat = open(csvPath,"r")
		while 1:
			data = FileMat.readline().rstrip('\n\r')
			if data == "":
				FileMat.close()
				break
			if data.count('#Reference labels (rows):')!=0:
				ref = data.split(":")[-1].split(",")
			elif data.count('#Produced labels (columns):')!=0:
				prod = data.split(":")[-1].split(",")
			else:
				y = ref[cpty]
				line = data.split(",")
				cptx = 0
				for val in line:
					x = prod[cptx]
					out.append([int(y),[int(x),float(val)]])
					cptx+=1
				cpty +=1
	return out

def gen_confusionMatrix(csv_f,AllClass):

	NbClasses = len(AllClass)

	confMat = [[0]*NbClasses]*NbClasses
	confMat = np.asarray(confMat)
	
	row = 0
	for classRef in AllClass:
		flag = 0#in order to manage the case "this reference label was never classified"
		for classRef_csv in csv_f:
			if classRef_csv[0] == classRef:
				col = 0
				for classProd in AllClass:
					for classProd_csv in classRef_csv[1]:
						if classProd_csv[0] == classProd:
							confMat[row][col] = confMat[row][col] + classProd_csv[1]
					col+=1
				#row +=1
		row+=1
		#if flag == 0:
		#	row+=1

	return confMat

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
"""
python confusionFusion.py -path.shapeIn /home/vincenta/Sentinel1/RES_EVOL_KAPPA_V2/Config_20150610_S2_L3_SEL_ON/Shapes/Group/ShapeGroup.shp -dataField Join_Count -path.csv.out /home/vincenta/tmp/matrice_out.csv -path.txt.out /home/vincenta/tmp/rapportTest.txt -path.csv /home/vincenta/tmp
"""
def confFusion(shapeIn,dataField,csv_out,txt_out,csvPath,pathConf):

	f = file(pathConf)
	cfg = Config(f)

	N = int(cfg.chain.runs)

	for seed in range(N):
		#Recherche de toute les classes possible
		AllClass = []

		driver = ogr.GetDriverByName("ESRI Shapefile")
		dataSource = driver.Open(shapeIn, 0)
		layer = dataSource.GetLayer()

		for feature in layer:
			feat = feature.GetField(dataField)
			try :
				ind = AllClass.index(feat)
			except ValueError:
				AllClass.append(feat)

		AllClass = sorted(AllClass)
		#Initialisation de la matrice finale
		
		AllConf = fu.FileSearch_AND(csvPath,True,"seed_"+str(seed)+".csv")

		csv = confCoordinatesCSV(AllConf)
		d = defaultdict(list)
		for k,v in csv:
   			d[k].append(v)

		csv_f = list(d.items())
		confMat = gen_confusionMatrix(csv_f,AllClass)
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
















