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

	pathToJob = jobPath+"/dataAppVal.pbs"
	if os.path.exists(pathToJob):
		os.system("rm "+pathToJob)

	AllShape = fu.FileSearch_AND(testPath+"/dataRegion",True,".shp")
	nbShape = len(AllShape)

	if nbShape>1:
		jobFile = open(pathToJob,"w")
		jobFile.write('#!/bin/bash\n\
#PBS -N Data_AppVal\n\
#PBS -J 0-%d:1\n\
#PBS -l select=1:ncpus=2:mem=8000mb\n\
#PBS -m be\n\
#PBS -l walltime=01:00:00\n\
#PBS -o %s/Data_AppVal_out.log\n\
#PBS -e %s/Data_AppVal_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
FileConfig=%s\n\
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "^((?!#).)*(?<=OTB_HOME\:).*" $FileConfig | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
PYPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=pyAppPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
DATAFIELD=$(grep --only-matching --perl-regex "^((?!#).)*(?<=dataField\:).*" $FileConfig | cut -d "\'" -f 2)\n\
Nsample=$(grep --only-matching --perl-regex "^((?!#).)*(?<=runs\:).*" $FileConfig | cut -d "\'" -f 2)\n\
TESTPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=outputPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
RATIO=$(grep --only-matching --perl-regex "^((?!#).)*(?<=ratio\:).*" $FileConfig | cut -d "\'" -f 2)\n\
cd $PYPATH\n\
\n\
listData=($(find $TESTPATH/dataRegion -maxdepth 1 -type f -name "*.shp"))\n\
path=${listData[${PBS_ARRAY_INDEX}]}\n\
python RandomInSituByTile.py -ratio $RATIO -shape.dataTile $path -shape.field $DATAFIELD --sample $Nsample -out $TESTPATH/dataAppVal --wd $TMPDIR'%(nbShape-1,logPath,logPath,pathConf))
		jobFile.close()
	else:
		jobFile = open(pathToJob,"w")
		jobFile.write('#!/bin/bash\n\
#PBS -N Data_AppVal\n\
#PBS -l select=1:ncpus=2:mem=8000mb\n\
#PBS -m be\n\
#PBS -l walltime=10:00:00\n\
#PBS -o %s/Data_AppVal_out.log\n\
#PBS -e %s/Data_AppVal_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
FileConfig=%s\n\
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "^((?!#).)*(?<=OTB_HOME\:).*" $FileConfig | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
PYPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=pyAppPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
DATAFIELD=$(grep --only-matching --perl-regex "^((?!#).)*(?<=dataField\:).*" $FileConfig | cut -d "\'" -f 2)\n\
Nsample=$(grep --only-matching --perl-regex "^((?!#).)*(?<=runs\:).*" $FileConfig | cut -d "\'" -f 2)\n\
TESTPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=outputPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
RATIO=$(grep --only-matching --perl-regex "^((?!#).)*(?<=ratio\:).*" $FileConfig | cut -d "\'" -f 2)\n\
cd $PYPATH\n\
\n\
listData=($(find $TESTPATH/dataRegion -maxdepth 1 -type f -name "*.shp"))\n\
path=${listData[0]}\n\
python RandomInSituByTile.py -ratio $RATIO -shape.dataTile $path -shape.field $DATAFIELD --sample $Nsample -out $TESTPATH/dataAppVal --wd $TMPDIR'%(logPath,logPath,pathConf))
		jobFile.close()

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function creates the jobArray.pbs for DataAppVal")
	parser.add_argument("-path.job",help ="path where are all jobs (mandatory)",dest = "jobPath",required=True)
	parser.add_argument("-path.test",help ="path to the folder which contains the test (mandatory)",dest = "testPath",required=True)
	parser.add_argument("-path.log",help ="path to the log folder (mandatory)",dest = "logPath",required=True)
	parser.add_argument("-conf",help ="path to the configuration file which describe the learning method (mandatory)",dest = "pathConf",required=True)
	args = parser.parse_args()

	genJob(args.jobPath,args.testPath,args.logPath,args.pathConf)










































