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
import sys,os
from Utils import run

def getDateL8(pathL8,tiles):
	"""
	"""
	dateMin = 30000000000
	dateMax = 0 #JC
	for tile in tiles:
		fold = os.listdir(pathL8+"/Landsat8_"+tile)
   		for i in range(len(fold)):
			if fold[i].count(".tgz")==0 and fold[i].count(".jpg")==0 and fold[i].count(".xml")==0:
				contenu = os.listdir(pathL8+"Landsat8_"+tile+"/"+fold[i])
				for i in range(len(contenu)):
					if contenu[i].count(".TIF")!=0:
						Date = int(contenu[i].split("_")[3])
						if Date > dateMax:
							dateMax = Date
						if Date < dateMin:
							dateMin = Date
	return str(dateMin),str(dateMax)

def genFeaturesData(appPath,configPath,pathL8,pathS2,pathS1,pathOut,tiles):

	print "Génération des primitives"
	gap = "16"
	wr = "30"
	fs = ""# -fs 5
	#Récupération des dates limites L8
	begDateL8,endDateL8 = getDateL8(pathL8,tiles)


	#gérer les != cas de présence ou non de tel ou tel capteur (lancement != de l'appli)
	for tile in tiles:
		if pathL8 != None :
			if not os.path.exists(pathOut+"/"+tile):
				run("mkdir "+pathOut+"/"+tile)
			#cmd = "New_ProcessingChain.py -cf "+configPath+" -iL "+pathL8+"/Landsat8_"+tile+" -w "+pathOut+"/"+tile+" -db "+str(begDateL8)+" -de "+str(endDateL8)+" -g "+gap+" -wr "+wr+" -vd /mnt/data/home/tardyb/These/DT/Donnees_Traitee/dt_so07.shp"
			cmd = "New_ProcessingChain.py -cf "+configPath+" -iL "+pathL8+"/Landsat8_"+tile+" -w "+pathOut+"/"+tile+" -db "+begDateL8+" -de "+endDateL8+" -g "+gap+" -wr "+wr+" "+fs
			print cmd
			run("python "+appPath+"/"+cmd)

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you to generate tile's envelope considering tile's priority")
	parser.add_argument("-path.application",dest = "appPath",help ="path to the application",required=True)
	parser.add_argument("-path.config",dest = "configPath",help ="path to the configuration file",required=True)
	parser.add_argument("--path.L8",dest = "pathL8",help ="path to Landsat 8 images",default = None,required=False)
	parser.add_argument("--path.S2",dest = "pathS2",help ="path to Sentinel 2 images",default = None,required=False)
	parser.add_argument("--path.S1",dest = "pathS1",help ="path to Sentinel 1 images",default = None,required=False)
	parser.add_argument("-path.out",dest = "pathOut",help ="path where features will be store",required=True)
	parser.add_argument("-tiles",dest = "tiles",help ="All the tiles", nargs='+',required=True)
	args = parser.parse_args()

	genFeaturesData(args.appPath,args.configPath,args.pathL8,args.pathS2,args.pathS1,args.pathOut,args.tiles)





























































