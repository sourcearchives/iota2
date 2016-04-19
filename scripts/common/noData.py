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
		pathToDirectory = pathTest
		if pathWd != None :
			pathToDirectory = pathWd

		cmd = "otbcli_ConcatenateImages -ram 128 -il "+stringClFus+" -out "+pathToDirectory+"/classif/"+currentTile+"_FUSION_concat_seed"+str(seed)+".tif"
		print cmd
		os.system(cmd)

		if not os.path.exists(pathTest+"/classif/"+currentTile+"_FUSION_concat_seed"+str(seed)+".tif"):
			cmd = "cp "+pathWd+"/"+currentTile+"_FUSION_concat.tif "+pathTest+"/classif"
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
			md = "cp "+pathWd+"/"+currentTile+"_MASK.tif "+pathTest+"/classif"
			print cmd
			os.system(cmd)
	return TileMask_concat

def noData(pathTest,pathFusion,fieldRegion,pathToImg,pathToRegion,N,pathConf,pathWd):

	Stack_ind = fu.getFeatStackName(pathConf)

	if pathWd != None :
		workingDir = pathWd
	else :
		workingDir = pathTest+"/classif/MASK"

	currentTile = pathFusion.split("/")[-1].split("_")[0]

	shpRName = pathToRegion.split("/")[-1].replace(".shp","")
	AllModel = fu.FileSearch_AND(pathTest+"/model",True,"model",".txt")

	modelTile = gen_MaskRegionByTile(fieldRegion,Stack_ind,workingDir,currentTile,AllModel,shpRName,pathToImg,pathTest,pathWd)

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

		pathDirectory = pathTest+"/classif"
		if pathWd != None :
			pathDirectory = pathWd

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

