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
#PBS -l select=1:ncpus=3:mem=20000mb\n\
#PBS -l walltime=80:00:00\n\
\n\
module load python/2.7.12\n\
#module remove xerces/2.7\n\
#module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
FileConfig=%s\n\
export ITK_AUTOLOAD_PATH=""\n\
#export OTB_HOME=$(grep --only-matching --perl-regex "^((?!#).)*(?<=OTB_HOME\:).*" $FileConfig | cut -d "\'" -f 2)\n\
#. $OTB_HOME/config_otb.sh\n\
. /home/user13/theia_oso/vincenta/OTB_5_3/config_otb.sh\n\
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=3\n\
\n\
PYPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=pyAppPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
GROUNDTRUTH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=groundTruth\:).*" $FileConfig | cut -d "\'" -f 2)\n\
TESTPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=outputPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
TILEPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=featuresPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
CONFIG=$FileConfig\n\
cd $PYPATH\n\
\n\
listData=($(find $TESTPATH/shapeRegion -maxdepth 1 -type f -name "*.shp"))\n\
path=${listData[${PBS_ARRAY_INDEX}]}\n\
python ExtractDataByRegion.py -conf $CONFIG -shape.region $path -shape.data $GROUNDTRUTH -out $TESTPATH/dataRegion --wd $TMPDIR -path.feat $TILEPATH'%(nbShape-1,pathConf))
        jobFile.close()
    else:
        jobFile = open(pathToJob,"w")
        jobFile.write('#!/bin/bash\n\
#PBS -N extractData\n\
#PBS -l select=1:ncpus=3:mem=20000mb\n\
#PBS -l walltime=50:00:00\n\
#PBS -o %s/extractData_out.log\n\
#PBS -e %s/extractData_err.log\n\
\n\
module load python/2.7.12\n\
#module remove xerces/2.7\n\
#module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
FileConfig=%s\n\
export ITK_AUTOLOAD_PATH=""\n\
#export OTB_HOME=$(grep --only-matching --perl-regex "^((?!#).)*(?<=OTB_HOME\:).*" $FileConfig | cut -d "\'" -f 2)\n\
#. $OTB_HOME/config_otb.sh\n\
. /home/user13/theia_oso/vincenta/OTB_5_3/config_otb.sh\n\
\n\
PYPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=pyAppPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
GROUNDTRUTH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=groundTruth\:).*" $FileConfig | cut -d "\'" -f 2)\n\
TESTPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=outputPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
TILEPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=featuresPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
CONFIG=$FileConfig\n\
cd $PYPATH\n\
\n\
listData=($(find $TESTPATH/shapeRegion -maxdepth 1 -type f -name "*.shp"))\n\
path=${listData[0]}\n\
echo $GROUNDTRUTH\n\
python ExtractDataByRegion.py -conf $CONFIG -shape.region $path -shape.data $GROUNDTRUTH -out $TESTPATH/dataRegion -path.feat $TILEPATH --wd $TMPDIR'%(logPath,logPath,pathConf))
        jobFile.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "This function creates the jobArray.pbs for extractData")
    parser.add_argument("-path.job",help ="path where are all jobs (mandatory)",dest = "jobPath",required=True)
    parser.add_argument("-path.test",help ="path to the folder which contains the test (mandatory)",dest = "testPath",required=True)
    parser.add_argument("-path.log",help ="path to the log folder (mandatory)",dest = "logPath",required=True)
    parser.add_argument("-conf",help ="path to the configuration file which describe the learning method (mandatory)",dest = "pathConf",required=True)
    args = parser.parse_args()

    genJob(args.jobPath,args.testPath,args.logPath,args.pathConf)










































