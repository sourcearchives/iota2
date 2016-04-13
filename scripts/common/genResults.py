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
import numpy as np
from scipy import stats
import fileUtils as fu 

def CreateCell(string,maxSize):

	if len(string)>maxSize:
		maxSize = len(string)

	newString = []
	out = ""
	for i in range(maxSize):
		newString.append(" ")

	start = round((maxSize-len(string))/2.0)
	for i in range(len(string)):
		newString[i+int(start)]=string[i]

	for i in range(len(newString)):
		out = out+newString[i]
	return out

def ConfMatrix(pathToCSV,pathToNom,ResFile):
	"""
	IN : 
	pathToCSV [string] : path to the csv file which contain the confusion matrix
	pathToNom [string] : path to the file which link the class's names and their numbers 
	pathOut [string] : path where writes the new confusion matrix

	CSV format :
	#............
	#............
	1,2,0,3,154,87,44
	4,5,5,7,8,5,2,2544
	...
	
	Nom format :
	vigne:89
	foret:78
	...
	"""
	#ResFile = open(pathOut,"a")
	ResFile.write("\n")
	#Lecture de la nomenclature
	Table_num,Table_cl = getNomenclature(pathToNom)

	#Verification des dimensions de la matrice de confusion (on l'a rend carrée)
	pathToMatrix = VerifConfMatrix(pathToCSV)

	MatFile = open(pathToMatrix,"r")
	classList = []
	matrix = [] #Les éléments de la matrice de conf
	matrix_size = []#le nombre de caractères dans la cellule qui n'est pas une cellule avec le nom de la classe
	sizeMax = 0 #nombre de caractère dans la classe qui a le nom le plus grand
	ws = ""
	while 1:
		data = MatFile.readline().rstrip('\n\r')
		if data == "":
			break
		if data.count("Reference labels (rows):"):
			classList_tmp = data.split(":")[-1].split(",")
			for numClass in classList_tmp:
				ind = Table_num.index(int(numClass))
				classList.append(Table_cl[ind])
				if len(Table_cl[ind])>sizeMax:
					sizeMax = len(Table_cl[ind]) #Récupération de la taille de la plus longue chaine de de caractères
		elif data.count("#")==0:
			matrix_tmp = data.split(",")
			matrix.append(matrix_tmp)
			buff = []
			for n in matrix_tmp:
				buff.append(len(n))
			matrix_size.append(buff)
	
	matrix_MaxSize = [0]*len(matrix_size)
	for i in range(len(matrix_size)):#lignes
		for j in range(len(matrix_size)):#colones
			if matrix_size[i][j] > matrix_MaxSize[j]:
				matrix_MaxSize[j] = matrix_size[i][j]
	maxSizeCol = [-1]*len(matrix_MaxSize)
	for i in range(len(matrix_MaxSize)):
		if matrix_MaxSize[i]>len(classList[i]):
			maxSizeCol[i]=matrix_MaxSize[i]
		else :
			maxSizeCol[i]=len(classList[i])

	for i in range(sizeMax):
		ws = ws+" "
	#Ecriture du fichier de résultats
	ResFile.write("%s  "%(ws))
	for i in range(len(classList)):
		ResFile.write("%s| "%(CreateCell(classList[i],maxSizeCol[i])))
	ResFile.write("\n")
	for i in range(len(classList)):
		spaceAdjust = ""
		for j in range(sizeMax-len(classList[i])):
			spaceAdjust = spaceAdjust+" "
		ResFile.write("%s%s|"%(classList[i],spaceAdjust))
		for j in range(len(matrix[i])):
			ResFile.write("%s |"%(CreateCell(matrix[i][j],maxSizeCol[j])))
		ResFile.write("%s\n"%(classList[i]))	
	ResFile.write("\n")
	#ResFile.close()

def getNomenclature(pathNomenclature):

	"""
	"""
	#Récupération d'informations sur la nomenclature 
	nomFile = open(pathNomenclature,"r")
	data = "Start"
	Table_num = []
	Table_cl = []

	while 1:
		data = nomFile.readline().rstrip('\n\r')
		if data == "":
			break
		class_tmp = data.split(':')[0]
		num_tmp = data.replace(' ','').split(':')[-1]
		Table_num.append(int(num_tmp))
		Table_cl.append(class_tmp)
	nomFile.close()
	return Table_num,Table_cl



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

def getCSVMatrix(pathtoCSV):
	"""
	IN :
	pathtoCSV [string]

	OUT :
	a matrix
	Matrix[raw][col]
	"""
	matrix = []
	File = open(pathtoCSV,"r")

	data = 'START'
	while data != '':
		data = File.readline().rstrip('\n\r')
		if data =="":
			break
		elif data.count("#")==0:
			line = data.split(",")
			line = map(int, line)
			matrix.append(line)
	File.close()
	return matrix

def ComputeAllMatrix(mode,pathToCSV,pathOUT):
	"""
	IN
	mode [string] : "mean" or "sum"
	pathToCSV [string] : path to the folder which contain all csv confusion matrix
	pathOUT [string] : path out, -> be careful maybe pathToCSV and pathOUT have to be different the algo use all .csv file in the folder do not iterate test into the same folder...
	"""
	csv = []
	AllMatrix=[]

	#Supression des csv tmp
	csvtmp= fu.FileSearch_AND(pathToCSV,".csv~")
	for i in range(len(csvtmp)):
		os.system("rm "+csvtmp[i])

	csvtmp_= fu.FileSearch_AND(pathToCSV,"_sq.csv")
	for i in range(len(csvtmp_)):
		os.system("rm "+csvtmp_[i])
	
	#Création des csv tmp
	csvFile = fu.FileSearch_AND(pathToCSV,"Classif_Seed")

	#Vérification et création des matrices carrées
	for mat in csvFile:
		csv.append(VerifConfMatrix(mat))
	for mat in csv:
		AllMatrix.append(getCSVMatrix(mat))#AllMatrix = [numMatrix][y][x]
	
	#Sum
	AllMatrix = np.array(AllMatrix)
	MatrixSum = []
	#initialisation de la matrice de Sum
	for y in range(len(AllMatrix[0])):
		MatrixSum.append([])
		for x in range(len(AllMatrix[0])):#car les matrices sont carrées
			MatrixSum[y].append(0)
			
	#calcul 
	for Mat in AllMatrix:
		for y in range(len(Mat)):
			for x in range(len(Mat[y])):
				MatrixSum[y][x] = MatrixSum[y][x] + Mat[y][x]

	#Récupération des classes
	FileIn = open(csv[0],"r")
	while 1 :
		data = FileIn.readline().rstrip('\n\r')
		if data.count("#Reference labels")!=0:
			head1 = data
		elif data.count("#Produced labels")!=0:
			head2 = data
			break		
	FileIn.close()

	nbMatrix = len(AllMatrix)

	FileOut = open(pathOUT,"w")
	FileOut.write("%s\n"%(head1))
	FileOut.write("%s\n"%(head2))

	
	if mode == "sum":
		for y in range(len(MatrixSum)):
			for x in range(len(MatrixSum[y])):
				if x == len(MatrixSum[y])-1:
					FileOut.write("%d"%(MatrixSum[y][x]))
				else :
					FileOut.write("%d,"%(MatrixSum[y][x]))
			FileOut.write("\n")
	elif mode == "mean":
		for y in range(len(MatrixSum)):
			for x in range(len(MatrixSum[y])):
				if x == len(MatrixSum[y])-1:
					FileOut.write("%s"%("{:.2f}".format(float(MatrixSum[y][x])/float(nbMatrix))))
					
				else :
					FileOut.write("%s,"%("{:.2f}".format(float(MatrixSum[y][x])/float(nbMatrix))))
			FileOut.write("\n")	
	FileOut.close()

def getCoeff(pathToResults,pathtoNom):

	"""
	the matrix in OTB's results must be square
	"""
	Pre = []
	Rec = []
	Fs = []
	Kappa = []
	OA = []
	
	Table_num,Table_cl = getNomenclature(pathtoNom)
	ResFile = fu.FileSearch_AND(pathToResults,"ClassificationResults_")
	
	#Récupération des classes
	listClass = []
	ClassFile = open(ResFile[0],'r')
	while 1 :
		data = ClassFile.readline().rstrip('\n\r')
		if data.count("#Reference labels (rows)")!=0:
			listClass_tmp = data.split(":")[-1].split(",")
			listClass_tmp = map(int, listClass_tmp)
			for numClass in listClass_tmp:
				ind = Table_num.index(int(numClass))
				listClass.append(Table_cl[ind])
			break
	ClassFile.close()

	#Récupération des infos dans le fichiers de résultats
	for res in ResFile:
		resFile = open(res,'r')
		while 1:
			
			data = resFile.readline().rstrip('\n\r')
			if data.count("Precision of the different classes:")!=0:
				Pre.append(data.split(":")[-1].replace("[","").replace("]","").replace(" ","").split(","))
			elif data.count("Recall of the different classes:")!=0:
				Rec.append(data.split(":")[-1].replace("[","").replace("]","").replace(" ","").split(","))
			elif data.count("F-score of the different classes:")!=0:
				Fs.append(data.split(":")[-1].replace("[","").replace("]","").replace(" ","").split(","))
			elif data.count("Kappa index")!=0:
				Kappa.append(float(data.split(":")[-1]))
			elif data.count("Overall accuracy index")!=0:
				OA.append(float(data.split(":")[-1]))
				break
		resFile.close()

	PreClass = []
	RcallClass = []
	FSClass = []
	
	for i in range(len(listClass)):	
		PreClass.append([])
		RcallClass.append([])
		FSClass.append([])

	for i in range(len(Pre)):
		for j in range(len(PreClass)):
			PreClass[j].append(float(Pre[i][j]))
			RcallClass[j].append(float(Rec[i][j]))
			FSClass[j].append(float(Fs[i][j]))

	return listClass,PreClass,RcallClass,FSClass,Kappa,OA

def genResults(pathRes,pathNom):

	mode = "mean"
	#génération de la matrice de confusion moyenne (moyenne entre tt les .csv dans le dossier)
	
	ComputeAllMatrix(mode,pathRes+"/TMP",pathRes+"/TMP/mean.csv")
	
	resfile = open(pathRes+"/RESULTS.txt","w")
	resfile.write("*********** Matrice de confusion : %s ***********\n"%(mode))
	ConfMatrix(pathRes+"/TMP/mean.csv",pathNom,resfile)#Ecriture de la matrice de confusion
	listClass,PreClass,RcallClass,FSClass,Kappa,OA = getCoeff(pathRes+"/TMP",pathNom)#Récupération de toutes les valeurs

	#Calcul des intervalles de confiances
	PreMean = []
	PreI = []
	RecMean = []
	RecI = []
	FSMean = []
	FSI = []
	
	#Les strings
	Pre_S = [] 
	Rec_S = []
	FS_S = []
	for i in range(len(listClass)):
		#Compute mean
		PreMean.append("{:.3f}".format(float(np.mean(PreClass[i]))))
		RecMean.append("{:.3f}".format(float(np.mean(RcallClass[i]))))
		FSMean.append("{:.3f}".format(float(np.mean(FSClass[i]))))
		

		binf, bSup = stats.t.interval(0.95, len(listClass)-1, loc=np.mean(np.mean(PreClass[i])), scale=stats.sem(PreClass[i]))
		PreI.append("{:.4f}".format(float(np.mean(PreClass[i])-binf)))
		binf, bSup = stats.t.interval(0.95, len(listClass)-1, loc=np.mean(np.mean(RcallClass[i])), scale=stats.sem(RcallClass[i]))
		RecI.append("{:.4f}".format(float(np.mean(RcallClass[i])-binf)))
		binf, bSup = stats.t.interval(0.95, len(listClass)-1, loc=np.mean(np.mean(FSClass[i])), scale=stats.sem(FSClass[i]))
		FSI.append("{:.4f}".format(float(np.mean(FSClass[i])-binf)))

		Pre_S.append(str(PreMean[i])+" +- "+str(PreI[i]))
		Rec_S.append(str(RecMean[i])+" +- "+str(RecI[i]))
		FS_S.append(str(FSMean[i])+" +- "+str(FSI[i]))

	KMean = "{:.3f}".format(float(np.mean(Kappa)))
	OAMean = "{:.3f}".format(float(np.mean(OA)))
	binf, bSup = stats.t.interval(0.95, len(listClass)-1, loc=np.mean(np.mean(Kappa)), scale=stats.sem(Kappa))
	KI = "{:.4f}".format(float(np.mean(Kappa)-binf))
	binf, bSup = stats.t.interval(0.95, len(listClass)-1, loc=np.mean(np.mean(OA)), scale=stats.sem(OA))
	OAI = "{:.4f}".format(float(np.mean(OA)-binf))

	
	resfile.write("KAPPA : %s +- %s\n"%(KMean,KI))
	resfile.write("OA : %s +- %s\n"%(OAMean,OAI))
	
	sizeClass = 0
	sizePre = 0
	sizeRec = 0
	sizeFS = 0
		
	for cl in listClass:
		if len(cl)>sizeClass:
			sizeClass = len(cl)
	for pr in Pre_S:
		if len(pr)>sizePre:
			if len("Precision moyenne")>sizePre :
				sizePre = len("Precision moyenne")
			else :
				sizePre = len(pr)
	for rec in Rec_S:
		if len(rec)>sizeRec :
			if len("Rappel moyen")>sizeRec :
				sizeRec = len("Rappel moyen")
			else :
				sizeRec = len(rec)
	for fs in FS_S:
		if len(fs)>sizeFS:
			if len("F-score moyen")>sizeFS:
				sizeFS = len("F-score moyen")
			else :
				sizeFS = len(fs)
	sep = ""
	for i in range(sizeClass+sizePre+sizeRec+sizeFS+9):
		sep=sep+"-"

	resfile.write("\n%s | %s | %s | %s\n"%(CreateCell("Classes",sizeClass),CreateCell("Precision moyenne",sizePre),CreateCell("Rappel moyen",sizeRec),CreateCell("F-score moyen",sizeFS)))
	resfile.write("%s\n"%(sep))
	for i in range(len(listClass)):
		resfile.write("%s | %s | %s | %s\n"%(CreateCell(listClass[i],sizeClass),CreateCell(Pre_S[i],sizePre),CreateCell(Rec_S[i],sizeRec),CreateCell(FS_S[i],sizeFS)))
	
	resfile.close()
	
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function shape classifications (fake fusion and tiles priority)")
	parser.add_argument("-path.res",help ="path to the folder which contains classification's results (mandatory)",dest = "pathRes",required=True)
	parser.add_argument("-path.nomenclature	",help ="path to the nomenclature (mandatory)",dest = "pathNom",required=True)	
	args = parser.parse_args()

	genResults(args.pathRes,args.pathNom)


































