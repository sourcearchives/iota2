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
    def __init__(self, cfg, config_ressources):
        #Config object
        self.cfg = cfg
        
        #working directory, HPC
        self.HPC_working_directory = "TMPDIR"
        
        #steps definitions
        self.steps_group = OrderedDict()

        self.steps_group["init"] = OrderedDict()
        self.steps_group["sampling"] = OrderedDict()
        self.steps_group["dimred"] = OrderedDict()
        self.steps_group["learning"] = OrderedDict()
        self.steps_group["classification"] = OrderedDict()
        self.steps_group["mosaic"] = OrderedDict()
        self.steps_group["validation"] = OrderedDict()
        #build steps
        self.steps = self.build_steps(self.cfg, config_ressources)

    def get_dir(self):
        """
        usage : return iota2_directories
        """
        import os
        directories = ['classif', 'config_model', 'dataRegion', 'envelope',
                       'formattingVectors', 'metaData', 'samplesSelection',
                       'stats', 'cmd', 'dataAppVal', 'dimRed', 'final',
                       'learningSamples', 'model', 'shapeRegion', "features"]

        iota2_outputs_dir = self.cfg.getParam('chain', 'outputPath')
        
        return [os.path.join(iota2_outputs_dir, d) for d in directories]

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


    def build_steps(self, cfg, config_ressources=None):
        """
        build steps
        """
        from Cluster import get_RAM
        from Validation import OutStats as OutS
        from Validation import MergeOutStats as MOutS
        from Sampling import TileEnvelope as env
        from Sampling import TileArea as area
        from Learning import TrainingCmd as TC
        from Classification import ClassificationCmd as CC
        from Validation import ClassificationShaping as CS
        from Validation import GenConfusionMatrix as GCM
        from Sampling import DataAugmentation
        from Learning import ModelStat as MS
        from Validation import GenResults as GR
        import os
        from Classification import Fusion as FUS
        from Classification import NoData as ND
        from Validation import ConfusionFusion as confFus
        from Sampling import VectorSampler as vs
        from Sampling import VectorSamplesMerge as VSM
        from Common import IOTA2Directory as IOTA2_dir
        from Common import FileUtils as fu
        from Common.Tools import CoRegister
        from Sampling import DimensionalityReduction as DR
        from Sensors import NbView
        from Sensors.SAR import S1Processor as SAR
        from Classification import ImageClassifier as imageClassifier
        from Sampling import VectorFormatting as VF
        from Sampling import SplitSamples as splitS
        from Sampling import SamplesMerge as samplesMerge
        from Sampling import SamplesStat
        from Sampling import SamplesSelection
        from Classification import MergeFinalClassifications as mergeCl

        # get variable from configuration file
        PathTEST = cfg.getParam('chain', 'outputPath')
        TmpTiles = cfg.getParam('chain', 'listTile')
        tiles = TmpTiles.split(" ")
        Sentinel1 = cfg.getParam('chain', 'S1Path')
	VHR = cfg.getParam('coregistration','VHRPath')
        pathTilesFeat = os.path.join(PathTEST, "features")
        shapeRegion = cfg.getParam('chain', 'regionPath')
        field_Region = cfg.getParam('chain', 'regionField')
        model = cfg.getParam('chain', 'model')
        shapeData = cfg.getParam('chain', 'groundTruth')
        dataField = cfg.getParam('chain', 'dataField')
        N = cfg.getParam('chain', 'runs')
        CLASSIFMODE = cfg.getParam('argClassification', 'classifMode')
        NOMENCLATURE = cfg.getParam('chain', 'nomenclaturePath')
        COLORTABLE = cfg.getParam('chain', 'colorTable')
        RATIO = cfg.getParam('chain', 'ratio')
        outStat = cfg.getParam('chain', 'outputStatistics')
        classifier = cfg.getParam('argTrain', 'classifier')
        ds_sar_opt = cfg.getParam('argTrain', 'dempster_shafer_SAR_Opt_fusion')
        cloud_threshold = cfg.getParam('chain', 'cloud_threshold')
        enableCrossValidation = cfg.getParam('chain', 'enableCrossValidation')
        fusionClaAllSamplesVal = cfg.getParam('chain', 'fusionOfClassificationAllSamplesValidation')
        sampleManagement = cfg.getParam('argTrain', 'sampleManagement')
        pixType = fu.getOutputPixType(NOMENCLATURE)

        merge_final_classifications = cfg.getParam('chain', 'merge_final_classifications')
        merge_final_classifications_method = cfg.getParam('chain',
                                                          'merge_final_classifications_method')
        undecidedlabel = cfg.getParam("chain", "merge_final_classifications_undecidedlabel")
        dempstershafer_mob = cfg.getParam("chain", "dempstershafer_mob")
        keep_runs_results = cfg.getParam('chain', 'keep_runs_results')

        dimred = cfg.getParam('dimRed', 'dimRed')
        targetDimension = cfg.getParam('dimRed', 'targetDimension')
        reductionMode = cfg.getParam('dimRed', 'reductionMode')
        sample_augmentation = dict(cfg.getParam('argTrain', 'sampleAugmentation'))
        sample_augmentation_flag = sample_augmentation["activate"]

        #do not change
        fieldEnv = "FID"

        pathModels = PathTEST + "/model"
        pathEnvelope = PathTEST + "/envelope"
        pathClassif = PathTEST + "/classif"
        pathTileRegion = PathTEST + "/shapeRegion"
        classifFinal = PathTEST + "/final"
        dataRegion = PathTEST + "/dataRegion"
        pathAppVal = PathTEST + "/dataAppVal"
        pathSamples = PathTEST + "/learningSamples"
        pathStats = PathTEST + "/stats"
        cmdPath = PathTEST + "/cmd"

        from MPI import launch_tasks as tLauncher
        from MPI import ressourcesByStep as iota2Ressources
        if config_ressources:
            ressourcesByStep = iota2Ressources.iota2_ressources(config_ressources)
        else:
            ressourcesByStep = iota2Ressources.iota2_ressources()

        nbRuns = N
        if enableCrossValidation:
            nbRuns = N - 1

        t_container = []
        t_counter = 0
        
        pathConf = cfg.pathConf
        workingDirectory = os.getenv(self.HPC_working_directory)
        
        bashLauncherFunction = tLauncher.launchBashCmd
        launchPythonCmd = tLauncher.launchPythonCmd

        # STEP : directories.
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: IOTA2_dir.GenerateDirectories(x), [pathConf]),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["iota2_dir"]))
        self.steps_group["init"][t_counter] = "create directories"

        # STEP : preprocess SAR data
        if not "None" in Sentinel1:
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: SAR.S1PreProcess(Sentinel1, x, workingDirectory), tiles),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["SAR_pre_process"]))
            self.steps_group["init"][t_counter] = "Sentinel-1 pre-processing"

        # STEP : Common masks generation
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: fu.getCommonMasks(x, pathConf, workingDirectory), tiles),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["get_common_mask"]))
        self.steps_group["init"][t_counter] = "generate common masks"
        
        # STEP : Time series coregistration
        if not "None" in VHR:
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: CoRegister.launch_coregister(x,pathConf, workingDirectory),tiles),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["coregistration"]))
            self.steps_group["init"][t_counter] = "Time series coregistration on a VHR reference"

        # STEP : pix Validity by tiles generation
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: NbView.genNbView(x, "CloudThreshold_" + str(cloud_threshold) + ".shp", cloud_threshold, pathConf, workingDirectory), [os.path.join(pathTilesFeat, tile) for tile in tiles]),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["get_pixValidity"]))
        self.steps_group["init"][t_counter] = "compute validity mask by tile" 

        # STEP : Envelope generation
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: env.GenerateShapeTile(tiles, pathTilesFeat,
                                                                                  x, workingDirectory,
                                                                                  pathConf), [pathEnvelope]),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["envelope"]))
        self.steps_group["sampling"][t_counter] = "generate envelopes" 

        if not shapeRegion:
            # STEP : Region shape generation
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: area.generateRegionShape(pathEnvelope,
                                                                                         model, x,
                                                                                         field_Region, pathConf,
                                                                                         workingDirectory), [shapeRegion]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["regionShape"]))
            self.steps_group["sampling"][t_counter] = "generate region shapes" 

        # STEP : Samples formatting
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: VF.VectorFormatting(pathConf, x, workingDirectory),
                                                  tiles),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["samplesFormatting"]))
        self.steps_group["sampling"][t_counter] = "Prepare samples"

        if shapeRegion and CLASSIFMODE == "fusion":
            # STEP : Split learning polygons and Validation polygons in sub-sample if necessary
            # (too many samples to learn a model)
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: splitS.splitSamples(x, workingDirectory),
                                                      [pathConf]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["split_samples"]))
            self.steps_group["sampling"][t_counter] = "split learning polygons and Validation polygons in sub-sample if necessary"

        # STEP : Samples models merge
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: samplesMerge.samples_merge(x, pathConf, workingDirectory),
                                                  lambda: samplesMerge.get_models(os.path.join(PathTEST, "formattingVectors"), field_Region, nbRuns)),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["samplesMerge"]))
        self.steps_group["sampling"][t_counter] = "merge samples by models"

        # STEP : Samples statistics
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: SamplesStat.samples_stats(x, pathConf, workingDirectory),
                                                  lambda: SamplesStat.region_tile(os.path.join(PathTEST, "samplesSelection"))),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["samplesStatistics"]))
        self.steps_group["sampling"][t_counter] = "generate samples statistics"

        # STEP : compute selection by models
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: SamplesSelection.samples_selection(x, pathConf, workingDirectory),
                                                  lambda: fu.FileSearch_AND(os.path.join(PathTEST, "samplesSelection"), True, ".shp")),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["samplesSelection"]))
        self.steps_group["sampling"][t_counter] = "select samples by models"

        # STEP : merge selection by tiles
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: SamplesSelection.prepareSelection(os.path.join(PathTEST, "samplesSelection"), x, workingDirectory),
                                                  tiles),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["samplesSelection_tiles"]))
        self.steps_group["sampling"][t_counter] = "merge selections by tiles"

        # STEP : Samples Extraction
        t_counter += 1
        RAM_extraction = 1024.0 * get_RAM(ressourcesByStep["vectorSampler"].ram)
        t_container.append(tLauncher.Tasks(tasks=(lambda x: vs.generateSamples(x, workingDirectory, pathConf, RAM_extraction),
                                                  lambda: vs.get_vectors_to_sample(os.path.join(PathTEST, "formattingVectors"), ds_sar_opt)),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["vectorSampler"]))
        self.steps_group["sampling"][t_counter] = "generate samples"

        # STEP : MergeSamples
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: VSM.vectorSamplesMerge(pathConf, x),
                                                  lambda: VSM.tile_vectors_to_models(os.path.join(PathTEST, "learningSamples"), ds_sar_opt)),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["mergeSample"]))
        self.steps_group["sampling"][t_counter] = "merge samples"
        
        if sampleManagement and sampleManagement.lower() != 'none':
            # STEP : sampleManagement
            t_counter+=1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: DataAugmentation.DataAugmentationByCopy(dataField.lower(),
                                                                                                        sampleManagement,
                                                                                                        x, workingDirectory),
                                                      lambda: DataAugmentation.GetDataAugmentationByCopyParameters(PathTEST + "/learningSamples")),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["samplesManagement"]))
            self.steps_group["sampling"][t_counter] = "copy samples between models according to user request"

        if sample_augmentation_flag:
            # STEP : sampleAugmentation
            t_counter+=1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: DataAugmentation.DataAugmentationSynthetic(x,
                                                                                                           shapeData,
                                                                                                           dataField.lower(),
                                                                                                           sample_augmentation,
                                                                                                           workingDirectory),
                                                      lambda: DataAugmentation.GetDataAugmentationSyntheticParameters(PathTEST)),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["samplesAugmentation"]))
            self.steps_group["sampling"][t_counter] = "generate synthetic samples"
        # STEP : Dimensionality Reduction
        if dimred:
            t_counter+=1
            t_container.append(
                tLauncher.Tasks(tasks=(lambda x: 
                                       DR.SampleDimensionalityReduction(x, PathTEST,
                                                                        targetDimension,
                                                                        reductionMode),
                                       lambda: DR.BuildIOSampleFileLists(PathTEST)),
                                iota2_config=cfg,
                                ressources=ressourcesByStep["dimensionalityReduction"]))
            self.steps_group["dimred"][t_counter] = "dimensionality reduction"

        if classifier == "svm":
            # STEP : Compute statistics by models
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                      lambda: MS.generateStatModel(pathAppVal,
                                                                                   pathTilesFeat,
                                                                                   pathStats,
                                                                                   cmdPath + "/stats",
                                                                                   None, cfg)),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["stats_by_models"]))
            self.steps_group["learning"][t_counter] = "compute statistics for each model"        

        # STEP : Learning
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                  lambda: TC.launchTraining(cfg,
                                                                            dataField,
                                                                            pathStats,
                                                                            nbRuns, cmdPath + "/train",
                                                                            pathModels, workingDirectory)),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["training"]))
        self.steps_group["learning"][t_counter] = "learning"

        # STEP : generate Classifications commands and masks
        RAM_classification = 1024.0 * get_RAM(ressourcesByStep["classifications"].ram)
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: CC.launchClassification(pathModels, pathConf, pathStats,
                                                                                    pathTileRegion, pathTilesFeat,
                                                                                    shapeRegion, x,
                                                                                    nbRuns, cmdPath + "/cla", pathClassif,
                                                                                    RAM_classification, workingDirectory), [field_Region]),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["cmdClassifications"]))
        self.steps_group["classification"][t_counter] = "generate classification commands"

        # STEP : generate Classifications
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: launchPythonCmd(imageClassifier.launchClassification, *x),
                                                  lambda: fu.parseClassifCmd(cmdPath + "/cla/class.txt")),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["classifications"]))
        self.steps_group["classification"][t_counter] = "generate classifications"

        if ds_sar_opt:
            # STEP : confusion matrix by tiles by models
            t_counter += 1
            sar_opt_conf_ram = 1024.0 * get_RAM(ressourcesByStep["SAROptConfusionMatrix"].ram)
            t_container.append(tLauncher.Tasks(tasks=(lambda x: GCM.confusion_sar_optical(x, dataField, sar_opt_conf_ram),
                                                      lambda: GCM.confusion_sar_optical_parameter(PathTEST)),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["SAROptConfusionMatrix"]))
            self.steps_group["classification"][t_counter] = "evaluate SAR vs optical performance"

            # STEP : confusion matrix fusion
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: confFus.confusion_models_merge(x, dataField),
                                                      lambda: confFus.confusion_models_merge_parameters(PathTEST)),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["SAROptConfusionMatrixFusion"]))
            self.steps_group["classification"][t_counter] = "merge confusion matrix by SAR / optical models"

            # STEP : Dempster-Shafer fusion of classifications
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: FUS.dempster_shafer_fusion(PathTEST, x, workingDirectory=workingDirectory),
                                                      lambda: FUS.dempster_shafer_fusion_parameters(PathTEST)),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["SAROptFusion"]))
            self.steps_group["classification"][t_counter] = "fusion of SAR and optical classifications"

        if CLASSIFMODE == "fusion" and shapeRegion:
            # STEP : Classifications fusion
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                      lambda: FUS.fusion(pathClassif, cfg, None)),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["fusion"]))
            self.steps_group["classification"][t_counter] = "fusion of classification"

            # STEP : Managing fusion's indecisions
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: ND.noData(PathTEST, x, field_Region,
                                                                          pathTilesFeat, shapeRegion,
                                                                          nbRuns, pathConf, workingDirectory),
                                                      lambda: fu.FileSearch_AND(pathClassif, True, "_FUSION_")),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["noData"]))
            self.steps_group["classification"][t_counter] = "process fusion tile" 

        # STEP : Classification's shaping
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: CS.ClassificationShaping(x,
                                                                                     pathEnvelope,
                                                                                     pathTilesFeat,
                                                                                     fieldEnv, nbRuns,
                                                                                     classifFinal, workingDirectory,
                                                                                     pathConf, COLORTABLE), [pathClassif]),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["classifShaping"]))
        self.steps_group["mosaic"][t_counter] = "classification shaping" 

        # STEP : confusion matrix commands generation
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: GCM.genConfMatrix(x, pathAppVal,
                                                                              nbRuns, dataField,
                                                                              cmdPath + "/confusion",
                                                                              pathConf, workingDirectory), [classifFinal]),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["gen_confusionMatrix"]))
        self.steps_group["validation"][t_counter] = "confusion matrix command generation"

        if keep_runs_results:
            # STEP : confusion matrix generation
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                      lambda: fu.getCmd(cmdPath + "/confusion/confusion.txt")),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["confusionMatrix"]))
            self.steps_group["validation"][t_counter] = "confusion matrix generation" 

            # STEP : confusion matrix fusion
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: confFus.confFusion(x, dataField,
                                                                                   classifFinal + "/TMP",
                                                                                   classifFinal + "/TMP",
                                                                                   classifFinal + "/TMP",
                                                                                   pathConf), [shapeData]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["confusionMatrixFusion"]))
            self.steps_group["validation"][t_counter] = "confusion matrix fusion"

            # STEP : results report generation
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: GR.genResults(x,
                                                                              NOMENCLATURE), [classifFinal]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["reportGen"]))
            self.steps_group["validation"][t_counter] = "result report generation" 

        if merge_final_classifications and N > 1:
            t_counter += 1
            validationShape = None
            if fusionClaAllSamplesVal is True:
                validationShape = shapeData

            t_container.append(tLauncher.Tasks(tasks=(lambda x: mergeCl.mergeFinalClassifications(x,
                                                                                                  dataField,
                                                                                                  NOMENCLATURE,
                                                                                                  COLORTABLE,
                                                                                                  nbRuns,
                                                                                                  pixType,
                                                                                                  merge_final_classifications_method,
                                                                                                  undecidedlabel,
                                                                                                  dempstershafer_mob,
                                                                                                  keep_runs_results,
                                                                                                  enableCrossValidation,
                                                                                                  validationShape,
                                                                                                  workingDirectory), [PathTEST]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["merge_final_classifications"]))
            self.steps_group["validation"][t_counter] = "use final classifications to compute a majority voting map"

        if outStat:
            # STEP : compute output statistics tiles
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: OutS.outStats(pathConf, x,
                                                                              nbRuns, workingDirectory), tiles),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["statsReport"]))
            self.steps_group["validation"][t_counter] = "compute output statistics"

            # STEP : merge statistics
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: MOutS.mergeOutStats(x), [pathConf]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["mergeOutStats"]))
            self.steps_group["validation"][t_counter] = "merge statistics"

        return t_container
