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
from osgeo import gdal, ogr,osr
from config import Config
from osgeo.gdalconst import *
from collections import defaultdict
import fileUtils as fu
import CreateIndexedColorImage as color

def getRasterExtent(raster_in):
	"""
		Get raster extent of raster_in from GetGeoTransform()
		ARGs:
			INPUT:
				- raster_in: input raster
			OUTPUT
				- ex: extent with [minX,maxX,minY,maxY]
	"""
	if not os.path.isfile(raster_in):
		return []
	raster = gdal.Open(raster_in, GA_ReadOnly)
	if raster is None:
		return []
	geotransform = raster.GetGeoTransform()
	originX = geotransform[0]
	originY = geotransform[3]
	spacingX = geotransform[1]
	spacingY = geotransform[5]
	r, c = raster.RasterYSize, raster.RasterXSize
	
	minX = originX
	maxY = originY
	maxX = minX + c*spacingX
	minY = maxY + r*spacingY
	
	return [minX,maxX,minY,maxY]

def ResizeImage(imgIn,imout,spx,spy,imref,proj):

	minX,maxX,minY,maxY = getRasterExtent(imref)

	Resize = 'gdalwarp -of GTiff -r cubic -tr '+spx+' '+spy+' -te '+str(minX)+' '+str(minY)+' '+str(maxX)+' '+str(maxY)+' -t_srs "EPSG:'+proj+'" '+imgIn+' '+imout
	print Resize
	os.system(Resize)

def mergeVectors(outname, opath,files):
   	"""
   	Merge a list of vector files in one 
   	"""

	file1 = files[0]
  	nbfiles = len(files)
  	filefusion = opath+"/"+outname+".shp"
	if os.path.exists(filefusion):
		os.system("rm "+filefusion)
  	fusion = "ogr2ogr "+filefusion+" "+file1
	print fusion
  	os.system(fusion)

	for f in range(1,nbfiles):
		fusion = "ogr2ogr -update -append "+filefusion+" "+files[f]+" -nln "+outname
		print fusion
		os.system(fusion)

	return filefusion

def getGroundSpacing(pathToFeat,ImgInfo):
	os.system("otbcli_ReadImageInfo -in "+pathToFeat+">"+ImgInfo)
	info = open(ImgInfo,"r")
	while True :
		data = info.readline().rstrip('\n\r')
		if data.count("spacingx: ")!=0:
			spx = data.split("spacingx: ")[-1]
		elif data.count("spacingy:")!=0:
			spy = data.split("spacingy: ")[-1]
			break
	info.close()
	return spx,spy

def assembleClassif(AllClassifSeed,pathWd,pathOut,seed):
	allCl = ""
	exp = ""
	for i in range(len(AllClassifSeed)):
		allCl = allCl+AllClassifSeed[i]+" "
		if i < len(AllClassifSeed)-1:
			exp = exp+"im"+str(i+1)+"b1 + "
		else:
			exp = exp+"im"+str(i+1)+"b1"

	pathDirectory = pathOut
	if pathWd !=None:
		pathDirectory = pathWd
	
	FinalClassif = pathDirectory+"/Classif_Seed_"+str(seed)+".tif"
	finalCmd = 'otbcli_BandMath -il '+allCl+'-out '+FinalClassif+' -exp "'+exp+'"'
	print finalCmd
	os.system(finalCmd)

	if pathWd !=None:
		os.system("cp "+FinalClassif+" "+pathOut+"/Classif_Seed_"+str(seed)+".tif")

	return pathOut+"/Classif_Seed_"+str(seed)+".tif"

def ClassificationShaping(pathClassif,pathEnvelope,pathImg,fieldEnv,N,pathOut,pathWd,pathConf,colorpath):

	f = file(pathConf)
	cfg = Config(f)

	Stack_ind = fu.getFeatStackName(pathConf)

	if pathWd == None:
		TMP = pathOut+"/TMP"
		if not os.path.exists(pathOut+"/TMP"):
			os.mkdir(TMP)
	else:
		TMP = pathWd
		if not os.path.exists(pathOut+"/TMP"):
			os.mkdir(pathOut+"/TMP")
	classifMode = cfg.argClassification.classifMode
	pathTest = cfg.chain.outputPath
	proj = cfg.GlobChain.proj.split(":")[-1]
	AllTile = cfg.chain.listTile.split(" ")
	mode = cfg.chain.mode
	
	if mode == "outside" and classifMode == "fusion":
		old_classif = fu.fileSearchRegEx(pathTest+"/classif/Classif_*_model_*f*_seed_*.tif")
		for rm in old_classif:
			os.remove(rm)
		

	#Création de l'image qui va recevoir les classifications
	AllEnv = fu.FileSearch_AND(pathEnvelope,True,".shp")
	nameBigSHP = "bigShp"
	mergeVectors(nameBigSHP,TMP,AllEnv)

	pathToFeat = pathImg+"/"+AllTile[0]+"/Final/"+Stack_ind
	ImgInfo = TMP+"/imageInfo.txt"
	spx,spy = getGroundSpacing(pathToFeat,ImgInfo)

	cmdRaster = "otbcli_Rasterization -in "+TMP+"/"+nameBigSHP+".shp -mode attribute -mode.attribute.field "+fieldEnv+" -epsg 2154 -spx "+spx+" -spy "+spy+" -out "+TMP+"/Emprise.tif"
	print cmdRaster
	os.system(cmdRaster)
	
	for seed in range(N):
		sort = []

		if classifMode == "seperate" or mode == "outside":
			AllClassifSeed = fu.FileSearch_AND(pathClassif,True,".tif","Classif","seed_"+str(seed))
			ind = 1
		elif classifMode == "fusion":
			AllClassifSeed = fu.FileSearch_AND(pathClassif,True,"_FUSION_NODATA_seed"+str(seed)+".tif")
			ind = 0
		for tile in AllClassifSeed:
			sort.append((tile.split("/")[-1].split("_")[ind],tile))
		d = defaultdict(list)
		for k, v in sort:
   			d[k].append(v)
		sort = list(d.items())#[(tile,[listOfClassification of tile]),(...),...]
		
		for tile, paths in sort:
			exp = ""
			allCl = ""
			for i in range(len(paths)):
				allCl = allCl+paths[i]+" "
				if i < len(paths)-1:
					exp = exp+"im"+str(i+1)+"b1 + "
				else:
					exp = exp+"im"+str(i+1)+"b1"
			path_Cl_final_tmp = TMP+"/"+tile+"_seed_"+str(seed)+".tif"
			cmd = 'otbcli_BandMath -il '+allCl+'-out '+path_Cl_final_tmp+' -exp "'+exp+'"'
			print cmd
			os.system(cmd)

			imgResize = TMP+"/"+tile+"_seed_"+str(seed)+"_resize.tif"
			ResizeImage(path_Cl_final_tmp,imgResize,spx,spy,TMP+"/Emprise.tif",proj)
	
	if pathWd != None:
			os.system("cp -a "+TMP+"/* "+pathOut+"/TMP")
	for seed in range(N):
		AllClassifSeed = fu.FileSearch_AND(TMP,True,"seed_"+str(seed)+"_resize.tif")
		pathToClassif = assembleClassif(AllClassifSeed,pathWd,pathOut,seed)
		color.CreateIndexedColorImage(pathToClassif,colorpath)

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function shape classifications (fake fusion and tiles priority)")
	parser.add_argument("-path.classif",help ="path to the folder which ONLY contains classification images (mandatory)",dest = "pathClassif",required=True)
	parser.add_argument("-path.envelope",help ="path to the folder which contains tile's envelope (with priority) (mandatory)",dest = "pathEnvelope",required=True)
	parser.add_argument("-path.img",help ="path to the folder which contains images (mandatory)",dest = "pathImg",required=True)
	parser.add_argument("-field.env",help ="envelope's field into shape(mandatory)",dest = "fieldEnv",required=True)
	parser.add_argument("-N",dest = "N",help ="number of random sample(mandatory)",type = int,required=True)
	parser.add_argument("-conf",help ="path to the configuration file which describe the classification (mandatory)",dest = "pathConf",required=False)
	parser.add_argument("-color",help ="path to the color file (mandatory)",dest = "colorpath",required=True)
	parser.add_argument("-path.out",help ="path to the folder which will contains all final classifications (mandatory)",dest = "pathOut",required=True)
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
	args = parser.parse_args()

	ClassificationShaping(args.pathClassif,args.pathEnvelope,args.pathImg,args.fieldEnv,args.N,args.pathOut,args.pathWd,args.pathConf,args.colorpath)




















































