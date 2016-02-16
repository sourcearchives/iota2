#!/usr/bin/python
#-*- coding: utf-8 -*-

import argparse,os
from config import Config

##################################################################################################################

def gen_oso_parallel(Fileconfig):

	f = file(Fileconfig)
	cfg = Config(f)

	PYPATH = cfg.chain.pyAppPath
	NOMENCLATURE= cfg.chain.nomenclaturePath
	JOBPATH= cfg.chain.jobsPath
	TESTPATH= cfg.chain.testPath
	LISTTILE= cfg.chain.listTile
	TILEPATH= cfg.chain.featuresPath
	L8PATH= cfg.chain.L8Path
	S2PATH= cfg.chain.S2Path
	S1PATH= cfg.chain.S1Path
	GROUNDTRUTH= cfg.chain.groundTruth
	DATAFIELD= cfg.chain.dataField
	Nsample= cfg.chain.sample
	MODE= cfg.chain.mode
	MODEL= cfg.chain.model
	REGIONFIELD= cfg.chain.regionField
	PATHREGION= cfg.chain.regionPath
	LOGPATH= cfg.chain.logPath

	chainName=cfg.chain.chainName
	
	pathChain = JOBPATH+"/"+chainName+".sh"
	chainFile = open(pathChain,"w")
	chainFile.write('\
#+BEGIN_SRC sh\n\
#!/bin/bash\n\
\n\
#Chargement des modules nécessaire pour la création des répertoires et des .py\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
cd %s\n\
\n\
#path to pythons function\n\
PYPATH=%s\n\
\n\
#path to log file\n\
LOGPATH=%s\n\
\n\
#Nomenclatures path\n\
NOMENCLATURE=%s\n\
\n\
#jobs path\n\
JOBPATH=%s\n\
#path to features generation application (code de benjamin Tardy)\n\
GENFEATPATH=%s\n\
\n\
#Emplacement de la classification ne pas changer le nom de la variable car écrite "en dur" dans les générateurs de job\n\
TESTPATH=%s\n\
\n\
#liste des tuiles à traiter, pas despace avant et après la liste\n\
LISTTILE="%s"\n\
\n\
#Emplacement des tuiles (avec leur primitives)\n\
TILEPATH=%s\n\
\n\
#Emplacement des tuiles L8\n\
L8PATH=%s\n\
\n\
#Emplacement des tuiles Sentinel 2\n\
S2PATH=%s\n\
#Emplacement des tuiles Sentinel 1\n\
S1PATH=%s\n\
#fichier de configuration pour la génération des primitives\n\
FEATCONFIG=%s\n\
\n\
#ground truth path\n\
GROUNDTRUTH=%s\n\
\n\
#data field\n\
DATAFIELD=%s\n\
\n\
#nb sample\n\
Nsample=%s\n\
\n\
#configFile\n\
CONFIG=%s\n\
\n\
MODE=%s\n\
MODEL=%s\n\
REGIONFIELD=%s\n\
PATHREGION=%s\n\
\n\
export PYPATH\n\
export JOBPATH\n\
export TESTPATH\n\
export TILEPATH\n\
export GROUNDTRUTH\n\
export DATAFIELD\n\
export Nsample\n\
export CONFIG\n\
export MODE\n\
export MODEL\n\
export REGIONFIELD\n\
export PATHREGION\n\
export NOMENCLATURE\n\
export LISTTILE\n\
export GENFEATPATH\n\
export FEATCONFIG\n\
export L8PATH\n\
export LOGPATH\n\
\n\
#suppression des jobArray\n\
JOBEXTRACTDATA=$JOBPATH/extractData.pbs\n\
if [ -f "$JOBEXTRACTDATA" ]\n\
	then\n\
		rm $JOBEXTRACTDATA\n\
	fi\n\
JOBDATAAPPVAL=$JOBPATH/dataAppVal.pbs\n\
if [ -f "$JOBDATAAPPVAL" ]\n\
	then\n\
		rm $JOBDATAAPPVAL\n\
	fi\n\
JOBLAUNCHSTAT=$JOBPATH/launchStats.pbs\n\
if [ -f "$JOBLAUNCHSTAT" ]\n\
	then\n\
		rm $JOBLAUNCHSTAT\n\
	fi\n\
JOBLAUNCHTRAIN=$JOBPATH/launchTrain.pbs\n\
if [ -f "$JOBLAUNCHTRAIN" ]\n\
	then\n\
		rm $JOBLAUNCHTRAIN\n\
	fi\n\
JOBLAUNCHCLASSIF=$JOBPATH/launchClassif.pbs\n\
if [ -f "$JOBLAUNCHCLASSIF" ]\n\
	then\n\
		rm $JOBLAUNCHCLASSIF\n\
	fi\n\
JOBLAUNCHCONFUSION=$JOBPATH/launchConf.pbs\n\
if [ -f "$JOBLAUNCHCONFUSION" ]\n\
	then\n\
		rm $JOBLAUNCHCONFUSION\n\
	fi\n\
JOBEXTRACTFEATURES=$JOBPATH/extractfeatures.pbs\n\
if [ -f "$JOBEXTRACTFEATURES" ]\n\
	then\n\
		rm $JOBEXTRACTFEATURES\n\
	fi\n\
#Création des répertoires pour la classification\n\
python $PYPATH/oso_directory.py -root $TESTPATH\n\
\n\
#génération des commandes pour calculer les primitives si nécessaire\n\
\n\
id_cmdLaunchFeat=$(qsub -V genCmdFeatures.pbs)\n\
id_pyLaunchFeat=$(qsub -V -W depend=afterok:$id_cmdLaunchFeat genJobLaunchFeat.pbs)\n\
\n\
flag=0\n\
while [ $flag -le 0 ]\n\
do\n\
	if [ -f "$JOBEXTRACTFEATURES" ]\n\
	then\n\
		flag=1\n\
		id_extractFeat=$(qsub -V extractfeatures.pbs)\n\
	fi\n\
done\n\
\n\
#Création des enveloppes\n\
id_env=$(qsub -V -W depend=afterok:$id_extractFeat envelope.pbs)\n\
\n\
'%(JOBPATH,PYPATH,LOGPATH,NOMENCLATURE,JOBPATH,PYPATH,TESTPATH,LISTTILE,TILEPATH,L8PATH,S2PATH,S1PATH,Fileconfig,GROUNDTRUTH,DATAFIELD,Nsample,Fileconfig,MODE,MODEL,REGIONFIELD,PATHREGION))
	if MODE != "outside":
		chainFile.write('\
#Création du shape de région\n\
id_reg=$(qsub -V -W depend=afterok:$id_env generateRegionShape.pbs)\n\
')
	chainFile.write('\
#Création des régions par tuiles\n\
id_regTile=$(qsub -V -W depend=afterok:$id_reg regionsByTiles.pbs)\n\
\n\
#Ecriture du job extractData.pbs\n\
id_pyExtract=$(qsub -V -W depend=afterok:$id_regTile genJobExtractData.pbs)\n\
\n\
#Extraction des data/tuiles/régions lorsque le job extractData.pbs est généré\n\
flag=0\n\
while [ $flag -le 0 ]\n\
do\n\
	if [ -f "$JOBEXTRACTDATA" ]\n\
	then\n\
		flag=1\n\
		id_extractData=$(qsub -V extractData.pbs)\n\
	fi\n\
done\n\
\n\
#Ecriture du jobdataAppVal.pbs\n\
id_pyDataAppVal=$(qsub -V -W depend=afterok:$id_extractData genJobDataAppVal.pbs)\n\
\n\
#Séparation en ensemble dapp/val lorsque le job dataAppVal.pbs est généré\n\
flag=0\n\
while [ $flag -le 0 ]\n\
do\n\
	if [ -f "$JOBDATAAPPVAL" ]\n\
	then\n\
		flag=1\n\
		id_appVal=$(qsub -V dataAppVal.pbs)\n\
	fi\n\
done\n\
\n\
#génération et lancement des commandes pour calculer les stats\n\
id_cmdGenStats=$(qsub -V -W depend=afterok:$id_appVal genCmdStats.pbs)\n\
id_pyLaunchStats=$(qsub -V -W depend=afterok:$id_cmdGenStats genJobLaunchStat.pbs)\n\
\n\
flag=0\n\
while [ $flag -le 0 ]\n\
do\n\
	if [ -f "$JOBLAUNCHSTAT" ]\n\
	then\n\
		flag=1\n\
		id_launchStat=$(qsub -V launchStats.pbs)\n\
	fi\n\
done\n\
\n\
#génération et lancement des commandes pour lapprentissage\n\
id_cmdTrain=$(qsub -V -W depend=afterok:$id_launchStat genCmdTrain.pbs)\n\
id_pyLaunchTrain=$(qsub -V -W depend=afterok:$id_cmdTrain genJobLaunchTrain.pbs)\n\
\n\
flag=0\n\
while [ $flag -le 0 ]\n\
do\n\
	if [ -f "$JOBLAUNCHTRAIN" ]\n\
	then\n\
		flag=1\n\
		id_launchTrain=$(qsub -V launchTrain.pbs)\n\
	fi\n\
done\n\
\n\
#génération et lancement des commandes pour la classification ->réécriture du .pbs avec py\n\
id_cmdClass=$(qsub -V -W depend=afterok:$id_launchTrain genCmdClass.pbs)\n\
id_pyLaunchClass=$(qsub -V -W depend=afterok:$id_cmdClass genJobLaunchClass.pbs)\n\
\n\
flag=0\n\
while [ $flag -le 0 ]\n\
do\n\
	if [ -f "$JOBLAUNCHCLASSIF" ]\n\
	then\n\
		flag=1\n\
		id_launchClassif=$(qsub -V launchClassif.pbs)\n\
	fi\n\
done\n\
\n\
#Mise en forme des classifications\n\
id_ClassifShaping=$(qsub -V -W depend=afterok:$id_launchClassif classifShaping.pbs)\n\
\n\
#génération des commandes pour les matrices de confusions\n\
id_CmdConfMatrix=$(qsub -V -W depend=afterok:$id_ClassifShaping genCmdConf.pbs)\n\
id_pyLaunchConf=$(qsub -V -W depend=afterok:$id_CmdConfMatrix genJobLaunchConfusion.pbs)\n\
flag=0\n\
while [ $flag -le 0 ]\n\
do\n\
	if [ -f "$JOBLAUNCHCONFUSION" ]\n\
	then\n\
		flag=1\n\
		id_launchConfusion=$(qsub -V launchConf.pbs)\n\
	fi\n\
done\n\
\n\
#génération des résultats\n\
id_res=$(qsub -V -W depend=afterok:$id_launchConfusion genResults.pbs)\n\
\n\
#+END_SRC\n\
')
	chainFile.close()
	return pathChain

##################################################################################################################

def gen_oso_sequential(Fileconfig):

	f = file(Fileconfig)
	cfg = Config(f)

	PYPATH = cfg.chain.pyAppPath
	NOMENCLATURE= cfg.chain.nomenclaturePath
	JOBPATH= cfg.chain.jobsPath
	TESTPATH= cfg.chain.testPath
	LISTTILE= cfg.chain.listTile
	TILEPATH= cfg.chain.featuresPath
	L8PATH= cfg.chain.L8Path
	S2PATH= cfg.chain.S2Path
	S1PATH= cfg.chain.S1Path
	GROUNDTRUTH= cfg.chain.groundTruth
	DATAFIELD= cfg.chain.dataField
	Nsample= cfg.chain.sample
	MODE= cfg.chain.mode
	MODEL= cfg.chain.model
	REGIONFIELD= cfg.chain.regionField
	PATHREGION= cfg.chain.regionPath

	chainName=cfg.chain.chainName
	LISTTILE = '["'+LISTTILE.replace(" ",'","')+'"]'
	pathChain = PYPATH+"/"+chainName+".py"
	chainFile = open(pathChain,"w")
	chainFile.write('\
#!/usr/bin/python\n\
#-*- coding: utf-8 -*-\n\
\n\
import tileEnvelope as env\n\
import tileArea as area\n\
import LaunchTraining as LT\n\
import createRegionsByTiles as RT\n\
import ExtractDataByRegion as ExtDR\n\
import RandomInSituByTile as RIST\n\
import launchClassification as LC\n\
import ClassificationShaping as CS\n\
import genConfusionMatrix as GCM\n\
import ModelStat as MS\n\
import genResults as GR\n\
import genCmdFeatures as GFD\n\
import os\n\
\n\
PathTEST = "%s"\n\
\n\
os.system("rm -r "+PathTEST)\n\
\n\
tiles = %s\n\
pathTilesL8 = "%s"\n\
pathNewProcessingChain = "%s"\n\
pathTilesFeat = "%s"\n\
configFeature = "%s"\n\
shapeRegion = "%s"\n\
field_Region = "%s"\n\
model = "%s"\n\
\n\
shapeData = "%s"\n\
dataField = "%s"\n\
\n\
#Param de la classif\n\
pathConf = "%s"\n\
N = %s\n\
fieldEnv = "FID"#do not change\n\
\n\
pathModels = PathTEST+"/model"\n\
pathEnvelope = PathTEST+"/envelope"\n\
pathClassif = PathTEST+"/classif"\n\
pathTileRegion = PathTEST+"/shapeRegion"\n\
classifFinal = PathTEST+"/final"\n\
dataRegion = PathTEST+"/dataRegion"\n\
pathAppVal = PathTEST+"/dataAppVal"\n\
pathStats = PathTEST+"/stats"\n\
cmdPath = PathTEST+"/cmd"\n\
\n\
if not os.path.exists(PathTEST):\n\
	os.system("mkdir "+PathTEST)\n\
if not os.path.exists(pathModels):\n\
	os.system("mkdir "+pathModels)\n\
if not os.path.exists(pathEnvelope):\n\
	os.system("mkdir "+pathEnvelope)\n\
if not os.path.exists(pathClassif):\n\
	os.system("mkdir "+pathClassif)\n\
if not os.path.exists(pathTileRegion):\n\
	os.system("mkdir "+pathTileRegion)\n\
if not os.path.exists(classifFinal):\n\
	os.system("mkdir "+classifFinal)\n\
if not os.path.exists(dataRegion):\n\
	os.system("mkdir "+dataRegion)\n\
if not os.path.exists(pathAppVal):\n\
	os.system("mkdir "+pathAppVal)\n\
if not os.path.exists(pathStats):\n\
	os.system("mkdir "+pathStats)\n\
if not os.path.exists(cmdPath):\n\
	os.system("mkdir "+cmdPath)\n\
	os.system("mkdir "+cmdPath+"/stats")\n\
	os.system("mkdir "+cmdPath+"/train")\n\
	os.system("mkdir "+cmdPath+"/cla")\n\
	os.system("mkdir "+cmdPath+"/confusion")\n\
	os.system("mkdir "+cmdPath+"/features")\n\
\n\
feat = GFD.CmdFeatures(PathTEST,tiles,pathNewProcessingChain,pathTilesL8,pathConf,pathTilesFeat,None)\n\
for i in range(len(feat)):\n\
	print feat[i]\n\
	os.system(feat[i])\n\
\n\
#Création des enveloppes\n\
env.GenerateShapeTile(tiles,pathTilesFeat,pathEnvelope,None)\n\
\n\
'%(TESTPATH,LISTTILE,L8PATH,PYPATH,TILEPATH,Fileconfig,PATHREGION,REGIONFIELD,MODEL,GROUNDTRUTH,DATAFIELD,Fileconfig,Nsample))
	if MODE != "outside":
		chainFile.write('\
area.generateRegionShape("%s",pathEnvelope,model,shapeRegion,field_Region,None)\n\
\
'%(MODE))
	chainFile.write('\
#Création des régions par tuiles\n\
RT.createRegionsByTiles(shapeRegion,field_Region,pathEnvelope,pathTileRegion,None)\n\
\n\
#pour tout les fichiers dans pathTileRegion\n\
regionTile = RT.FileSearch_AND(pathTileRegion,".shp")\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
for path in regionTile:\n\
	ExtDR.ExtractData(path,shapeData,dataRegion,None)\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
\n\
\n\
#pour tout les shape file par tuiles présent dans dataRegion, créer un ensemble dapp et de val\n\
dataTile = RT.FileSearch_AND(dataRegion,".shp")\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
for path in dataTile:\n\
	RIST.RandomInSituByTile(path,dataField,N,pathAppVal,None)\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
#génération des fichiers de statistiques\n\
AllCmd = MS.generateStatModel(pathAppVal,pathTilesFeat,pathStats,cmdPath+"/stats",None)\n\
\n\
for cmd in AllCmd:\n\
	print cmd\n\
	print ""\n\
	#os.system(cmd)\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
\n\
#génération des commandes pour lApp\n\
allCmd = LT.launchTraining(pathAppVal,pathConf,pathTilesFeat,dataField,pathStats,N,cmdPath+"/train",pathModels,None)\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
for cmd in allCmd:\n\
	print cmd\n\
	print ""\n\
	os.system(cmd)\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
\n\
\n\
#génération des commandes pour la classification\n\
cmdClassif = LC.launchClassification(pathModels,pathConf,pathStats,pathTileRegion,pathTilesFeat,shapeRegion,field_Region,N,cmdPath+"/cla",pathClassif,None)\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
for cmd in cmdClassif:\n\
	print cmd \n\
	print ""\n\
	os.system(cmd)\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
\n\
#Mise en forme des classifications\n\
CS.ClassificationShaping(pathClassif,pathEnvelope,pathTilesFeat,fieldEnv,N,classifFinal,None)\n\
\n\
#génération des commandes pour les matrices de confusions\n\
allCmd_conf = GCM.genConfMatrix(classifFinal,pathAppVal,N,dataField,cmdPath+"/confusion",None)\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
for cmd in allCmd_conf:\n\
	print cmd\n\
	os.system(cmd)\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
\n\
GR.genResults(classifFinal,"%s")\n\
\n\
'%(NOMENCLATURE))
	chainFile.close()
	return pathChain

##################################################################################################################
def gen_jobGenCmdFeatures(JOBPATH,LOGPATH):
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
version="5.0.0"\n\
name=$pkg-$version\n\
install_dir=/data/qtis/inglada/modules/repository/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}:/usr/lib64/\n\
\n\
cd $PYPATH\n\
\n\
python genCmdFeatures.py -path.test $TESTPATH -tiles $LISTTILE -path.application $GENFEATPATH -path.out $TILEPATH --path.L8 $L8PATH -path.config $FEATCONFIG --wd $TMPDIR\n\
\n\
'%(LOGPATH,LOGPATH))
	jobFile.close()
##################################################################################################################
def gen_jobGenJobLaunchFeat(JOBPATH,LOGPATH):
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
version="5.0.0"\n\
name=$pkg-$version\n\
install_dir=/data/qtis/inglada/modules/repository/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}:/usr/lib64/\n\
\n\
cd $PYPATH\n\
\n\
python genJobLaunchFeat.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH\n\
\n\
'%(LOGPATH,LOGPATH))
	jobFile.close()
##################################################################################################################
def gen_jobEnvelope(JOBPATH,LOGPATH):
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
version="5.0.0"\n\
name=$pkg-$version\n\
install_dir=/data/qtis/inglada/modules/repository/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}:/usr/lib64/\n\
\n\
cd $PYPATH\n\
\n\
python tileEnvelope.py -t $LISTTILE -t.path $TILEPATH -out $TESTPATH/envelope --wd $TMPDIR\n\
\n\
'%(LOGPATH,LOGPATH))
	jobFile.close()
##################################################################################################################
def gen_jobGenerateRegionShape(JOBPATH,LOGPATH):
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
version="5.0.0"\n\
name=$pkg-$version\n\
install_dir=/data/qtis/inglada/modules/repository/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}:/usr/lib64/\n\
\n\
cd $PYPATH\n\
\n\
python tileArea.py -pathTiles $TESTPATH/envelope -mode $MODE -fieldOut $REGIONFIELD --multi.models $MODEL -out $PATHREGION --wd $TMPDIR\n\
\n\
'%(LOGPATH,LOGPATH))
	jobFile.close()
##################################################################################################################
def gen_jobRegionByTiles(JOBPATH,LOGPATH):
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
version="5.0.0"\n\
name=$pkg-$version\n\
install_dir=/data/qtis/inglada/modules/repository/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}:/usr/lib64/\n\
\n\
cd $PYPATH\n\
\n\
python createRegionsByTiles.py -region.shape $PATHREGION -region.field $REGIONFIELD -tiles.envelope $TESTPATH/envelope -out $TESTPATH/shapeRegion --wd $TMPDIR\n\
\n\
'%(LOGPATH,LOGPATH))
	jobFile.close()
##################################################################################################################
def gen_jobExtractactData(JOBPATH,LOGPATH):
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
version="5.0.0"\n\
name=$pkg-$version\n\
install_dir=/data/qtis/inglada/modules/repository/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}:/usr/lib64/\n\
\n\
cd $PYPATH\n\
\n\
python genJobExtractData.py -path.job $JOBPATH -path.test $TESTPATH -path.log \n\
\n\
'%(LOGPATH,LOGPATH))
	jobFile.close()
##################################################################################################################
def gen_jobGenJobDataAppVal(JOBPATH,LOGPATH):
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
version="5.0.0"\n\
name=$pkg-$version\n\
install_dir=/data/qtis/inglada/modules/repository/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}:/usr/lib64/\n\
\n\
cd $PYPATH\n\
\n\
python genJobDataAppVal.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH\n\
\n\
'%(LOGPATH,LOGPATH))
	jobFile.close()
##################################################################################################################
def gen_jobGenCmdStat(JOBPATH,LOGPATH):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N genCmdStats\n\
#PBS -l select=1:ncpus=5:mem=4000mb\n\
#PBS -l walltime=00:30:00\n\
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
version="5.0.0"\n\
name=$pkg-$version\n\
install_dir=/data/qtis/inglada/modules/repository/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}:/usr/lib64/\n\
\n\
cd $PYPATH\n\
\n\
python ModelStat.py -shapesIn $TESTPATH/dataAppVal -tiles.path $TILEPATH -Stats.out $TESTPATH/stats -Stat.out.cmd $TESTPATH/cmd/stats --wd $TMPDIR\n\
\n\
'%(LOGPATH,LOGPATH))
	jobFile.close()
##################################################################################################################
def gen_jobGenJobLaunchStat(JOBPATH,LOGPATH):
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
version="5.0.0"\n\
name=$pkg-$version\n\
install_dir=/data/qtis/inglada/modules/repository/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}:/usr/lib64/\n\
\n\
cd $PYPATH\n\
\n\
python genJobLaunchStat.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH\n\
\n\
'%(LOGPATH,LOGPATH))
	jobFile.close()
##################################################################################################################
def gen_jobGenCmdTrain(JOBPATH,LOGPATH):
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
version="5.0.0"\n\
name=$pkg-$version\n\
install_dir=/data/qtis/inglada/modules/repository/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}:/usr/lib64/\n\
\n\
cd $PYPATH\n\
\n\
#python LaunchTraining.py -shapesIn $TESTPATH/dataAppVal -conf $CONFIG -tiles.path $TILEPATH -data.field $DATAFIELD -N $Nsample -train.out.cmd $TESTPATH/cmd/train -out $TESTPATH/model --wd $TMPDIR\n\
python LaunchTraining.py -shapesIn $TESTPATH/dataAppVal -conf $CONFIG -tiles.path $TILEPATH -data.field $DATAFIELD -N $Nsample -train.out.cmd $TESTPATH/cmd/train -out $TESTPATH/model\n\
\n\
'%(LOGPATH,LOGPATH))
	jobFile.close()
##################################################################################################################
def gen_jobGenJobLaunchTrain(JOBPATH,LOGPATH):
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
version="5.0.0"\n\
name=$pkg-$version\n\
install_dir=/data/qtis/inglada/modules/repository/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}:/usr/lib64/\n\
\n\
cd $PYPATH\n\
\n\
python genJobLaunchTrain.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH\n\
\n\
'%(LOGPATH,LOGPATH))
	jobFile.close()
##################################################################################################################
def gen_jobGenCmdClass(JOBPATH,LOGPATH):
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
version="5.0.0"\n\
name=$pkg-$version\n\
install_dir=/data/qtis/inglada/modules/repository/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}:/usr/lib64/\n\
\n\
cd $PYPATH\n\
\n\
python launchClassification.py -classif.out.cmd $TESTPATH/cmd/cla -path.model $TESTPATH/model -conf $CONFIG -path.region.tile $TESTPATH/shapeRegion -path.img $TILEPATH -path.region $PATHREGION -region.field $REGIONFIELD -N $Nsample -out $TESTPATH/classif --wd $TMPDIR\n\
\n\
'%(LOGPATH,LOGPATH))
	jobFile.close()
##################################################################################################################
def gen_jobGenJobLaunchClass(JOBPATH,LOGPATH):
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
version="5.0.0"\n\
name=$pkg-$version\n\
install_dir=/data/qtis/inglada/modules/repository/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}:/usr/lib64/\n\
\n\
cd $PYPATH\n\
\n\
python genJobLaunchClassif.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH\n\
\n\
'%(LOGPATH,LOGPATH))
	jobFile.close()
##################################################################################################################
def gen_jobClassifShaping(JOBPATH,LOGPATH):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N classifShaping\n\
#PBS -l select=1:ncpus=10:mem=8000mb\n\
#PBS -l walltime=00:30:00\n\
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
version="5.0.0"\n\
name=$pkg-$version\n\
install_dir=/data/qtis/inglada/modules/repository/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}:/usr/lib64/\n\
\n\
cd $PYPATH\n\
\n\
python ClassificationShaping.py -path.classif $TESTPATH/classif -path.envelope $TESTPATH/envelope -path.img $TILEPATH -field.env FID -N $Nsample -path.out $TESTPATH/final --wd $TMPDIR\n\
\n\
'%(LOGPATH,LOGPATH))
	jobFile.close()
##################################################################################################################
def gen_jobGenCmdConf(JOBPATH,LOGPATH):
	jobFile = open(JOBPATH,"w")
	jobFile.write('\
#!/bin/bash\n\
#PBS -N genCmdConfusion\n\
#PBS -l select=1:ncpus=5:mem=4000mb\n\
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
version="5.0.0"\n\
name=$pkg-$version\n\
install_dir=/data/qtis/inglada/modules/repository/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}:/usr/lib64/\n\
\n\
cd $PYPATH\n\
\n\
python genConfusionMatrix.py -path.classif $TESTPATH/final -path.valid $TESTPATH/dataAppVal -N $Nsample -data.field $DATAFIELD -confusion.out.cmd $TESTPATH/cmd/confusion --wd $TMPDIR\n\
\n\
'%(LOGPATH,LOGPATH))
	jobFile.close()
##################################################################################################################
def gen_jobGenJobLaunchConfusion(JOBPATH,LOGPATH):
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
version="5.0.0"\n\
name=$pkg-$version\n\
install_dir=/data/qtis/inglada/modules/repository/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}:/usr/lib64/\n\
\n\
cd $PYPATH\n\
\n\
python genJobLaunchConfusion.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH\n\
\n\
'%(LOGPATH,LOGPATH))
	jobFile.close()
##################################################################################################################
def gen_jobGenResults(JOBPATH,LOGPATH):
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
version="5.0.0"\n\
name=$pkg-$version\n\
install_dir=/data/qtis/inglada/modules/repository/$pkg/$name-install/\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export PATH=$install_dir/bin:$PATH\n\
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}:/usr/lib64/\n\
\n\
cd $PYPATH\n\
\n\
python genResults.py -path.res $TESTPATH/final -path.nomenclature $NOMENCLATURE\n\
\n\
'%(LOGPATH,LOGPATH))
	jobFile.close()
##################################################################################################################

def genJobs(Fileconfig):

	f = file(Fileconfig)
	cfg = Config(f)

	LOGPATH = cfg.chain.logPath
	JOBPATH = cfg.chain.jobsPath

	jobGenCmdFeatures = JOBPATH+"/genCmdFeatures.pbs"
	jobGenJobLaunchFeat = JOBPATH+"/genJobLaunchFeat.pbs"
	jobEnvelope = JOBPATH+"/envelope.pbs"
	jobGenerateRegionShape = JOBPATH+"/generateRegionShape.pbs"
	jobRegionByTiles = JOBPATH+"/regionsByTiles.pbs"
	jobExtractactData = JOBPATH+"/genJobExtractData.pbs"
	jobGenJobDataAppVal = JOBPATH+"/genJobDataAppVal.pbs"
	jobGenCmdStat = JOBPATH+"/genCmdStats.pbs"
	jobGenJobLaunchStat = JOBPATH+"/genJobLaunchStat.pbs"
	jobGenCmdTrain = JOBPATH+"/genCmdTrain.pbs"
	jobGenJobLaunchTrain = JOBPATH+"/genJobLaunchTrain.pbs"
	jobGenCmdClass = JOBPATH+"/genCmdClass.pbs"
	jobGenJobLaunchClass = JOBPATH+"/genJobLaunchClass.pbs"
	jobClassifShaping = JOBPATH+"/classifShaping.pbs"
	jobGenCmdConf = JOBPATH+"/genCmdConf.pbs"
	jobGenJobLaunchConfusion = JOBPATH+"/genJobLaunchConfusion.pbs"
	jobGenResults = JOBPATH+"/genResults.pbs"

	if not os.path.exists(JOBPATH):
		os.system("mkdir "+JOBPATH)

	if not os.path.exists(LOGPATH):
		os.system("mkdir "+LOGPATH)

	if os.path.exists(jobGenCmdFeatures):
		os.system("rm "+jobGenCmdFeatures)
	gen_jobGenCmdFeatures(jobGenCmdFeatures,LOGPATH)

	if os.path.exists(jobGenJobLaunchFeat):
		os.system("rm "+jobGenJobLaunchFeat)
	gen_jobGenJobLaunchFeat(jobGenJobLaunchFeat,LOGPATH)

	if os.path.exists(jobEnvelope):
		os.system("rm "+jobEnvelope)
	gen_jobEnvelope(jobEnvelope,LOGPATH)

	if os.path.exists(jobGenerateRegionShape):
		os.system("rm "+jobGenerateRegionShape)
	gen_jobGenerateRegionShape(jobGenerateRegionShape,LOGPATH)

	if os.path.exists(jobRegionByTiles):
		os.system("rm "+jobRegionByTiles)
	gen_jobRegionByTiles(jobRegionByTiles,LOGPATH)

	if os.path.exists(jobExtractactData):
		os.system("rm "+jobExtractactData)
	gen_jobExtractactData(jobExtractactData,LOGPATH)

	if os.path.exists(jobGenJobDataAppVal):
		os.system("rm "+jobGenJobDataAppVal)
	gen_jobGenJobDataAppVal(jobGenJobDataAppVal,LOGPATH)

	if os.path.exists(jobGenCmdStat):
		os.system("rm "+jobGenCmdStat)
	gen_jobGenCmdStat(jobGenCmdStat,LOGPATH)

	if os.path.exists(jobGenJobLaunchStat):
		os.system("rm "+jobGenJobLaunchStat)
	gen_jobGenJobLaunchStat(jobGenJobLaunchStat,LOGPATH)

	if os.path.exists(jobGenCmdTrain):
		os.system("rm "+jobGenCmdTrain)
	gen_jobGenCmdTrain(jobGenCmdTrain,LOGPATH)

	if os.path.exists(jobGenJobLaunchTrain):
		os.system("rm "+jobGenJobLaunchTrain)
	gen_jobGenJobLaunchTrain(jobGenJobLaunchTrain,LOGPATH)

	if os.path.exists(jobGenCmdClass):
		os.system("rm "+jobGenCmdClass)
	gen_jobGenCmdClass(jobGenCmdClass,LOGPATH)

	if os.path.exists(jobGenJobLaunchClass):
		os.system("rm "+jobGenJobLaunchClass)
	gen_jobGenJobLaunchClass(jobGenJobLaunchClass,LOGPATH)

	if os.path.exists(jobClassifShaping):
		os.system("rm "+jobClassifShaping)
	gen_jobClassifShaping(jobClassifShaping,LOGPATH)

	if os.path.exists(jobGenCmdConf):
		os.system("rm "+jobGenCmdConf)
	gen_jobGenCmdConf(jobGenCmdConf,LOGPATH)

	if os.path.exists(jobGenJobLaunchConfusion):
		os.system("rm "+jobGenJobLaunchConfusion)
	gen_jobGenJobLaunchConfusion(jobGenJobLaunchConfusion,LOGPATH)

	if os.path.exists(jobGenResults):
		os.system("rm "+jobGenResults)
	gen_jobGenResults(jobGenResults,LOGPATH)

##################################################################################################################

def launchChain(Fileconfig):

	f = file(Fileconfig)
	cfg = Config(f)
	chainType = cfg.chain.type
	if chainType == "parallel":
		genJobs(Fileconfig)
		pathChain = gen_oso_parallel(Fileconfig)
		print pathChain
		os.system("chmod u+rwx "+pathChain)
		os.system(pathChain)

	elif chainType == "sequential":
		pathChain = gen_oso_sequential(Fileconfig)
		print pathChain
		os.system("chmod u+rwx "+pathChain)
		os.system(pathChain)

	
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you launch oso chain according to a configuration file")
	parser.add_argument("-launch.config",dest = "config",help ="path to configuration file",required=True)
	args = parser.parse_args()

	launchChain(args.config)



















