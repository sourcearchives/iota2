#!/usr/bin/python
#-*- coding: utf-8 -*-

import argparse,os
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

def getModel(pathShapes):

	sort = []
	pathAppVal = FileSearch_AND(pathShapes,"seed",".shp","learn")
	for path in pathAppVal:
		sort.append((int(path.split("/")[-1].split("_")[-3]),path.split("/")[-1].split("_")[0]))
	
	d = defaultdict(list)
	for k, v in sort:
   		d[k].append(v)
	sort = list(d.items())#[(RegionNumber,[tile1,tile2,...]),(...),...]
	
	return sort

#############################################################################################################################

if __name__ == "__main__":
	
	parser = argparse.ArgumentParser(description = "This function link models and their tiles")
	parser.add_argument("-shapesIn",help ="path to the folder which ONLY contains shapes for the classification (learning and validation) (mandatory)",dest = "pathShapes",required=True)
	args = parser.parse_args()

	print getModel(args.pathShapes)


























































