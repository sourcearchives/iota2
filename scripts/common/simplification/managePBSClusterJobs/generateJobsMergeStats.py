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

import os, argparse
#cmd="python -c 'import fileUtils;fileUtils.mergeSQLite_cmd(\""$nameOut_tmp"\",\""$folderOut"\",$listOfSample)'"
def generateJob(out, ndept):

    jobname = out + '/' + 'mergeStatsDept%s.pbs'%(ndept)
    command='python -c "import fileUtils;fileUtils.mergeSQLite_cmd({}{}"{}"{}{},{}{}"{}"{}{},{})"'.format("\\","\"", "$nameOut_tmp","\\","\"", "\\", "\"", "$folderOut", "\\", "\"", "$listOfSample")

    jobFile = open(jobname,"w")
    jobFile.write('#!/bin/bash\n\
#PBS -N mergeStatsDept%s\n\
#PBS -l select=1:ncpus=1:mem=20000mb\n\
#PBS -l walltime=10:00:00\n\
#PBS -q qoper\n\
\n\
sampleDirectory=%s/dept_%s/splits\n\
listSample=($(ls -d $sampleDirectory/sample_extract*))\n\
var=""\n\
for ((i=0; i<${#listSample[@]}; i++)); do\n\
    var=\"${listSample[$i]}\"","$var\n\
done\n\
listOfSample=${var:0:${#var}-1}\n\
echo $listOfSample\n\
\n\
IOTAPATH=/home/qt/thierionv/chaineIOTA/scripts/common\n\
cd $IOTAPATH\n\
folderOut=$TMPDIR\n\
nameOut_tmp=sample_extract_tmp\n\
nameOut=sample_extract\n\
cmd="%s"\n\
echo $cmd\n\
eval $cmd\n\
\n\
ogr2ogr -f SQLite -a_srs EPSG:2154 "$folderOut"/"$nameOut".sqlite "$folderOut"/"$nameOut_tmp".sqlite\n\
\n\
cp "$folderOut"/"$nameOut".sqlite %s/dept_%s'%(ndept, out, ndept, command, out, ndept))
    jobFile.close()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "This function creates the job to merge subtiles stats")
    parser.add_argument("-output",help ="outputPath (mandatory)",dest = "output",required=True)
    parser.add_argument("-deptNumber",help ="Dept number",dest = "deptNumber",required=True)
    args = parser.parse_args()

    generateJob(args.output, args.deptNumber)
    
