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

def genJob(jobPath,testPath,logPath,pathConf):

	f = file(pathConf)
	cfg = Config(f)

	OTB_VERSION = cfg.chain.OTB_version
	OTB_BUILDTYPE = cfg.chain.OTB_buildType
	OTB_INSTALLDIR = cfg.chain.OTB_installDir

	pathToJob = jobPath+"/launchClassif.pbs"
	if os.path.exists(pathToJob):
		os.system("rm "+pathToJob)

	f = open(testPath+"/cmd/cla/class.txt","r")
	Ncmd=0
	for line in f:
		Ncmd+=1
	f.close()

	if Ncmd!=1:
		jobFile = open(pathToJob,"w")
		jobFile.write('#!/bin/bash\n\
#PBS -N LaunchClassif\n\
#PBS -J 0-%d:1\n\
#PBS -l select=ncpus=10:mem=40000mb\n\
#PBS -l walltime=20:00:00\n\
#PBS -o %s/LaunchClassif_out.log\n\
#PBS -e %s/LaunchClassif_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
j=0\n\
old_IFS=$IFS\n\
IFS=$\'%s\'\n\
for ligne in $(cat $TESTPATH/cmd/cla/class.txt)\n\
do\n\
	cmd[$j]=$ligne\n\
	j=$j+1\n\
done\n\
IFS=$old_IFS\n\
\n\
echo ${cmd[${PBS_ARRAY_INDEX}]}\n\
until eval ${cmd[${PBS_ARRAY_INDEX}]}; do echo $?; done\n\
#eval ${cmd[${PBS_ARRAY_INDEX}]}\n\
dataCp=($(find $TMPDIR -maxdepth 1 -type f -name "*.tif"))\n\
cp ${dataCp[0]} $TESTPATH/classif\n\
'%(Ncmd-1,logPath,logPath,pathConf,'\\n'))

		jobFile.close()
	elif Ncmd==1:
		jobFile = open(pathToJob,"w")
		jobFile.write('#!/bin/bash\n\
#PBS -N LaunchClassif\n\
#PBS -l select=ncpus=10:mem=40000mb\n\
#PBS -l walltime=20:00:00\n\
#PBS -o %s/LaunchClassif_out.log\n\
#PBS -e %s/LaunchClassif_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
j=0\n\
old_IFS=$IFS\n\
IFS=$\'%s\'\n\
for ligne in $(cat $TESTPATH/cmd/cla/class.txt)\n\
do\n\
	cmd[$j]=$ligne\n\
	j=$j+1\n\
done\n\
IFS=$old_IFS\n\
\n\
echo ${cmd[0]}\n\
until eval ${cmd[0]}; do echo $?; done\n\
#eval ${cmd[0]}\n\
dataCp=($(find $TMPDIR -maxdepth 1 -type f -name "*.tif"))\n\
cp ${dataCp[0]} $TESTPATH/classif\n\
'%(logPath,logPath,pathConf,'\\n'))
		jobFile.close()
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function creates the jobArray.pbs for classification")
	parser.add_argument("-path.job",help ="path where are all jobs (mandatory)",dest = "jobPath",required=True)
	parser.add_argument("-path.test",help ="path to the folder which contains the test (mandatory)",dest = "testPath",required=True)
	parser.add_argument("-path.log",help ="path to the log folder (mandatory)",dest = "logPath",required=True)	
	parser.add_argument("-conf",help ="path to the configuration file which describe the learning method (mandatory)",dest = "pathConf",required=True)	
	args = parser.parse_args()

	genJob(args.jobPath,args.testPath,args.logPath,args.pathConf)










































