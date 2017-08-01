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

def genJob(jobPath,nbJobs,splitFolder,deptNumber,vector, nbcore, field, sea=""):

    if sea is not None:
        paramsea = "-sea %s"%(sea)
    else:
        paramsea = ""
        
    jobFile = open(jobPath,"w")
    jobFile.write('#!/bin/bash\n\
#PBS -N prepareStats%s\n\
#PBS -J 1-%s:1\n\
#PBS -l select=1:ncpus=%s:mem=10000mb\n\
#PBS -l walltime=40:00:00\n\
\n\
module load python/2.7.12\n\
\n\
source /work/OT/theia/oso/OTB/otb_superbuild/otb_superbuild-5.10.1-Release-install/config_otb.sh\n\
PYPATH=/home/qt/thierionv/simplification/post-processing-oso/script_oso/\n\
cd $PYPATH\n\
splitFolder=%s\n\
cp $splitFolder/* $TMPDIR\n\
deptNumber=%s\n\
classif=$TMPDIR/Classif_dept_"$deptNumber"_"${PBS_ARRAY_INDEX}".tif\n\
confidence=$TMPDIR/Confidence_dept_"$deptNumber"_"${PBS_ARRAY_INDEX}".tif\n\
pixVal=$splitFolder/PixelsValidity_dept_"$deptNumber"_"${PBS_ARRAY_INDEX}".tif\n\
python zonal_stats_otb_v2.py -wd $TMPDIR -classif $classif -vecteur %s -confid $confidence -validity $pixVal -nbcore %s -strippe 2 -otbversion 5.9 -out $splitFolder -ndept $deptNumber -split ${PBS_ARRAY_INDEX} -field %s %s\n\
'%(deptNumber, nbJobs, nbcore, splitFolder,deptNumber,vector, nbcore, field, paramsea))
    jobFile.close()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "This function creates the jobArray.pbs for DataAppVal")
    parser.add_argument("-output",help ="outputPath (mandatory)",dest = "output",required=True)
    parser.add_argument("-nbJobs",help ="job Array size",dest = "nbJobs",required=True)
    parser.add_argument("-deptNumber",help ="job Array size",dest = "deptNumber",required=True)
    parser.add_argument("-vectorPath",help ="vector path",dest = "vector",required=True)
    parser.add_argument("-splitTileFolder",help ="path to the folder which contain raster splits",dest = "splitFolder",required=True)
    parser.add_argument("-threads",dest = "threads",help ="number of threads",required=False,default='2')
    parser.add_argument("-field", dest="field", action="store", help="Classe field name", default = "value",required = False)
    parser.add_argument("-sea", dest="sea", action="store", help="terrestrial mask (to separate sea and inland waters)", required = False)    
    args = parser.parse_args()

    genJob(args.output,args.nbJobs,args.splitFolder,args.deptNumber,args.vector, args.threads, args.field, args.sea)
