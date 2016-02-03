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

PathTEST = "/mnt/data/home/vincenta/THEIA_OSO/Test10"

#Test9 contient la classification qui a servi à la comparaison avec celle de marcela

os.system("rm -r "+PathTEST)#--------------------------------------------------------------------------------------------------

#tiles = ["D0003H0005","D0004H0005","D0005H0005","D0005H0004","D0003H0004","D0004H0004","D0003H0003","D0004H0003","D0005H0003"]
tiles = ["D0005H0005","D0004H0005","D0005H0004","D0004H0004"]

pathTilesL8 = "/mnt/MD1200/DONNEES/LANDSAT8/N2_THEIA/"

pathNewProcessingChain = "/mnt/data/home/vincenta/THEIA_OSO/oso"
#pathTilesFeat = "/mnt/data/home/vincenta/THEIA_OSO/IMG_Feat/"
pathTilesFeat = "/mnt/data/home/vincenta/THEIA_OSO/img_feat_test/"
configFeature = "/mnt/data/home/vincenta/THEIA_OSO/conf/ConfigChaineSat_1Tile.cfg"

#shapeRegion = "/mnt/data/home/vincenta/Shape/TestRep.shp"
#field_Region = "id"
shapeRegion = "/mnt/data/home/vincenta/Shape/OneRegion.shp"
field_Region = "id"
model = "/mnt/data/home/vincenta/THEIA_OSO/ShapeLearn/model2.txt"

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










