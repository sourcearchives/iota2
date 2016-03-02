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
			- out : a list containing all file name (without extension) which are containing all name
	"""
	out = []
	for path, dirs, files in os.walk(PathToFolder):
   		 for i in range(len(files)):
			flag=0
			for name in names:
				if files[i].count(name)!=0 and files[i].count(".aux.xml")==0:
					flag+=1
			if flag == len(names):
       				out.append(files[i].split(".")[0])
	return out

#############################################################################################################################

def genJob(jobPath,testPath,logPath):

	pathToJob = jobPath+"/noData.pbs"
	if os.path.exists(pathToJob):
		os.system("rm "+pathToJob)

	AllShape = FileSearch_AND(testPath+"/classif","_FUSION_seed_")
	nbShape = len(AllShape)

	jobFile = open(pathToJob,"w")
	jobFile.write('#!/bin/bash\n\
#PBS -N noData\n\
#PBS -J 0-%d:1\n\
#PBS -l select=1:ncpus=3:mem=8000mb\n\
#PBS -l walltime=01:00:00\n\
#PBS -o %s/noData_out.log\n\
#PBS -e %s/noData_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="5.0.0"\n\
name=$pkg-$version\n\
install_dir=/data/qtis/inglada/modules/repository/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}:/usr/lib64/\n\
\n\
cd $PYPATH\n\
\n\
listData=($(find $TESTPATH/classif -maxdepth 1 -type f -name "*_FUSION_seed_*"))\n\
pathfusion=${listData[${PBS_ARRAY_INDEX}]}\n\
python noData.py -test.path $TESTPATH -tile.fusion.path $pathfusion --wd $TMPDIR -region.field $REGIONFIELD -path.img $TILEPATH -path.region $PATHREGION -N $Nsample'%(nbShape-1,logPath,logPath))
	jobFile.close()

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function creates the jobArray.pbs for extractData")
	parser.add_argument("-path.job",help ="path where are all jobs (mandatory)",dest = "jobPath",required=True)
	parser.add_argument("-path.test",help ="path to the folder which contains the test (mandatory)",dest = "testPath",required=True)
	parser.add_argument("-path.log",help ="path to the log folder (mandatory)",dest = "logPath",required=True)	
	args = parser.parse_args()

	genJob(args.jobPath,args.testPath,args.logPath)










































