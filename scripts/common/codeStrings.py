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


parallelChainStep1='\
#!/bin/bash\n\
\n\
#Chargement des modules nécessaire pour la création des répertoires et des .py\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
\n\
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
#Emplacement des tuiles L5\n\
L5PATH=%s\n\
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
REARRANGE_PATH=%s\n\
COLORTABLE=%s\n\
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
export L5PATH\n\
export LOGPATH\n\
export REARRANGE_PATH\n\
export COLORTABLE\n\
\n\
#suppression des jobArray\n\
JOBSPLITSHAPE=$JOBPATH/splitShape.pbs\n\
if [ -f "$JOBSPLITSHAPE" ]\n\
	then\n\
		rm $JOBSPLITSHAPE\n\
	fi\n\
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
JOBLAUNCHFUSION=$JOBPATH/fusion.pbs\n\
if [ -f "$JOBLAUNCHFUSION" ]\n\
	then\n\
		rm $JOBLAUNCHFUSION\n\
	fi\n\
JOBNODATA=$JOBPATH/noData.pbs\n\
if [ -f "$JOBNODATA" ]\n\
	then\n\
		rm $JOBNODATA\n\
	fi\n\
#Création des répertoires pour la classification\n\
python $PYPATH/oso_directory.py -root $TESTPATH\n\
\n\
#génération des commandes pour calculer les primitives si nécessaire\n\
\n\
id_cmdLaunchFeat=$(qsub genCmdFeatures.pbs)\n\
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
'

parallelChainStep2 = '\
#Création du shape de région\n\
id_reg=$(qsub -V -W depend=afterok:$id_env generateRegionShape.pbs)\n\
\n\
#Création des régions par tuiles\n\
id_regTile=$(qsub -V -W depend=afterok:$id_reg regionsByTiles.pbs)\n\
'

parallelChainStep3 = '\
#Création des régions par tuiles\n\
id_regTile=$(qsub -V -W depend=afterok:$id_env regionsByTiles.pbs)\n\
'

parallelChainStep4 = '\
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
'
parallelChainStep5 = '\
#split shape\n\
id_CmdsplitShape=$(qsub -V -W depend=afterok:$id_appVal genCmdsplitShape.pbs)\n\
id_genJobsplitShape=$(qsub -V -W depend=afterok:$id_CmdsplitShape genJobsplitShape.pbs)\n\
flag=0\n\
while [ $flag -le 0 ]\n\
do\n\
	if [ -f "$JOBSPLITSHAPE" ]\n\
	then\n\
		flag=1\n\
		id_splitShape=$(qsub -V splitShape.pbs)\n\
	fi\n\
done\n\
\n\
#génération et lancement des commandes pour calculer les stats\n\
id_cmdGenStats=$(qsub -V -W depend=afterok:$id_splitShape genCmdStats.pbs)\n\
'

parallelChainStep6 = '\
#ré-arrangement de la distribution des tuiles par modèles\n\
id_rearrange=$(qsub -V -W depend=afterok:$id_appVal reArrangeModel.pbs)\n\
\n\
#génération et lancement des commandes pour calculer les stats\n\
id_cmdGenStats=$(qsub -V -W depend=afterok:$id_rearrange genCmdStats.pbs)\n\
'

parallelChainStep7 = '\
id_cmdGenStats=$(qsub -V -W depend=afterok:$id_appVal genCmdStats.pbs)\n\
'

parallelChainStep8 = '\
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
#remove core file\n\
coreFile=($(find ~/ -maxdepth 5 -type f -name "core.*"))\n\
COUNTER=0\n\
while [  $COUNTER -lt ${#coreFile[@]} ]; do\n\
	rm ${coreFile[$COUNTER]}\n\
	let COUNTER=COUNTER+1\n\
done\n\
\n\
'

parallelChainStep9 = '\
#Mise en forme des classifications\n\
id_ClassifShaping=$(qsub -V -W depend=afterany:$id_launchClassif classifShaping.pbs)\n\
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
#confusion fusion\n\
id_fusConf=$(qsub -V -W depend=afterok:$id_launchConfusion fusionConfusion.pbs)\n\
#génération des résultats\n\
id_res=$(qsub -V -W depend=afterok:$id_fusConf genResults.pbs)\n\
\n\
'

parallelChainStep10 = '\
#génération des commandes pour la fusion, création du job pour lancer les fusion, lancement des fusions\n\
id_cmdFusion=$(qsub -V -W depend=afterany:$id_launchClassif genCmdFusion.pbs)\n\
id_pyLaunchFusion=$(qsub -V -W depend=afterok:$id_cmdFusion genJobLaunchFusion.pbs)\n\
flag=0\n\
while [ $flag -le 0 ]\n\
do\n\
	if [ -f "$JOBLAUNCHFUSION" ]\n\
	then\n\
		flag=1\n\
		id_launchFusion=$(qsub -V fusion.pbs)\n\
	fi\n\
done\n\
\n\
#Gestion des noData dans la fusion\n\
id_pyNoData=$(qsub -V -W depend=afterok:$id_launchFusion genJobNoData.pbs)\n\
\n\
flag=0\n\
while [ $flag -le 0 ]\n\
do\n\
	if [ -f "$JOBNODATA" ]\n\
	then\n\
		flag=1\n\
		id_NoData=$(qsub -V noData.pbs)\n\
	fi\n\
done\n\
\n\
#Mise en forme des classifications\n\
id_ClassifShaping=$(qsub -V -W depend=afterok:$id_NoData classifShaping.pbs)\n\
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
#confusion fusion\n\
id_fusConf=$(qsub -V -W depend=afterok:$id_launchConfusion fusionConfusion.pbs)\n\
#génération des résultats\n\
id_res=$(qsub -V -W depend=afterok:$id_fusConf genResults.pbs)\n\
\n\
#+END_SRC\n\
'

jobGenCmdFeatures='\
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
FileConfig=%s\n\
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" $FileConfig | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
TESTPATH=$(grep --only-matching --perl-regex "(?<=outputPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
LISTTILE=$(grep --only-matching --perl-regex "(?<=listTile\:).*" $FileConfig | cut -d "\'" -f 2)\n\
GENFEATPATH=$(grep --only-matching --perl-regex "(?<=pyAppPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
TILEPATH=$(grep --only-matching --perl-regex "(?<=featuresPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
L8PATH=$(grep --only-matching --perl-regex "(?<=L8Path\:).*" $FileConfig | cut -d "\'" -f 2)\n\
L5PATH=$(grep --only-matching --perl-regex "(?<=L5Path\:).*" $FileConfig | cut -d "\'" -f 2)\n\
FEATCONFIG=$(grep --only-matching --perl-regex "(?<=featuresPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
PYPATH=$(grep --only-matching --perl-regex "(?<=pyAppPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
cd $PYPATH\n\
\n\
python genCmdFeatures.py -path.test $TESTPATH -tiles $LISTTILE -path.application $GENFEATPATH -path.out $TILEPATH --path.L8 $L8PATH --path.L5 $L5PATH -path.config $FEATCONFIG --wd $TMPDIR\n\
\n\
'

jobGenJobLaunchFeat='\
#!/bin/bash\n\
#PBS -N genJob_L_Feat\n\
#PBS -l select=1:ncpus=5:mem=100mb\n\
#PBS -l walltime=00:10:00\n\
#PBS -o %s/genJobLaunchFeatures_out.log\n\
#PBS -e %s/genJobLaunchFeatures_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xercesf/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
cd $PYPATH\n\
\n\
python genJobLaunchFeat.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH -conf $CONFIG\n\
\n\
'

jobEnvelope='\
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
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
cd $PYPATH\n\
\n\
python tileEnvelope.py -t $LISTTILE -t.path $TILEPATH -out $TESTPATH/envelope --wd $TMPDIR -conf $CONFIG\n\
\n\
'

jobGenerateRegionShape='\
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
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
cd $PYPATH\n\
\n\
python tileArea.py -conf $CONFIG -pathTiles $TESTPATH/envelope -mode $MODE -fieldOut $REGIONFIELD --multi.models $MODEL -out $PATHREGION --wd $TMPDIR\n\
\n\
'

jobRegionByTiles='\
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
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
cd $PYPATH\n\
\n\
python createRegionsByTiles.py -region.shape $PATHREGION -region.field $REGIONFIELD -tiles.envelope $TESTPATH/envelope -out $TESTPATH/shapeRegion --wd $TMPDIR\n\
\n\
'

jobExtractactData='\
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
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
cd $PYPATH\n\
\n\
python genJobExtractData.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH -conf $CONFIG\n\
\n\
'

jobGenJobDataAppVal='\
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
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
cd $PYPATH\n\
\n\
python genJobDataAppVal.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH -conf $CONFIG\n\
\n\
'

jobCmdSplitShape='\
#!/bin/bash\n\
#PBS -N CmdSplitShape\n\
#PBS -l select=1:ncpus=1:mem=4000mb\n\
#PBS -l walltime=01:00:00\n\
#PBS -o %s/CmdSplitShape_out.log\n\
#PBS -e %s/CmdSplitShape_err.log\n\
\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
cd $PYPATH\n\
\n\
python genCmdSplitShape.py -config $CONFIG\n\
\n\
'

jobGenJobSplitShape='\
#!/bin/bash\n\
#PBS -N genJobSplitShape\n\
#PBS -l select=1:ncpus=1:mem=4000mb\n\
#PBS -l walltime=00:10:00\n\
#PBS -o %s/genJobSplitShape_out.log\n\
#PBS -e %s/genJobSplitShape_err.log\n\
\n\
module load python/2.7.5\n\
module remove xerces/2.7\n\
module load xerces/2.8\n\
module load gdal/1.11.0-py2.7\n\
\n\
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
cd $PYPATH\n\
\n\
python genJobSplitShape.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH -conf $CONFIG\n\
\n\
'

jobRearrange='\
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
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
cd $PYPATH\n\
\n\
python reArrangeModel.py -path.test $TESTPATH -conf $CONFIG -repartition.in $MODEL -repartition.out $REARRANGE_PATH -data.field $DATAFIELD\n\
'

jobGenCmdStat='\
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
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
cd $PYPATH\n\
\n\
python ModelStat.py -shapesIn $TESTPATH/dataAppVal -tiles.path $TILEPATH -Stats.out $TESTPATH/stats -Stat.out.cmd $TESTPATH/cmd/stats --wd $TMPDIR -conf $CONFIG\n\
\n\
'

jobGenJobLaunchFusion='\
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
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
cd $PYPATH\n\
\n\
python genJobLaunchFusion.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH -conf $CONFIG\n\
\n\
'

jobGenJobLaunchStat='\
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
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
cd $PYPATH\n\
\n\
python genJobLaunchStat.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH -conf $CONFIG\n\
\n\
'

jobGenCmdTrain='\
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
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
cd $PYPATH\n\
\n\
#python LaunchTraining.py -shapesIn $TESTPATH/dataAppVal -conf $CONFIG -tiles.path $TILEPATH -data.field $DATAFIELD -N $Nsample -train.out.cmd $TESTPATH/cmd/train -out $TESTPATH/model --wd $TMPDIR\n\
python LaunchTraining.py --path.log $LOGPATH --stat $TESTPATH/stats -shapesIn $TESTPATH/dataAppVal -conf $CONFIG -tiles.path $TILEPATH -data.field $DATAFIELD -N $Nsample -train.out.cmd $TESTPATH/cmd/train -out $TESTPATH/model\n\
\n\
'

jobGenJobLaunchTrain='\
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
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
cd $PYPATH\n\
\n\
python genJobLaunchTrain.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH -conf $CONFIG\n\
\n\
'

jobGenCmdClass='\
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
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
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
'

jobGenJobLaunchClass='\
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
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
cd $PYPATH\n\
\n\
python genJobLaunchClassif.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH -conf $CONFIG\n\
\n\
'

jobCmdFusion='\
#!/bin/bash\n\
#PBS -N genCmdFusion\n\
#PBS -l select=1:ncpus=1:mem=4000mb\n\
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
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
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
'

jobGenJobNoData='\
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
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
cd $PYPATH\n\
\n\
python genJobNoData.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH -conf $CONFIG\n\
\n\
'

jobClassifShaping='\
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
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
cd $PYPATH\n\
\n\
python ClassificationShaping.py -color $COLORTABLE -path.classif $TESTPATH/classif -path.envelope $TESTPATH/envelope -path.img $TILEPATH -field.env FID -N $Nsample -path.out $TESTPATH/final --wd $TMPDIR -conf $CONFIG\n\
\n\
'

jobGenCmdConf='\
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
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
cd $PYPATH\n\
\n\
python genConfusionMatrix.py -path.classif $TESTPATH/final -path.valid $TESTPATH/dataAppVal -N $Nsample -data.field $DATAFIELD -confusion.out.cmd $TESTPATH/cmd/confusion --wd $TMPDIR -conf $CONFIG\n\
\n\
'

jobGenJobLaunchConfusion='\
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
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
cd $PYPATH\n\
\n\
python genJobLaunchConfusion.py -path.job $JOBPATH -path.test $TESTPATH -path.log $LOGPATH -conf $CONFIG\n\
\n\
'

jobfusionConfusion='\
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
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
cd $PYPATH\n\
\n\
python confusionFusion.py -path.shapeIn $GROUNDTRUTH -dataField $DATAFIELD -path.csv.out $TESTPATH/final/TMP -path.txt.out $TESTPATH/final/TMP -path.csv $TESTPATH/final/TMP -conf $CONFIG\n\
\n\
'

jobGenResults='\
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
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" %s | cut -d "\'" -f 2)\n\
export PATH=${OTB_HOME}/bin:$PATH\n\
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}\n\
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}\n\
export GDAL_DATA=${OTB_HOME}/share/gdal\n\
export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv\n\
\n\
cd $PYPATH\n\
\n\
python genResults.py -path.res $TESTPATH/final -path.nomenclature $NOMENCLATURE\n\
\n\
'
