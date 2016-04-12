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
import codeStrings

def gen_oso_parallel(Fileconfig):

	f = file(Fileconfig)
	cfg = Config(f)

	PYPATH = cfg.chain.pyAppPath
	NOMENCLATURE= cfg.chain.nomenclaturePath
	JOBPATH= cfg.chain.jobsPath
	TESTPATH= cfg.chain.outputPath
	LISTTILE= cfg.chain.listTile
	TILEPATH= cfg.chain.featuresPath
        L5PATH= cfg.chain.L5Path
	L8PATH= cfg.chain.L8Path
	S2PATH= cfg.chain.S2Path
	S1PATH= cfg.chain.S1Path
	GROUNDTRUTH= cfg.chain.groundTruth
	DATAFIELD= cfg.chain.dataField
	Nsample= cfg.chain.runs
	MODE= cfg.chain.mode
	MODEL= cfg.chain.model
	REGIONFIELD= cfg.chain.regionField
	PATHREGION= cfg.chain.regionPath
	LOGPATH= cfg.chain.logPath
	CLASSIFMODE = cfg.argClassification.classifMode
	chainName=cfg.chain.chainName
	REARRANGE_FLAG = cfg.argTrain.rearrangeModelTile
	REARRANGE_PATH = cfg.argTrain.rearrangeModelTile_out
	
	pathChain = JOBPATH+"/"+chainName+".sh"
	chainFile = open(pathChain,"w")
        chainFile.write(codeStrings.parallelChainStep1%(JOBPATH,PYPATH,LOGPATH,NOMENCLATURE,JOBPATH,PYPATH,TESTPATH,LISTTILE,TILEPATH,L8PATH,L5PATH,S2PATH,S1PATH,Fileconfig,GROUNDTRUTH,DATAFIELD,Nsample,Fileconfig,MODE,MODEL,REGIONFIELD,PATHREGION,REARRANGE_PATH))
	if MODE != "outside":
		chainFile.write(codeStrings.parallelChainStep2)
	else :
		chainFile.write(codeStrings.parallelChainStep3)
	chainFile.write(codeStrings.parallelChainStep4)
	if REARRANGE_FLAG :
		chainFile.write(codeStrings.parallelChainStep5)
	else:
		chainFile.write(codeStrings.parallelChainStep6)
	chainFile.write(codeStrings.parallelChainStep7)
	if CLASSIFMODE == "separate":
		chainFile.write(codeStrings.parallelChainStep8)
		chainFile.close()
	elif CLASSIFMODE == "fusion" and MODE !="one_region":
		chainFile.write(codeStrings.parallelChainStep9)
		chainFile.close()
	elif CLASSIFMODE == "fusion" and MODE =="one_region":
		print "you can't choose the 'one region' mode and use the fusion mode together"
	return pathChain

def gen_oso_sequential(Fileconfig):

	f = file(Fileconfig)
	cfg = Config(f)

	PYPATH = cfg.chain.pyAppPath
	NOMENCLATURE= cfg.chain.nomenclaturePath
	JOBPATH= cfg.chain.jobsPath
	TESTPATH= cfg.chain.outputPath
	LISTTILE= cfg.chain.listTile
	TILEPATH= cfg.chain.featuresPath
	L5PATH= cfg.chain.L5Path
	L8PATH= cfg.chain.L8Path
	S2PATH= cfg.chain.S2Path
	S1PATH= cfg.chain.S1Path
	GROUNDTRUTH= cfg.chain.groundTruth
	DATAFIELD= cfg.chain.dataField
	Nsample= cfg.chain.runs
	MODE= cfg.chain.mode
	MODEL= cfg.chain.model
	REGIONFIELD= cfg.chain.regionField
	PATHREGION= cfg.chain.regionPath
	REARRANGE_FLAG = cfg.argTrain.rearrangeModelTile
	REARRANGE_PATH = cfg.argTrain.rearrangeModelTile_out
	CLASSIFMODE = cfg.argClassification.classifMode
	chainName=cfg.chain.chainName
	LISTTILE = '["'+LISTTILE.replace(" ",'","')+'"]'
	pathChain = PYPATH+"/"+chainName+".py"
	chainFile = open(pathChain,"w")

        import launchChainSequential as lcs
        lcs.launchChainSequential(TESTPATH, LISTTILE, L8PATH, L5PATH, PYPATH, TILEPATH, Fileconfig, PATHREGION, REGIONFIELD, MODEL, GROUNDTRUTH, DATAFIELD, Fileconfig, Nsample, REARRANGE_PATH)

def gen_jobGenCmdFeatures(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N genJobFeatures\n\
#PBS -l select=1:ncpus=1:mem=100mb\n\
#PBS -l walltime=00:10:00\n\
#PBS -o %s/genCmdFeatures_out.log\n\
#PBS -e %s/genCmdFeatures_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
cd $PYPATH\n\
\n\
python genCmdFeatures.py -path.test $TESTPATH -tiles $LISTTILE -path.application $GENFEATPATH -path.out $TILEPATH --path.L8 $L8PATH --path.L5 $L5PATH -path.config $FEATCONFIG --wd $TMPDIR\n\
\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()


def gen_jobGenJobLaunchFeat(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N genJob_L_Feat\n\
#PBS -l select=1:ncpus=5:mem=100mb\n\
#PBS -l walltime=00:10:00\n\
#PBS -o %s/genJobLaunchFeatures_out.log\n\
#PBS -e %s/genJobLaunchFeatures_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
cd $PYPATH\n\
\n\
python genJobLaunchFeat.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH -conf $CONFIG\n\
\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()
##################################################################################################################
def gen_jobEnvelope(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N Envelope\n\
#PBS -l select=1:ncpus=2:mem=8000mb\n\
#PBS -l walltime=00:10:00\n\
#PBS -o %s/envelope_out.log\n\
#PBS -e %s/envelope_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
cd $PYPATH\n\
\n\
python tileEnvelope.py -t $LISTTILE -t.path $TILEPATH -out $TESTPATH/envelope --wd $TMPDIR -conf $CONFIG\n\
\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()


def gen_jobGenerateRegionShape(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N genRegionShape\n\
#PBS -l select=1:ncpus=2:mem=8000mb\n\
#PBS -l walltime=00:30:00\n\
#PBS -o %s/RegionShape_out.log\n\
#PBS -e %s/RegionShape_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
cd $PYPATH\n\
\n\
python tileArea.py -pathTiles $TESTPATH/envelope -mode $MODE -fieldOut $REGIONFIELD --multi.models $MODEL -out $PATHREGION --wd $TMPDIR\n\
\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()
##################################################################################################################
def gen_jobRegionByTiles(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N regionByTiles\n\
#PBS -l select=1:ncpus=2:mem=8000mb\n\
#PBS -l walltime=00:30:00\n\
#PBS -o %s/regionByTiles_out.log\n\
#PBS -e %s/regionByTiles_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
cd $PYPATH\n\
\n\
python createRegionsByTiles.py -region.shape $PATHREGION -region.field $REGIONFIELD -tiles.envelope $TESTPATH/envelope -out $TESTPATH/shapeRegion --wd $TMPDIR\n\
\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()
##################################################################################################################
def gen_jobExtractactData(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N genJobExtData\n\
#PBS -l select=1:ncpus=1:mem=4000mb\n\
#PBS -l walltime=00:10:00\n\
#PBS -o %s/genJobExtractData_out.log\n\
#PBS -e %s/genJobExtractData_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
cd $PYPATH\n\
\n\
python genJobExtractData.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH -conf $CONFIG\n\
\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()
##################################################################################################################
def gen_jobGenJobDataAppVal(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N genJobAppVal\n\
#PBS -l select=1:ncpus=5:mem=4000mb\n\
#PBS -l walltime=00:30:00\n\
#PBS -o %s/genJobDataAppVal_out.log\n\
#PBS -e %s/genJobDataAppVal_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
cd $PYPATH\n\
\n\
python genJobDataAppVal.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH -conf $CONFIG\n\
\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()
##################################################################################################################
def gen_jobRearrange(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N reArrange\n\
#PBS -l select=1:ncpus=1:mem=1000mb\n\
#PBS -l walltime=00:10:00\n\
#PBS -o %s/reArrange_out.log\n\
#PBS -e /%s/reArrange_err.log\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
cd $PYPATH\n\
\n\
python reArrangeModel.py -path.test $TESTPATH -conf $CONFIG -repartition.in $MODEL -repartition.out $REARRANGE_PATH -data.field $DATAFIELD\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()
##################################################################################################################
def gen_jobGenCmdStat(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N genCmdStats\n\
#PBS -l select=1:ncpus=5:mem=4000mb\n\
#PBS -l walltime=03:00:00\n\
#PBS -o %s/cmdStats_out.log\n\
#PBS -e %s/cmdStats_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
cd $PYPATH\n\
\n\
python ModelStat.py -shapesIn $TESTPATH/dataAppVal -tiles.path $TILEPATH -Stats.out $TESTPATH/stats -Stat.out.cmd $TESTPATH/cmd/stats --wd $TMPDIR -conf $CONFIG\n\
\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()
##################################################################################################################
def gen_jobGenJobLaunchFusion(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N genJob_L_Fusion\n\
#PBS -l select=1:ncpus=1:mem=4000mb\n\
#PBS -l walltime=00:30:00\n\
#PBS -o %s/genJobLaunchFusion_out.log\n\
#PBS -e %s/genJobLaunchFusion_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
cd $PYPATH\n\
\n\
python genJobLaunchFusion.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH -conf $CONFIG\n\
\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()
##################################################################################################################
def gen_jobGenJobLaunchStat(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N genJob_L_Stat\n\
#PBS -l select=1:ncpus=5:mem=4000mb\n\
#PBS -l walltime=00:30:00\n\
#PBS -o %s/genJobLaunchStatistics_out.log\n\
#PBS -e %s/genJobLaunchStatistics_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
cd $PYPATH\n\
\n\
python genJobLaunchStat.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH -conf $CONFIG\n\
\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()
##################################################################################################################
def gen_jobGenCmdTrain(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N genCmdTrain\n\
#PBS -l select=1:ncpus=5:mem=4000mb\n\
#PBS -l walltime=00:30:00\n\
#PBS -o %s/cmdTrain_out.log\n\
#PBS -e %s/cmdTrain_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
cd $PYPATH\n\
\n\
#python LaunchTraining.py -shapesIn $TESTPATH/dataAppVal -conf $CONFIG -tiles.path $TILEPATH -data.field $DATAFIELD -N $Nsample -train.out.cmd $TESTPATH/cmd/train -out $TESTPATH/model --wd $TMPDIR\n\
python LaunchTraining.py --path.log $LOGPATH --stat $TESTPATH/stats -shapesIn $TESTPATH/dataAppVal -conf $CONFIG -tiles.path $TILEPATH -data.field $DATAFIELD -N $Nsample -train.out.cmd $TESTPATH/cmd/train -out $TESTPATH/model\n\
\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()
##################################################################################################################
def gen_jobGenJobLaunchTrain(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N genJob_L_Train\n\
#PBS -l select=1:ncpus=2:mem=4000mb\n\
#PBS -l walltime=00:10:00\n\
#PBS -o %s/genJobLaunchTrain_out.log\n\
#PBS -e %s/genJobLaunchTrain_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
cd $PYPATH\n\
\n\
python genJobLaunchTrain.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH -conf $CONFIG\n\
\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()
##################################################################################################################
def gen_jobGenCmdClass(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N genCmdClass\n\
#PBS -l select=1:ncpus=5:mem=4000mb\n\
#PBS -l walltime=00:30:00\n\
#PBS -o %s/cmdClass_out.log\n\
#PBS -e %s/cmdClass_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
\n\
#remove core file\n\
coreFile=($(find ~/ -maxdepth 5 -type f -name "core.*"))\n\
COUNTER=0\n\
while [  $COUNTER -lt ${#coreFile[@]} ]; do\n\
	rm ${coreFile[$COUNTER]}\n\
	let COUNTER=COUNTER+1\n\
done\n\
\n\
cd $PYPATH\n\
\n\
python launchClassification.py --stat $TESTPATH/stats -classif.out.cmd $TESTPATH/cmd/cla -path.model $TESTPATH/model -conf $CONFIG -path.region.tile $TESTPATH/shapeRegion -path.img $TILEPATH -path.region $PATHREGION -region.field $REGIONFIELD -N $Nsample -out $TESTPATH/classif --wd $TMPDIR\n\
\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()
##################################################################################################################
def gen_jobGenJobLaunchClass(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N genJob_L_Class\n\
#PBS -l select=1:ncpus=2:mem=4000mb\n\
#PBS -l walltime=00:10:00\n\
#PBS -o %s/genJobLaunchClassif_out.log\n\
#PBS -e %s/genJobLaunchClassif_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
cd $PYPATH\n\
\n\
python genJobLaunchClassif.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH -conf $CONFIG\n\
\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()
##################################################################################################################
def gen_jobCmdFusion(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N genCmdFusion\n\
#PBS -l select=1:ncpus=10:mem=8000mb\n\
#PBS -l walltime=00:30:00\n\
#PBS -o %s/genCmdFusion_out.log\n\
#PBS -e %s/genCmdFusion_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
#remove core file\n\
coreFile=($(find ~/ -maxdepth 5 -type f -name "core.*"))\n\
COUNTER=0\n\
while [  $COUNTER -lt ${#coreFile[@]} ]; do\n\
	echo ${coreFile[$COUNTER]}\n\
	rm ${coreFile[$COUNTER]}\n\
	let COUNTER=COUNTER+1\n\
done\n\
\n\
cd $PYPATH\n\
\n\
python fusion.py -path.classif $TESTPATH/classif -conf $CONFIG --wd $TMPDIR\n\
\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()
##################################################################################################################
def gen_jobGenJobNoData(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N genJobNoData\n\
#PBS -l select=1:ncpus=1:mem=4000mb\n\
#PBS -l walltime=00:10:00\n\
#PBS -o %s/genJobNoData_out.log\n\
#PBS -e %s/genJobNoData_err.log\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
cd $PYPATH\n\
\n\
python genJobNoData.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH -conf $CONFIG\n\
\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()
##################################################################################################################
def gen_jobClassifShaping(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N classifShaping\n\
#PBS -l select=1:ncpus=2:mem=8000mb\n\
#PBS -l walltime=05:00:00\n\
#PBS -o %s/ClassifShaping_out.log\n\
#PBS -e %s/ClassifShaping_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
cd $PYPATH\n\
\n\
python ClassificationShaping.py -path.classif $TESTPATH/classif -path.envelope $TESTPATH/envelope -path.img $TILEPATH -field.env FID -N $Nsample -path.out $TESTPATH/final --wd $TMPDIR -conf $CONFIG\n\
\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()
##################################################################################################################
def gen_jobGenCmdConf(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N genCmdConfusion\n\
#PBS -l select=1:ncpus=1:mem=4000mb\n\
#PBS -l walltime=00:30:00\n\
#PBS -o %s/cmdConfusion_out.log\n\
#PBS -e %s/cmdConfusion_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
cd $PYPATH\n\
\n\
python genConfusionMatrix.py -path.classif $TESTPATH/final -path.valid $TESTPATH/dataAppVal -N $Nsample -data.field $DATAFIELD -confusion.out.cmd $TESTPATH/cmd/confusion --wd $TMPDIR -conf $CONFIG\n\
\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()
##################################################################################################################
def gen_jobGenJobLaunchConfusion(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N genJob_L_Confu\n\
#PBS -l select=1:ncpus=1:mem=1000mb\n\
#PBS -l walltime=00:30:00\n\
#PBS -o %s/genJobLaunchConfusionMatrix_out.log\n\
#PBS -e %s/genJobLaunchConfusionMatrix_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
cd $PYPATH\n\
\n\
python genJobLaunchConfusion.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH -conf $CONFIG\n\
\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()
##################################################################################################################

def gen_jobfusionConfusion(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N confusionFusion\n\
#PBS -l select=1:ncpus=1:mem=100mb\n\
#PBS -l walltime=00:10:00\n\
#PBS -o %s/fusionConfusion_out.log\n\
#PBS -e %s/fusionConfusion_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
cd $PYPATH\n\
\n\
python confusionFusion.py -path.shapeIn $GROUNDTRUTH -dataField $DATAFIELD -path.csv.out $TESTPATH/final/TMP -path.txt.out $TESTPATH/final/TMP -path.csv $TESTPATH/final/TMP -conf $CONFIG\n\
\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()
##################################################################################################################
def gen_jobGenResults(JOBPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N genResults\n\
#PBS -l select=1:ncpus=1:mem=1000mb\n\
#PBS -l walltime=00:10:00\n\
#PBS -o %s/genResults_out.log\n\
#PBS -e %s/genResults_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
pkg="otb_superbuild"\n\
version="%s"\n\
build_type="%s"\n\
name=$pkg-$version\n\
install_dir=%s/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}\n\
\n\
cd $PYPATH\n\
\n\
python genResults.py -path.res $TESTPATH/final -path.nomenclature $NOMENCLATURE\n\
\n\
'%(LOGPATH,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR))
	jobFile.close()
##################################################################################################################

def genJobs(Fileconfig):

	f = file(Fileconfig)
	cfg = Config(f)

	LOGPATH = cfg.chain.logPath
	JOBPATH = cfg.chain.jobsPath

	OTB_VERSION = cfg.chain.OTB_version
	OTB_BUILDTYPE = cfg.chain.OTB_buildType
	OTB_INSTALLDIR = cfg.chain.OTB_installDir

	jobGenCmdFeatures = JOBPATH+"/genCmdFeatures.pbs"
	jobGenJobLaunchFeat = JOBPATH+"/genJobLaunchFeat.pbs"
	jobEnvelope = JOBPATH+"/envelope.pbs"
	jobGenerateRegionShape = JOBPATH+"/generateRegionShape.pbs"
	jobRegionByTiles = JOBPATH+"/regionsByTiles.pbs"
	jobExtractactData = JOBPATH+"/genJobExtractData.pbs"
	jobGenJobDataAppVal = JOBPATH+"/genJobDataAppVal.pbs"
	jobRearrange = JOBPATH+"/reArrangeModel.pbs"
	jobGenCmdStat = JOBPATH+"/genCmdStats.pbs"
	jobGenJobLaunchStat = JOBPATH+"/genJobLaunchStat.pbs"
	jobGenCmdTrain = JOBPATH+"/genCmdTrain.pbs"
	jobGenJobLaunchTrain = JOBPATH+"/genJobLaunchTrain.pbs"
	jobGenCmdClass = JOBPATH+"/genCmdClass.pbs"
	jobGenJobLaunchClass = JOBPATH+"/genJobLaunchClass.pbs"
	jobCmdFusion = JOBPATH+"/genCmdFusion.pbs"
	jobGenJobLaunchFusion = JOBPATH+"/genJobLaunchFusion.pbs"
	jobGenJobNoData = JOBPATH+"/genJobNoData.pbs"
	jobClassifShaping = JOBPATH+"/classifShaping.pbs"
	jobGenCmdConf = JOBPATH+"/genCmdConf.pbs"
	jobGenJobLaunchConfusion = JOBPATH+"/genJobLaunchConfusion.pbs"
	jobfusionConfusion = JOBPATH+"/fusionConfusion.pbs"
	jobGenResults = JOBPATH+"/genResults.pbs"

	if not os.path.exists(JOBPATH):
		os.system("mkdir "+JOBPATH)

	if not os.path.exists(LOGPATH):
		os.system("mkdir "+LOGPATH)

	if os.path.exists(jobGenCmdFeatures):
		os.system("rm "+jobGenCmdFeatures)
	gen_jobGenCmdFeatures(jobGenCmdFeatures,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)

	if os.path.exists(jobGenJobLaunchFeat):
		os.system("rm "+jobGenJobLaunchFeat)
	gen_jobGenJobLaunchFeat(jobGenJobLaunchFeat,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)

	if os.path.exists(jobEnvelope):
		os.system("rm "+jobEnvelope)
	gen_jobEnvelope(jobEnvelope,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)

	if os.path.exists(jobGenerateRegionShape):
		os.system("rm "+jobGenerateRegionShape)
	gen_jobGenerateRegionShape(jobGenerateRegionShape,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)

	if os.path.exists(jobRegionByTiles):
		os.system("rm "+jobRegionByTiles)
	gen_jobRegionByTiles(jobRegionByTiles,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)

	if os.path.exists(jobExtractactData):
		os.system("rm "+jobExtractactData)
	gen_jobExtractactData(jobExtractactData,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)

	if os.path.exists(jobGenJobDataAppVal):
		os.system("rm "+jobGenJobDataAppVal)
	gen_jobGenJobDataAppVal(jobGenJobDataAppVal,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)

	if os.path.exists(jobRearrange):
		os.system("rm "+jobRearrange)
	gen_jobRearrange(jobRearrange,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)

	if os.path.exists(jobGenCmdStat):
		os.system("rm "+jobGenCmdStat)
	gen_jobGenCmdStat(jobGenCmdStat,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)

	if os.path.exists(jobGenJobLaunchStat):
		os.system("rm "+jobGenJobLaunchStat)
	gen_jobGenJobLaunchStat(jobGenJobLaunchStat,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)

	if os.path.exists(jobGenCmdTrain):
		os.system("rm "+jobGenCmdTrain)
	gen_jobGenCmdTrain(jobGenCmdTrain,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)

	if os.path.exists(jobGenJobLaunchTrain):
		os.system("rm "+jobGenJobLaunchTrain)
	gen_jobGenJobLaunchTrain(jobGenJobLaunchTrain,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)

	if os.path.exists(jobGenCmdClass):
		os.system("rm "+jobGenCmdClass)
	gen_jobGenCmdClass(jobGenCmdClass,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)

	if os.path.exists(jobGenJobLaunchClass):
		os.system("rm "+jobGenJobLaunchClass)
	gen_jobGenJobLaunchClass(jobGenJobLaunchClass,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)
	
	if os.path.exists(jobCmdFusion):
		os.system("rm "+jobCmdFusion)
	gen_jobCmdFusion(jobCmdFusion,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)
	
	if os.path.exists(jobGenJobLaunchFusion):
		os.system("rm "+jobGenJobLaunchFusion)
	gen_jobGenJobLaunchFusion(jobGenJobLaunchFusion,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)

	if os.path.exists(jobGenJobNoData):
		os.system("rm "+jobGenJobNoData)
	gen_jobGenJobNoData(jobGenJobNoData,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)

	if os.path.exists(jobClassifShaping):
		os.system("rm "+jobClassifShaping)
	gen_jobClassifShaping(jobClassifShaping,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)

	if os.path.exists(jobGenCmdConf):
		os.system("rm "+jobGenCmdConf)
	gen_jobGenCmdConf(jobGenCmdConf,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)

	if os.path.exists(jobGenJobLaunchConfusion):
		os.system("rm "+jobGenJobLaunchConfusion)
	gen_jobGenJobLaunchConfusion(jobGenJobLaunchConfusion,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)

	if os.path.exists(jobfusionConfusion):
		os.system("rm "+jobfusionConfusion)
	gen_jobfusionConfusion(jobfusionConfusion,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)
	
	if os.path.exists(jobGenResults):
		os.system("rm "+jobGenResults)
	gen_jobGenResults(jobGenResults,LOGPATH,OTB_VERSION,OTB_BUILDTYPE,OTB_INSTALLDIR)

	
##################################################################################################################

def launchChain(Fileconfig):

	f = file(Fileconfig)
	cfg = Config(f)
	chainType = cfg.chain.executionMode
	if chainType == "parallel":
		genJobs(Fileconfig)
		pathChain = gen_oso_parallel(Fileconfig)
		print pathChain
		os.system("chmod u+rwx "+pathChain)
		os.system(pathChain)
	elif chainType == "sequential":
		gen_oso_sequential(Fileconfig)
        else:
            raise Exception("Execution mode "+chainType+" does not exist.")

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allows you launch the chain according to a configuration file")
	parser.add_argument("-launch.config",dest = "config",help ="path to configuration file",required=True)
	args = parser.parse_args()

	launchChain(args.config)
