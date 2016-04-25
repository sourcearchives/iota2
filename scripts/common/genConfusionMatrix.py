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

import argparse
import sys,os
from config import Config
import fileUtils as fu

def mergeVectors(outname, opath,files):
   	"""
   	Merge a list of vector files in one 
   	"""

	file1 = files[0]
  	nbfiles = len(files)
  	filefusion = opath+"/"+outname+".shp"
	if os.path.exists(filefusion):
		os.remove(filefusion)
  	fusion = "ogr2ogr "+filefusion+" "+file1
	print fusion
  	os.system(fusion)

	for f in range(1,nbfiles):
		fusion = "ogr2ogr -update -append "+filefusion+" "+files[f]+" -nln "+outname
		print fusion
		os.system(fusion)

	return filefusion


def genConfMatrix(pathClassif,pathValid,N,dataField,pathToCmdConfusion,pathConf,pathWd):

	AllCmd = []
	pathTMP = pathClassif+"/TMP"

	f = file(pathConf)
	cfg = Config(f)

	AllTiles = cfg.chain.listTile.split(" ")
	for seed in range(N):
		#recherche de tout les shapeFiles par seed, par tuiles pour les fusionner
		for tile in AllTiles:		
			valTile = fu.FileSearch_AND(pathValid,True,tile,"_seed"+str(seed)+"_val.shp")
			mergeVectors("ShapeValidation_"+tile+"_seed_"+str(seed), pathTMP,valTile)
			pathDirectory = pathTMP
			if pathWd != None:
				pathDirectory = "$TMPDIR"
			cmd = 'otbcli_ComputeConfusionMatrix -in '+pathClassif+'/Classif_Seed_'+str(seed)+'.tif -out '+pathDirectory+'/'+tile+'_seed_'+str(seed)+'.csv -ref.vector.field '+dataField+' -ref vector -ref.vector.in '+pathTMP+'/ShapeValidation_'+tile+'_seed_'+str(seed)+'.shp'
			AllCmd.append(cmd)

	fu.writeCmds(pathToCmdConfusion+"/confusion.txt",AllCmd)
                                           
	return(AllCmd)

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "this function create a confusion matrix")
	parser.add_argument("-path.classif",help ="path to the folder which contains classification images (mandatory)",dest = "pathClassif",required=True)
	parser.add_argument("-path.valid",help ="path to the folder which contains validation samples (with priority) (mandatory)",dest = "pathValid",required=True)
	parser.add_argument("-N",dest = "N",help ="number of random sample(mandatory)",required=True,type = int)
	parser.add_argument("-data.field",dest = "dataField",help ="data's field into data shape (mandatory)",required=True)
	parser.add_argument("-confusion.out.cmd",dest = "pathToCmdConfusion",help ="path where all confusion cmd will be stored in a text file(mandatory)",required=True)	
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
	parser.add_argument("-conf",help ="path to the configuration file which describe the classification (mandatory)",dest = "pathConf",required=False)
	args = parser.parse_args()

	genConfMatrix(args.pathClassif,args.pathValid,args.N,args.dataField,args.pathToCmdConfusion,args.pathConf,args.pathWd)



















































