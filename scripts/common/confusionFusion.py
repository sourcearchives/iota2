#!/usr/bin/python
#-*- coding: utf-8 -*-

from collections import defaultdict
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from osgeo.gdalconst import *
import os
import numpy as np
import argparse
from config import Config

###################################################################################################################################

def FileSearch_AND(PathToFolder,*names):
	"""
		search all files in a folder or sub folder which contains all names in their name
		
		IN :
			- PathToFolder : target folder 
					ex : /xx/xxx/xx/xxx 
			- *names : target names
					ex : "target1","target2"
		OUT :
			- out : a list containing all path to the file which are containing all name 
	"""
	out = []
	for path, dirs, files in os.walk(PathToFolder):
   		 for i in range(len(files)):
			flag=0
			for name in names:
				if files[i].count(name)!=0 and files[i].count(".aux.xml")==0:
					flag+=1

			if flag == len(names):
				pathOut = path+'/'+files[i]
       				out.append(pathOut)
	return out

###################################################################################################################################

def VerifConfMatrix(pathToCSV):
	"""
	this function will create a new csv file (*_sq.csv) next to the old one . The new csv file contain confusion matrix which is square.
	"""
	pathToCSV_tmp = pathToCSV.split(".csv")[0]+"_sq.csv"

	FileMat = open(pathToCSV,"r")
	FileMatTEMP = open(pathToCSV_tmp,"w")

	data = 'START'
	while data != '':
		data = FileMat.readline().rstrip('\n\r')
		if data.count('#Reference labels (rows):')!=0:
			head = data
			FileMatTEMP.write("%s\n"%(head))
			ClassRef = data.split(':')[-1].split(',')
		if data.count('#Produced labels (columns):')!=0:
			head2= head.replace('Reference','Produced').replace('rows','columns')
			FileMatTEMP.write("%s\n"%(head2))
			ClassProd = data.split(':')[-1].split(',')
			if len(ClassProd) != len(ClassRef):
				ClassMiss = []
				index = []
				cptRef = 0
				while cptRef<len(ClassRef):
					if ClassProd.count(ClassRef[cptRef])==0:
						ClassMiss.append(ClassRef[cptRef])
					cptRef +=1
				for i in range(len(ClassMiss)):
					index.append(ClassRef.index(ClassMiss[i]))
				#On continu a lire le fichier
				while 1:
					data = FileMat.readline().rstrip('\n\r')
					if data == "":
						break
					
					Line = data.split(',')
					for j in range(len(index)):
						Line.insert(int(index[j]),'0')
					for j in range(len(Line)):
						if j == len(Line)-1:
							FileMatTEMP.write("%s\n"%(Line[j]))
						else:
							FileMatTEMP.write("%s,"%(Line[j]))
			else:
				while 1:
					data = FileMat.readline().rstrip('\n\r')
					if data == "":
						break
					FileMatTEMP.write("%s\n"%(data))
				break
	FileMat.close()
	FileMatTEMP.close()

	return pathToCSV_tmp

###################################################################################################################################
def confCoordinatesCSV(csvPaths):
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

###################################################################################################################################
	
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
		confMat = [[0]*len(AllClass)]*len(AllClass)
		confMat = np.asarray(confMat)
		AllConf = FileSearch_AND(csvPath,"seed_"+str(seed)+".csv")

		csv = confCoordinatesCSV(AllConf)

		d = defaultdict(list)
		for k,v in csv:
   			d[k].append(v)

		csv_f = list(d.items())
		row = 0
		for classRef in AllClass:
			for classRef_csv in csv_f:
				if classRef_csv[0] == classRef:
					col = 0
					for classProd in AllClass:
						for classProd_csv in classRef_csv[1]:
							if classProd_csv[0] == classProd:
								confMat[row][col] = confMat[row][col] + classProd_csv[1]
						col+=1
					row +=1

		#Ecriture de la matrice.csv en sortie

		#head 
		allC = ""
		for i in range(len(AllClass)):
			if i<len(AllClass)-1:
				allC = allC+str(AllClass[i])+","
			else:
				allC = allC+str(AllClass[i])
		csvFile = open(csv_out+"/Classif_Seed_"+str(seed)+".csv","w")
		csvFile.write("#Reference labels (rows):"+allC+"\n")
		csvFile.write("#Produced labels (columns):"+allC+"\n")
		for i in range(len(confMat)):
			for j in range(len(confMat[i])):
				if j < len(confMat[i])-1:
					csvFile.write(str(confMat[i][j])+",")
				else:
					csvFile.write(str(confMat[i][j])+"\n")
		csvFile.close()

		#Calcul des différents indices
		nbrGood = confMat.trace()
		nbrSample = confMat.sum()

		#OA
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

		#Pre by class
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

		#Recall by class
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

		#F-score by class
		Fs = []
		for i in range(len(AllClass)):
			if float(Rec[i][1]+Pre[i][1]) != 0:
				Fs.append((AllClass[i],float(2*Rec[i][1]*Pre[i][1])/float(Rec[i][1]+Pre[i][1])))
			else:
				Fs.append((AllClass[i],0.0))

		#write results
		resFile = open(txt_out+"/ClassificationResults_seed_"+str(seed)+".txt","w")

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
















