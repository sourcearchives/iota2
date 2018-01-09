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

from collections import OrderedDict

class iota2():
    """
    class use to describe steps sequence and variable to use at each step (config)
    """
    def __init__(self, cfg):
        #Config object
        self.cfg = cfg
        
        #working directory, HPC
        self.HPC_working_directory = "TMPDIR"
        
        #steps definitions
        self.steps_group = OrderedDict()
        self.steps_group["init"] = []
        self.steps_group["sampling"] = []
        self.steps_group["learning"] = []
        self.steps_group["classification"] = []
        self.steps_group["mosaic"] = []
        self.steps_group["validation"] = []

        #build steps
        self.steps = self.build_steps(self.cfg)

    def get_steps_number(self):
        
        start = self.cfg.getParam('chain', 'firstStep')
        end = self.cfg.getParam('chain', 'lastStep')
        start_ind = self.steps_group.keys().index(start)
        end_ind = self.steps_group.keys().index(end)
        
        steps = []
        for key in self.steps_group.keys()[start_ind:end_ind+1]:
            steps.append(self.steps_group[key])

        step_to_compute = [step for step_group in steps for step in step_group]
        
        return step_to_compute

    def build_steps(self, cfg):
        """
        build steps
        """
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
        import fusion as FUS
        import noData as ND
        import confusionFusion as confFus
        import reArrangeModel as RAM
        import genCmdSplitShape as genCmdSplitS
        import vectorSampler as vs
        import vectorSamplesMerge as VSM
        import oso_directory as IOTA2_dir
        import fileUtils as fu
        import NbView
        import bPy_ImageClassifier as imageClassifier

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
        MODE = cfg.getParam('chain', 'mode')
        CLASSIFMODE = cfg.getParam('argClassification', 'classifMode')
        NOMENCLATURE = cfg.getParam('chain', 'nomenclaturePath')
        COLORTABLE = cfg.getParam('chain', 'colorTable')
        RATIO = cfg.getParam('chain', 'ratio')
        outStat = cfg.getParam('chain', 'outputStatistics')
        classifier = cfg.getParam('argTrain', 'classifier')
        cloud_threshold = cfg.getParam('chain', 'cloud_threshold')

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

        import launch_tasks as tLauncher
        import ressourcesByStep as iota2Ressources
        ressourcesByStep = iota2Ressources.iota2_ressources()
        
        t_container = []
        t_counter = 0
        
        pathConf = cfg.pathConf
        workingDirectory = os.getenv(self.HPC_working_directory)

        bashLauncherFunction = tLauncher.launchBashCmd
        launchPythonCmd = tLauncher.launchPythonCmd
        #STEP : directories.
        t_counter+=1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: IOTA2_dir.GenerateDirectories(x), [pathConf]),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["iota2_dir"]))
        self.steps_group["init"].append(t_counter)

        #STEP : Common masks generation
        t_counter+=1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: fu.getCommonMasks(x, pathConf, workingDirectory), tiles),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["get_common_mask"]))
        self.steps_group["init"].append(t_counter)
        
        #STEP : pix Validity by tiles generation
        t_counter+=1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: NbView.genNbView(x, "CloudThreshold_" + str(cloud_threshold) + ".shp", cloud_threshold, pathConf, workingDirectory), [os.path.join(pathTilesFeat,tile) for tile in tiles]),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["get_pixValidity"]))
        self.steps_group["init"].append(t_counter)

        #STEP : Envelope generation
        t_counter+=1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: env.GenerateShapeTile(tiles, pathTilesFeat,
                                                                                  x, workingDirectory,
                                                                                  pathConf), [pathEnvelope]),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["envelope"]))
        self.steps_group["sampling"].append(t_counter)

        if MODE != "outside":
            #STEP : Region shape generation
            t_counter+=1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: area.generateRegionShape(MODE, pathEnvelope,
                                                                                         model, x,
                                                                                         field_Region, pathConf,
                                                                                         workingDirectory), [shapeRegion]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["regionShape"]))
            self.steps_group["sampling"].append(t_counter)

        #STEP : Split region shape by tiles
        t_counter+=1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: RT.createRegionsByTiles(x, field_Region,
                                                                                    pathEnvelope, pathTileRegion,
                                                                                    workingDirectory), [shapeRegion]),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["splitRegions"]))
        self.steps_group["sampling"].append(t_counter)

        #STEP : Extract groundTruth by regions and by tiles
        t_counter+=1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: ExtDR.ExtractData(x, shapeData,
                                                                              dataRegion, pathTilesFeat,
                                                                              pathConf, workingDirectory),
                                                  lambda: fu.FileSearch_AND(pathTileRegion, True, ".shp")),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["extract_data_region_tiles"]))
        self.steps_group["sampling"].append(t_counter)

        #STEP : Split learning polygons and Validation polygons
        t_counter+=1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: RIST.RandomInSituByTile(x, dataField, N,
                                                                                    pathAppVal, RATIO,
                                                                                    pathConf, workingDirectory),
                                                  lambda: fu.FileSearch_AND(dataRegion, True, ".shp")),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["split_learning_val"]))
        self.steps_group["sampling"].append(t_counter)

        if MODE == "outside" and CLASSIFMODE == "fusion":
            #STEP : Split learning polygons and Validation polygons in sub-sample if necessary
            t_counter+=1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                      lambda: genCmdSplitS.genCmdSplitShape(cfg)),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["split_learning_val_sub"]))
            self.steps_group["sampling"].append(t_counter)

        #STEP : Samples generation
        t_counter+=1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: vs.generateSamples(x, workingDirectory, pathConf),
                                                  lambda: fu.FileSearch_AND(PathTEST + "/dataAppVal", True, ".shp", "learn")),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["vectorSampler"]))
        self.steps_group["sampling"].append(t_counter)

        #STEP : MergeSamples
        t_counter+=1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: VSM.vectorSamplesMerge(pathConf,x),
                                                  lambda: fu.split_vectors_by_regions((fu.FileSearch_AND(PathTEST + "/learningSamples", True, "Samples.sqlite")))),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["mergeSample"]))
        self.steps_group["sampling"].append(t_counter)

        if classifier == "svm":
            #STEP : Compute statistics by models
            t_counter+=1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                      lambda: MS.generateStatModel(pathAppVal,
                                                                                   pathTilesFeat,
                                                                                   pathStats,
                                                                                   cmdPath + "/stats",
                                                                                   None, cfg)),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["stats_by_models"]))
            self.steps_group["learning"].append(t_counter)

        #STEP : Learning
        t_counter+=1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                  lambda: LT.launchTraining(pathAppVal,
                                                                            cfg, pathTilesFeat,
                                                                            dataField,
                                                                            pathStats,
                                                                            N, cmdPath + "/train",
                                                                            pathModels, workingDirectory, None)),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["training"]))
        self.steps_group["learning"].append(t_counter)

        #STEP : generate Classifications commands and masks
        t_counter+=1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: LC.launchClassification(pathModels, pathConf, pathStats,
                                                                                    pathTileRegion, pathTilesFeat,
                                                                                    shapeRegion, x,
                                                                                    N, cmdPath + "/cla", pathClassif, workingDirectory), [field_Region]),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["cmdClassifications"]))
        self.steps_group["classification"].append(t_counter)

        #STEP : generate Classifications
        t_counter+=1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: launchPythonCmd(imageClassifier.launchClassification, *x),
                                                  lambda: fu.parseClassifCmd(cmdPath + "/cla/class.txt")),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["classifications"]))
        self.steps_group["classification"].append(t_counter)

        if CLASSIFMODE == "separate":
            #STEP : Classification's shaping
            t_counter+=1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: CS.ClassificationShaping(x,
                                                                                         pathEnvelope,
                                                                                         pathTilesFeat,
                                                                                         fieldEnv, N,
                                                                                         classifFinal, workingDirectory,
                                                                                         pathConf, COLORTABLE), [pathClassif]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["classifShaping"]))
            self.steps_group["mosaic"].append(t_counter)

            #STEP : confusion matrix commands generation
            t_counter+=1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: GCM.genConfMatrix(x, pathAppVal,
                                                                                  N, dataField,
                                                                                  cmdPath + "/confusion",
                                                                                  pathConf, workingDirectory), [classifFinal]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["gen_confusionMatrix"]))
            self.steps_group["validation"].append(t_counter)

            #STEP : confusion matrix generation
            t_counter+=1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                      lambda: fu.getCmd(cmdPath + "/confusion/confusion.txt")),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["confusionMatrix"]))
            self.steps_group["validation"].append(t_counter)

            #STEP : confusion matrix fusion
            t_counter+=1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: confFus.confFusion(x, dataField,
                                                                                   classifFinal + "/TMP",
                                                                                   classifFinal + "/TMP",
                                                                                   classifFinal + "/TMP",
                                                                                   pathConf), [shapeData]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["confusionMatrixFusion"]))
            self.steps_group["validation"].append(t_counter)

            #STEP : results report generation
            t_counter+=1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: GR.genResults(x,
                                                                              NOMENCLATURE), [classifFinal]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["reportGen"]))
            self.steps_group["validation"].append(t_counter)

        elif CLASSIFMODE == "fusion" and MODE != "one_region":
            #STEP : Classifications fusion
            t_counter+=1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                      lambda: FUS.fusion(pathClassif, cfg, workingDirectory)),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["fusion"]))
            self.steps_group["classification"].append(t_counter)

            #STEP : Managing fusion's indecisions
            t_counter+=1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: ND.noData(PathTEST, x, field_Region,
                                                                          pathTilesFeat, shapeRegion,
                                                                          N, pathConf, workingDirectory),
                                                      lambda: fu.FileSearch_AND(pathClassif, True, "_FUSION_")),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["noData"]))
            self.steps_group["classification"].append(t_counter)

            #STEP : Classification's shaping
            t_counter+=1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: CS.ClassificationShaping(x,
                                                                                         pathEnvelope,
                                                                                         pathTilesFeat,
                                                                                         fieldEnv, N,
                                                                                         classifFinal, workingDirectory,
                                                                                         pathConf, COLORTABLE), [pathClassif]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["classifShaping"]))
            self.steps_group["mosaic"].append(t_counter)

            #STEP : confusion matrix commands generation
            t_counter+=1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: GCM.genConfMatrix(x, pathAppVal,
                                                                                  N, dataField,
                                                                                  cmdPath + "/confusion",
                                                                                  pathConf, workingDirectory), [classifFinal]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["gen_confusionMatrix"]))
            self.steps_group["validation"].append(t_counter)

            #STEP : confusion matrix generation
            t_counter+=1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                      lambda: fu.getCmd(cmdPath + "/confusion/confusion.txt")),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["confusionMatrix"]))
            self.steps_group["validation"].append(t_counter)

            #STEP : confusion matrix fusion
            t_counter+=1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: confFus.confFusion(x, dataField,
                                                                                   classifFinal + "/TMP",
                                                                                   classifFinal + "/TMP",
                                                                                   classifFinal + "/TMP",
                                                                                   pathConf), [shapeData]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["confusionMatrixFusion"]))
            self.steps_group["validation"].append(t_counter)

            #STEP : results report generation
            t_counter+=1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: GR.genResults(x,
                                                                              NOMENCLATURE), [classifFinal]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["reportGen"]))
            self.steps_group["validation"].append(t_counter)

        if outStat == "True":
            #STEP : compute output statistics tiles
            t_counter+=1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: OutS.outStats(pathConf, x,
                                                                              N, workingDirectory), tiles),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["statsReport"]))
            self.steps_group["validation"].append(t_counter)

            #STEP : merge statistics
            t_counter+=1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: MOutS.mergeOutStats(x), [pathConf]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["mergeOutStats"]))
            self.steps_group["validation"].append(t_counter)

        return t_container
