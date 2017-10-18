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

"""
TODO : create a Task container, then iterate over tasks...
the container must be ordered
pbs intermediate step Ex : cmdClassif = fu.getCmd(cmdPath+ "/cla/class.txt")
need some outputs... -> add fu.getCmd
maybe serialize it in order to re-run the chain from a specific step.
"""


def launchChainSequential(cfg):

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
    import os
    import sys
    import fusion as FUS
    import noData as ND
    import confusionFusion as confFus
    import reArrangeModel as RAM
    import genCmdSplitShape as genCmdSplitS
    import vectorSampler as vs
    import vectorSamplesMerge as VSM
    import shutil
    import serviceConfigFile as SCF
    import fileUtils as fu

    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    fu.updatePyPath()
    # get variable from configuration file
    PathTEST = cfg.getParam('chain', 'outputPath')
    TmpTiles = cfg.getParam('chain', 'listTile')
    tiles = TmpTiles.split(" ")
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
    exeMode = cfg.getParam("chain", "executionMode")

    logDirectory = cfg.getParam("chain", "logPath")

    if PathTEST != "/" and os.path.exists(PathTEST) and not exeMode == 'parallel':
        choice = ""
        while (choice != "yes") and (choice != "no") and (choice != "y") and (choice != "n"):
            choice = raw_input("the path " + PathTEST + " already exist, do you want to remove it ? yes or no : ")
        if (choice == "yes") or (choice == "y"):
            shutil.rmtree(PathTEST)
        else:
            sys.exit(-1)

    #do not change
    fieldEnv = "FID"

    pathModels = PathTEST + "/model"
    pathEnvelope = PathTEST + "/envelope"
    pathClassif = PathTEST + "/classif"
    pathTileRegion = PathTEST + "/shapeRegion"
    classifFinal = PathTEST + "/final"
    dataRegion = PathTEST + "/dataRegion"
    pathAppVal = PathTEST + "/dataAppVal"
    pathStats = PathTEST + "/stats"
    cmdPath = PathTEST + "/cmd"
    config_model = PathTEST + "/config_model"

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
        os.mkdir(cmdPath + "/stats")
        os.mkdir(cmdPath + "/train")
        os.mkdir(cmdPath + "/cla")
        os.mkdir(cmdPath + "/confusion")
        os.mkdir(cmdPath + "/features")
        os.mkdir(cmdPath + "/fusion")
        os.mkdir(cmdPath + "/splitShape")

    import launch_tasks as tLauncher

    import ressourcesByStep

    pathConf = cfg.pathConf
    workingDirectory = None
    """
    Ne va pas fonctionner, trouver un moyen...
    if exeMode == 'parallel'
        workingDirectory = '$TMPDIR'
        dans chaque scripts, tester si mode // -> alors getEnv($TMPDIR) ?
    """

    #removeMain log
    log_chain_report = os.path.join(logDirectory, "IOTA2_main_report.log")
    if os.path.exists(log_chain_report):
        os.remove(log_chain_report)

    bashLauncherFunction = tLauncher.launchBashCmd

    #STEP : Common masks generation
    tLauncher.Tasks(tasks=(lambda x: fu.getCommonMasks(x, pathConf, None), tiles),
                    iota2_config=cfg,
                    ressources=ressourcesByStep.get_common_mask).run()

    #STEP : Envelope generation
    tLauncher.Tasks(tasks=lambda: env.GenerateShapeTile(tiles, pathTilesFeat,
                                                        pathEnvelope, None,
                                                        pathConf),
                    iota2_config=cfg,
                    ressources=ressourcesByStep.envelope).run()

    if MODE != "outside":
        #STEP : Region shape generation
        tLauncher.Tasks(tasks=lambda: area.generateRegionShape(MODE, pathEnvelope,
                                                               model, shapeRegion,
                                                               field_Region, pathConf,
                                                               None),
                        iota2_config=cfg,
                        ressources=ressourcesByStep.regionShape).run()

    #STEP : Split region shape by tiles
    tLauncher.Tasks(tasks=lambda: RT.createRegionsByTiles(shapeRegion, field_Region,
                                                          pathEnvelope, pathTileRegion,
                                                          None),
                    iota2_config=cfg,
                    ressources=ressourcesByStep.splitRegions).run()

    regionTile = fu.FileSearch_AND(pathTileRegion, True, ".shp")
    #STEP : Extract groundTruth by regions and by tiles
    tLauncher.Tasks(tasks=(lambda x: ExtDR.ExtractData(x, shapeData, dataRegion,
                                                       pathTilesFeat, pathConf, None), regionTile),
                    iota2_config=cfg,
                    ressources=ressourcesByStep.extract_data_region_tiles).run()

    if REARRANGE_FLAG == 'True':
        #STEP : Rearrange models
        RAM.generateRepartition(PathTEST, cfg, shapeRegion, REARRANGE_PATH, dataField)

    dataTile = fu.FileSearch_AND(dataRegion, True, ".shp")
    #STEP : Split learning polygons and Validation polygons
    tLauncher.Tasks(tasks=(lambda x: RIST.RandomInSituByTile(x, dataField, N,
                                                             pathAppVal, RATIO,
                                                             pathConf, None), dataTile),
                    iota2_config=cfg,
                    ressources=ressourcesByStep.split_learning_val).run()

    if MODE == "outside" and CLASSIFMODE == "fusion":
        #STEP : Split learning polygons and Validation polygons in sub-sample if necessary
        Allcmd = genCmdSplitS.genCmdSplitShape(cfg)
        tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x), Allcmd),
                        iota2_config=cfg,
                        ressources=ressourcesByStep.split_learning_val_sub).run()

    if TRAIN_MODE == "points":
        trainShape = fu.FileSearch_AND(PathTEST + "/dataAppVal", True, ".shp", "learn")
        #STEP : Samples generation
        tLauncher.Tasks(tasks=(lambda x: vs.generateSamples(x, None, pathConf), trainShape),
                        iota2_config=cfg,
                        ressources=ressourcesByStep.vectorSampler).run()
        #STEP : MergeSamples
        tLauncher.Tasks(tasks=lambda: VSM.vectorSamplesMerge(pathConf),
                        iota2_config=cfg,
                        ressources=ressourcesByStep.mergeSample).run()

    if not TRAIN_MODE == "points":
        #STEP : Compute statistics by models
        AllCmd = MS.generateStatModel(pathAppVal, pathTilesFeat, pathStats,
                                      cmdPath + "/stats", None, cfg)
        tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x), AllCmd),
                        iota2_config=cfg,
                        ressources=ressourcesByStep.stats_by_models).run()

    #STEP : Learning
    AllCmd = LT.launchTraining(pathAppVal, cfg, pathTilesFeat, dataField,
                               pathStats, N, cmdPath + "/train", pathModels,
                               None, None)

    tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x), AllCmd),
                    iota2_config=cfg,
                    ressources=ressourcesByStep.training).run()

    #STEP : generate Classifications commands and masks
    tLauncher.Tasks(tasks=lambda: LC.launchClassification(pathModels, pathConf, pathStats,
                                                          pathTileRegion, pathTilesFeat,
                                                          shapeRegion, field_Region,
                                                          N, cmdPath + "/cla", pathClassif, None),
                    iota2_config=cfg,
                    ressources=ressourcesByStep.cmdClassifications).run()

    #STEP : generate Classifications
    cmdClassif = fu.getCmd(cmdPath + "/cla/class.txt")
    tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x), cmdClassif),
                    iota2_config=cfg,
                    ressources=ressourcesByStep.classifications).run()

    if CLASSIFMODE == "separate":
        #STEP : Classification's shaping
        tLauncher.Tasks(tasks=lambda: CS.ClassificationShaping(pathClassif,
                                                               pathEnvelope,
                                                               pathTilesFeat,
                                                               fieldEnv, N,
                                                               classifFinal, None,
                                                               pathConf, COLORTABLE),
                        iota2_config=cfg,
                        ressources=ressourcesByStep.classifShaping).run()

        #STEP : confusion matrix commands generation
        tLauncher.Tasks(tasks=lambda: GCM.genConfMatrix(classifFinal, pathAppVal,
                                                        N, dataField,
                                                        cmdPath + "/confusion",
                                                        pathConf, None),
                        iota2_config=cfg,
                        ressources=ressourcesByStep.gen_confusionMatrix).run()

        allCmd_conf = fu.getCmd(cmdPath + "/confusion/confusion.txt")
        #STEP : confusion matrix generation
        tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x), allCmd_conf),
                        iota2_config=cfg,
                        ressources=ressourcesByStep.confusionMatrix).run()
        #STEP : confusion matrix fusion
        tLauncher.Python_Task(task=lambda: confFus.confFusion(shapeData, dataField,
                                                              classifFinal + "/TMP",
                                                              classifFinal + "/TMP",
                                                              classifFinal + "/TMP",
                                                              pathConf),
                              iota2_config=cfg,
                              taskName="ConfusionFusion").run()
        #STEP : results report generation
        tLauncher.Python_Task(task=lambda: GR.genResults(classifFinal,
                                                         NOMENCLATURE),
                              iota2_config=cfg,
                              taskName="reportGeneration").run()

    elif CLASSIFMODE == "fusion" and MODE != "one_region":

        cmdFus = FUS.fusion(pathClassif, cfg, None)
        #STEP : Classifications fusion
        tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x), cmdFus),
                        iota2_config=cfg,
                        ressources=ressourcesByStep.fusion).run()
        #STEP : Managing fusion's indecisions
        fusionFiles = fu.FileSearch_AND(pathClassif, True, "_FUSION_")
        tLauncher.Tasks(tasks=(lambda x: ND.noData(PathTEST, x, field_Region,
                                                   pathTilesFeat, shapeRegion,
                                                   N, pathConf, None), fusionFiles),
                        iota2_config=cfg,
                        ressources=ressourcesByStep.noData).run()
        #STEP : Classification's shaping
        tLauncher.Tasks(tasks=lambda: CS.ClassificationShaping(pathClassif,
                                                               pathEnvelope,
                                                               pathTilesFeat,
                                                               fieldEnv, N,
                                                               classifFinal, None,
                                                               pathConf, COLORTABLE),
                        iota2_config=cfg,
                        ressources=ressourcesByStep.classifShaping).run()
        #STEP : confusion matrix commands generation
        tLauncher.Tasks(tasks=lambda: GCM.genConfMatrix(classifFinal, pathAppVal,
                                                        N, dataField,
                                                        cmdPath + "/confusion",
                                                        pathConf, None),
                        iota2_config=cfg,
                        ressources=ressourcesByStep.gen_confusionMatrix).run()

        allCmd_conf = fu.getCmd(cmdPath + "/confusion/confusion.txt")
        #STEP : confusion matrix generation
        tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x), allCmd_conf),
                        iota2_config=cfg,
                        ressources=ressourcesByStep.confusionMatrix).run()

        #STEP : confusion matrix fusion
        tLauncher.Python_Task(task=lambda: confFus.confFusion(shapeData, dataField,
                                                              classifFinal + "/TMP",
                                                              classifFinal + "/TMP",
                                                              classifFinal + "/TMP",
                                                              pathConf),
                              iota2_config=cfg,
                              taskName="ConfusionFusion").run()

        #STEP : results report generation
        tLauncher.Python_Task(task=lambda: GR.genResults(classifFinal,
                                                         NOMENCLATURE),
                              iota2_config=cfg,
                              taskName="reportGeneration").run()

    elif CLASSIFMODE == "fusion" and MODE == "one_region":
        raise Exception("You can't choose the 'one region' mode and use the fusion mode together")

    outStat = cfg.getParam('chain', 'outputStatistics')
    if outStat == "True":
        AllTile = list(set([classif.split("_")[1] for classif in fu.FileSearch_AND(PathTEST + "/classif", True, "Classif", ".tif")]))
        #STEP : compute output statistics
        tLauncher.Tasks(tasks=(lambda x: OutS.outStats(pathConf, x,
                                                       N, None), AllTile),
                        iota2_config=cfg,
                        ressources=ressourcesByStep.statsReport).run()
        #STEP : merge statistics
        tLauncher.Python_Task(task=lambda: MOutS.mergeOutStats(pathConf),
                              iota2_config=cfg,
                              taskName="mergeOutputStats").run()

    with open(log_chain_report, 'a+') as f:
        f.write("\n****************************")
        f.write("\nIOTA2 chain is ended\n")
        f.write("****************************\n")

if __name__ == "__main__":
    import sys
    configurationFile = sys.argv[1]
    launchChainSequential(configurationFile)
