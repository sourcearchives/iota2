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
from config import Config

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

def fusion(pathClassif,pathConf,pathWd):
	
	f = file(pathConf)
	cfg = Config(f)
	classifMode = cfg.argClassification.classifMode
	N = int(cfg.chain.runs)
	allTiles = cfg.chain.listTile.split(" ")
	fusionOptions = cfg.argClassification.fusionOptions

	AllCmd = []
	for seed in range(N):
		for tile in allTiles:
			classifPath = FileSearch_AND(pathClassif,tile,"seed_"+str(seed)+".tif")
			allPathFusion = " ".join(classifPath)
			if pathWd == None:
				cmd = "otbcli_FusionOfClassifications -il "+allPathFusion+" "+fusionOptions+" -out "+pathClassif+"/"+tile+"_FUSION_seed_"+str(seed)+".tif"      
			#hpc case
			else:
				cmd = "otbcli_FusionOfClassifications -il "+allPathFusion+" "+fusionOptions+" -out $TMPDIR/"+tile+"_FUSION_seed_"+str(seed)+".tif"      
			AllCmd.append(cmd)

	#écriture du fichier de cmd
	pathToCmdFusion = pathClassif.replace("classif","cmd/fusion")
	cmdFile = open(pathToCmdFusion+"/fusion.txt","w")
	for i in range(len(AllCmd)):
		if i == 0:
			cmdFile.write("%s"%(AllCmd[i]))
		else:
			cmdFile.write("\n%s"%(AllCmd[i]))
	cmdFile.close()

	return AllCmd

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you launch oso chain according to a configuration file")
	parser.add_argument("-path.classif",help ="path to the folder which ONLY contains classification images (mandatory)",dest = "pathClassif",required=True)
	parser.add_argument("-conf",help ="path to the configuration file which describe the classification (mandatory)",dest = "pathConf",required=False)
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
	args = parser.parse_args()

	fusion(args.pathClassif,args.pathConf,args.pathWd)















