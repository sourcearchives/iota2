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

def launchClassification(model,pathConf,stat,pathToRT,pathToImg,pathToRegion,fieldRegion,N,pathToCmdClassif,pathOut,pathWd):

	
	f = file(pathConf)
	
	cfg = Config(f)
	train = cfg.argTrain

	for conf in train:
		classif = conf.classifier
	
	#classif = "rf"
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
		for tile in tiles:

			#Img = pathToImg+"/Landsat8_"+tile+"/Final/LANDSAT8_Landsat8_"+tile+"_TempRes_NDVI_NDWI_Brightness_.tif"
			contenu = os.listdir(pathToImg+"/"+tile+"/Final")
			pathToFeat = pathToImg+"/"+tile+"/Final/"+str(max(contenu))

			maskSHP = pathToRT+"/"+shpRName+"_region_"+model+"_"+tile+".shp"
			maskTif = maskFiles+"/"+shpRName+"_region_"+model+"_"+tile+".tif"
			#Création du mask
			if not os.path.exists(maskTif):
				cmdRaster = "otbcli_Rasterization -in "+maskSHP+" -mode attribute -mode.attribute.field "+fieldRegion+" -im "+pathToFeat+" -out "+maskTif
				print cmdRaster
				os.system(cmdRaster)
			
			if pathWd == None:
				out = pathOut+"/Classif_"+tile+"_model_"+model+"_seed_"+seed+".tif"
			#hpc case
			else :
				out = "$TMPDIR/Classif_"+tile+"_model_"+model+"_seed_"+seed+".tif"

			cmd = "otbcli_ImageClassifier -in "+pathToFeat+" -model "+path+" -mask "+maskTif+" -out "+out
			if classif == "svm":
				cmd = cmd+" -imstat "+stat+"/Model_"+str(model)+".xml"
			AllCmd.append(cmd)
	
	#écriture du fichier de cmd
	if pathWd ==  None:
		cmdFile = open(pathToCmdClassif+"/class.txt","w")
		for i in range(len(AllCmd)):
			if i == 0:
				cmdFile.write("%s"%(AllCmd[i]))
			else:
				cmdFile.write("\n%s"%(AllCmd[i]))
		cmdFile.close()
	#hpc case
	else:
		cmdFile = open(pathWd+"/class.txt","w")
		for i in range(len(AllCmd)):
			if i == 0:
				cmdFile.write("%s"%(AllCmd[i]))
			else:
				cmdFile.write("\n%s"%(AllCmd[i]))
		cmdFile.close()
		os.system("cp "+pathWd+"/class.txt "+pathToCmdClassif)

	return AllCmd
			
#############################################################################################################################

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you to create all classification command")
	parser.add_argument("-path.model",help ="path to the folder which ONLY contains models for the classification(mandatory)",dest = "model",required=True)
	parser.add_argument("-conf",help ="path to the configuration file which describe the learning method (mandatory)",dest = "pathConf",required=False)
	parser.add_argument("--stat",dest = "stat",help ="statistics for classification",required=False)
	parser.add_argument("-path.region.tile",dest = "pathToRT",help ="path to the folder which contains all region shapefile by tiles (mandatory)",required=True)
	parser.add_argument("-path.img",dest = "pathToImg",help ="path where all images are stored",required=True)
	parser.add_argument("-path.region",dest = "pathToRegion",help ="path to the global region shape",required=True)
	parser.add_argument("-region.field",dest = "fieldRegion",help ="region field into region shape",required=True)
	parser.add_argument("-N",dest = "N",help ="number of random sample(mandatory)",required=True)
	parser.add_argument("-classif.out.cmd",dest = "pathToCmdClassif",help ="path where all classification cmd will be stored in a text file(mandatory)",required=True)	
	parser.add_argument("-out",dest = "pathOut",help ="path where to stock all classifications",required=True)
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)

	args = parser.parse_args()

	launchClassification(args.model,args.pathConf,args.stat,args.pathToRT,args.pathToImg,args.pathToRegion,args.fieldRegion,args.N,args.pathToCmdClassif,args.pathOut,args.pathWd)
































