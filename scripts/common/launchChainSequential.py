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
    import datetime
    
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
    
    #(re)start chain from step...
    START = cfg.getParam("chain", "startFromStep")

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

    t_container = []
    pathConf = cfg.pathConf
    workingDirectory = None

    
    """
    workingDirectory problem : $TMPDIR will not work from here 
    $TMPDIR launchChainSequential != $TMPDIR jobs and they one can't access with
    the other one.
    solution ?
    test if execution mode is 'parallel' if ok get $TMPDIR
    if exeMode == 'parallel'
        workingDirectory = getEnv(TMPDIR)
    """

    #removeMain log
    log_chain_report = os.path.join(logDirectory, "IOTA2_main_report.log")
    if os.path.exists(log_chain_report):
        os.remove(log_chain_report)
    
    startDate = datetime.datetime.now()
    Log_header = "IOTA 2 launched at {0} UTC\n".format(startDate)
    
    with open(log_chain_report,"a+") as f:
        f.write(Log_header)

    bashLauncherFunction = tLauncher.launchBashCmd

    #STEP : Common masks generation
    t_container.append(tLauncher.Tasks(tasks=(lambda x: fu.getCommonMasks(x, pathConf, None), tiles),
                                       iota2_config=cfg,
                                       ressources=ressourcesByStep.get_common_mask))

    #STEP : Envelope generation
    t_container.append(tLauncher.Tasks(tasks=lambda: env.GenerateShapeTile(tiles, pathTilesFeat,
                                                                           pathEnvelope, None,
                                                                           pathConf),
                                       iota2_config=cfg,
                                       ressources=ressourcesByStep.envelope))

    if MODE != "outside":
        #STEP : Region shape generation
        t_container.append(tLauncher.Tasks(tasks=lambda: area.generateRegionShape(MODE, pathEnvelope,
                                                                                  model, shapeRegion,
                                                                                  field_Region, pathConf,
                                                                                  None),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep.regionShape))

    #STEP : Split region shape by tiles
    t_container.append(tLauncher.Tasks(tasks=lambda: RT.createRegionsByTiles(shapeRegion, field_Region,
                                                                             pathEnvelope, pathTileRegion,
                                                                             None),
                                       iota2_config=cfg,
                                       ressources=ressourcesByStep.splitRegions))

    #STEP : Extract groundTruth by regions and by tiles
    t_container.append(tLauncher.Tasks(tasks=(lambda x: ExtDR.ExtractData(x, shapeData,
                                                                          dataRegion, pathTilesFeat,
                                                                          pathConf, None),
                                              lambda: fu.FileSearch_AND(pathTileRegion, True, ".shp")),
                                       iota2_config=cfg,
                                       ressources=ressourcesByStep.extract_data_region_tiles))

    if REARRANGE_FLAG == 'True':
        #STEP : Rearrange models
        RAM.generateRepartition(PathTEST, cfg, shapeRegion, REARRANGE_PATH, dataField)

    #STEP : Split learning polygons and Validation polygons
    t_container.append(tLauncher.Tasks(tasks=(lambda x: RIST.RandomInSituByTile(x, dataField, N,
                                                                                pathAppVal, RATIO,
                                                                                pathConf, None),
                                              lambda: fu.FileSearch_AND(dataRegion, True, ".shp")),
                                       iota2_config=cfg,
                                       ressources=ressourcesByStep.split_learning_val))
    if MODE == "outside" and CLASSIFMODE == "fusion":
        #STEP : Split learning polygons and Validation polygons in sub-sample if necessary
        t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                  lambda: genCmdSplitS.genCmdSplitShape(cfg)),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep.split_learning_val_sub))
    if TRAIN_MODE == "points":
        #STEP : Samples generation
        t_container.append(tLauncher.Tasks(tasks=(lambda x: vs.generateSamples(x, None, pathConf),
                                                  lambda: fu.FileSearch_AND(PathTEST + "/dataAppVal", True, ".shp", "learn")),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep.vectorSampler))
        #STEP : MergeSamples
        t_container.append(tLauncher.Tasks(tasks=lambda: VSM.vectorSamplesMerge(pathConf),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep.mergeSample))

    if not TRAIN_MODE == "points":
        #STEP : Compute statistics by models
        t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                  lambda: MS.generateStatModel(pathAppVal,
                                                                               pathTilesFeat,
                                                                               pathStats,
                                                                               cmdPath + "/stats",
                                                                               None, cfg)),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep.stats_by_models))
    #STEP : Learning
    t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                              lambda: LT.launchTraining(pathAppVal,
                                                                        cfg, pathTilesFeat,
                                                                        dataField,
                                                                        pathStats,
                                                                        N, cmdPath + "/train",
                                                                        pathModels, None, None)),
                                       iota2_config=cfg,
                                       ressources=ressourcesByStep.training))
    #STEP : generate Classifications commands and masks
    t_container.append(tLauncher.Tasks(tasks=lambda: LC.launchClassification(pathModels, pathConf, pathStats,
                                                                             pathTileRegion, pathTilesFeat,
                                                                             shapeRegion, field_Region,
                                                                             N, cmdPath + "/cla", pathClassif, None),
                                       iota2_config=cfg,
                                       ressources=ressourcesByStep.cmdClassifications))

    #STEP : generate Classifications
    t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                              lambda: fu.getCmd(cmdPath + "/cla/class.txt")),
                                       iota2_config=cfg,
                                       ressources=ressourcesByStep.classifications))
    if CLASSIFMODE == "separate":
        #STEP : Classification's shaping
        t_container.append(tLauncher.Tasks(tasks=lambda: CS.ClassificationShaping(pathClassif,
                                                                                  pathEnvelope,
                                                                                  pathTilesFeat,
                                                                                  fieldEnv, N,
                                                                                  classifFinal, None,
                                                                                  pathConf, COLORTABLE),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep.classifShaping))

        #STEP : confusion matrix commands generation
        t_container.append(tLauncher.Tasks(tasks=lambda: GCM.genConfMatrix(classifFinal, pathAppVal,
                                                                           N, dataField,
                                                                           cmdPath + "/confusion",
                                                                           pathConf, None),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep.gen_confusionMatrix))

        #STEP : confusion matrix generation
        t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                  lambda: fu.getCmd(cmdPath + "/confusion/confusion.txt")),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep.confusionMatrix))
        #STEP : confusion matrix fusion
        t_container.append(tLauncher.Python_Task(task=lambda: confFus.confFusion(shapeData, dataField,
                                                                                 classifFinal + "/TMP",
                                                                                 classifFinal + "/TMP",
                                                                                 classifFinal + "/TMP",
                                                                                 pathConf),
                                                 iota2_config=cfg,
                                                 taskName="ConfusionFusion"))
        #STEP : results report generation
        t_container.append(tLauncher.Python_Task(task=lambda: GR.genResults(classifFinal,
                                                                            NOMENCLATURE),
                                                 iota2_config=cfg,
                                                 taskName="reportGeneration"))

    elif CLASSIFMODE == "fusion" and MODE != "one_region":

        #STEP : Classifications fusion
        t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                  lambda: FUS.fusion(pathClassif, cfg, None)),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep.fusion))

        #STEP : Managing fusion's indecisions
        t_container.append(tLauncher.Tasks(tasks=(lambda x: ND.noData(PathTEST, x, field_Region,
                                                                      pathTilesFeat, shapeRegion,
                                                                      N, pathConf, None),
                                                  lambda: fu.FileSearch_AND(pathClassif, True, "_FUSION_")),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep.noData))
        #STEP : Classification's shaping
        t_container.append(tLauncher.Tasks(tasks=lambda: CS.ClassificationShaping(pathClassif,
                                                                                  pathEnvelope,
                                                                                  pathTilesFeat,
                                                                                  fieldEnv, N,
                                                                                  classifFinal, None,
                                                                                  pathConf, COLORTABLE),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep.classifShaping))
        #STEP : confusion matrix commands generation
        t_container.append(tLauncher.Tasks(tasks=lambda: GCM.genConfMatrix(classifFinal, pathAppVal,
                                                                           N, dataField,
                                                                           cmdPath + "/confusion",
                                                                           pathConf, None),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep.gen_confusionMatrix))

        #STEP : confusion matrix generation
        t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                  lambda: fu.getCmd(cmdPath + "/confusion/confusion.txt")),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep.confusionMatrix))
        #STEP : confusion matrix fusion
        t_container.append(tLauncher.Python_Task(task=lambda: confFus.confFusion(shapeData, dataField,
                                                                                 classifFinal + "/TMP",
                                                                                 classifFinal + "/TMP",
                                                                                 classifFinal + "/TMP",
                                                                                 pathConf),
                                                 iota2_config=cfg,
                                                 taskName="ConfusionFusion"))

        #STEP : results report generation
        t_container.append(tLauncher.Python_Task(task=lambda: GR.genResults(classifFinal,
                                                                            NOMENCLATURE),
                                                 iota2_config=cfg,
                                                 taskName="reportGeneration"))

    elif CLASSIFMODE == "fusion" and MODE == "one_region":
        raise Exception("You can't choose the 'one region' mode and use the fusion mode together")

    outStat = cfg.getParam('chain', 'outputStatistics')
    if outStat == "True":
        #STEP : compute output statistics tiles
        t_container.append(tLauncher.Tasks(tasks=(lambda x: OutS.outStats(pathConf, x,
                                                                          N, None), tiles),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep.statsReport))
        #STEP : merge statistics
        t_container.append(tLauncher.Python_Task(task=lambda: MOutS.mergeOutStats(pathConf),
                                                 iota2_config=cfg,
                                                 taskName="mergeOutputStats"))

    #Launch All steps
    for task_number, task_to_exe in enumerate(t_container):
        step = ("\nRUNNING : STEP {0}/{1} : {2}").format(task_number + 1,
                                                         len(t_container),
                                                         task_to_exe.TaskName)
        print step
        with open(log_chain_report, 'a+') as f:
            f.write(step)
        if task_number + 1 >= START:
            task_to_exe.run()

    endDate = datetime.datetime.now()
    Log_tail = "\nIOTA 2 ended at {0} UTC\n".format(endDate)
    
    with open(log_chain_report,"a+") as f:
        f.write(Log_tail)

if __name__ == "__main__":
    import sys
    configurationFile = sys.argv[1]
    launchChainSequential(configurationFile)
