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

import argparse,os,re,shutil
from osgeo import gdal, ogr,osr
from config import Config
from osgeo.gdalconst import *
from collections import defaultdict
import fileUtils as fu
import CreateIndexedColorImage as color

def assembleTile(AllClassifSeed,pathWd,pathOut,seed,pixType,NameOut):
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
	
	FinalClassif = pathDirectory+"/"+NameOut
	finalCmd = 'otbcli_BandMath -il '+allCl+'-out '+FinalClassif+' '+pixType+' -exp "'+exp+'"'
	print finalCmd
	os.system(finalCmd)

	if pathWd !=None:
		os.system("cp "+FinalClassif+" "+pathOut+"/"+NameOut)

	return pathOut+"/"+NameOut

def BuildNbVoteCmd(classifTile,VoteMap):
	
	exp = []
	for i in range(len(classifTile)):
		exp.append("(im"+str(i+1)+"b1!=0?1:0)")
	expVote="+".join(exp)
	imgs = ' '.join(classifTile)
	cmd = 'otbcli_BandMath -il '+imgs+' -out '+VoteMap+' -exp "'+expVote+'"'
	return cmd

def BuildConfidenceCmd(finalTile,classifTile,confidence,OutPutConfidence,fact=1):

	if len(classifTile)!=len(confidence):
		raise Exception("number of confidence map and classifcation map must be the same")

	N = len(classifTile)
	exp = []
	for i in range(len(classifTile)):
		exp.append("(im"+str(i+2)+"b1==0?0:im1b1!=im"+str(i+2)+"b1?1-im"+str(i+2+N)+"b1:im"+str(i+2+N)+"b1)")
	#expConfidence="im1b1==0?0:("+"+".join(exp)+")/im"+str(2+2*N)+"b1"
	expConfidence="im1b1==0?0:("+"+".join(exp)+")/"+str(len(classifTile))
	All = classifTile+confidence
	All = " ".join(All)

	#cmd = 'otbcli_BandMath -il '+finalTile+' '+All+' '+VoteMap+' -out '+OutPutConfidence+' -exp "'+expConfidence+'"'
	cmd = 'otbcli_BandMath -il '+finalTile+' '+All+' -out '+OutPutConfidence+' -exp "'+str(fact)+'*('+expConfidence+')"'
	return cmd

def removeInListByRegEx(InputList,RegEx):
	Outlist = []
	for elem in InputList: 
		match = re.match(RegEx,elem)
		if not match:
			Outlist.append(elem)
	
	return Outlist

def genGlobalConfidence(AllTile,pathTest,N,mode,classifMode,pathWd,pathConf):


	tmpClassif = pathTest+"/classif/tmpClassif"
	pathToClassif = pathTest+"/classif"
	
	f = file(pathConf)
	cfg = Config(f)
	spatialRes = cfg.chain.spatialResolution
	proj = cfg.GlobChain.proj.split(":")[-1]
	pathTest = cfg.chain.outputPath

	if pathWd:
		tmpClassif=pathWd+"/tmpClassif"
	
	if not os.path.exists(tmpClassif):
		os.system("mkdir "+tmpClassif)

	for seed in range(N):
		for tuile in AllTile:
			if mode!= 'outside':
				if classifMode == "separate":
					confidence = fu.fileSearchRegEx(pathToClassif+"/"+tuile+"*model*confidence_seed_"+str(seed)+"*")
					#for currentConf in confidence:
					globalConf = tmpClassif+"/"+tuile+"_GlobalConfidence_seed_"+str(seed)+".tif"
					globalConf_f = pathTest+"/final/TMP/"+tuile+"_GlobalConfidence_seed_"+str(seed)+".tif"
					cmd = 'otbcli_BandMath -il '+currentConf+' -out '+globalConf+' -exp "100*im1b1"'
					print confidence
					print cmd
					os.system(cmd)
					shutil.copyfile(globalConf, globalConf_f)
				else:
					finalTile = fu.fileSearchRegEx(pathToClassif+"/"+tuile+"*NODATA*_seed"+str(seed)+"*")#final tile (without nodata)
					classifTile = fu.fileSearchRegEx(pathToClassif+"/Classif_"+tuile+"*model*_seed_"+str(seed)+"*")# tmp tile (produce by each classifier, without nodata)
					confidence = fu.fileSearchRegEx(pathToClassif+"/"+tuile+"*model*confidence_seed_"+str(seed)+"*")
					classifTile = sorted(classifTile)
					confidence = sorted(confidence)
					#OutPutConfidence = tmpClassif+"/"+tuile+"_model_"+model+"_confidence_seed_"+str(seed)+".tif"
					OutPutConfidence = tmpClassif+"/"+tuile+"_GlobalConfidence_seed_"+str(seed)+".tif"
					cmd = BuildConfidenceCmd(finalTile,classifTile,confidence,OutPutConfidence,fact=100) 
					print cmd
					os.system(cmd)

					shutil.copy(OutPutConfidence, pathTest+"/final/TMP")
					#shutil.rmtree(tmpClassif)
			else:#output Mode
				if classifMode != "separate":
					classifTile = fu.fileSearchRegEx(pathToClassif+"/Classif_"+tuile+"*model_*f*_seed_"+str(seed)+"*")# tmp tile (produce by each classifier, without nodata)
					splitModel = []
					for classif in classifTile :
						model = classif.split("/")[-1].split("_")[3].split("f")[0]
						try:
							ind = splitModel.index(model)
						except ValueError:
							splitModel.append(model)
					splitConfidence = []
					for model in splitModel:
						classifTile = fu.fileSearchRegEx(pathToClassif+"/Classif_"+tuile+"*model_"+model+"f*_seed_"+str(seed)+"*")# tmp tile (produce by each classifier, without nodata)
						finalTile = pathToClassif+"/Classif_"+tuile+"_model_"+model+"_seed_"+str(seed)+".tif"
						confidence = fu.fileSearchRegEx(pathToClassif+"/"+tuile+"*model_"+model+"f*_confidence_seed_"+str(seed)+"*")
						classifTile = sorted(classifTile)
						confidence = sorted(confidence)
						OutPutConfidence = tmpClassif+"/"+tuile+"_model_"+model+"_confidence_seed_"+str(seed)+".tif"
						cmd = BuildConfidenceCmd(finalTile,classifTile,confidence,OutPutConfidence) 
						print cmd
						os.system(cmd)
						splitConfidence.append(OutPutConfidence)
				
					confidenceTMP = fu.fileSearchRegEx(pathToClassif+"/"+tuile+"*model_*_confidence_seed_"+str(seed)+"*")
					conf = removeInListByRegEx(confidenceTMP,".*model_.*f.*_confidence.*")

					for split in splitConfidence:
						conf.append(split)

					exp = "+".join(["100*im"+str(i+1)+"b1" for i in range(len(conf))])
					AllConfidence = " ".join(conf)
					OutPutConfidence = tmpClassif+"/"+tuile+"_GlobalConfidence_seed_"+str(seed)+".tif"
					cmd = 'otbcli_BandMath -il '+AllConfidence+' -out '+OutPutConfidence+' uint8 -exp "'+exp+'"'
					print cmd
					os.system(cmd)
					shutil.copy(OutPutConfidence, pathTest+"/final/TMP")
					#shutil.rmtree(tmpClassif)
				else:
					confidence = fu.fileSearchRegEx(pathToClassif+"/"+tuile+"*model*confidence_seed_"+str(seed)+"*")
					exp = "+".join(["im"+str(i+1)+"b1" for i in range(len(confidence))])
					AllConfidence = " ".join(confidence)
					#for currentConf in confidence:
					globalConf = tmpClassif+"/"+tuile+"_GlobalConfidence_seed_"+str(seed)+".tif"
					globalConf_f = pathTest+"/final/TMP/"+tuile+"_GlobalConfidence_seed_"+str(seed)+".tif"
					cmd = 'otbcli_BandMath -il '+AllConfidence+' -out '+globalConf+' -exp "100*('+exp+')"'
					print confidence
					print cmd
					os.system(cmd)
					shutil.copyfile(globalConf, globalConf_f)

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
	pixType = cfg.argClassification.pixType
	featuresPath = cfg.chain.featuresPath
	outputStatistics = cfg.chain.outputStatistics
	spatialResolution = cfg.chain.spatialResolution

	genGlobalConfidence(AllTile,pathTest,N,mode,classifMode,pathWd,pathConf)

	
	if mode == "outside" and classifMode == "fusion":
		old_classif = fu.fileSearchRegEx(pathTest+"/classif/Classif_*_model_*f*_seed_*.tif")
		for rm in old_classif:
			print ""
			os.remove(rm)
			#os.system("mv "+rm+" "+pathTest+"/final/TMP/")
	
	classification = []
	confidence = []
	cloud = []
	for seed in range(N):
		classification.append([])
		confidence.append([])
		cloud.append([])

		sort = []

		if classifMode == "separate" or mode == "outside":
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
			allCl_rm = []
			for i in range(len(paths)):
				allCl = allCl+paths[i]+" "
				allCl_rm.append(paths[i])
				if i < len(paths)-1:
					exp = exp+"im"+str(i+1)+"b1 + "
				else:
					exp = exp+"im"+str(i+1)+"b1"
			path_Cl_final = TMP+"/"+tile+"_seed_"+str(seed)+".tif"
			classification[seed].append(path_Cl_final)
			cmd = 'otbcli_BandMath -il '+allCl+'-out '+path_Cl_final+' '+pixType+' -exp "'+exp+'"'
			print cmd
			os.system(cmd)
		
			for currentTileClassif in allCl_rm:
				os.remove(currentTileClassif)
		
			tileConfidence = pathOut+"/TMP/"+tile+"_GlobalConfidence_seed_"+str(seed)+".tif"
			confidence[seed].append(tileConfidence)

			cloudTile = fu.FileSearch_AND(featuresPath+"/"+tile,True,"nbView.tif")[0]
			ClassifTile = TMP+"/"+tile+"_seed_"+str(seed)+".tif"
			cloudTilePriority = pathTest+"/final/TMP/"+tile+"_Cloud.tif"
			cloudTilePriority_tmp = TMP+"/"+tile+"_Cloud.tif"

			cloudTilePriority_StatsOK = pathTest+"/final/TMP/"+tile+"_Cloud_StatsOK.tif"
			cloudTilePriority_tmp_StatsOK = TMP+"/"+tile+"_Cloud_StatsOK.tif"
			cloud[seed].append(cloudTilePriority)
			if not os.path.exists(cloudTilePriority):
				cmd_cloud = 'otbcli_BandMath -il '+cloudTile+' '+ClassifTile+' -out '+cloudTilePriority_tmp+' int16 -exp "im2b1>0?im1b1:0"'
				print cmd_cloud
				os.system(cmd_cloud)
				if outputStatistics ==  "True":
					cmd_cloud = 'otbcli_BandMath -il '+cloudTile+' '+ClassifTile+' -out '+cloudTilePriority_tmp_StatsOK+' int16 -exp "im2b1>0?im1b1:-1"'
					print cmd_cloud
					os.system(cmd_cloud)
					shutil.copy(cloudTilePriority_tmp_StatsOK,cloudTilePriority_StatsOK)
					os.remove(cloudTilePriority_tmp_StatsOK)

				shutil.copy(cloudTilePriority_tmp,cloudTilePriority)
				os.remove(cloudTilePriority_tmp)

	if pathWd != None:
			os.system("cp -a "+TMP+"/* "+pathOut+"/TMP")
	for seed in range(N):
		fu.assembleTile_Merge(classification[seed],spatialResolution,pathWd+"/Classif_Seed_"+str(seed)+".tif")
		if pathWd : shutil.copy(pathWd+"/Classif_Seed_"+str(seed)+".tif",pathTest+"/final")
		fu.assembleTile_Merge(confidence[seed],spatialResolution,pathWd+"/Confidence_Seed_"+str(seed)+".tif")
		if pathWd : shutil.copy(pathWd+"/Confidence_Seed_"+str(seed)+".tif",pathTest+"/final")
		color.CreateIndexedColorImage(pathTest+"/final/Classif_Seed_"+str(seed)+".tif",colorpath)
		
	fu.assembleTile_Merge(cloud[0],spatialResolution,pathWd+"/PixelsValidity.tif")
	if pathWd : shutil.copy(pathWd+"/PixelsValidity.tif",pathTest+"/final")
	

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




















































