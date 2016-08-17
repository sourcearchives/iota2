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

	pathToJob = jobPath+"/vectorSampler.pbs"
	if os.path.exists(pathToJob):
		os.system("rm "+pathToJob)

	AllTrainShape = fu.FileSearch_AND(testPath+"/dataAppVal",True,"learn.shp")
	nbShape = len(AllTrainShape)

	if nbShape>1:
		jobFile = open(pathToJob,"w")
		jobFile.write('#!/bin/bash\n\
#PBS -N vectorSampler\n\
#PBS -J 0-%d:1\n\
#PBS -l select=1:ncpus=1:mem=8000mb\n\
#PBS -m be\n\
#PBS -l walltime=01:00:00\n\
#PBS -o %s/vectorSampler_out.log\n\
#PBS -e %s/vectorSampler_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
FileConfig=%s\n\
. /data/qtis/inglada/modules/repository/otb_superbuild/otb_superbuild-5.7.0-Release-install/config_otb.sh\n\
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=1\n\
\n\
PYPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=pyAppPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
TESTPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=outputPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
cd $PYPATH\n\
\n\
listData=($(find $TESTPATH/dataAppVal -maxdepth 1 -type f -name "*learn.shp"))\n\
InShape=${listData[${PBS_ARRAY_INDEX}]}\n\
python vectorSampler.py -shape $InShape -conf $FileConfig --wd $TMPDIR'%(nbShape-1,logPath,logPath,pathConf))
		jobFile.close()
	else:
		jobFile = open(pathToJob,"w")
		jobFile.write('#!/bin/bash\n\
#PBS -N vectorSampler\n\
#PBS -l select=1:ncpus=1:mem=8000mb\n\
#PBS -m be\n\
#PBS -l walltime=02:00:00\n\
#PBS -o %s/vectorSampler_out.log\n\
#PBS -e %s/vectorSampler_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
FileConfig=%s\n\
export ITK_AUTOLOAD_PATH=""\n\
. /data/qtis/inglada/modules/repository/otb_superbuild/otb_superbuild-5.7.0-Release-install/config_otb.sh\n\
\n\
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=1\n\
PYPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=pyAppPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
TESTPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=outputPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
cd $PYPATH\n\
\n\
listData=($(find $TESTPATH/dataAppVal -maxdepth 1 -type f -name "*learn.shp"))\n\
InShape=${listData[0]}\n\
python vectorSampler.py -shape $InShape -conf $FileConfig --wd $TMPDIR'%(logPath,logPath,pathConf))
		jobFile.close()

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function creates the jobArray.pbs for DataAppVal")
	parser.add_argument("-path.job",help ="path where are all jobs (mandatory)",dest = "jobPath",required=True)
	parser.add_argument("-path.test",help ="path to the folder which contains the test (mandatory)",dest = "testPath",required=True)
	parser.add_argument("-path.log",help ="path to the log folder (mandatory)",dest = "logPath",required=True)
	parser.add_argument("-conf",help ="path to the configuration file which describe the learning method (mandatory)",dest = "pathConf",required=True)
	args = parser.parse_args()

	genJob(args.jobPath,args.testPath,args.logPath,args.pathConf)









































