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

	pathToJob = jobPath+"/extractData.pbs"
	if os.path.exists(pathToJob):
		os.remove(pathToJob)

	AllShape = fu.FileSearch_AND(testPath+"/shapeRegion",True,".shp")
	nbShape = len(AllShape)

	if nbShape>1:
		jobFile = open(pathToJob,"w")
		jobFile.write('#!/bin/bash\n\
#PBS -N extractData\n\
#PBS -J 0-%d:1\n\
#PBS -l select=1:ncpus=2:mem=8000mb\n\
#PBS -l walltime=50:00:00\n\
#PBS -o %s/extractData_out.log\n\
#PBS -e %s/extractData_err.log\n\
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
cd $PYPATH\n\
\n\
listData=($(find $TESTPATH/shapeRegion -maxdepth 1 -type f -name "*.shp"))\n\
path=${listData[${PBS_ARRAY_INDEX}]}\n\
python ExtractDataByRegion.py -shape.region $path -shape.data $GROUNDTRUTH -out $TESTPATH/dataRegion --wd $TMPDIR -path.feat $TILEPATH'%(nbShape-1,logPath,logPath,pathConf))
		jobFile.close()
	else:
		jobFile = open(pathToJob,"w")
		jobFile.write('#!/bin/bash\n\
#PBS -N extractData\n\
#PBS -l select=1:ncpus=2:mem=8000mb\n\
#PBS -l walltime=50:00:00\n\
#PBS -o %s/extractData_out.log\n\
#PBS -e %s/extractData_err.log\n\
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
cd $PYPATH\n\
\n\
listData=($(find $TESTPATH/shapeRegion -maxdepth 1 -type f -name "*.shp"))\n\
path=${listData[0]}\n\
python ExtractDataByRegion.py -shape.region $path -shape.data $GROUNDTRUTH -out $TESTPATH/dataRegion -path.feat $TILEPATH --wd $TMPDIR'%(logPath,logPath,pathConf))
		jobFile.close()
		

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function creates the jobArray.pbs for extractData")
	parser.add_argument("-path.job",help ="path where are all jobs (mandatory)",dest = "jobPath",required=True)
	parser.add_argument("-path.test",help ="path to the folder which contains the test (mandatory)",dest = "testPath",required=True)
	parser.add_argument("-path.log",help ="path to the log folder (mandatory)",dest = "logPath",required=True)	
	parser.add_argument("-conf",help ="path to the configuration file which describe the learning method (mandatory)",dest = "pathConf",required=True)
	args = parser.parse_args()

	genJob(args.jobPath,args.testPath,args.logPath,args.pathConf)










































