#!/usr/bin/python
#-*- coding: utf-8 -*-

import argparse
import sys,os

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

def genConfMatrix(pathClassif,pathValid,N,dataField,pathToCmdConfusion,pathWd):
	
	AllCmd = []
	pathTMP = pathClassif+"/TMP"
	for seed in range(N):
		valFiles = FileSearch_AND(pathValid,"_seed"+str(seed)+"_val.shp")
		if pathWd == None:
			mergeVectors("ShapeValidation_seed_"+str(seed), pathTMP,valFiles)  
			cmd = 'otbcli_ComputeConfusionMatrix -in '+pathClassif+'/Classif_Seed_'+str(seed)+'.tif -out '+pathTMP+'/Classif_Seed_'+str(seed)+'.csv -ref.vector.field '+dataField+' -ref vector -ref.vector.in '+pathTMP+'/ShapeValidation_seed_'+str(seed)+'.shp > '+pathTMP+'/ClassificationResults_seed_'+str(seed)+'.txt'                                                  
		else :
			mergeVectors("ShapeValidation_seed_"+str(seed), pathTMP,valFiles)
			cmd = 'otbcli_ComputeConfusionMatrix -in '+pathClassif+'/Classif_Seed_'+str(seed)+'.tif -out $TMPDIR/Classif_Seed_'+str(seed)+'.csv -ref.vector.field '+dataField+' -ref vector -ref.vector.in '+pathTMP+'/ShapeValidation_seed_'+str(seed)+'.shp > $TMPDIR/ClassificationResults_seed_'+str(seed)+'.txt'                                                  
		AllCmd.append(cmd)

	#écriture du fichier de cmd
	cmdFile = open(pathToCmdConfusion+"/confusion.txt","w")
	for i in range(len(AllCmd)):
		if i == 0:
			cmdFile.write("%s"%(AllCmd[i]))
		else:
			cmdFile.write("\n%s"%(AllCmd[i]))
	cmdFile.close()

	return(AllCmd)
#############################################################################################################################

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "this function create a confusion matrix")
	parser.add_argument("-path.classif",help ="path to the folder which contains classification images (mandatory)",dest = "pathClassif",required=True)
	parser.add_argument("-path.valid",help ="path to the folder which contains validation samples (with priority) (mandatory)",dest = "pathValid",required=True)
	parser.add_argument("-N",dest = "N",help ="number of random sample(mandatory)",required=True,type = int)
	parser.add_argument("-data.field",dest = "dataField",help ="data's field into data shape (mandatory)",required=True)
	parser.add_argument("-confusion.out.cmd",dest = "pathToCmdConfusion",help ="path where all confusion cmd will be stored in a text file(mandatory)",required=True)	
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
	args = parser.parse_args()

	genConfMatrix(args.pathClassif,args.pathValid,args.N,args.dataField,args.pathToCmdConfusion,args.pathWd)



















































