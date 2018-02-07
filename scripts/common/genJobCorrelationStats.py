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

    pathToJob = jobPath+"/extractStatsByPolygons.pbs"
    if os.path.exists(pathToJob):os.remove(pathToJob)

    AllShape = fu.FileSearch_AND(testPath+"/dataAppVal",True,".shp")
    nbShape = len(AllShape)

    jobFile = open(pathToJob,"w")
    jobFile.write('#!/bin/bash\n\
#PBS -N Data_statsExtraction\n\
#PBS -J 0-%d:1\n\
#PBS -l select=1:ncpus=5:mem=80000mb\n\
#PBS -l walltime=10:00:00\n\
\n\
module load python/2.7.12\n\
module load gcc/6.3.0\n\
\n\
FileConfig=%s\n\
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "^((?!#).)*(?<=OTB_HOME\:).*" $FileConfig | cut -d "\'" -f 2)\n\
. $OTB_HOME/config_otb.sh\n\
\n\
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=5\n\
PYPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=pyAppPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
TESTPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=outputPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
cd $PYPATH\n\
\n\
listData=($(find $TESTPATH/dataAppVal -maxdepth 1 -type f -name "*.shp"))\n\
path=${listData[${PBS_ARRAY_INDEX}]}\n\
python extractStats.py -conf $FileConfig -vector $path -wd $TMPDIR'%(nbShape-1,pathConf))
    jobFile.close()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "This function creates the jobArray.pbs for DataAppVal")
    parser.add_argument("-path.job",help ="path where are all jobs (mandatory)",dest = "jobPath",required=True)
    parser.add_argument("-path.test",help ="path to the folder which contains the test (mandatory)",dest = "testPath",required=True)
    parser.add_argument("-path.log",help ="path to the log folder (mandatory)",dest = "logPath",required=True)
    parser.add_argument("-conf",help ="path to the configuration file which describe the learning method (mandatory)",dest = "pathConf",required=True)
    args = parser.parse_args()

    genJob(args.jobPath,args.testPath,args.logPath,args.pathConf)
