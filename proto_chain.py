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
import os

"""
	pour qu'une tuile soit classée, elle doit apparaître au moins une fois dans les régions !
	pour qu'une tuile apparatiennent à un modèle, la région du modèle dans la tuile doit contenir des polygônes de données. Dans le cas contraire le modèle ne classera pas la tuile mm si la région est dans la tuile
"""

#########################################################################

#pour phase de tests
os.system("rm -r ~/THEIA_OSO/Test/dataAppVal")
os.system("mkdir ~/THEIA_OSO/Test/dataAppVal")
os.system("rm -r ~/THEIA_OSO/Test/dataRegion")
os.system("mkdir ~/THEIA_OSO/Test/dataRegion")
os.system("rm -r ~/THEIA_OSO/Test/shapeRegion")
os.system("mkdir ~/THEIA_OSO/Test/shapeRegion")
os.system("rm -r ~/THEIA_OSO/Test/model")
os.system("mkdir ~/THEIA_OSO/Test/model")
os.system("rm -r ~/THEIA_OSO/Test/classif")
os.system("mkdir ~/THEIA_OSO/Test/classif")
os.system("rm -r ~/THEIA_OSO/Test/final")
os.system("mkdir ~/THEIA_OSO/Test/final")
os.system("rm -r ~/THEIA_OSO/Test/envelope")
os.system("mkdir ~/THEIA_OSO/Test/envelope")
os.system("rm -r ~/THEIA_OSO/Test/stats")
os.system("mkdir ~/THEIA_OSO/Test/stats")

#########################################################################

#tiles = ["D0003H0005","D0004H0005","D0005H0005","D0005H0004","D0003H0004","D0004H0004","D0003H0003","D0004H0003","D0005H0003"]
tiles = ["D0003H0005","D0004H0005","D0005H0005","D0005H0004","D0003H0004","D0004H0004","D0003H0003","D0004H0003","D0005H0003"]
pathTiles = "/mnt/MD1200/DONNEES/S2_AGRI/GAPFILLING/FranceSudOuest"

#shapeRegion = "/mnt/data/home/vincenta/Shape/TestRep.shp"
#field_Region = "id"

shapeData = "/mnt/data/home/vincenta/Shape/FakeData.shp"
#shapeData = "/mnt/MD1200/DONNEES/S2_AGRI/GAPFILLING/FranceSudOuest/RPG/FinalFile/FR_SUDF_LC_SM_2015_V6.shp"
dataField = "CODE"

#dossier internes
pathModels = "/mnt/data/home/vincenta/THEIA_OSO/Test/model"
pathEnvelope = "/mnt/data/home/vincenta/THEIA_OSO/Test/envelope"
pathClassif = "/mnt/data/home/vincenta/THEIA_OSO/Test/classif"
pathTileRegion = "/mnt/data/home/vincenta/THEIA_OSO/Test/shapeRegion"
classifFinal = "/mnt/data/home/vincenta/THEIA_OSO/Test/final"
dataRegion = "/mnt/data/home/vincenta/THEIA_OSO/Test/dataRegion"
pathAppVal = "/mnt/data/home/vincenta/THEIA_OSO/Test/dataAppVal"
pathStats = "/mnt/data/home/vincenta/THEIA_OSO/Test/stats"

#Param de la classif
pathConf = "/mnt/data/home/vincenta/THEIA_OSO/conf/config_test.conf"
N = 2
fieldEnv = "FID"#do not change

#Création des enveloppes
env.GenerateShapeTile(tiles,pathTiles,pathEnvelope)

#Création du shp de région
shapeRegion = "/mnt/data/home/vincenta/Shape/MultiRegion.shp"
field_Region = "id"
model = "/mnt/data/home/vincenta/THEIA_OSO/ShapeLearn/model2.txt"
area.generateRegionShape("multi_regions",pathEnvelope,model,shapeRegion,field_Region)

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
AllCmd = MS.generateStatModel(pathAppVal,pathTiles,pathStats)
for cmd in AllCmd:
	print cmd
	print ""
	os.system(cmd)
#/////////////////////////////////////////////////////////////////////////////////////////


#génération des commandes pour l'App
allCmd = LT.launchTraining(pathAppVal,pathConf,pathTiles,dataField,N,pathStats,pathModels)
#/////////////////////////////////////////////////////////////////////////////////////////
for cmd in allCmd:
	print cmd
	print ""
	os.system(cmd)
#/////////////////////////////////////////////////////////////////////////////////////////


#génération des commandes pour la classification
cmdClassif = LC.launchClassification(pathModels,pathConf,pathStats,pathTileRegion,pathTiles,shapeRegion,field_Region,N,pathClassif)
#/////////////////////////////////////////////////////////////////////////////////////////
for cmd in cmdClassif:
	print cmd 
	print ""
	os.system(cmd)
#/////////////////////////////////////////////////////////////////////////////////////////


#Mise en forme des classifications
CS.ClassificationShaping(pathClassif,pathEnvelope,pathTiles,fieldEnv,N,classifFinal)


#génération des commandes pour les matrices de confusions
allCmd_conf = GCM.genConfMatrix(classifFinal,pathAppVal,N,dataField)
#/////////////////////////////////////////////////////////////////////////////////////////
for cmd in allCmd_conf:
	print cmd
	os.system(cmd)
#/////////////////////////////////////////////////////////////////////////////////////////




#########################
"""
 - tester les différents cas du shp région avec/sans trou (cas 1 -> region type ecoClimatique OK, cas 2 -> multi_region OK, cas 3 -> une seule grosse région OK)
 - écrire la partie analyse des résultats (récup la matrice de conf et le rapport dans classifFinal/TMP)
 - vérifier qu'il n'y est pas de "2" dans les classifs (sinon superposition des classif) Ok
 - trouver une solution aux "No Data" en bord d'image OK

1 - pb avec le mode multi model - tuiles :
	actuellement, un modèle constitué des tuiles 1 et 2 ne classera que ces tuiles... il faut classer tte les tuiles et faire une fusion ?

2 - ajouter l'écriture des commandes dans un fichier texte comment ca marche avec pbs ??
	Extraction des data/tuiles/régions
	Création d'un ensemble d'app/Val pour tte les data/tuiles/régions
	App
	classif
	génération des matrices de conf

3 - idée de test :
	tester avec un très grand offset (dans tileEnvelope -> subMeter) de NoData pour voir si les performances baissent ce qui justifierai les prioritées
		ou directement changer les priorité ? 
		
4 - ajouter la génération des fichiers de stats et leur prise en compte dans les classif si le classifieur choisi n'est pas SVM -> et comparer des résultats entre rf/svm
"""
#########################

























