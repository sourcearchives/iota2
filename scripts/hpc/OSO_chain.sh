#+BEGIN_SRC sh
#!/bin/bash

#Chargement des modules nécessaire pour la création des répertoires et des .py
module load python/2.7.5
module remove xerces/2.7
module load xerces/2.8

#path to python's function
PYPATH=/home/user13/theia_oso/vincenta/THEIA_OSO/oso/oso/scripts/common

#Nomenclature's path
NOMENCLATURE=/home/user13/theia_oso/vincenta/Nomenclature_SudFrance.csv

#job's path
JOBPATH=/home/user13/theia_oso/vincenta/THEIA_OSO/oso/oso/scripts/hpc
#path to features generation application (code de benjamin Tardy)
GENFEATPATH=/home/user13/theia_oso/vincenta/THEIA_OSO/oso/oso/scripts/common

#Emplacement de la classification -> GPFS /!\ ne pas changer le nom de la variable car écrite "en dur" dans les générateurs de job 
TESTPATH=/ptmp/vincenta/tmp/Test4

#liste des tuiles à traiter, pas d'espace avant et après la liste, ne pas faire LISTTILE=" D0004H0002 D0004H0003" ou LISTTILE="D0004H0002 D0004H0003 " ni LISTTILE=" D0004H0002 D0004H0003 "
#LISTTILE="D0003H0003 D0003H0001 D0004H0005 D0006H0004 D0003H0002 D0005H0001 D0006H0005 D0005H0002 D0007H0002 D0003H0004 D0005H0003 D0007H0003 D0003H0005 D0005H0004 D0007H0004 D0004H0001 D0005H0005 D0007H0005 D0004H0002 D0006H0001 D0008H0002 D0004H0003 D0006H0002 D0008H0003 D0004H0004 D0006H0003 D0008H0004"
#LISTTILE="D0004H0002 D0004H0003"
LISTTILE="D0005H0005 D0004H0005"


#Emplacement des tuiles (avec leur primitives)
TILEPATH=/ptmp/vincenta/TILES
#TILEPATH=/ptmp/vincenta/tmp
#Emplacement des tuiles L8
L8PATH=/ptmp/inglada/tuiles/2013
#Emplacement des tuiles Sentinel 2
S2PATH=/
#Emplacement des tuiles Sentinel 1
S1PATH=/
#fichier de configuration pour la génération des primitives
FEATCONFIG=~/THEIA_OSO/oso/featConfig.conf

#ground truth path
#GROUNDTRUTH=/ptmp/inglada/tuiles/in-situ/FR_SUD_2013_LC_SM_V2.shp
GROUNDTRUTH=/ptmp/vincenta/groundTruth/FR_SUD_2013_LC_SM_V4_c.shp

#data field
DATAFIELD=CODE

#nb sample
Nsample=1

#configFile
CONFIG=~/THEIA_OSO/oso/config_test.conf

#region's shapefile definition
#	if the region shape comes from an other source, you don't have to use MODE and MODEL, but you must specify REGIONFIELD 
#       and PATHREGION. Also, you musn't use the the job generateRegionShape.pbs

MODE=one_region
MODEL=/home/user13/theia_oso/vincenta/THEIA_OSO/oso/model_1.txt
REGIONFIELD=region
PATHREGION=/ptmp/vincenta/tmp/Test4/OneRegion.shp

export PYPATH
export JOBPATH
export TESTPATH
export TILEPATH
export GROUNDTRUTH
export DATAFIELD
export Nsample
export CONFIG
export MODE
export MODEL
export REGIONFIELD
export PATHREGION
export NOMENCLATURE
export LISTTILE
export GENFEATPATH
export FEATCONFIG
export L8PATH
# ------------------------------------------ DO NOT MODIFY THE SCRIPT BELOW
#suppression des jobArray
JOBEXTRACTDATA=$JOBPATH/extractData.pbs
if [ -f "$JOBEXTRACTDATA" ]
	then
		rm $JOBEXTRACTDATA
	fi
JOBDATAAPPVAL=$JOBPATH/dataAppVal.pbs
if [ -f "$JOBDATAAPPVAL" ]
	then
		rm $JOBDATAAPPVAL
	fi
JOBLAUNCHSTAT=$JOBPATH/launchStats.pbs
if [ -f "$JOBLAUNCHSTAT" ]
	then
		rm $JOBLAUNCHSTAT
	fi
JOBLAUNCHTRAIN=$JOBPATH/launchTrain.pbs
if [ -f "$JOBLAUNCHTRAIN" ]
	then
		rm $JOBLAUNCHTRAIN
	fi
JOBLAUNCHCLASSIF=$JOBPATH/launchClassif.pbs
if [ -f "$JOBLAUNCHCLASSIF" ]
	then
		rm $JOBLAUNCHCLASSIF
	fi
JOBLAUNCHCONFUSION=$JOBPATH/launchConf.pbs
if [ -f "$JOBLAUNCHCONFUSION" ]
	then
		rm $JOBLAUNCHCONFUSION
	fi
JOBEXTRACTFEATURES=$JOBPATH/extractfeatures.pbs
if [ -f "$JOBEXTRACTFEATURES" ]
	then
		rm $JOBEXTRACTFEATURES
	fi

<<'END'
#Création des répertoires pour la classification
python $PYPATH/oso_directory.py -root $TESTPATH

#génération des commandes pour calculer les primitives si nécessaire

id_cmdLaunchFeat=$(qsub -V genCmdFeatures.pbs)
id_pyLaunchFeat=$(qsub -V -W depend=afterok:$id_cmdLaunchFeat genJobLaunchFeat.pbs)

flag=0
while [ $flag -le 0 ]
do
	if [ -f "$JOBEXTRACTFEATURES" ]
	then
		flag=1
		id_extractFeat=$(qsub -V extractfeatures.pbs)
	fi
done

#Création des enveloppes
id_env=$(qsub -V -W depend=afterok:$id_extractFeat envelope.pbs)

#Création du shape de région
id_reg=$(qsub -V -W depend=afterok:$id_env generateRegionShape.pbs)

#Création des régions par tuiles
id_regTile=$(qsub -V -W depend=afterok:$id_reg regionsByTiles.pbs)

#Ecriture du job extractData.pbs
id_pyExtract=$(qsub -V -W depend=afterok:$id_regTile genJobExtractData.pbs)

#Extraction des data/tuiles/régions lorsque le job extractData.pbs est généré
flag=0
while [ $flag -le 0 ]
do
	if [ -f "$JOBEXTRACTDATA" ]
	then
		flag=1
		id_extractData=$(qsub -V extractData.pbs)
	fi
done

#Ecriture du jobdataAppVal.pbs
id_pyDataAppVal=$(qsub -V -W depend=afterok:$id_extractData genJobDataAppVal.pbs)

#Séparation en ensemble d'app/val lorsque le job dataAppVal.pbs est généré
flag=0
while [ $flag -le 0 ]
do
	if [ -f "$JOBDATAAPPVAL" ]
	then
		flag=1
		id_appVal=$(qsub -V dataAppVal.pbs)
	fi
done

#génération et lancement des commandes pour calculer les stats 
id_cmdGenStats=$(qsub -V -W depend=afterok:$id_appVal genCmdStats.pbs)
id_pyLaunchStats=$(qsub -V -W depend=afterok:$id_cmdGenStats genJobLaunchStat.pbs)

flag=0
while [ $flag -le 0 ]
do
	if [ -f "$JOBLAUNCHSTAT" ]
	then
		flag=1
		id_launchStat=$(qsub -V launchStats.pbs)
	fi
done

#génération et lancement des commandes pour l'apprentissage
id_cmdTrain=$(qsub -V -W depend=afterok:$id_launchStat genCmdTrain.pbs)
id_pyLaunchTrain=$(qsub -V -W depend=afterok:$id_cmdTrain genJobLaunchTrain.pbs)

flag=0
while [ $flag -le 0 ]
do
	if [ -f "$JOBLAUNCHTRAIN" ]
	then
		flag=1
		id_launchTrain=$(qsub -V launchTrain.pbs)
	fi
done
END

#génération et lancement des commandes pour la classification ->réécriture du .pbs avec py
#id_cmdClass=$(qsub -V -W depend=afterok:$id_launchTrain genCmdClass.pbs)
id_cmdClass=$(qsub -V genCmdClass.pbs)
id_pyLaunchClass=$(qsub -V -W depend=afterok:$id_cmdClass genJobLaunchClass.pbs)

flag=0
while [ $flag -le 0 ]
do
	if [ -f "$JOBLAUNCHCLASSIF" ]
	then
		flag=1
		id_launchClassif=$(qsub -V launchClassif.pbs)
	fi
done
<<'END'
#Mise en forme des classifications
id_ClassifShaping=$(qsub -V -W depend=afterok:$id_launchClassif classifShaping.pbs)


#génération des commandes pour les matrices de confusions
id_CmdConfMatrix=$(qsub -V -W depend=afterok:$id_ClassifShaping genCmdConf.pbs)
id_pyLaunchConf=$(qsub -V -W depend=afterok:$id_CmdConfMatrix genJobLaunchConfusion.pbs)
flag=0
while [ $flag -le 0 ]
do
	if [ -f "$JOBLAUNCHCONFUSION" ]
	then
		flag=1
		id_launchConfusion=$(qsub -V launchConf.pbs)
	fi
done

#génération des résultats
id_res=$(qsub -V -W depend=afterok:$id_launchConfusion genResults.pbs)


END
























#+END_SRC




























