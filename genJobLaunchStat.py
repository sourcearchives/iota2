#!/usr/bin/python
#-*- coding: utf-8 -*-

import argparse,os


#############################################################################################################################

def genJob(jobPath,testPath):

	pathToJob = jobPath+"/launchStats.pbs"
	if os.path.exists(pathToJob):
		os.system("rm "+pathToJob)

	f = open(testPath+"/cmd/stats/stats.txt","r")
	Ncmd=0
	for line in f:
		Ncmd+=1
	f.close()

	#si il y a plusieurs modèles écrire un Job Array, sinon un job "normal"
	if Ncmd != 1:
		jobFile = open(pathToJob,"w")
		jobFile.write('#!/bin/bash\n\
#PBS -N LaunchStats\n\
#PBS -J 0-%d:1\n\
#PBS -l select=1:ncpus=5:mem=5000mb\n\
#PBS -l walltime=02:00:00\n\
#PBS -o /ptmp/vincenta/tmp/Log/LaunchStats_out.log\n\
#PBS -e /ptmp/vincenta/tmp/Log/LaunchStats_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="5.0.0"\n\
name=$pkg-$version\n\
install_dir=/data/qtis/inglada/modules/repository/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}:/usr/lib64/\n\
\n\
j=0\n\
old_IFS=$IFS\n\
IFS=$\'%s\'\n\
for ligne in $(cat $TESTPATH/cmd/stats/stats.txt)\n\
do\n\
	cmd[$j]=$ligne\n\
	j=$j+1\n\
done\n\
IFS=$old_IFS\n\
\n\
${cmd[${PBS_ARRAY_INDEX}]}\n\
'%(Ncmd-1,'\\n'))

		jobFile.close()
	elif Ncmd == 1:
		jobFile = open(pathToJob,"w")
		jobFile.write('#!/bin/bash\n\
#PBS -N LaunchStats\n\
#PBS -l select=1:ncpus=5:mem=5000mb\n\
#PBS -l walltime=00:30:00\n\
#PBS -o /ptmp/vincenta/tmp/Log/LaunchStats_out.log\n\
#PBS -e /ptmp/vincenta/tmp/Log/LaunchStats_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="5.0.0"\n\
name=$pkg-$version\n\
install_dir=/data/qtis/inglada/modules/repository/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}:/usr/lib64/\n\
\n\
j=0\n\
old_IFS=$IFS\n\
IFS=$\'%s\'\n\
for ligne in $(cat $TESTPATH/cmd/stats/stats.txt)\n\
do\n\
	cmd[$j]=$ligne\n\
	j=$j+1\n\
done\n\
IFS=$old_IFS\n\
\n\
${cmd[0]}\n\
'%('\\n'))

		jobFile.close()

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function creates the jobArray.pbs for statistics")
	parser.add_argument("-path.job",help ="path where are all jobs (mandatory)",dest = "jobPath",required=True)
	parser.add_argument("-path.test",help ="path to the folder which contains the test (mandatory)",dest = "testPath",required=True)
	args = parser.parse_args()

	genJob(args.jobPath,args.testPath)










































