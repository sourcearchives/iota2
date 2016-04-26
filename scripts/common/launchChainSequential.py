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
import genCmdFeatures as GFD
import os,sys
import fusion as FUS
import noData as ND
import confusionFusion as confFus
import reArrangeModel as RAM
import fileUtils as fu
import shutil

def launchChainSequential(PathTEST, tiles, pathTilesL8, pathTilesL5,pathNewProcessingChain, pathTilesFeat, configFeature, shapeRegion, field_Region, model, shapeData, dataField, pathConf, N, REARRANGE_PATH,MODE,REARRANGE_FLAG,CLASSIFMODE,NOMENCLATURE,COLORTABLE):
    
    if PathTEST!="/" and os.path.exists(PathTEST):
	choice = ""
	while (choice!="yes") and (choice!="no") and (choice!="y") and (choice!="n"):
		choice = raw_input("the path "+PathTEST+" already exist, do you want to remove it ? yes or no : ")
	if (choice == "yes") or (choice == "y"):
    		shutil.rmtree(PathTEST)
	else :
		sys.exit(-1)
    fieldEnv = "FID"#do not change

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
        os.mkdir(PathTEST)
    if not os.path.exists(pathModels):
        os.mkdir(pathModels)
    if not os.path.exists(pathEnvelope):
        os.mkdir(pathEnvelope)
    if not os.path.exists(pathClassif):
        os.mkdir(pathClassif)
    if not os.path.exists(pathTileRegion):
        os.mkdir(pathTileRegion)
    if not os.path.exists(classifFinal):
        os.mkdir(classifFinal)
    if not os.path.exists(dataRegion):
        os.mkdir(dataRegion)
    if not os.path.exists(pathAppVal):
        os.mkdir(pathAppVal)
    if not os.path.exists(pathStats):
        os.mkdir(pathStats)
    if not os.path.exists(cmdPath):
        os.mkdir(cmdPath)
        os.mkdir(cmdPath+"/stats")
        os.mkdir(cmdPath+"/train")
        os.mkdir(cmdPath+"/cla")
        os.mkdir(cmdPath+"/confusion")
        os.mkdir(cmdPath+"/features")
        os.mkdir(cmdPath+"/fusion")

    feat = GFD.CmdFeatures(PathTEST,tiles,pathNewProcessingChain,pathTilesL8,pathTilesL5,pathConf,pathTilesFeat,None)
    for i in range(len(feat)):
        print feat[i]
        os.system(feat[i])

    #Création des enveloppes
    env.GenerateShapeTile(tiles,pathTilesFeat,pathEnvelope,None,configFeature)
    
    if MODE != "outside":
        area.generateRegionShape(MODE,pathEnvelope,model,shapeRegion,field_Region,None)

    #Création des régions par tuiles
    RT.createRegionsByTiles(shapeRegion,field_Region,pathEnvelope,pathTileRegion,None)
    
    #pour tout les fichiers dans pathTileRegion
    regionTile = fu.FileSearch_AND(pathTileRegion,True,".shp")

    #/////////////////////////////////////////////////////////////////////////////////////////
    for path in regionTile:
        ExtDR.ExtractData(path,shapeData,dataRegion,pathTilesFeat,None)
        #/////////////////////////////////////////////////////////////////////////////////////////

    if REARRANGE_FLAG :
        RAM.generateRepartition(PathTEST,pathConf,shapeRegion,REARRANGE_PATH,dataField)
        #pour tout les shape file par tuiles présent dans dataRegion, créer un ensemble dapp et de val
    dataTile = fu.FileSearch_AND(dataRegion,True,".shp")
    #/////////////////////////////////////////////////////////////////////////////////////////
    for path in dataTile:
        RIST.RandomInSituByTile(path,dataField,N,pathAppVal,None)
        #/////////////////////////////////////////////////////////////////////////////////////////

    #/////////////////////////////////////////////////////////////////////////////////////////
    #génération des fichiers de statistiques
    AllCmd = MS.generateStatModel(pathAppVal,pathTilesFeat,pathStats,cmdPath+"/stats",None,configFeature)

    for cmd in AllCmd:
        print cmd
        print ""
        os.system(cmd)
        #/////////////////////////////////////////////////////////////////////////////////////////

    #génération des commandes pour lApp
    allCmd = LT.launchTraining(pathAppVal,pathConf,pathTilesFeat,dataField,pathStats,N,cmdPath+"/train",pathModels,None,None)
    #/////////////////////////////////////////////////////////////////////////////////////////
    for cmd in allCmd:
        print cmd
        print ""
        os.system(cmd)
        #/////////////////////////////////////////////////////////////////////////////////////////


    #génération des commandes pour la classification
    cmdClassif = LC.launchClassification(pathModels,pathConf,pathStats,pathTileRegion,pathTilesFeat,shapeRegion,field_Region,N,cmdPath+"/cla",pathClassif,None)
    #/////////////////////////////////////////////////////////////////////////////////////////
    for cmd in cmdClassif:
        print cmd 
        print ""
        os.system(cmd)
        #/////////////////////////////////////////////////////////////////////////////////////////

    if CLASSIFMODE == "separate":
        #Mise en forme des classifications
        CS.ClassificationShaping(pathClassif,pathEnvelope,pathTilesFeat,fieldEnv,N,classifFinal,None,configFeature,COLORTABLE)

        #génération des commandes pour les matrices de confusions
        allCmd_conf = GCM.genConfMatrix(classifFinal,pathAppVal,N,dataField,cmdPath+"/confusion",configFeature,None)
        for cmd in allCmd_conf:
        	print cmd
        	os.system(cmd)

        confFus.confFusion(shapeData,dataField,classifFinal+"/TMP",classifFinal+"/TMP",classifFinal+"/TMP",configFeature)
        GR.genResults(classifFinal,NOMENCLATURE)
    elif CLASSIFMODE == "fusion" and MODE != "one_region":
        cmdFus = FUS.fusion(pathClassif,configFeature,None)
        for cmd in cmdFus:
            print cmd
            os.system(cmd)

        #gestion des nodata
        fusionFiles = fu.FileSearch_AND(pathClassif,True,"_FUSION_seed_")
        for fusionpath in fusionFiles:
            ND.noData(PathTEST,fusionpath,field_Region,pathTilesFeat,shapeRegion,N,configFeature,None)

        #Mise en forme des classifications
        CS.ClassificationShaping(pathClassif,pathEnvelope,pathTilesFeat,fieldEnv,N,classifFinal,None,configFeature,COLORTABLE)

        #génération des commandes pour les matrices de confusions
        allCmd_conf = GCM.genConfMatrix(classifFinal,pathAppVal,N,dataField,cmdPath+"/confusion",configFeature,None)
        #/////////////////////////////////////////////////////////////////////////////////////////
        for cmd in allCmd_conf:
            print cmd
            os.system(cmd)
            #/////////////////////////////////////////////////////////////////////////////////////////

        confFus.confFusion(shapeData,dataField,classifFinal+"/TMP",classifFinal+"/TMP",classifFinal+"/TMP",configFeature)
        GR.genResults(classifFinal,NOMENCLATURE)

    elif CLASSIFMODE == "fusion" and MODE =="one_region":
        raise Exception("You can't choose the 'one region' mode and use the fusion mode together")

