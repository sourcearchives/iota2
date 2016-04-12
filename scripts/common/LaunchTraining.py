#!/usr/bin/python
#-*- coding: utf-8 -*-

import argparse,os
from config import Config
from collections import defaultdict

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

def launchTraining(pathShapes,pathConf,pathToTiles,dataField,stat,N,pathToCmdTrain,out,pathWd,pathlog):

	"""
	OUT : les commandes pour l'app
	"""
	cmd_out = []

	f = file(pathConf)
	cfg = Config(f)
	classif = cfg.argTrain.classifier
	options = cfg.argTrain.options

	listIndices = cfg.GlobChain.features
	if len(listIndices)>1:
		listIndices = list(listIndices)
		listIndices = sorted(listIndices)
		listFeat = "_".join(listIndices)
	else:
		listFeat = listIndices[0]

	Stack_ind = "SL_MultiTempGapF_"+listFeat+"__.tif"

	for seed in range(N):
		pathAppVal = FileSearch_AND(pathShapes,"seed"+str(seed),".shp","learn")

		#training cmd generation
		sort = []
		for path in pathAppVal:
			sort.append((int(path.split("/")[-1].split("_")[-3]),path))
	
		d = defaultdict(list)
		for k, v in sort:
   			d[k].append(v)
		sort = list(d.items())#[(RegionNumber,[shp1,shp2,...]),(...),...]

		#get tiles by model
		names = []
		for r,paths in sort:
			tmp = ""
			for i in range(len(paths)):
				if i <len(paths)-1:
					tmp = tmp+paths[i].split("/")[-1].split("_")[0]+"_"
				else :
					tmp = tmp+paths[i].split("/")[-1].split("_")[0]
			names.append(tmp)
		cpt = 0
		for r,paths in sort:
			cmd = "otbcli_TrainImagesClassifier -io.il "
			for path in paths:
				if path.count("learn")!=0:
					tile = path.split("/")[-1].split("_")[0]

					#contenu = os.listdir(pathToTiles+"/"+tile+"/Final")
					#pathToFeat = pathToTiles+"/"+tile+"/Final/"+str(max(contenu))
					pathToFeat = pathToTiles+"/"+tile+"/Final/"+"SL_MultiTempGapF_"+listFeat+"__.tif"
					cmd = cmd+pathToFeat+" " 

			cmd = cmd+"-io.vd"
			for path in paths:
				if path.count("learn")!=0:
					cmd = cmd +" "+path

			cmd = cmd+" -classifier "+classif+" "+options+" -sample.vfn "+dataField
			if pathWd == None:
				cmd = cmd+" -io.out "+out+"/model_"+str(r)+"_"+names[cpt]+"_seed_"+str(seed)+".txt"
			else:
				cmd = cmd+" -io.out $TMPDIR/model_"+str(r)+"_"+names[cpt]+"_seed_"+str(seed)+".txt"
			if classif == "svm" or classif == "rf":
				cmd = cmd + " -io.imstat "+stat+"/Model_"+str(r)+".xml"

			if pathlog != None:
				cmd = cmd +" > "+pathlog+"/LOG_model_"+str(r)+"_"+names[cpt]+"_seed_"+str(seed)+".out"
			cmd_out.append(cmd)
			cpt+=1

	#écriture du fichier de cmd
	if pathWd == None:
		cmdFile = open(pathToCmdTrain+"/train.txt","w")
		for i in range(len(cmd_out)):
			if i == 0:
				cmdFile.write("%s"%(cmd_out[i]))
			else:
				cmdFile.write("\n%s"%(cmd_out[i]))
		cmdFile.close()
	else:
		cmdFile = open(pathWd+"/train.txt","w")
		for i in range(len(cmd_out)):
			if i == 0:
				cmdFile.write("%s"%(cmd_out[i]))
			else:
				cmdFile.write("\n%s"%(cmd_out[i]))
		cmdFile.close()
		os.system("cp "+pathWd+"/train.txt "+pathToCmdTrain)

	return cmd_out
#############################################################################################################################

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you to create a training command for a classifieur according to a configuration file")
	parser.add_argument("-shapesIn",help ="path to the folder which ONLY contains shapes for the classification (learning and validation) (mandatory)",dest = "pathShapes",required=True)
	parser.add_argument("-conf",help ="path to the configuration file which describe the learning method (mandatory)",dest = "pathConf",required=True)
	parser.add_argument("-tiles.path",dest = "pathToTiles",help ="path where tiles are stored (mandatory)",required=True)
	parser.add_argument("-data.field",dest = "dataField",help ="data field into data shape (mandatory)",required=True)
	parser.add_argument("-N",dest = "N",type = int,help ="number of random sample(mandatory)",required=True)
	parser.add_argument("--stat",dest = "stat",help ="statistics for classification",required=False)
	parser.add_argument("-train.out.cmd",dest = "pathToCmdTrain",help ="path where all training cmd will be stored in a text file(mandatory)",required=True)	
	parser.add_argument("-out",dest = "out",help ="path where all models will be stored(mandatory)",required=True)
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
	parser.add_argument("--path.log",dest = "pathlog",help ="path to the log file",default=None,required=False)
	args = parser.parse_args()

	launchTraining(args.pathShapes,args.pathConf,args.pathToTiles,args.dataField,args.stat,args.N,args.pathToCmdTrain,args.out,args.pathWd,args.pathlog)


























































