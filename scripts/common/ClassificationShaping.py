#!/usr/bin/python
#-*- coding: utf-8 -*-

import argparse,os
from osgeo import gdal, ogr,osr
from osgeo.gdalconst import *
from collections import defaultdict

#############################################################################################################################

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

#############################################################################################################################

def ResizeImage(imgIn,imout,spx,spy,imref):

	minX,maxX,minY,maxY = getRasterExtent(imref)

	Resize = 'gdalwarp -of GTiff -r cubic -tr '+spx+' '+spy+' -te '+str(minX)+' '+str(minY)+' '+str(maxX)+' '+str(maxY)+' -t_srs "EPSG:2154" '+imgIn+' '+imout
	print Resize
	os.system(Resize)
#############################################################################################################################

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

def ClassificationShaping(pathClassif,pathEnvelope,pathImg,fieldEnv,N,pathOut,pathWd):

	if pathWd == None:
		TMP = pathOut+"/TMP"
		if not os.path.exists(pathOut+"/TMP"):
			os.system("mkdir "+TMP)
	else:
		TMP = pathWd
		if not os.path.exists(pathOut+"/TMP"):
			os.system("mkdir "+pathOut+"/TMP")

	AllClassif = FileSearch_AND(pathClassif,".tif","Classif")
	
	#getAllTile
	AllTile = []
	for tile in AllClassif:
		try:
			ind = AllTile.index(tile.split("/")[-1].split("_")[1])
		except ValueError :
			AllTile.append(tile.split("/")[-1].split("_")[1])
	
	#Création de l'image qui va recevoir les classifications
	AllEnv = FileSearch_AND(pathEnvelope,".shp")
	nameBigSHP = "bigShp"
	mergeVectors(nameBigSHP,TMP,AllEnv)
	
	#get ground spacing in images (assuming ground spacing is the same for all images)
	#Img = pathImg+"/Landsat8_"+AllTile[0]+"/Final/LANDSAT8_Landsat8_"+AllTile[0]+"_TempRes_NDVI_NDWI_Brightness_.tif"
	contenu = os.listdir(pathImg+"/"+AllTile[0]+"/Final")
	pathToFeat = pathImg+"/"+AllTile[0]+"/Final/"+str(max(contenu))

	ImgInfo = TMP+"/imageInfo.txt"
	os.system("otbcli_ReadImageInfo -in "+pathToFeat+">"+ImgInfo)
	
	info = open(ImgInfo,"r")
	while 1:
		data = info.readline().rstrip('\n\r')
		if data.count("spacingx: ")!=0:
			spx = data.split("spacingx: ")[-1]
		elif data.count("spacingy:")!=0:
			spy = data.split("spacingy: ")[-1]
			break
	info.close()
	
	cmdRaster = "otbcli_Rasterization -in "+TMP+"/"+nameBigSHP+".shp -mode attribute -mode.attribute.field "+fieldEnv+" -epsg 2154 -spx "+spx+" -spy "+spy+" -out "+TMP+"/Emprise.tif"
	print cmdRaster
	os.system(cmdRaster)

	for seed in range(N):
		sort = []
		AllClassifSeed = FileSearch_AND(pathClassif,".tif","Classif","seed_"+str(seed))

		for tile in AllClassifSeed:
			sort.append((tile.split("/")[-1].split("_")[1],tile))

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
			ResizeImage(path_Cl_final_tmp,imgResize,spx,spy,TMP+"/Emprise.tif")
	
	if pathWd != None:
		os.system("cp -a "+TMP+"/* "+pathOut+"/TMP")
	for seed in range(N):
		AllClassifSeed = FileSearch_AND(TMP,"seed_"+str(seed)+"_resize.tif")
		allCl = ""
		exp = ""
		for i in range(len(AllClassifSeed)):
			allCl = allCl+AllClassifSeed[i]+" "
			if i < len(AllClassifSeed)-1:
				exp = exp+"im"+str(i+1)+"b1 + "
			else:
				exp = exp+"im"+str(i+1)+"b1"

		FinalClassif = pathOut+"/Classif_Seed_"+str(seed)+".tif"
		finalCmd = 'otbcli_BandMath -il '+allCl+'-out '+FinalClassif+' -exp "'+exp+'"'
		print finalCmd
		os.system(finalCmd)






#############################################################################################################################

#choix de ne pas rendre // cette fonction

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function shape classifications (fake fusion and tiles priority)")
	parser.add_argument("-path.classif",help ="path to the folder which ONLY contains classification images (mandatory)",dest = "pathClassif",required=True)
	parser.add_argument("-path.envelope",help ="path to the folder which contains tile's envelope (with priority) (mandatory)",dest = "pathEnvelope",required=True)
	parser.add_argument("-path.img",help ="path to the folder which contains images (mandatory)",dest = "pathImg",required=True)
	parser.add_argument("-field.env",help ="envelope's field into shape(mandatory)",dest = "fieldEnv",required=True)
	parser.add_argument("-N",dest = "N",help ="number of random sample(mandatory)",type = int,required=True)
	parser.add_argument("-path.out",help ="path to the folder which will contains all final classifications (mandatory)",dest = "pathOut",required=True)
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
	args = parser.parse_args()

	ClassificationShaping(args.pathClassif,args.pathEnvelope,args.pathImg,args.fieldEnv,args.N,args.pathOut,args.pathWd)




















































