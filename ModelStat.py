#!/usr/bin/python
#-*- coding: utf-8 -*-

import argparse,os
import getModel as GM

def generateStatModel(pathShapes,pathToTiles,pathToStats):

	AllCmd = []
	modTiles = GM.getModel(pathShapes)
	
	for mod, Tiles in modTiles:
		allpath = ""
		for tile in Tiles:
			allpath = allpath+" "+pathToTiles+"/Landsat8_"+tile+"/Final/LANDSAT8_Landsat8_"+tile+"_TempRes_NDVI_NDWI_Brightness_.tif "
		cmd = "otbcli_ComputeImagesStatistics -il "+allpath+"-out "+pathToStats+"/Model_"+str(mod)+".xml"
		AllCmd.append(cmd)
	return AllCmd
	"""
	allpath = ""
	for tile in tiles:
		allpath = allpath+" "+tilesPath+"/Landsat8_"+tile+"/Final/LANDSAT8_Landsat8_"+tile+"_TempRes_NDVI_NDWI_Brightness_.tif "
	cmd = "otbcli_ComputeImagesStatistics -il "+allpath+"-out "+out
	print cmd
	os.system(cmd)
	"""

#############################################################################################################################

if __name__ == "__main__":
	
	parser = argparse.ArgumentParser(description = "This function compute the statistics for a model compose by N tiles")

	parser.add_argument("-shapesIn",help ="path to the folder which ONLY contains shapes for the classification (learning and validation) (mandatory)",dest = "pathShapes",required=True)
	parser.add_argument("-tiles.path",dest = "pathToTiles",help ="path where tiles are stored (mandatory)",required=True)
	parser.add_argument("-Stats.out",dest = "pathToStats",help ="path where all statistics will be stored (mandatory)",required=True)
	"""
	parser.add_argument("-tiles",dest = "tiles",help ="All the tiles for one model", nargs='+',required=True)
	parser.add_argument("-tiles.path",dest = "pathToTiles",help ="path where tiles are stored (mandatory)",required=True)
	parser.add_argument("-out",help ="path to the region shape (mandatory)",dest = "out",required=True)
	args = parser.parse_args()
	
	generateStatModel(args.tiles,args.pathToTiles,args.out)
	"""
	generateStatModel(args.pathShapes,args.pathToTiles,args.pathToStats)






































