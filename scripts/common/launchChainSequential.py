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

class IOTA2():
    """
    describe steps
    """
    def __init__(self, cfg):
        import serviceConfigFile as SCF
        import os
        #Config object
        self.cfg = cfg

        #logs
        logDirectory = self.cfg.getParam("chain", "logPath")
        #removeMain log
        log_chain_report = os.path.join(logDirectory, "IOTA2_main_report.log")
        if os.path.exists(log_chain_report):
            os.remove(log_chain_report)

        self.HPC_working_directory = "TMPDIR"
        #build steps
        self.steps = self.build_steps(self.cfg)

    def build_steps(self, cfg):

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
        import serviceConfigFile as SCF
        import sys
        import fusion as FUS
        import noData as ND
        import confusionFusion as confFus
        import reArrangeModel as RAM
        import genCmdSplitShape as genCmdSplitS
        import vectorSampler as vs
        import vectorSamplesMerge as VSM
        import shutil
        import oso_directory as IOTA2_dir
        import fileUtils as fu
        import datetime

        fu.updatePyPath()
        # get variable from configuration file
        PathTEST = cfg.getParam('chain', 'outputPath')
        rm_PathTEST = cfg.getParam("chain", "remove_outputPath")
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
        pathSamples = PathTEST + "/learningSamples"
        
        import launch_tasks as tLauncher
        import ressourcesByStep

        t_container = []
        pathConf = cfg.pathConf
        workingDirectory = os.getenv(self.HPC_working_directory)

        bashLauncherFunction = tLauncher.launchBashCmd
        #STEP : directories
        t_container.append(tLauncher.Tasks(tasks=(lambda x: IOTA2_dir.GenerateDirectories(x), [pathConf]),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep.iota2_dir)
                                           )
    
        #STEP : Common masks generation
        t_container.append(tLauncher.Tasks(tasks=(lambda x: fu.getCommonMasks(x, pathConf, None), tiles),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep.get_common_mask)
                                           )
        #STEP : Envelope generation
        t_container.append(tLauncher.Tasks(tasks=(lambda x: env.GenerateShapeTile(tiles, pathTilesFeat,
                                                                                  x, None,
                                                                                  pathConf),[pathEnvelope]),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep.envelope))

        if MODE != "outside":
            #STEP : Region shape generation
            t_container.append(tLauncher.Tasks(tasks=(lambda x: area.generateRegionShape(MODE, pathEnvelope,
                                                                                        model, x,
                                                                                        field_Region, pathConf,
                                                                                        None),[shapeRegion]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep.regionShape))

        #STEP : Split region shape by tiles
        t_container.append(tLauncher.Tasks(tasks=(lambda x: RT.createRegionsByTiles(x, field_Region,
                                                                                  pathEnvelope, pathTileRegion,
                                                                                  None),[shapeRegion]),
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
            t_container.append(tLauncher.Tasks(tasks=(lambda x: VSM.vectorSamplesMerge(x),[pathConf]),
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
        t_container.append(tLauncher.Tasks(tasks=(lambda x: LC.launchClassification(pathModels, pathConf, pathStats,
                                                                                 pathTileRegion, pathTilesFeat,
                                                                                 shapeRegion, x,
                                                                                 N, cmdPath + "/cla", pathClassif, None),[field_Region]),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep.cmdClassifications))

        #STEP : generate Classifications
        t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                  lambda: fu.getCmd(cmdPath + "/cla/class.txt")),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep.classifications))
        if CLASSIFMODE == "separate":
            #STEP : Classification's shaping
            t_container.append(tLauncher.Tasks(tasks=(lambda x: CS.ClassificationShaping(x,
                                                                                      pathEnvelope,
                                                                                      pathTilesFeat,
                                                                                      fieldEnv, N,
                                                                                      classifFinal, None,
                                                                                      pathConf, COLORTABLE),[pathClassif]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep.classifShaping))

            #STEP : confusion matrix commands generation
            t_container.append(tLauncher.Tasks(tasks=(lambda x: GCM.genConfMatrix(x, pathAppVal,
                                                                               N, dataField,
                                                                               cmdPath + "/confusion",
                                                                               pathConf, None),[classifFinal]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep.gen_confusionMatrix))

            #STEP : confusion matrix generation
            t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                      lambda: fu.getCmd(cmdPath + "/confusion/confusion.txt")),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep.confusionMatrix))
            #STEP : confusion matrix fusion
            t_container.append(tLauncher.Tasks(tasks=(lambda x: confFus.confFusion(x, dataField,
                                                                                     classifFinal + "/TMP",
                                                                                     classifFinal + "/TMP",
                                                                                     classifFinal + "/TMP",
                                                                                     pathConf),[shapeData]),
                                                     iota2_config=cfg,
                                                     ressources=ressourcesByStep.confusionMatrixFusion))
            #STEP : results report generation
            t_container.append(tLauncher.Tasks(tasks=(lambda x: GR.genResults(x,
                                                                            NOMENCLATURE),[classifFinal]),
                                                     iota2_config=cfg,
                                                     ressources=ressourcesByStep.reportGen))

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
            t_container.append(tLauncher.Tasks(tasks=(lambda x: CS.ClassificationShaping(x,
                                                                                      pathEnvelope,
                                                                                      pathTilesFeat,
                                                                                      fieldEnv, N,
                                                                                      classifFinal, None,
                                                                                      pathConf, COLORTABLE),[pathClassif]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep.classifShaping))
            #STEP : confusion matrix commands generation
            t_container.append(tLauncher.Tasks(tasks=(lambda x: GCM.genConfMatrix(x, pathAppVal,
                                                                               N, dataField,
                                                                               cmdPath + "/confusion",
                                                                               pathConf, None),[classifFinal]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep.gen_confusionMatrix))

            #STEP : confusion matrix generation
            t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                      lambda: fu.getCmd(cmdPath + "/confusion/confusion.txt")),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep.confusionMatrix))
            #STEP : confusion matrix fusion
            t_container.append(tLauncher.Tasks(tasks=(lambda x: confFus.confFusion(x, dataField,
                                                                                     classifFinal + "/TMP",
                                                                                     classifFinal + "/TMP",
                                                                                     classifFinal + "/TMP",
                                                                                     pathConf),[shapeData]),
                                                     iota2_config=cfg,
                                                     ressources=ressourcesByStep.confusionMatrixFusion))

            #STEP : results report generation
            t_container.append(tLauncher.Tasks(tasks=(lambda x: GR.genResults(x,
                                                                           NOMENCLATURE),[classifFinal]),
                                                     iota2_config=cfg,
                                                     ressources=ressourcesByStep.reportGen))

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
            t_container.append(tLauncher.Tasks(tasks=(lambda x: MOutS.mergeOutStats(x),[pathConf]),
                                                     iota2_config=cfg,
                                                     ressources=ressourcesByStep.mergeOutStats))
        return t_container
