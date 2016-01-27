#!/usr/bin/python
#-*- coding: utf-8 -*-

import tileEnvelope as env
import tileArea as area
import LaunchTraining as LT
import createRegionsByTiles as RT
import ExtractDataByRegion as ExtDR
import RandomInSituByTile as RIST
import launchClassification as LC
import ClassificationShaping as CS
import genConfusionMatrix as GCM
import ModelStat as MS
import genResults as GR
import genFeaturesData as GFD
import os

"""
	pour qu'une tuile soit classée, elle doit apparaître au moins une fois dans les régions !
	pour qu'une tuile apparatiennent à un modèle, la région du modèle dans la tuile doit contenir des polygônes de données. Dans le cas contraire le modèle ne classera pas la tuile mm si la région est dans la tuile
"""

PathTEST = "/mnt/data/home/vincenta/THEIA_OSO/Test8"

#Test3 -> avec gapfilling otbtest
#Test4 -> idem que test3
#Test5 avec gapfilling dans /home/ingladaj

#Test7 -> avec modif code trouver date BJ
#Test8:test...
os.system("rm -r "+PathTEST)#--------------------------------------------------------------------------------------------------

#tiles = ["D0003H0005","D0004H0005","D0005H0005","D0005H0004","D0003H0004","D0004H0004","D0003H0003","D0004H0003","D0005H0003"]
tiles = ["D0005H0005","D0004H0005","D0005H0004","D0004H0004"]

#tiles = ["D0004H0002","D0004H0003","D0005H0002","D0005H0003"]
pathTilesL8 = "/mnt/MD1200/DONNEES/LANDSAT8/N2_THEIA/"

pathNewProcessingChain = "/mnt/data/home/vincenta/THEIA_OSO/oso"
#pathTilesFeat = "/mnt/data/home/vincenta/THEIA_OSO/IMG_Feat/"
pathTilesFeat = "/mnt/data/home/vincenta/THEIA_OSO/img_feat_test/"
configFeature = "/mnt/data/home/vincenta/THEIA_OSO/conf/ConfigChaineSat_1Tile.cfg"

#shapeRegion = "/mnt/data/home/vincenta/Shape/TestRep.shp"
#field_Region = "id"

#shapeData = "/mnt/data/home/vincenta/Shape/FakeData.shp"
shapeData = "/mnt/MD1200/DONNEES/S2_AGRI/GAPFILLING/FranceSudOuest/RPG/FinalFile/FR_SUD_2013_LC_SM_V4_c.shp"
dataField = "CODE"

#Param de la classif
pathConf = "/mnt/data/home/vincenta/THEIA_OSO/conf/config_test.conf"
N = 1
fieldEnv = "FID"#do not change

#---------------------------------------------------------------------------------------------------------------------------
#------------------------------------   Ne pas modifier la suite du script   -----------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------

#dossier internes
pathModels = PathTEST+"/model"
pathEnvelope = PathTEST+"/envelope"
pathClassif = PathTEST+"/classif"
pathTileRegion = PathTEST+"/shapeRegion"
classifFinal = PathTEST+"/final"
dataRegion = PathTEST+"/dataRegion"
pathAppVal = PathTEST+"/dataAppVal"
pathStats = PathTEST+"/stats"
cmdPath = PathTEST+"/cmd"

if not os.path.exists(PathTEST):
	os.system("mkdir "+PathTEST)
if not os.path.exists(pathModels):
	os.system("mkdir "+pathModels)
if not os.path.exists(pathEnvelope):
	os.system("mkdir "+pathEnvelope)
if not os.path.exists(pathClassif):
	os.system("mkdir "+pathClassif)
if not os.path.exists(pathTileRegion):
	os.system("mkdir "+pathTileRegion)
if not os.path.exists(classifFinal):
	os.system("mkdir "+classifFinal)
if not os.path.exists(dataRegion):
	os.system("mkdir "+dataRegion)
if not os.path.exists(pathAppVal):
	os.system("mkdir "+pathAppVal)
if not os.path.exists(pathStats):
	os.system("mkdir "+pathStats)
if not os.path.exists(cmdPath):
	os.system("mkdir "+cmdPath)
	os.system("mkdir "+cmdPath+"/stats")
	os.system("mkdir "+cmdPath+"/train")
	os.system("mkdir "+cmdPath+"/cla")
	os.system("mkdir "+cmdPath+"/confusion")
	os.system("mkdir "+cmdPath+"/features")

#Génération des primitives 
GFD.genFeaturesData(pathNewProcessingChain,configFeature,pathTilesL8,"","",pathTilesFeat,tiles)

#Création des enveloppes
env.GenerateShapeTile(tiles,pathTilesFeat,pathEnvelope)

#shp de région
shapeRegion = "/mnt/data/home/vincenta/Shape/OneRegion.shp"
field_Region = "id"
model = "/mnt/data/home/vincenta/THEIA_OSO/ShapeLearn/model2.txt"
area.generateRegionShape("one_region",pathEnvelope,model,shapeRegion,field_Region)

#Création des régions par tuiles
RT.createRegionsByTiles(shapeRegion,field_Region,pathEnvelope,pathTileRegion)

#pour tout les fichiers dans pathTileRegion
regionTile = RT.FileSearch_AND(pathTileRegion,".shp")
#/////////////////////////////////////////////////////////////////////////////////////////
for path in regionTile:
	ExtDR.ExtractData(path,shapeData,dataRegion)
#/////////////////////////////////////////////////////////////////////////////////////////


#pour tout les shape file par tuiles présent dans dataRegion, créer un ensemble d'app et de val
dataTile = RT.FileSearch_AND(dataRegion,".shp")
#/////////////////////////////////////////////////////////////////////////////////////////
for path in dataTile:
	RIST.RandomInSituByTile(path,dataField,N,pathAppVal)
#/////////////////////////////////////////////////////////////////////////////////////////


#/////////////////////////////////////////////////////////////////////////////////////////
#génération des fichiers de statistiques
AllCmd = MS.generateStatModel(pathAppVal,pathTilesFeat,pathStats,cmdPath+"/stats")

for cmd in AllCmd:
	print cmd
	print ""
	#os.system(cmd)
#/////////////////////////////////////////////////////////////////////////////////////////

#génération des commandes pour l'App
allCmd = LT.launchTraining(pathAppVal,pathConf,pathTilesFeat,dataField,N,pathStats,cmdPath+"/train",pathModels)
#/////////////////////////////////////////////////////////////////////////////////////////
for cmd in allCmd:
	print cmd
	print ""
	os.system(cmd)
#/////////////////////////////////////////////////////////////////////////////////////////


#génération des commandes pour la classification
cmdClassif = LC.launchClassification(pathModels,pathConf,pathStats,pathTileRegion,pathTilesFeat,shapeRegion,field_Region,N,cmdPath+"/cla",pathClassif)
#/////////////////////////////////////////////////////////////////////////////////////////
for cmd in cmdClassif:
	print cmd 
	print ""
	os.system(cmd)
#/////////////////////////////////////////////////////////////////////////////////////////


#Mise en forme des classifications
CS.ClassificationShaping(pathClassif,pathEnvelope,pathTilesFeat,fieldEnv,N,classifFinal)


#génération des commandes pour les matrices de confusions
allCmd_conf = GCM.genConfMatrix(classifFinal,pathAppVal,N,dataField,cmdPath+"/confusion")
#/////////////////////////////////////////////////////////////////////////////////////////
for cmd in allCmd_conf:
	print cmd
	os.system(cmd)
#/////////////////////////////////////////////////////////////////////////////////////////

GR.genResults(classifFinal,"/mnt/data/home/vincenta/Nomenclature_SudFranceAuch.csv")



#########################
"""
 - tester les différents cas du shp région avec/sans trou (cas 1 -> region type ecoClimatique OK, cas 2 -> multi_region OK, cas 3 -> une seule grosse région OK)
 - écrire la partie analyse des résultats (récup la matrice de conf et le rapport dans classifFinal/TMP)
 - vérifier qu'il n'y est pas de "2" dans les classifs (sinon superposition des classif) Ok
 - trouver une solution aux "No Data" en bord d'image OK

3 - idée de test :
	tester avec un très grand offset (dans tileEnvelope -> subMeter) de NoData pour voir si les performances baissent ce qui justifierai les prioritées
		ou directement changer les priorité ? 

4 - Ajouter la possibilité, au niveau de la classification, de choisir quel model classe quelle région. Comme pour la phase d'apprentissage, avoir le choix 
		4.1 La région est classé par le modèle qui a uniquement appris la région
		4.2 La région est classé par N modèles choisi par l'utilisateur (fusion vote maj)
		4.3 La région est classé par tout les modèles (fusion vote maj)

git clone ssh://vincenta@venuscalc.cesbio.cnes.fr/mnt/data/home/vincenta/THEIA_OSO/oso
scp -r vincenta@linux3-ci.cst.cnes.fr:/ptmp/vincenta/tmp/Test ~/ResCNES
scp vincenta@linux3-ci.cst.cnes.fr:/ptmp/inglada/tuiles/in-situ/FR_SUD_2013_LC_SM_V2.shp ~/ResCNES

scp vincenta@venuscalc:/mnt/MD1200/DONNEES/S2_AGRI/GAPFILLING/FranceSudOuest/RPG/FinalFile/FR_SUDF_LC_SM_2015_V6.shp /home/user13/theia_oso/vincenta/THEIA_OSO/oso
firefox http://gbu:8080 &


Idée pour newprocessingChain:
passer a concatenate les listes déjà calculées pour qu'il ne concatene que celle calculé


#########################










