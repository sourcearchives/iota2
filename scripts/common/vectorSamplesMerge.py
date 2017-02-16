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

import argparse,os,shutil
import fileUtils as fu
from config import Config

def genJobArray(jobArrayPath,nbCmd,pathConf,cmdPathMerge):
	jobFile = open(jobArrayPath,"w")
	jobFile.write('#!/bin/bash\n\
#PBS -N MergeSamples\n\
#PBS -J 0-%d:1\n\
#PBS -l select=ncpus=5:mem=40000mb\n\
#PBS -l walltime=20:00:00\n\
\n\
module load python/2.7.12\n\
module load pygdal/2.1.0-py2.7\n\
\n\
FileConfig=%s\n\
PYPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=pyAppPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "^((?!#).)*(?<=OTB_HOME\:).*" $FileConfig | cut -d "\'" -f 2)\n\
. $OTB_HOME/config_otb.sh\n\
TESTPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=outputPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
\n\
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=5\n\
cd $PYPATH\n\
echo $PYPATH\n\
j=0\n\
old_IFS=$IFS\n\
IFS=$\'%s\'\n\
for ligne in $(cat %s)\n\
do\n\
	cmd[$j]=$ligne\n\
	j=$j+1\n\
done\n\
IFS=$old_IFS\n\
\n\
echo ${cmd[${PBS_ARRAY_INDEX}]}\n\
#until eval ${cmd[${PBS_ARRAY_INDEX}]}; do echo $?; done\n\
eval ${cmd[${PBS_ARRAY_INDEX}]}\n\
'%(nbCmd-1,pathConf,'\\n',cmdPathMerge))
	jobFile.close()



def getAllModelsFromShape(PathLearningSamples):
	#AllSample = fu.fileSearchRegEx(PathLearningSamples+"/*.shp")
	AllSample = fu.fileSearchRegEx(PathLearningSamples+"/*.sqlite")
	AllModels = []
	for currentSample in AllSample:
		try:
			model = currentSample.split("/")[-1].split("_")[-4]
			ind = AllModels.index(model)
		except ValueError:
			AllModels.append(model)
	return AllModels

def vectorSamplesMerge(pathConf):
	
	f = file(pathConf)
	cfg = Config(f)
	outputPath = cfg.chain.outputPath
	runs = int(cfg.chain.runs)
	mode = cfg.chain.executionMode
	
	jobArrayPath = cfg.chain.jobsPath+"/SamplesMerge.pbs"
	logPath = cfg.chain.logPath
	cmdPathMerge = outputPath+"/cmd/mergeSamplesCmd.txt"
	if os.path.exists(jobArrayPath):os.remove(jobArrayPath)

	AllModels = getAllModelsFromShape(outputPath+"/learningSamples")
	allCmd = []
	for seed in range(runs):
		for currentModel in AllModels:
			learningShapes = fu.fileSearchRegEx(outputPath+"/learningSamples/*_region_"+currentModel+"_seed"+str(seed)+"*Samples.sqlite")
			shapeOut = "Samples_region_"+currentModel+"_seed"+str(seed)+"_learn"
			folderOut = outputPath+"/learningSamples"
			if mode == "sequential" : fu.mergeSQLite(shapeOut, folderOut,learningShapes)
			elif mode == "parallel" : 
				allCmd.append("python -c 'import fileUtils;fileUtils.mergeSQLite_cmd(\""+shapeOut+"\",\""+folderOut+"\",\""+"\",\"".join(learningShapes)+"\")'")
			for currentShape in learningShapes:
				if mode == "sequential" : os.remove(currentShape)
	if mode == "parallel" :
		fu.writeCmds(cmdPathMerge,allCmd,mode="w")
		genJobArray(jobArrayPath,len(allCmd),pathConf,cmdPathMerge)
		os.system("qsub -W block=true "+jobArrayPath)

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function merge sqlite to feed training")	
	parser.add_argument("-conf",help ="path to the configuration file (mandatory)",dest = "pathConf",required=True)	
	args = parser.parse_args()

	vectorSamplesMerge(args.pathConf)
