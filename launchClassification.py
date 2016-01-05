#!/usr/bin/python
#-*- coding: utf-8 -*-

import argparse,os
from config import Config
from collections import defaultdict

#############################################################################################################################

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

#############################################################################################################################

def launchClassification(model,pathConf,stat,pathToRT,pathToImg,pathToRegion,fieldRegion,N,pathOut):

	f = file(pathConf)
	
	cfg = Config(f)
	train = cfg.argTrain

	for conf in train:
		classif = conf.classifier

	AllCmd = []
	maskFiles = pathOut+"/MASK"
	if not os.path.exists(maskFiles):
		os.system("mkdir "+maskFiles)
		
	shpRName = pathToRegion.split("/")[-1].replace(".shp","")

	AllModel = FileSearch_AND(model,"model",".txt")

	for path in AllModel :
		tiles = path.replace(".txt","").split("/")[-1].split("_")[2:len(path.split("/")[-1].split("_"))-2]
		model = path.split("/")[-1].split("_")[1]
		seed = path.split("/")[-1].split("_")[-1].replace(".txt","")
		
		#construction du string de sortie
		"""
		nameOut = ""
		for i in range(len(tiles)):
			if i < len(tiles)-1:
				nameOut = nameOut+tiles[i]+"_"
			else:
				nameOut = nameOut+tiles[i]
		print nameOut
		"""
		for tile in tiles:

			Img = pathToImg+"/Landsat8_"+tile+"/Final/LANDSAT8_Landsat8_"+tile+"_TempRes_NDVI_NDWI_Brightness_.tif"
			maskSHP = pathToRT+"/"+shpRName+"_region_"+model+"_"+tile+".shp"
			maskTif = maskFiles+"/"+shpRName+"_region_"+model+"_"+tile+".tif"
			#Création du mask
			if not os.path.exists(maskTif):
				cmdRaster = "otbcli_Rasterization -in "+maskSHP+" -mode attribute -mode.attribute.field "+fieldRegion+" -im "+Img+" -out "+maskTif
				print cmdRaster
				os.system(cmdRaster)
			
			#les statistiques pour svm = ...
			out = pathOut+"/Classif_"+tile+"_model_"+model+"_seed_"+seed+".tif"
			cmd = "otbcli_ImageClassifier -in "+Img+" -model "+path+" -mask "+maskTif+" -out "+out
			if classif == "svm":
				cmd = cmd+" -imstat "+stat+"/Model_"+str(model)+".xml"
			AllCmd.append(cmd)
	
	return AllCmd
			
#############################################################################################################################

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you to create all classification command")
	parser.add_argument("-path.model",help ="path to the folder which ONLY contains models for the classification(mandatory)",dest = "model",required=True)
	parser.add_argument("--conf",help ="path to the configuration file which describe the learning method (mandatory)",dest = "pathConf",required=False)
	parser.add_argument("--stat",dest = "stat",help ="statistics for classification",required=False)
	parser.add_argument("-path.region.tile",dest = "pathToRT",help ="path to the folder which contains all region shapefile by tiles (mandatory)",required=True)
	parser.add_argument("-path.img",dest = "pathToImg",help ="path where all models will be stored",required=True)
	parser.add_argument("-path.region",dest = "pathToRegion",help ="path to the global region shape",required=True)
	parser.add_argument("-region.field",dest = "fieldRegion",help ="region field into region shape",required=True)
	parser.add_argument("-N",dest = "N",help ="number of random sample(mandatory)",required=True)
	parser.add_argument("-out",dest = "pathOut",help ="path where to stock all classifications",required=True)
	args = parser.parse_args()

	launchClassification(args.model,args.pathConf,args.stat,args.pathToRT,args.pathToImg,args.pathToRegion,args.fieldRegion,args.N,args.pathOut)
































