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
from config import Config

def launchChainSequential(PathTEST, tiles, pathTilesL8, pathTilesL5, pathTilesS2, pathNewProcessingChain, pathTilesFeat, configFeature, shapeRegion, field_Region, model, shapeData, dataField, pathConf, N, REARRANGE_PATH,MODE,REARRANGE_FLAG,CLASSIFMODE,NOMENCLATURE,COLORTABLE,RATIO,TRAIN_MODE):

    if PathTEST!="/" and os.path.exists(PathTEST):
	choice = ""
	while (choice!="yes") and (choice!="no") and (choice!="y") and (choice!="n"):
		choice = raw_input("the path "+PathTEST+" already exist, do you want to remove it ? yes or no : ")
	if (choice == "yes") or (choice == "y"):
    		shutil.rmtree(PathTEST)
	else :
		sys.exit(-1)
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
    
    if not os.path.exists(PathTEST):
        os.mkdir(PathTEST)
    if not os.path.exists(pathModels):
        os.mkdir(pathModels)
    if not os.path.exists(pathEnvelope):
        os.mkdir(pathEnvelope)
    if not os.path.exists(pathClassif):
        os.mkdir(pathClassif)
    if not os.path.exists(config_model):
        os.mkdir(config_model)
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
	os.mkdir(cmdPath+"/splitShape")
    """
    startFeatures = time.time()
    feat = GFD.CmdFeatures(PathTEST,tiles,pathNewProcessingChain,pathTilesL8,pathTilesL5,pathTilesS2,pathConf,pathTilesFeat,None)
    for i in range(len(feat)):
        print feat[i]
        os.system(feat[i])
    endFeatures = time.time()
    Features_time = endFeatures-startFeatures
    fu.AddStringToFile("Features production time : "+str(Features_time)+"\n",timingLog)
    """
    startGT = time.time()
    #Création des enveloppes
    env.GenerateShapeTile(tiles,pathTilesFeat,pathEnvelope,None,configFeature)
    
    if MODE != "outside":
        area.generateRegionShape(MODE,pathEnvelope,model,shapeRegion,field_Region,configFeature,None)

    #Création des régions par tuiles
    RT.createRegionsByTiles(shapeRegion,field_Region,pathEnvelope,pathTileRegion,None)
    
    #pour tout les fichiers dans pathTileRegion
    regionTile = fu.FileSearch_AND(pathTileRegion,True,".shp")

    #/////////////////////////////////////////////////////////////////////////////////////////
    for path in regionTile:
        ExtDR.ExtractData(path,shapeData,dataRegion,pathTilesFeat,configFeature,None)
        #/////////////////////////////////////////////////////////////////////////////////////////

    if REARRANGE_FLAG == 'True' :
        RAM.generateRepartition(PathTEST,pathConf,shapeRegion,REARRANGE_PATH,dataField)
        #pour tout les shape file par tuiles présent dans dataRegion, créer un ensemble dapp et de val

    dataTile = fu.FileSearch_AND(dataRegion,True,".shp")
    
    #/////////////////////////////////////////////////////////////////////////////////////////
    for path in dataTile:
        RIST.RandomInSituByTile(path,dataField,N,pathAppVal,RATIO,pathConf,None)
        #/////////////////////////////////////////////////////////////////////////////////////////
    
    if MODE == "outside" and CLASSIFMODE == "fusion":
	Allcmd = genCmdSplitS.genCmdSplitShape(pathConf)
	for cmd in Allcmd:
		print cmd
        	os.system(cmd)

    endGT = time.time()
    groundTruth_time = endGT-startGT
    fu.AddStringToFile("split learning/valdiation time : "+str(groundTruth_time)+"\n",timingLog)

    if TRAIN_MODE == "points" :
	trainShape = fu.FileSearch_AND(PathTEST+"/dataAppVal",True,".shp","learn")
	startSamples = time.time()
        for shape in trainShape:
		print ""
		vs.generateSamples(shape,None,configFeature)
	VSM.vectorSamplesMerge(configFeature)
        endSamples = time.time()
        samples_time = endSamples-startSamples
        fu.AddStringToFile("generate samples points : "+str(samples_time)+"\n",timingLog)
    #génération des fichiers de statistiques
    if not TRAIN_MODE == "points" :
        AllCmd = MS.generateStatModel(pathAppVal,pathTilesFeat,pathStats,cmdPath+"/stats",None,configFeature)

    	for cmd in AllCmd:
        	print cmd
        	print ""
        	os.system(cmd)
        	#/////////////////////////////////////////////////////////////////////////////////////////
    
    #génération des commandes pour lApp
    allCmd = LT.launchTraining(pathAppVal,pathConf,pathTilesFeat,dataField,pathStats,N,cmdPath+"/train",pathModels,None,None)
    startLearning = time.time()
    #/////////////////////////////////////////////////////////////////////////////////////////
    for cmd in allCmd:
        print cmd
        print ""
        os.system(cmd)
        #/////////////////////////////////////////////////////////////////////////////////////////
    endLearning = time.time()
    learning_time = endLearning-startLearning
    fu.AddStringToFile("Learning time : "+str(learning_time)+"\n",timingLog)
        
    #génération des commandes pour la classification
    cmdClassif = LC.launchClassification(pathModels,pathConf,pathStats,pathTileRegion,pathTilesFeat,shapeRegion,field_Region,N,cmdPath+"/cla",pathClassif,None)
    startClassification = time.time()
    #/////////////////////////////////////////////////////////////////////////////////////////
    for cmd in cmdClassif:
        print cmd 
        print ""
        os.system(cmd)
        #/////////////////////////////////////////////////////////////////////////////////////////
    endClassification = time.time()
    classification_time = endClassification-startClassification
    fu.AddStringToFile("Classification time : "+str(classification_time)+"\n",timingLog)
    if CLASSIFMODE == "separate":
        #Mise en forme des classifications
        startShaping = time.time()
        CS.ClassificationShaping(pathClassif,pathEnvelope,pathTilesFeat,fieldEnv,N,classifFinal,None,configFeature,COLORTABLE)
        endShaping = time.time()
        shaping_time = endShaping-startShaping
        fu.AddStringToFile("Shaping time : "+str(shaping_time)+"\n",timingLog)

        #génération des commandes pour les matrices de confusions
        allCmd_conf = GCM.genConfMatrix(classifFinal,pathAppVal,N,dataField,cmdPath+"/confusion",configFeature,None)
        startConfusion = time.time()
        for cmd in allCmd_conf:
        	print cmd
        	os.system(cmd)
        endConfusion = time.time()
        confusion_time = endConfusion-startConfusion
        fu.AddStringToFile("Confusion time : "+str(confusion_time)+"\n",timingLog)

        startReport = time.time()
        confFus.confFusion(shapeData,dataField,classifFinal+"/TMP",classifFinal+"/TMP",classifFinal+"/TMP",configFeature)
        GR.genResults(classifFinal,NOMENCLATURE)
        endReport = time.time()
        report_time = endReport-startReport
        fu.AddStringToFile("Report time : "+str(report_time)+"\n",timingLog)
    
    elif CLASSIFMODE == "fusion" and MODE != "one_region":
	
        startClassificationFusion = time.time()
        cmdFus = FUS.fusion(pathClassif,configFeature,None)
        for cmd in cmdFus:
            print cmd
            os.system(cmd)
	
        #gestion des nodata
        fusionFiles = fu.FileSearch_AND(pathClassif,True,"_FUSION_")
        for fusionpath in fusionFiles:
            ND.noData(PathTEST,fusionpath,field_Region,pathTilesFeat,shapeRegion,N,configFeature,None)

        endClassificationFusion = time.time()
        classificationFusion_time = endClassificationFusion-startClassificationFusion
        fu.AddStringToFile("Fusion of classifications time : "+str(classificationFusion_time)+"\n",timingLog)
	
        startShaping = time.time()
        #Mise en forme des classifications
        CS.ClassificationShaping(pathClassif,pathEnvelope,pathTilesFeat,fieldEnv,N,classifFinal,None,configFeature,COLORTABLE)
        endShaping = time.time()
        shaping_time = endShaping-startShaping
        fu.AddStringToFile("Shaping time : "+str(shaping_time)+"\n",timingLog)

        #génération des commandes pour les matrices de confusions
        allCmd_conf = GCM.genConfMatrix(classifFinal,pathAppVal,N,dataField,cmdPath+"/confusion",configFeature,None)
        startConfusion = time.time()
        #/////////////////////////////////////////////////////////////////////////////////////////
        for cmd in allCmd_conf:
            print cmd
            os.system(cmd)
            #/////////////////////////////////////////////////////////////////////////////////////////

        endConfusion = time.time()
        confusion_time = endConfusion-startConfusion
        fu.AddStringToFile("Confusion time : "+str(confusion_time)+"\n",timingLog)

        startReport = time.time()
        confFus.confFusion(shapeData,dataField,classifFinal+"/TMP",classifFinal+"/TMP",classifFinal+"/TMP",configFeature)
        GR.genResults(classifFinal,NOMENCLATURE)
        endReport = time.time()
        report_time = endReport-startReport
        fu.AddStringToFile("Report time : "+str(report_time)+"\n",timingLog)

    elif CLASSIFMODE == "fusion" and MODE =="one_region":
        raise Exception("You can't choose the 'one region' mode and use the fusion mode together")

    startStats = time.time()
    outStat = Config(file(pathConf)).chain.outputStatistics
    if outStat == "True":
	AllTiles = Config(file(pathConf)).chain.listTile
	AllTiles = AllTiles.split(" ")
	for currentTile in AllTiles:
		OutS.outStats(pathConf,currentTile,N,None)
	MOutS.mergeOutStats(pathConf)
    endStats = time.time()
    stats_time = endStats-startStats
    fu.AddStringToFile("stats time : "+str(stats_time)+"\n",timingLog)

    finIOTA = time.time()
    IOTA = finIOTA-startIOTA
    fu.AddStringToFile("Total time : "+str(IOTA),timingLog)

