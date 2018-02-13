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

import outStats as OutS
import mergeOutStats as MOutS
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
import os,sys,time
import fusion as FUS
import noData as ND
import confusionFusion as confFus
import reArrangeModel as RAM
import fileUtils as fu
import genCmdSplitShape as genCmdSplitS
import vectorSampler as vs
import vectorSamplesMerge as VSM
import shutil
import prepareStack as PS
import oso_directory as directory
import formatting_vectors as FV
from config import Config
from Utils import run

def launchChainSequential(cfg):
    
    # get variable from configuration file
    PathTEST = cfg.getParam('chain', 'outputPath')
    TmpTiles = cfg.getParam('chain', 'listTile')
    tiles = TmpTiles.split(" ")
    pathTilesL8 = cfg.getParam('chain', 'L8Path')
    pathTilesL5 = cfg.getParam('chain', 'L5Path')
    pathTilesS2 = cfg.getParam('chain', 'S2Path')
    pathNewProcessingChain = cfg.getParam('chain', 'pyAppPath')
    pathTilesFeat = cfg.getParam('chain', 'featuresPath')
    shapeRegion = cfg.getParam('chain', 'regionPath')
    field_Region = cfg.getParam('chain', 'regionField')
    model = cfg.getParam('chain', 'model')
    shapeData = cfg.getParam('chain', 'groundTruth')
    dataField = cfg.getParam('chain', 'dataField')
    N = cfg.getParam('chain', 'runs')
    REARRANGE_PATH = cfg.getParam('argTrain', 'rearrangeModelTile_out')
    MODE = cfg.getParam('chain', 'mode')
    REARRANGE_FLAG = cfg.getParam('argTrain', 'rearrangeModelTile')
    CLASSIFMODE = cfg.getParam('argClassification', 'classifMode')
    NOMENCLATURE = cfg.getParam('chain', 'nomenclaturePath')
    COLORTABLE = cfg.getParam('chain', 'colorTable')
    RATIO = cfg.getParam('chain', 'ratio')
    TRAIN_MODE = cfg.getParam('argTrain', 'shapeMode')
    
    """
    if PathTEST!="/" and os.path.exists(PathTEST):
        choice = ""
        while (choice!="yes") and (choice!="no") and (choice!="y") and (choice!="n"):
            choice = raw_input("the path "+PathTEST+" already exist, do you want to remove it ? yes or no : ")
        if (choice == "yes") or (choice == "y"):
            shutil.rmtree(PathTEST)
        else :
            sys.exit(-1)
    """
    timingLog = PathTEST+"/timingLog.txt"
    startIOTA = time.time()
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
    config_model = PathTEST+"/config_model"
    """
    directory.GenerateDirectories(PathTEST)
    
    #Création des masks d'emprise commune
    for tile in tiles:
        fu.getCommonMasks(tile, cfg, None)

    startGT = time.time()
    #Création des enveloppes
    env.GenerateShapeTile(tiles, pathTilesFeat, pathEnvelope, None, cfg)

    if MODE != "outside":
        area.generateRegionShape(MODE, pathEnvelope, model, shapeRegion, field_Region, cfg, None)

    #Création des régions par tuiles
    RT.createRegionsByTiles(shapeRegion, field_Region, pathEnvelope, pathTileRegion, None)
    
    #pour tout les fichiers dans pathTileRegion
    regionTile = fu.FileSearch_AND(pathTileRegion, True, ".shp")

    #/////////////////////////////////////////////////////////////////////////////////////////
    for path in regionTile:
        ExtDR.ExtractData(path, shapeData, dataRegion, pathTilesFeat, cfg, None)
    #/////////////////////////////////////////////////////////////////////////////////////////

    if REARRANGE_FLAG == 'True' :
        RAM.generateRepartition(PathTEST, cfg, shapeRegion, REARRANGE_PATH, dataField)
    #pour tout les shape file par tuiles présent dans dataRegion, créer un ensemble dapp et de val

    dataTile = fu.FileSearch_AND(dataRegion, True, ".shp")

    #/////////////////////////////////////////////////////////////////////////////////////////
    for path in dataTile:
        RIST.RandomInSituByTile(path, dataField, N, pathAppVal, RATIO, cfg, None)
    #/////////////////////////////////////////////////////////////////////////////////////////
    
    if MODE == "outside" and CLASSIFMODE == "fusion":
        Allcmd = genCmdSplitS.genCmdSplitShape(cfg)
        for cmd in Allcmd:
            run(cmd)

    endGT = time.time()
    groundTruth_time = endGT-startGT
    fu.AddStringToFile("split learning/valdiation time : "+str(groundTruth_time)+"\n",timingLog)
    
    FV.formatting_vectors(cfg.pathConf, None)
    """

    if TRAIN_MODE == "points":
        trainShape = fu.FileSearch_AND(PathTEST+"/formattingVectors",True,".shp")
        startSamples = time.time()
        for shape in trainShape:
            vs.generateSamples(shape, None, cfg)
        VSM.vectorSamplesMerge(cfg)
        endSamples = time.time()
        samples_time = endSamples-startSamples
        fu.AddStringToFile("generate samples points : "+str(samples_time)+"\n",timingLog)
    #génération des fichiers de statistiques
    if not TRAIN_MODE == "points" :
        AllCmd = MS.generateStatModel(pathAppVal,pathTilesFeat,pathStats,cmdPath+"/stats",None, cfg)

        for cmd in AllCmd:
            print ""
            run(cmd)
    #/////////////////////////////////////////////////////////////////////////////////////////

    #génération des commandes pour lApp
    allCmd = LT.launchTraining(pathAppVal, cfg, pathTilesFeat, dataField,
                               pathStats, N, cmdPath+"/train", pathModels,
                               None, None)
    startLearning = time.time()
    #/////////////////////////////////////////////////////////////////////////////////////////
    for cmd in allCmd:
        print ""
        run(cmd)
        #/////////////////////////////////////////////////////////////////////////////////////////
    endLearning = time.time()
    learning_time = endLearning-startLearning
    fu.AddStringToFile("Learning time : "+str(learning_time)+"\n",timingLog)
    
    #génération des commandes pour la classification
    cmdClassif = LC.launchClassification(pathModels, cfg, pathStats, 
                                         pathTileRegion, pathTilesFeat,
                                         shapeRegion, field_Region,
                                         N, cmdPath+"/cla", pathClassif, None)
    startClassification = time.time()
    #/////////////////////////////////////////////////////////////////////////////////////////
    
    for cmd in cmdClassif:
        print ""
        run(cmd)
        #/////////////////////////////////////////////////////////////////////////////////////////
    endClassification = time.time()
    classification_time = endClassification-startClassification
    fu.AddStringToFile("Classification time : "+str(classification_time)+"\n",timingLog)
    if CLASSIFMODE == "separate":
        #Mise en forme des classifications
        startShaping = time.time()
        CS.ClassificationShaping(pathClassif, pathEnvelope, pathTilesFeat,
                                 fieldEnv, N, classifFinal, None, cfg, 
                                 COLORTABLE)
        endShaping = time.time()
        shaping_time = endShaping-startShaping
        fu.AddStringToFile("Shaping time : "+str(shaping_time)+"\n",timingLog)

        #génération des commandes pour les matrices de confusions
        allCmd_conf = GCM.genConfMatrix(classifFinal, pathAppVal, N, dataField,
                                        cmdPath+"/confusion", cfg, None)
        startConfusion = time.time()
        for cmd in allCmd_conf:
        	run(cmd)
        endConfusion = time.time()
        confusion_time = endConfusion-startConfusion
        fu.AddStringToFile("Confusion time : "+str(confusion_time)+"\n",timingLog)

        startReport = time.time()
        confFus.confFusion(shapeData, dataField, classifFinal+"/TMP",
                           classifFinal+"/TMP", classifFinal+"/TMP", cfg)
        GR.genResults(classifFinal,NOMENCLATURE)
        endReport = time.time()
        report_time = endReport-startReport
        fu.AddStringToFile("Report time : "+str(report_time)+"\n",timingLog)
    
    elif CLASSIFMODE == "fusion" and MODE != "one_region":
	
        startClassificationFusion = time.time()
        cmdFus = FUS.fusion(pathClassif, cfg, None)
        for cmd in cmdFus:
            run(cmd)
	
        #gestion des nodata
        fusionFiles = fu.FileSearch_AND(pathClassif,True,"_FUSION_")
        for fusionpath in fusionFiles:
            ND.noData(PathTEST, fusionpath, field_Region, pathTilesFeat,
                      shapeRegion, N, cfg, None)

        endClassificationFusion = time.time()
        classificationFusion_time = endClassificationFusion-startClassificationFusion
        fu.AddStringToFile("Fusion of classifications time : "+str(classificationFusion_time)+"\n",timingLog)
	
        startShaping = time.time()
        #Mise en forme des classifications
        CS.ClassificationShaping(pathClassif, pathEnvelope, pathTilesFeat,
                                 fieldEnv, N, classifFinal, None, cfg,
                                 COLORTABLE)
        endShaping = time.time()
        shaping_time = endShaping-startShaping
        fu.AddStringToFile("Shaping time : "+str(shaping_time)+"\n",timingLog)

        #génération des commandes pour les matrices de confusions
        allCmd_conf = GCM.genConfMatrix(classifFinal, pathAppVal, N, dataField,
                                        cmdPath+"/confusion", cfg, None)
        startConfusion = time.time()
        #/////////////////////////////////////////////////////////////////////////////////////////
        for cmd in allCmd_conf:
            run(cmd)
        #/////////////////////////////////////////////////////////////////////////////////////////

        endConfusion = time.time()
        confusion_time = endConfusion-startConfusion
        fu.AddStringToFile("Confusion time : "+str(confusion_time)+"\n",timingLog)

        startReport = time.time()
        confFus.confFusion(shapeData, dataField, classifFinal+"/TMP",
                           classifFinal+"/TMP", classifFinal+"/TMP", cfg)
        GR.genResults(classifFinal,NOMENCLATURE)
        endReport = time.time()
        report_time = endReport-startReport
        fu.AddStringToFile("Report time : "+str(report_time)+"\n",timingLog)

    elif CLASSIFMODE == "fusion" and MODE =="one_region":
        raise Exception("You can't choose the 'one region' mode and use the fusion mode together")

    startStats = time.time()
    outStat = cfg.getParam('chain', 'outputStatistics')
    if outStat == "True":
        AllTiles = cfg.getParam('chain', 'listTile')
        AllTiles = AllTiles.split(" ")
        for currentTile in AllTiles:
            OutS.outStats(cfg, currentTile, N, None)
        MOutS.mergeOutStats(cfg)
    endStats = time.time()
    stats_time = endStats-startStats
    fu.AddStringToFile("stats time : "+str(stats_time)+"\n",timingLog)

    finIOTA = time.time()
    IOTA = finIOTA-startIOTA
    fu.AddStringToFile("Total time : "+str(IOTA),timingLog)

