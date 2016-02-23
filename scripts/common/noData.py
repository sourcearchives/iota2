#!/usr/bin/python
#-*- coding: utf-8 -*-

import argparse,os

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
def getModelinClassif(item):
	return item.split("_")[-3]
def getModelinMASK(item):
	return item.split("_")[-2]
#############################################################################################################################
def noData(pathTest,pathFusion,fieldRegion,pathToImg,pathToRegion,N,pathWd):

	if pathWd != None :
		workingDir = pathWd
	else :
		workingDir = pathTest+"/classif/MASK"

	currentTile = pathFusion.split("/")[-1].split("_")[0]

	shpRName = pathToRegion.split("/")[-1].replace(".shp","")
	AllModel = FileSearch_AND(pathTest+"/model","model",".txt")
	modelTile = []
	#Création du mask de region/tuiles
	for path in AllModel :
		tiles = path.replace(".txt","").split("/")[-1].split("_")[2:len(path.split("/")[-1].split("_"))-2]
		model = path.split("/")[-1].split("_")[1]
		seed = path.split("/")[-1].split("_")[-1].replace(".txt","")
		for tile in tiles:
			#get the model which learn the current tile
			if tile == currentTile:
				modelTile.append(model)
			contenu = os.listdir(pathToImg+"/"+tile+"/Final")
			pathToFeat = pathToImg+"/"+tile+"/Final/"+str(max(contenu))
			maskSHP = pathTest+"/shapeRegion/"+shpRName+"_region_"+model+"_"+tile+".shp"
			maskTif = workingDir+"/"+shpRName+"_region_"+model+"_"+tile+".tif"
			maskTif_f = pathTest+"/classif/MASK/"+shpRName+"_region_"+model+"_"+tile+".tif"
			#Création du mask
			if not os.path.exists(maskTif_f):
				cmdRaster = "otbcli_Rasterization -in "+maskSHP+" -mode attribute -mode.attribute.field "+fieldRegion+" -im "+pathToFeat+" -out "+maskTif
				print cmdRaster
				os.system(cmdRaster)
				if pathWd != None :
					cmd = "cp "+maskTif+" "+pathTest+"/classif/MASK"
					print cmd
					os.system(cmd)
	for seed in range(N):
		#Concaténation des classifications de fusion pour une tuile (qui a ou non plusieurs régions) et Concaténation des masques de régions pour une tuile (qui a ou non plusieurs régions)
		classifFusion = []
		for model in modelTile:
			classifFusion.append(pathTest+"/classif/Classif_"+currentTile+"_model_"+model+"_seed_"+str(seed)+".tif")
		if len(classifFusion)==1:
			cmd = "cp "+classifFusion[0]+" "+pathTest+"/classif/"+currentTile+"_FUSION_concat_seed"+str(seed)+".tif"
			os.system(cmd)
		else :
			classifFusion_sort = sorted(classifFusion,key=getModelinClassif)#in order to match images and their mask
			stringClFus = " ".join(classifFusion_sort)
			if pathWd != None :
				cmd = "otbcli_ConcatenateImages -ram 128 -il "+stringClFus+" -out "+pathTest+"/classif/"+currentTile+"_FUSION_concat_seed"+str(seed)+".tif"
				print cmd
				os.system(cmd)
			else:
				cmd = "otbcli_ConcatenateImages -ram 128 -il "+stringClFus+" -out "+pathWd+"/"+currentTile+"_FUSION_concat_seed"+str(seed)+".tif"
				print cmd
				os.system(cmd)
				cmd = "cp "+pathWd+"/"+currentTile+"_FUSION_concat.tif "+pathTest+"/classif"
				print cmd
				os.system(cmd)

		classifFusion_mask = FileSearch_AND(pathTest+"/classif/MASK",currentTile+".tif","region")
		TileMask_concat = pathTest+"/classif/"+currentTile+"_MASK.tif"
		if len(classifFusion_mask)==1 and not os.path.exists(TileMask_concat) :
			cmd = "cp "+classifFusion_mask[0]+" "+TileMask_concat
			os.system(cmd)
		elif len(classifFusion_mask)!=1 and not os.path.exists(TileMask_concat):
			classifFusion_MASK_sort = sorted(classifFusion_mask,key=getModelinMASK)#in order to match images and their mask
			stringClFus = " ".join(classifFusion_MASK_sort)
			if pathWd != None :
				cmd = "otbcli_ConcatenateImages -ram 128 -il "+stringClFus+" -out "+TileMask_concat
				print cmd
				os.system(cmd)
			else:
				cmd = "otbcli_ConcatenateImages -ram 128 -il "+stringClFus+" -out "+pathWd+"/"+currentTile+"_MASK.tif"
				print cmd
				os.system(cmd)
				cmd = "cp "+pathWd+"/"+currentTile+"_MASK.tif "+pathTest+"/classif"
				print cmd
				os.system(cmd)
		#construction de la commande 
		exp = ""
		im1 = pathFusion
		im2 = pathTest+"/classif/"+currentTile+"_MASK.tif"
		im3 = pathTest+"/classif/"+currentTile+"_FUSION_concat_seed"+str(seed)+".tif"

		for i in range(len(classifFusion_mask)):
			if i+1<len(classifFusion_mask):
				exp=exp+"im2b"+str(i+1)+">=1?im3b"+str(i+1)+":"
			else:
				exp=exp+"im2b"+str(i+1)+">=1?im3b"+str(i+1)+":0"
		exp = "im1b1!=0?im1b1:("+exp+")"
		if pathWd == None :
			imgData = pathTest+"/classif/"+currentTile+"_FUSION_NODATA_seed"+str(seed)+".tif"
			cmd = 'otbcli_BandMath -il '+im1+' '+im2+' '+im3+' -out '+imgData+' exp '+'"'+exp+'"'
			print cmd
			os.system(cmd)
		else:
			imgData = pathWd+"/"+currentTile+"_FUSION_NODATA_seed"+str(seed)+".tif"
			cmd = 'otbcli_BandMath -il '+im1+' '+im2+' '+im3+' -out '+imgData+' -exp '+'"'+exp+'"'
			print cmd
			os.system(cmd)
			os.system("cp "+imgData+" "+pathTest+"/classif")
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function creates the jobArray.pbs for extractData")
	parser.add_argument("-test.path",help ="Test's path",dest = "pathTest",required=True)
	parser.add_argument("-tile.fusion.path",help ="path to the classification's images (with fusion)",dest = "pathFusion",required=True)
	parser.add_argument("-region.field",dest = "fieldRegion",help ="region field into region shape",required=True)
	parser.add_argument("-path.img",dest = "pathToImg",help ="path where all images are stored",required=True)
	parser.add_argument("-path.region",dest = "pathToRegion",help ="path to the global region shape",required=True)
	parser.add_argument("-N",dest = "N",help ="number of random sample(mandatory)",type = int,required=True)
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
	args = parser.parse_args()

	noData(args.pathTest,args.pathFusion,args.fieldRegion,args.pathToImg,args.pathToRegion,args.N,args.pathWd)

