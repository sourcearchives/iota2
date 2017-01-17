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
import fileUtils as fu 



def genJob(jobPath,testPath,logPath,pathConf):

	f = file(pathConf)
	cfg = Config(f)

	pathToJob = jobPath+"/noData.pbs"
	if os.path.exists(pathToJob):
		os.remove(pathToJob)

	AllShape = fu.FileSearch_AND(testPath+"/classif",True,"_FUSION_","seed_")
	nbShape = len(AllShape)

	jobFile = open(pathToJob,"w")
	jobFile.write('#!/bin/bash\n\
#PBS -N noData\n\
#PBS -J 0-%d:1\n\
#PBS -l select=1:ncpus=2:mem=8000mb\n\
#PBS -l walltime=02:00:00\n\
#PBS -o %s/noData_out.log\n\
#PBS -e %s/noData_err.log\n\
\n\
\n\
module load python/2.7.12\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
FileConfig=%s\n\
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "^((?!#).)*(?<=OTB_HOME\:).*" $FileConfig | cut -d "\'" -f 2)\n\
. $OTB_HOME/config_otb.sh\n\
\n\
PYPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=pyAppPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
TESTPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=outputPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
CONFIG=$FileConfig\n\
REGIONFIELD=$(grep --only-matching --perl-regex "^((?!#).)*(?<=regionField\:).*" $FileConfig | cut -d "\'" -f 2)\n\
TILEPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=featuresPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
PATHREGION=$(grep --only-matching --perl-regex "^((?!#).)*(?<=regionPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
Nsample=$(grep --only-matching --perl-regex "^((?!#).)*(?<=runs\:).*" $FileConfig | cut -d "\'" -f 2)\n\
cd $PYPATH\n\
\n\
listData=($(find $TESTPATH/classif -maxdepth 1 -type f -name "*_FUSION_*seed_*"))\n\
pathfusion=${listData[${PBS_ARRAY_INDEX}]}\n\
until eval python noData.py -conf $CONFIG -test.path $TESTPATH -tile.fusion.path $pathfusion --wd $TMPDIR -region.field $REGIONFIELD -path.img $TILEPATH -path.region $PATHREGION -N $Nsample; do echo $?; done\n\
#python noData.py -test.path $TESTPATH -tile.fusion.path $pathfusion --wd $TMPDIR -region.field $REGIONFIELD -path.img $TILEPATH -path.region $PATHREGION -N $Nsample'%(nbShape-1,logPath,logPath,pathConf))
	jobFile.close()

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function creates the jobArray.pbs for extractData")
	parser.add_argument("-path.job",help ="path where are all jobs (mandatory)",dest = "jobPath",required=True)
	parser.add_argument("-path.test",help ="path to the folder which contains the test (mandatory)",dest = "testPath",required=True)
	parser.add_argument("-path.log",help ="path to the log folder (mandatory)",dest = "logPath",required=True)	
	parser.add_argument("-conf",help ="path to the configuration file which describe the learning method (mandatory)",dest = "pathConf",required=True)		
	args = parser.parse_args()

	genJob(args.jobPath,args.testPath,args.logPath,args.pathConf)










































