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
from config import Config
import math

def launchChainSequential(cfg):
    fu.updatePyPath()
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
    exeMode = cfg.getParam("chain","executionMode")

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

    import launch_tasks as tLauncher
    import pbs_config_file

    pathConf = cfg.pathConf
    workingDirectory = None
    """
    Ne va pas fonctionner, trouver un moyen...
    if exeMode == 'parallel'
        workingDirectory = '$TMPDIR'
    """
    bashLauncherFunction = tLauncher.launchBashCmd

    print ("\nSTEP : common masks generation")
    tLauncher.MPI_Tasks(tasks=(lambda x: fu.getCommonMasks(x, pathConf, None), tiles),
                        nb_procs=10,
                        nb_mpi_procs=len(tiles)+1,
                        iota2_config=cfg,
                        pbs_config=pbs_config_file.get_common_mask).run()

    startGT = time.time()
    print ("\nSTEP : Envelope generation")
    tLauncher.Task(task=lambda: env.GenerateShapeTile(tiles, pathTilesFeat,
                                                      pathEnvelope, None,
                                                      pathConf),
                       nb_procs=1,
                       iota2_config=cfg,
                       pbs_config=pbs_config_file.envelope).run()
    if MODE != "outside":
        print ("\nSTEP : Region shape generation")
        tLauncher.Task(task=lambda: area.generateRegionShape(MODE, pathEnvelope,
                                                             model, shapeRegion,
                                                             field_Region, pathConf,
                                                             None),
                       nb_procs=1,
                       iota2_config=cfg,
                       pbs_config=pbs_config_file.regionShape).run()

    print ("\nSTEP : Split region shape by tiles")
    tLauncher.Task(task=lambda: RT.createRegionsByTiles(shapeRegion, field_Region,
                                                        pathEnvelope, pathTileRegion,
                                                        None),
                       nb_procs=1,
                       iota2_config=cfg,
                       pbs_config=pbs_config_file.splitRegions).run()

    regionTile = fu.FileSearch_AND(pathTileRegion, True, ".shp")
    print("\nSTEP : Extract groundTruth by regions and by tiles")

    tLauncher.MPI_Tasks(tasks=(lambda x: ExtDR.ExtractData(x, shapeData, dataRegion, pathTilesFeat, pathConf, None), regionTile),
                    nb_procs=10,
                    nb_mpi_procs=4,
                    iota2_config=cfg,
                    pbs_config=pbs_config_file.extract_data_region_tiles).run()

    if REARRANGE_FLAG == 'True' :
        print("\nSTEP : Rearrange models")
        RAM.generateRepartition(PathTEST, cfg, shapeRegion, REARRANGE_PATH, dataField)

    dataTile = fu.FileSearch_AND(dataRegion, True, ".shp")
    print("\nSTEP : Split learning polygons and Validation polygons")
    tLauncher.MPI_Tasks(tasks=(lambda x: RIST.RandomInSituByTile(x, dataField, N, pathAppVal, RATIO, pathConf, None), dataTile),
                    nb_procs=5,
                    nb_mpi_procs=5,
                    iota2_config=cfg,
                    pbs_config=pbs_config_file.split_learning_val).run()

    if MODE == "outside" and CLASSIFMODE == "fusion":
        print("\nSTEP : Split learning polygons and Validation polygons in sub-sample if necessary")
        Allcmd = genCmdSplitS.genCmdSplitShape(cfg)
        tLauncher.MPI_Tasks(tasks=(lambda x: bashLauncherFunction(x), Allcmd),
                        nb_procs=5,
                        nb_mpi_procs=5,
                        iota2_config=cfg,
                        pbs_config=pbs_config_file.split_learning_val_sub).run()

    endGT = time.time()
    groundTruth_time = endGT-startGT
    fu.AddStringToFile("split learning/valdiation time : "+str(groundTruth_time)+"\n",timingLog)

    if TRAIN_MODE == "points":
        trainShape = fu.FileSearch_AND(PathTEST+"/dataAppVal",True,".shp","learn")
        startSamples = time.time()
        print("\nSTEP : Samples generation")
        tLauncher.MPI_Tasks(tasks=(lambda x: vs.generateSamples(x, None, pathConf), trainShape),
                        nb_procs=10,
                        nb_mpi_procs=5,
                        iota2_config=cfg,
                        pbs_config=pbs_config_file.vectorSampler).run()
        print("\nSTEP : MergeSamples")
        tLauncher.Task(task=lambda : VSM.vectorSamplesMerge(pathConf),
                        nb_procs=10,
                        iota2_config=cfg,
                        pbs_config=pbs_config_file.mergeSample).run()
        endSamples = time.time()
        samples_time = endSamples-startSamples
        fu.AddStringToFile("generate samples points : "+str(samples_time)+"\n",timingLog)

    if not TRAIN_MODE == "points" :
        print("\nSTEP : Compute statistics by models")
        AllCmd = MS.generateStatModel(pathAppVal,pathTilesFeat,pathStats,cmdPath+"/stats",None, cfg)
        tLauncher.MPI_Tasks(tasks=(lambda x: bashLauncherFunction(x), AllCmd),
                        nb_procs=5,
                        nb_mpi_procs=3,
                        iota2_config=cfg,
                        pbs_config=pbs_config_file.stats_by_models).run()

    print("\nSTEP : Learning")
    AllCmd = LT.launchTraining(pathAppVal, cfg, pathTilesFeat, dataField,
                               pathStats, N, cmdPath+"/train", pathModels,
                               None, None)
    startLearning = time.time()

    tLauncher.MPI_Tasks(tasks=(lambda x: bashLauncherFunction(x), AllCmd),
                    nb_procs=5,
                    nb_mpi_procs=3,
                    iota2_config=cfg,
                    pbs_config=pbs_config_file.training).run()

    endLearning = time.time()
    learning_time = endLearning-startLearning
    fu.AddStringToFile("Learning time : "+str(learning_time)+"\n",timingLog)

    print("\nSTEP : generate Classifications commands and masks")

    tLauncher.Task(task=lambda: LC.launchClassification(pathModels, pathConf, pathStats,
                                                        pathTileRegion, pathTilesFeat,
                                                        shapeRegion, field_Region,
                                                        N, cmdPath+"/cla", pathClassif, None),
                   nb_procs=5,
                   iota2_config=cfg,
                   pbs_config=pbs_config_file.cmdClassifications).run()

    startClassification = time.time()
    print("\nSTEP : generate Classifications")
    cmdClassif = fu.getCmd(cmdPath+ "/cla/class.txt")
    tLauncher.MPI_Tasks(tasks=(lambda x: bashLauncherFunction(x), cmdClassif),
                        nb_procs=5,
                        nb_mpi_procs=int(math.ceil(len(cmdClassif)/5.0))+1,
                        iota2_config=cfg,
                        pbs_config=pbs_config_file.classifications).run()

    endClassification = time.time()
    classification_time = endClassification-startClassification
    fu.AddStringToFile("Classification time : "+str(classification_time)+"\n",timingLog)

    if CLASSIFMODE == "separate":

        startShaping = time.time()
        print("\nSTEP : Classification's shaping")
        tLauncher.Task(task=lambda: CS.ClassificationShaping(pathClassif,
                                                             pathEnvelope,
                                                             pathTilesFeat,
                                                             fieldEnv, N,
                                                             classifFinal, None,
                                                             pathConf, COLORTABLE),
                       nb_procs=5,
                       iota2_config=cfg,
                       pbs_config=pbs_config_file.classifShaping).run()

        endShaping = time.time()
        shaping_time = endShaping-startShaping
        fu.AddStringToFile("Shaping time : "+str(shaping_time)+"\n",timingLog)

        print("\nSTEP : confusion matrix commands generation")
        tLauncher.Task(task=lambda: GCM.genConfMatrix(classifFinal, pathAppVal,
                                                      N, dataField,
                                                      cmdPath+"/confusion",
                                                      pathConf, None),
                       nb_procs=5,
                       iota2_config=cfg,
                       pbs_config=pbs_config_file.confusionMatrix).run()

        startConfusion = time.time()
        allCmd_conf = fu.getCmd(cmdPath+ "/confusion/confusion.txt")
        print("\nSTEP : confusion matrix generation")
        tLauncher.MPI_Tasks(tasks=(lambda x: bashLauncherFunction(x), allCmd_conf),
                            nb_procs=5,
                            nb_mpi_procs=3,
                            iota2_config=cfg,
                            pbs_config=pbs_config_file.training).run()

        endConfusion = time.time()
        confusion_time = endConfusion-startConfusion
        fu.AddStringToFile("Confusion time : "+str(confusion_time)+"\n",timingLog)

        startReport = time.time()

        print("\nSTEP : confusion matrix fusion")
        tLauncher.Python_Task(task=lambda x: confFus.confFusion(shapeData, dataField,
                                                                 classifFinal+"/TMP",
                                                                 classifFinal+"/TMP",
                                                                 classifFinal+"/TMP",
                                                                 pathConf),
                              iota2_config=cfg,
                              taskName="ConfusionFusion").run()

        print("\nSTEP : results report generation")
        tLauncher.Python_Task(task=lambda x: GR.genResults(classifFinal,
                                                           NOMENCLATURE),
                              iota2_config=cfg,
                              taskName="reportGeneration").run()

        endReport = time.time()
        report_time = endReport-startReport
        fu.AddStringToFile("Report time : "+str(report_time)+"\n",timingLog)

    elif CLASSIFMODE == "fusion" and MODE != "one_region":

        startClassificationFusion = time.time()
        cmdFus = FUS.fusion(pathClassif, cfg, None)
        print("\nSTEP : Classifications fusion")
        tLauncher.MPI_Tasks(tasks=(lambda x: bashLauncherFunction(x), cmdFus),
                            nb_procs=5,
                            nb_mpi_procs=3,
                            iota2_config=cfg,
                            pbs_config=pbs_config_file.fusion).run()

        print("\nSTEP : Managing fusion's indecisions")
        fusionFiles = fu.FileSearch_AND(pathClassif,True,"_FUSION_")
        tLauncher.MPI_Tasks(tasks=(lambda x: ND.noData(PathTEST, x, field_Region,
                                                       pathTilesFeat, shapeRegion,
                                                       N, pathConf, None), fusionFiles),
                        nb_procs=5,
                        nb_mpi_procs=int(math.ceil(len(fusionFiles)/5.0))+1,
                        iota2_config=cfg,
                        pbs_config=pbs_config_file.noData).run()

        endClassificationFusion = time.time()
        classificationFusion_time = endClassificationFusion-startClassificationFusion
        fu.AddStringToFile("Fusion of classifications time : "+str(classificationFusion_time)+"\n",timingLog)

        startShaping = time.time()
        print("\nSTEP : Classification's shaping")
        tLauncher.Task(task=lambda: CS.ClassificationShaping(pathClassif,
                                                             pathEnvelope,
                                                             pathTilesFeat,
                                                             fieldEnv, N,
                                                             classifFinal, None,
                                                             pathConf, COLORTABLE),
                       nb_procs=5,
                       iota2_config=cfg,
                       pbs_config=pbs_config_file.classifShaping).run()

        endShaping = time.time()
        shaping_time = endShaping-startShaping
        fu.AddStringToFile("Shaping time : "+str(shaping_time)+"\n",timingLog)

        print("\nSTEP : confusion matrix commands generation")
        tLauncher.Task(task=lambda: GCM.genConfMatrix(classifFinal, pathAppVal,
                                                      N, dataField,
                                                      cmdPath+"/confusion",
                                                      pathConf, None),
                       nb_procs=5,
                       iota2_config=cfg,
                       pbs_config=pbs_config_file.confusionMatrix).run()

        startConfusion = time.time()
        allCmd_conf = fu.getCmd(cmdPath+ "/confusion/confusion.txt")
        print("\nSTEP : confusion matrix generation")
        tLauncher.MPI_Tasks(tasks=(lambda x: bashLauncherFunction(x), allCmd_conf),
                            nb_procs=5,
                            nb_mpi_procs=3,
                            iota2_config=cfg,
                            pbs_config=pbs_config_file.training).run()

        endConfusion = time.time()
        confusion_time = endConfusion-startConfusion
        fu.AddStringToFile("Confusion time : "+str(confusion_time)+"\n",timingLog)

        startReport = time.time()

        print("\nSTEP : confusion matrix fusion")
        tLauncher.Python_Task(task=lambda x: confFus.confFusion(shapeData, dataField,
                                                                 classifFinal+"/TMP",
                                                                 classifFinal+"/TMP",
                                                                 classifFinal+"/TMP",
                                                                 pathConf),
                              iota2_config=cfg,
                              taskName="ConfusionFusion").run()

        print("\nSTEP : results report generation")
        tLauncher.Python_Task(task=lambda x: GR.genResults(classifFinal,
                                                           NOMENCLATURE),
                              iota2_config=cfg,
                              taskName="reportGeneration").run()

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

