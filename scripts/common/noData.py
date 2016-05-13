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

import argparse,os,shutil
import fileUtils as fu
from config import Config

def getModelinClassif(item):
	return item.split("_")[-3]

def getModelinMASK(item):
	return item.split("_")[-2]

def gen_MaskRegionByTile(fieldRegion,Stack_ind,workingDir,currentTile,AllModel,shpRName,pathToImg,pathTest,pathWd):
	modelTile = []
	for path in AllModel :
		tiles = path.replace(".txt","").split("/")[-1].split("_")[2:len(path.split("/")[-1].split("_"))-2]
		model = path.split("/")[-1].split("_")[1]
		seed = path.split("/")[-1].split("_")[-1].replace(".txt","")
		for tile in tiles:
			#get the model which learn the current tile
			if tile == currentTile:
				modelTile.append(model)
			pathToFeat = pathToImg+"/"+tile+"/Final/"+Stack_ind
			maskSHP = pathTest+"/shapeRegion/"+shpRName+"_region_"+model+"_"+tile+".shp"
			maskTif = workingDir+"/"+shpRName+"_region_"+model+"_"+tile+"_NODATA.tif"
			maskTif_f = pathTest+"/classif/MASK/"+shpRName+"_region_"+model+"_"+tile+"_NODATA.tif"
			#Création du mask
			if not os.path.exists(maskTif_f):
				cmdRaster = "otbcli_Rasterization -in "+maskSHP+" -mode attribute -mode.attribute.field "+fieldRegion+" -im "+pathToFeat+" -out "+maskTif
				print cmdRaster
				
				os.system(cmdRaster)
				if pathWd != None :
					cmd = "cp "+maskTif+" "+pathTest+"/classif/MASK"
					print cmd
					os.system(cmd)
	return modelTile

def concatClassifs_OneTile(pathWd,seed,currentTile,pathTest,modelTile):

	classifFusion = []

	for model in modelTile:
		classifFusion.append(pathTest+"/classif/Classif_"+currentTile+"_model_"+model+"_seed_"+str(seed)+".tif")
	if len(classifFusion)==1:
		cmd = "cp "+classifFusion[0]+" "+pathTest+"/classif/"+currentTile+"_FUSION_concat_seed"+str(seed)+".tif"
		os.system(cmd)
	else :
		classifFusion_sort = sorted(classifFusion,key=getModelinClassif)#in order to match images and their mask
		stringClFus = " ".join(classifFusion_sort)
		pathToDirectory = pathTest+"/classif/"
		if pathWd != None :
			pathToDirectory = pathWd

		cmd = "otbcli_ConcatenateImages -ram 128 -il "+stringClFus+" -out "+pathToDirectory+"/"+currentTile+"_FUSION_concat_seed"+str(seed)+".tif"
		print cmd
		os.system(cmd)

		if not os.path.exists(pathTest+"/classif/"+currentTile+"_FUSION_concat_seed"+str(seed)+".tif"):
			cmd = "cp "+pathWd+"/"+currentTile+"_FUSION_concat_seed"+str(seed)+".tif "+pathTest+"/classif"
			#cmd = "cp "+pathWd+"/"+currentTile+"_FUSION_concat.tif "+pathTest+"/classif"
			print cmd
			os.system(cmd)

	return pathTest+"/classif/"+currentTile+"_FUSION_concat_seed"+str(seed)+".tif"

def concatRegion_OneTile(currentTile,pathTest,classifFusion_mask,pathWd):

	TileMask_concat = pathTest+"/classif/"+currentTile+"_MASK.tif"
	if len(classifFusion_mask)==1 and not os.path.exists(TileMask_concat) :
		shutil.copy(classifFusion_mask[0],TileMask_concat)
	elif len(classifFusion_mask)!=1 and not os.path.exists(TileMask_concat):
		classifFusion_MASK_sort = sorted(classifFusion_mask,key=getModelinMASK)#in order to match images and their mask
		stringClFus = " ".join(classifFusion_MASK_sort)

		pathDirectory = pathTest+"/classif"
		if pathWd != None :
			pathDirectory = pathWd
		cmd = "otbcli_ConcatenateImages -ram 128 -il "+stringClFus+" -out "+pathDirectory+"/"+currentTile+"_MASK.tif"
		print cmd
		os.system(cmd)

		if pathWd != None :
			cmd = "cp "+pathWd+"/"+currentTile+"_MASK.tif "+pathTest+"/classif"
			print cmd
			os.system(cmd)
	return TileMask_concat

def buildConfidenceExp(imgClassif_FUSION,imgConfidence,imgClassif):
	"""
	IN : 
		imgClassif_FUSION [string] : path to the classification merged with or without pixels with no label
		imgConfidence [list string] : paths to confidence map
		imgClassif [list string] : paths to images of classifications

	OUT : 
		exp [string] : Mathematical expression
		il [string] : input img list to give to otbcli_BandMath

	/!\ the list of images of classifications and the list of confidence map must have the same order.
		example :
			classif = ["cl1","cl2","cl3","cl4"]
			confidences = ["c1","c2","c3","c4"]
		
			'c1' must be the confidence map of the classification 'cl1' etc...
	"""

	if len(imgConfidence)!=len(imgClassif):
		raise Exception("Error, the list of classification and the list of confidence map must have the same length")
	im_conf = []
	im_class = []
	im_ref = "im"+str(2*len(imgConfidence)+1)+"b1"

	for i in range(len(imgConfidence)):
		im_conf.append("im"+str(i+1)+"b1")
	for i in range(len(imgConfidence),2*len(imgConfidence)):
		im_class.append("im"+str(i+1)+"b1")

	#(c1>c2 and c1>c3 and c1>c4)?cl1:(c2>c1 and c2>c3 and c2>c4)?cl2:etc...  
	#(c1>c2)?cl1:(c2>c1)?:cl2:0
	exp = im_ref+"!=0?"+im_ref+":"
	for i in range(len(im_conf)):
		tmp = []
		for j in range(len(im_conf)):
			if (im_conf[i]!=im_conf[j]):
				tmp.append(im_conf[i]+">"+im_conf[j])
		exp_tmp=" and ".join(tmp)
		exp += "("+exp_tmp+")?"+im_class[i]+":"

	exp+=im_class[0]

	#build images list
	il =""
	for i in range(len(imgConfidence)):
		il+=" "+imgConfidence[i]
	for i in range(len(imgClassif)):
		il+=" "+imgClassif[i]
	il+=" "+imgClassif_FUSION

	return exp,il

def noData(pathTest,pathFusion,fieldRegion,pathToImg,pathToRegion,N,pathConf,pathWd):

	Stack_ind = fu.getFeatStackName(pathConf)

	f = file(pathConf)
	cfg = Config(f)

	noLabelManagement = cfg.argClassification.noLabelManagement
	modeClassif = cfg.chain.mode

	pathDirectory = pathTest+"/classif"
	if pathWd != None :
		workingDir = pathWd
		pathDirectory = pathWd
	else :
		workingDir = pathTest+"/classif/MASK"

	currentTile = pathFusion.split("/")[-1].split("_")[0]

	shpRName = pathToRegion.split("/")[-1].replace(".shp","")
	AllModel = fu.FileSearch_AND(pathTest+"/model",True,"model",".txt")
	if modeClassif != "outside":
		modelTile = gen_MaskRegionByTile(fieldRegion,Stack_ind,workingDir,currentTile,AllModel,shpRName,pathToImg,pathTest,pathWd)		
	else :
		modelTile = pathFusion.split("/")[-1].split("_")[3]

	
	if len(modelTile)== 0 or noLabelManagement == "maxConfidence":
		for seed in range(N):
			imgConfidence=fu.FileSearch_AND(pathTest+"/classif",True,"confidence_seed_"+str(seed)+".tif",currentTile)
			imgClassif=fu.FileSearch_AND(pathTest+"/classif",True,"Classif_"+currentTile,"seed_"+str(seed))
			imgData = pathDirectory+"/"+currentTile+"_FUSION_NODATA_seed"+str(seed)+".tif"
			if modeClassif == "outside":
				imgConfidence=fu.fileSearchRegEx(pathTest+"/classif/"+currentTile+"_model_"+modelTile+"f*_confidence_seed_"+str(seed)+".tif")
				imgClassif=fu.fileSearchRegEx(pathTest+"/classif/Classif_"+currentTile+"_model_"+modelTile+"f*_seed_"+str(seed)+".tif")
				imgData = pathDirectory+"/Classif_"+currentTile+"_model_"+modelTile+"_seed_"+str(seed)+".tif"
			imgConfidence.sort()
			imgClassif.sort()
			exp,il = buildConfidenceExp(pathFusion,imgConfidence,imgClassif)
			cmd = "otbcli_BandMath -il "+il+" -out "+imgData+' -exp "'+exp+'"'
			print cmd
			os.system(cmd)
			old_classif = fu.fileSearchRegEx(pathTest+"/classif/Classif_"+currentTile+"_model_"+modelTile+"f*_seed_"+str(seed)+".tif")
			print "old_classif"
			print old_classif
			for rm in old_classif:
				os.remove(rm)
			if pathWd != None :
				os.system("cp "+imgData+" "+pathTest+"/classif")
			
	elif len(modelTile)!= 0 and noLabelManagement == "learningPriority":
		for seed in range(N):
			#Concaténation des classifications pour une tuile (qui a ou non plusieurs régions) et Concaténation des masques de régions pour une tuile (qui a ou non plusieurs régions)
			pathToClassifConcat = concatClassifs_OneTile(pathWd,seed,currentTile,pathTest,modelTile)

			classifFusion_mask = fu.FileSearch_AND(pathTest+"/classif/MASK",True,currentTile+"_NODATA.tif","region")
			pathToRegionMaskConcat = concatRegion_OneTile(currentTile,pathTest,classifFusion_mask,pathWd)

			#construction de la commande 
			exp = ""
			im1 = pathFusion
			im2 = pathToRegionMaskConcat
			im3 = pathToClassifConcat

			for i in range(len(classifFusion_mask)):
				if i+1<len(classifFusion_mask):
					exp=exp+"im2b"+str(i+1)+">=1?im3b"+str(i+1)+":"
				else:
					exp=exp+"im2b"+str(i+1)+">=1?im3b"+str(i+1)+":0"
			exp = "im1b1!=0?im1b1:("+exp+")"

			imgData = pathDirectory+"/"+currentTile+"_FUSION_NODATA_seed"+str(seed)+".tif"
			cmd = 'otbcli_BandMath -il '+im1+' '+im2+' '+im3+' -out '+imgData+' -exp '+'"'+exp+'"'
			print cmd
			os.system(cmd)

			if pathWd != None :
				os.system("cp "+imgData+" "+pathTest+"/classif")

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function creates the jobArray.pbs for extractData")
	parser.add_argument("-test.path",help ="Test's path",dest = "pathTest",required=True)
	parser.add_argument("-tile.fusion.path",help ="path to the classification's images (with fusion)",dest = "pathFusion",required=True)
	parser.add_argument("-region.field",dest = "fieldRegion",help ="region field into region shape",required=True)
	parser.add_argument("-path.img",dest = "pathToImg",help ="path where all images are stored",required=True)
	parser.add_argument("-path.region",dest = "pathToRegion",help ="path to the global region shape",required=True)
	parser.add_argument("-N",dest = "N",help ="number of random sample(mandatory)",type = int,required=True)
	parser.add_argument("-conf",help ="path to the configuration file which describe the learning method (mandatory)",dest = "pathConf",required=True)
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
	args = parser.parse_args()

	noData(args.pathTest,args.pathFusion,args.fieldRegion,args.pathToImg,args.pathToRegion,args.N,args.pathConf,args.pathWd)

