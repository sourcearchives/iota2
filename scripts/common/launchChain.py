#!/usr/bin/python
#-*- coding: utf-8 -*-

import argparse,os
from config import Config


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
'%(JOBPATH,PYPATH,NOMENCLATURE,JOBPATH,PYPATH,TESTPATH,LISTTILE,TILEPATH,L8PATH,S2PATH,S1PATH,Fileconfig,GROUNDTRUTH,DATAFIELD,Nsample,Fileconfig,MODE,MODEL,REGIONFIELD,PATHREGION))
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
feat = GFD.genCmdFeatures(PathTEST,tiles,PYPATH,pathTilesL8,pathConf,pathTilesFeat,None)\n\
for i in range(len(feat)):\n\
	print feat[i]\n\
	os.system(feat[i])\n\
#Création des enveloppes\n\
env.GenerateShapeTile(tiles,pathTilesFeat,pathEnvelope)\n\
\n\
'%(TESTPATH,LISTTILE,L8PATH,PYPATH,TILEPATH,Fileconfig,PATHREGION,REGIONFIELD,MODEL,GROUNDTRUTH,DATAFIELD,Fileconfig,Nsample))
	if MODE != "outside":
		chainFile.write('\
area.generateRegionShape("%s",pathEnvelope,model,shapeRegion,field_Region)\n\
\
'%(MODE))
	chainFile.write('\
#Création des régions par tuiles\n\
RT.createRegionsByTiles(shapeRegion,field_Region,pathEnvelope,pathTileRegion)\n\
\n\
#pour tout les fichiers dans pathTileRegion\n\
regionTile = RT.FileSearch_AND(pathTileRegion,".shp")\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
for path in regionTile:\n\
	ExtDR.ExtractData(path,shapeData,dataRegion)\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
\n\
\n\
#pour tout les shape file par tuiles présent dans dataRegion, créer un ensemble dapp et de val\n\
dataTile = RT.FileSearch_AND(dataRegion,".shp")\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
for path in dataTile:\n\
	RIST.RandomInSituByTile(path,dataField,N,pathAppVal)\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
\n\
\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
#génération des fichiers de statistiques\n\
AllCmd = MS.generateStatModel(pathAppVal,pathTilesFeat,pathStats,cmdPath+"/stats")\n\
\n\
for cmd in AllCmd:\n\
	print cmd\n\
	print ""\n\
	#os.system(cmd)\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
\n\
#génération des commandes pour lApp\n\
allCmd = LT.launchTraining(pathAppVal,pathConf,pathTilesFeat,dataField,N,pathStats,cmdPath+"/train",pathModels)\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
for cmd in allCmd:\n\
	print cmd\n\
	print ""\n\
	os.system(cmd)\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
\n\
\n\
#génération des commandes pour la classification\n\
cmdClassif = LC.launchClassification(pathModels,pathConf,pathStats,pathTileRegion,pathTilesFeat,shapeRegion,field_Region,N,cmdPath+"/cla",pathClassif)\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
for cmd in cmdClassif:\n\
	print cmd \n\
	print ""\n\
	os.system(cmd)\n\
#/////////////////////////////////////////////////////////////////////////////////////////\n\
\n\
#Mise en forme des classifications\n\
CS.ClassificationShaping(pathClassif,pathEnvelope,pathTilesFeat,fieldEnv,N,classifFinal)\n\
\n\
#génération des commandes pour les matrices de confusions\n\
allCmd_conf = GCM.genConfMatrix(classifFinal,pathAppVal,N,dataField,cmdPath+"/confusion")\n\
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
def launchChain(Fileconfig):

	f = file(Fileconfig)
	cfg = Config(f)
	chainType = cfg.chain.type
	if chainType == "parallel":
		pathChain = gen_oso_parallel(Fileconfig)
		print pathChain
		os.system("chmod u+rwx "+pathChain)
		os.system(pathChain)
	elif chainType == "sequential":
		pathChain = gen_oso_sequential(Fileconfig)

	
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you launch oso chain according to a configuration file")
	parser.add_argument("-launch.config",dest = "config",help ="path to configuration file",required=True)
	args = parser.parse_args()

	launchChain(args.config)



















