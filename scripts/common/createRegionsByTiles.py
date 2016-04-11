#!/usr/bin/python
#-*- coding: utf-8 -*-

import argparse
import sys,os,random
from osgeo import gdal, ogr,osr

def splitVectorLayer(shp_in, attribute, attribute_type,field_vals,pathOut):
	"""
		Split a vector layer in function of its attribute
		ARGs:
			INPUT:
				- shp_in: input shapefile
				- attribute: attribute to look for
				- attribute_type: attribute type which could be "string" or "int"
			OUTPUT
				- shp_out_list: list of shapefile names
	"""
	short_shp_in = shp_in.split('.')
	shp_out_list = []
	name = shp_in.split("/")[-1].split(".")[0]

	if attribute_type == "string":
		for val in field_vals:
			if val!= "None":
				shp_out = pathOut+"/"+name+"_region_"+str(val)+".shp"
				if ( not os.path.isfile(shp_out) ):
					cmd = "ogr2ogr "
					cmd += "-where '" + attribute + ' = "' + val + '"' + "' "					
					cmd += shp_out + " "
					cmd += shp_in + " "
					print cmd
					os.system(cmd)
				shp_out_list.append(shp_out)

	elif attribute_type == "int":
		for val in field_vals:
			shp_out = pathOut+"/"+name+"_region_"+str(val)+".shp"

			if ( not os.path.isfile(shp_out) ):
				cmd = "ogr2ogr "			
				cmd += "-where '" + attribute + " = " + str(val) + "' "
				cmd += shp_out + " "
				cmd += shp_in + " "
				print cmd
				os.system(cmd)
			shp_out_list.append(shp_out)
	else:
		print "Error for attribute_type ", attribute_type, '! Should be "string" or "int"'
		sys.exit(1)
	return shp_out_list

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

def ClipVectorData(vectorFile, cutFile, opath):
   """
   Cuts a shapefile with another shapefile
   ARGs:
       INPUT:
            -vectorFile: the shapefile to be cut
            -shpMask: the other shapefile 
       OUTPUT:
            -the vector file clipped
   """
   
   nameVF = vectorFile.split("/")[-1].split(".")[0]
   nameCF = cutFile.split("/")[-1].split(".")[0]
   outname = opath+"/"+nameVF+"_"+nameCF+".shp"
   if os.path.exists(outname):
      os.remove(outname)
   Clip = "ogr2ogr -clipsrc "+cutFile+" "+outname+" "+vectorFile+" -progress"
   print Clip
   os.system(Clip)
   return outname

#############################################################################################################################

def createRegionsByTiles(shapeRegion,field_Region,pathToEnv,pathOut,pathWd):

	"""
		create a shapeFile into tile's envelope for each regions in shapeRegion and for each tiles

		IN :
			- shapeRegion : the shape which contains all regions
			- field_Region : the field into the region's shape which describes each tile belong to which model
			- pathToEnv : path to the tile's envelope with priority
			- pathOut : path to store all resulting shapeFile
			- pathWd : path to working directory (not mandatory, due to cluster's architecture default = None)

	"""

	if pathWd == None:
		#getAllTiles
		AllTiles = FileSearch_AND(pathToEnv,".shp")

		#get all region possible in the shape
		regionList = []
		driver = ogr.GetDriverByName("ESRI Shapefile")
		dataSource = driver.Open(shapeRegion, 0)
		layer = dataSource.GetLayer()
		for feature in layer:
			currentRegion = feature.GetField(field_Region)
    			try:
				ind = regionList.index(currentRegion)
			except ValueError :
				regionList.append(currentRegion)
	
		shpRegionList = splitVectorLayer(shapeRegion, field_Region,"int",regionList,pathOut)

		AllClip = []
		for shp in shpRegionList :
			for tile in AllTiles:
				pathToClip = ClipVectorData(shp, tile, pathOut)
				AllClip.append(pathToClip)

		for shp in shpRegionList:
			path = shp.replace(".shp","")
			os.system("rm "+path+".shp")
			os.system("rm "+path+".shx")
			os.system("rm "+path+".dbf")
			os.system("rm "+path+".prj")

		return AllClip
	#Cluster case
	else:
		print "CLUSTER CASE"+pathWd
		#getAllTiles
		AllTiles = FileSearch_AND(pathToEnv,".shp")

	
		#get all region possible in the shape
		regionList = []
		driver = ogr.GetDriverByName("ESRI Shapefile")
		dataSource = driver.Open(shapeRegion, 0)
		layer = dataSource.GetLayer()
		for feature in layer:
			currentRegion = feature.GetField(field_Region)
    			try:
				ind = regionList.index(currentRegion)
			except ValueError :
				regionList.append(currentRegion)
	
		shpRegionList = splitVectorLayer(shapeRegion, field_Region,"int",regionList,pathWd)

		AllClip = []
		for shp in shpRegionList :
			for tile in AllTiles:
				pathToClip = ClipVectorData(shp, tile, pathWd)
				AllClip.append(pathToClip)

		for clip in AllClip:
			cmd = "cp "+clip.replace(".shp","*")+" "+pathOut
			print cmd
			os.system(cmd)
		"""
		for shp in shpRegionList:
			path = shp.replace(".shp","")
			os.system("rm "+path+".shp")
			os.system("rm "+path+".shx")
			os.system("rm "+path+".dbf")
			os.system("rm "+path+".prj")
		"""
		
		return AllClip
	
#############################################################################################################################

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you to create a region per tile")

	parser.add_argument("-region.shape",help ="path to the region shape (mandatory)",dest = "region",required=True)
	parser.add_argument("-region.field",dest = "regionField",help ="region's field into shapeFile, must be an integer field (mandatory)",required=True)
	parser.add_argument("-tiles.envelope",dest = "pathToEnv",help ="path where tile's Envelope are stored (mandatory)",required=True)
	parser.add_argument("-out",dest = "pathOut",help ="path where to store all shapes by tiles (mandatory)",required=True)
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=True)
	args = parser.parse_args()

	createRegionsByTiles(args.region,args.regionField,args.pathToEnv,args.pathOut,args.pathWd)















