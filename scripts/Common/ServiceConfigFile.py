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


import os
import sys
from osgeo import ogr
from config import Config, Sequence, Mapping, Container
from FileUtils import getFeatStackName, FileSearch_AND, getRasterNbands
from Common import ServiceError as sErr

# this is a pointer to the module object instance itself.
this = sys.modules[__name__]

# declaration of pathConf and cfg variables
this.pathConf = None
this.cfg = None

def clearConfig():
    if this.pathConf is not None:
        # also in local function scope. no scope specifier like global is needed
        this.pathConf = None
        this.cfg = None

class serviceConfigFile:
    """
    The class serviceConfigFile defines all methods to access to the
    configuration file and to check the variables.
    """

    def __init__(self, pathConf, iota_config=True):
        """
            Init class serviceConfigFile
            :param pathConf: string path of the config file
        """
        self.pathConf = pathConf
        self.cfg = Config(file(pathConf))
        #set default values
        if iota_config:
            #init chain section
            chain_default = {"outputStatistics": False,
                             "L5Path": "None",
                             "L8Path": "None",
                             "S2Path": "None",
                             "S2_output_path" : None,
                             "S2_S2C_Path": "None",
                             "S2_S2C_output_path": None,
                             "S1Path": "None",
                             "userFeatPath": "None",
                             "jobsPath" : None,
                             "runs": 1,
                             "enableCrossValidation" : False,
                             "model": "None",
                             "cloud_threshold": 0,
                             "splitGroundTruth":True,
                             "ratio": 0.5,
                             "firstStep": "init",
                             "lastStep": "validation",
                             "logFileLevel": "INFO",
                             "mode_outside_RegionSplit": 0.1,
                             "logFile": "iota2LogFile.log",
                             "logConsoleLevel": "INFO",
                             "regionPath": None,
                             "regionField": "region",
                             "logConsole": True,
                             "enableConsole": False,
                             "merge_final_classifications": False,
                             "merge_final_classifications_method": "majorityvoting",
                             "merge_final_classifications_undecidedlabel": 255,
                             "fusionOfClassificationAllSamplesValidation":False,
                             "dempstershafer_mob": "precision",
                             "merge_final_classifications_ratio": 0.1,
                             "keep_runs_results": True,
                             "remove_tmp_files": False}
            self.init_section("chain", chain_default)
            #init coregistration section
            coregistration_default = {"VHRPath":"None",
                              "dateVHR":"None",
                              "dateSrc":"None",
                              "bandRef":1,
                              "bandSrc":3,
                              "resample": True,
                              "step":256,
                              "minstep":16,
                              "minsiftpoints":40,
                              "iterate": True,
                              "prec":3,
                              "mode":2,
                              "pattern":'*STACK*'
                              }
            self.init_section("coregistration",coregistration_default)
            #init argTrain section
            sampleSel_default = self.init_dicoMapping({"sampler":"random",
                                                       "strategy":"all"})
            sampleAugmentationg_default = self.init_dicoMapping({"activate":False})
            annualCrop = self.init_listSequence(["11", "12"])
            ACropLabelReplacement = self.init_listSequence(["10", "annualCrop"])
            argTrain_default = {"sampleSelection": sampleSel_default,
                                "sampleAugmentation": sampleAugmentationg_default,
                                "sampleManagement": None,
                                "dempster_shafer_SAR_Opt_fusion":False,
                                "cropMix": False,
                                "prevFeatures":"None",
                                "outputPrevFeatures":"None",
                                "annualCrop": annualCrop,
                                "ACropLabelReplacement": ACropLabelReplacement,
                                "samplesClassifMix": False,
                                "annualClassesExtractionSource":"None",
                                "validityThreshold": 1}
            self.init_section("argTrain", argTrain_default)
            #init argClassification section
            argClassification_default = {"noLabelManagement": "maxConfidence",
                                         "fusionOptions": "-nodatalabel 0 -method majorityvoting"}
            self.init_section("argClassification", argClassification_default)
            #init GlobChain section
            GlobChain_default = {"features": self.init_listSequence(["NDVI", "NDWI", "Brightness"]),
                                 "autoDate": True,
                                 "writeOutputs": False,
                                 "useAdditionalFeatures": False,
                                 "useGapFilling": True}
            self.init_section("GlobChain", GlobChain_default)
            #init iota2FeatureExtraction reduction
            iota2FeatureExtraction_default = {"copyinput": True,
                                              "relrefl": False,
                                              "keepduplicates": True,
                                              "extractBands": False,
                                              "acorfeat": False}
            self.init_section("iota2FeatureExtraction", iota2FeatureExtraction_default)
            #init dimensionality reduction
            dimRed_default = {"dimRed": False,
                              "targetDimension": 4,
                              "reductionMode": "global"}
            self.init_section("dimRed", dimRed_default)
            #init sensors parameters
            Landsat8_default = {"additionalFeatures": "",
                                "temporalResolution": 16,
                                "startDate": "",
                                "endDate": "",
                                "keepBands": self.init_listSequence(["B1", "B2", "B3", "B4", "B5", "B6", "B7"])}
            Landsat5_default = {"additionalFeatures": "",
                                "temporalResolution": 16,
                                "startDate": "",
                                "endDate": "",
                                "keepBands": self.init_listSequence(["B1", "B2", "B3", "B4", "B5", "B6", "B7"])}
            Sentinel_2_default = {"additionalFeatures": "",
                                  "temporalResolution": 10,
                                  "startDate": "",
                                  "endDate": "",
                                  "keepBands": self.init_listSequence(["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11"])}
            Sentinel_2_S2C_default = {"additionalFeatures": "",
                                      "temporalResolution": 10,
                                      "startDate": "",
                                      "endDate": "",
                                      "keepBands": self.init_listSequence(["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11"])}
            userFeat =  {"arbo": "/*",
                         "patterns":"ALT,ASP,SLP"}

            self.init_section("Landsat5", Landsat5_default)
            self.init_section("Landsat8", Landsat8_default)
            self.init_section("Sentinel_2", Sentinel_2_default)
            self.init_section("Sentinel_2_S2C", Sentinel_2_S2C_default)
            self.init_section("userFeat", userFeat)

    def init_section(self, sectionName, sectionDefault):
        """use to initialize a full configuration file section
        
        Parameters
        ----------
        sectionName : string
            section's name
        sectionDefault : dict
            default values are store in a python dictionnary
        """
        if not hasattr(self.cfg, sectionName):
            section_default = self.init_dicoMapping(sectionDefault)
            self.cfg.addMapping(sectionName, section_default, "")
        for key, value in sectionDefault.items():
            self.addParam(sectionName, key, value)

    def init_dicoMapping(self, myDict):
        """use to init a mapping object from a dict
        """
        new_map = Mapping()
        for key, value in myDict.items():
            new_map.addMapping(key, value, "")
        return new_map

    def init_listSequence(self, myList):
        """use to init a Sequence object from a list
        """
        new_seq = Sequence()
        for elem in myList:
            new_seq.append(elem, "#comment")
        return new_seq

    def __repr__(self):
        return "Configuration file : " + self.pathConf

    def testVarConfigFile(self, section, variable, varType, valeurs="", valDefaut=""):
        """
            This function check if variable is in obj
            and if it has varType type.
            Optionnaly it can check if variable has values in valeurs
            Exit the code if any error are detected
            :param section: section name of the obj where to find
            :param variable: string name of the variable
            :param varType: type type of the variable for verification
            :param valeurs: string list of the possible value of variable
            :param valDefaut: value by default if variable is not in the configuration file
        """

        if not hasattr(self.cfg, section):
            raise sErr.configFileError("Section '" + str(section)
                                               + "' is not in the configuration file")

        objSection = getattr(self.cfg, section)

        if not hasattr(objSection, variable):
            if valDefaut != "":
                setattr(objSection, variable, valDefaut)
            else:
                raise sErr.parameterError(section,
                                                  "mandatory variable '" + str(variable) +
                                                  "' is missing in the configuration file")
        else:
            tmpVar = getattr(objSection, variable)

            if not isinstance(tmpVar, varType):
                message = "variable '" + str(variable) +\
                "' has a wrong type\nActual: " + str(type(tmpVar)) +\
                " expected: " + str(varType)
                raise sErr.parameterError(section, message)

            if valeurs != "":
                ok = 0
                for index in range(len(valeurs)):
                    if tmpVar == valeurs[index]:
                        ok = 1
                if ok == 0:
                    message = "bad value for '" + variable +\
                    "' variable. Value accepted: " + str(valeurs) +\
                    " Value read: " + str(tmpVar)
                    raise sErr.parameterError(section, message)

    def testDirectory(self, directory):
        if not os.path.exists(directory):
            raise sErr.dirError(directory)

    def checkConfigParameters(self):
        """
            check parameters coherence
            :return: true if ok
        """

        def check_sampleAugmentation():
            """
            """
            def check_parameters(sampleAug):

                not_allowed_p = ["in", "out", "field", "layer", "label", "seed", "inxml", "progress", "help"]
                for p in not_allowed_p:
                    if p in sampleAug:
                        raise sErr.configError("'{}' parameter must not be set in argTrain.sampleAugmentation".format(p))

                if "strategy" in sampleAug:
                    strategy = sampleAug["strategy"]
                    if strategy not in ["replicate", "jitter", "smote"]:
                        raise sErr.configError("augmentation strategy must be 'replicate', 'jitter' or 'smote'")
                if "strategy.jitter.stdFactor" in sampleAug:
                    jitter = sampleAug["strategy.jitter.stdFactor"]
                    if not isinstance(jitter, int):
                        raise sErr.configError("strategy.jitter.stdFactor must an integer")
                if "strategy.smote.neighbors" in sampleAug:
                    byclass = sampleAug["strategy.smote.neighbors"]
                    if not isinstance(byclass, int):
                        raise sErr.configError("strategy.smote.neighbors must be an integer")
                if "samples.strategy" in sampleAug:
                    samples_strategy = sampleAug["samples.strategy"]
                    if samples_strategy not in ["minNumber", "balance", "byClass"]:
                        raise sErr.configError("augmentation strategy must be 'minNumber', 'balance' or 'byClass'")
                if "samples.strategy.minNumber" in sampleAug:
                    minNumber = sampleAug["samples.strategy.minNumber"]
                    if not isinstance(minNumber, int):
                        raise sErr.configError("samples.strategy.minNumber must an integer")
                if "samples.strategy.byClass" in sampleAug:
                    byClass = sampleAug["samples.strategy.byClass"]
                    if not isinstance(byClass, str):
                        raise sErr.configError("samples.strategy.byClass must be a string")
                if "activate" in sampleAug:
                    activate = sampleAug["activate"]
                    if not isinstance(activate, bool):
                        raise sErr.configError("activate must be a bool")
                if "target_models" in sampleAug:
                    TargetModels = sampleAug["target_models"]
                    if not isinstance(TargetModels, Sequence):
                        raise sErr.configError("target_models must a list")
                    if not isinstance(TargetModels[0], str):
                        raise sErr.configError("target_models must constains strings")

            sampleAug = dict(self.cfg.argTrain.sampleAugmentation)
            check_parameters(sampleAug)

        def check_sampleSelection():
            """
            """
            def check_parameters(sampleSel):

                not_allowed_p = ["outrates", "in", "mask", "vec", "out", "instats", "field", "layer", "rand", "inxml"]
                strats = ["byclass", "constant", "percent", "total", "smallest", "all"]
                for p in not_allowed_p:
                    if p in sampleSel:
                        raise sErr.configError("'{}' parameter must not be set in argTrain.sampleSelection".format(p))

                if "sampler" in sampleSel:
                    sampler = sampleSel["sampler"]
                    if sampler not in ["periodic", "random"]:
                        raise sErr.configError("sampler must be 'periodic' or 'random'")
                if "sampler.periodic.jitter" in sampleSel:
                    jitter = sampleSel["sampler.periodic.jitter"]
                    if not isinstance(jitter, int):
                        raise sErr.configError("jitter must an integer")
                if "strategy" in sampleSel:
                    strategy = sampleSel["strategy"]
                    if strategy not in strats:
                        raise sErr.configError("strategy must be {}".format(' or '.join(["'{}'".format(elem) for elem in strats])))
                if "strategy.byclass.in" in sampleSel:
                    byclass = sampleSel["strategy.byclass.in"]
                    if not isinstance(byclass, str):
                        raise sErr.configError("strategy.byclass.in must a string")
                if "strategy.constant.nb" in sampleSel:
                    constant = sampleSel["strategy.constant.nb"]
                    if not isinstance(constant, int):
                        raise sErr.configError("strategy.constant.nb must an integer")
                if "strategy.percent.p" in sampleSel:
                    percent = sampleSel["strategy.percent.p"]
                    if not isinstance(percent, float):
                        raise sErr.configError("strategy.percent.p must a float")
                if "strategy.total.v" in sampleSel:
                    total = sampleSel["strategy.total.v"]
                    if not isinstance(total, int):
                        raise sErr.configError("strategy.total.v must an integer")
                if "elev.dem" in sampleSel:
                    dem = sampleSel["elev.dem"]
                    if not isinstance(dem, str):
                        raise sErr.configError("elev.dem must a string")
                if "elev.geoid" in sampleSel:
                    geoid = sampleSel["elev.geoid"]
                    if not isinstance(geoid, str):
                        raise sErr.configError("elev.geoid must a string")
                if "elev.default" in sampleSel:
                    default = sampleSel["elev.default"]
                    if not isinstance(default, float):
                        raise sErr.configError("elev.default must a float")
                if "ram" in sampleSel:
                    ram = sampleSel["ram"]
                    if not isinstance(ram, int):
                        raise sErr.configError("ram must a int")
                if "target_model" in sampleSel:
                    target_model = sampleSel["target_model"]
                    if not isinstance(target_model, int):
                        raise sErr.configError("target_model must an integer")

            sampleSel = dict(self.cfg.argTrain.sampleSelection)
            check_parameters(sampleSel)
            if "per_model" in sampleSel:
                for model in sampleSel["per_model"]:
                    check_parameters(dict(model))

        def check_region_vector(cfg):
            """
            """
            region_path = cfg.chain.regionPath
            if not region_path:
                raise sErr.configError("chain.regionPath must be set")

            region_field = cfg.chain.regionField
            if not region_path:
                raise sErr.configError("chain.regionField must be set")

            driver = ogr.GetDriverByName("ESRI Shapefile")
            dataSource = driver.Open(region_path, 0)
            if dataSource is None:
                raise Exception("Could not open " + region_path)
            layer = dataSource.GetLayer()
            field_index = layer.FindFieldIndex(region_field, False)
            layerDefinition = layer.GetLayerDefn()
            fieldTypeCode = layerDefinition.GetFieldDefn(field_index).GetType()
            fieldType = layerDefinition.GetFieldDefn(field_index).GetFieldTypeName(fieldTypeCode)
            if fieldType != "String":
                raise sErr.configError("the region field must be a string")


        def all_sameBands(items):
            return all(bands == items[0][1] for path, bands in items)

        try:
            # test of variable
            self.testVarConfigFile('chain', 'outputPath', str)
            self.testVarConfigFile('chain', 'pyAppPath', str)
            self.testVarConfigFile('chain', 'nomenclaturePath', str)
            self.testVarConfigFile('chain', 'listTile', str)
            self.testVarConfigFile('chain', 'L5Path', str)
            self.testVarConfigFile('chain', 'L8Path', str)
            self.testVarConfigFile('chain', 'S2Path', str)
            self.testVarConfigFile('chain', 'S1Path', str)

            self.testVarConfigFile('chain', 'firstStep', str, ["init", "sampling", "dimred", "learning", "classification", "mosaic", "validation"])
            self.testVarConfigFile('chain', 'lastStep', str, ["init", "sampling", "dimred", "learning", "classification", "mosaic", "validation"])

            if self.getParam("chain", "regionPath"):
                check_region_vector(self.cfg)
            self.testVarConfigFile('chain', 'regionField', str)
            self.testVarConfigFile('chain', 'model', str)
            self.testVarConfigFile('chain', 'enableCrossValidation', bool)
            self.testVarConfigFile('chain', 'groundTruth', str)
            self.testVarConfigFile('chain', 'dataField', str)
            self.testVarConfigFile('chain', 'runs', int)
            self.testVarConfigFile('chain', 'ratio', float)
            self.testVarConfigFile('chain', 'splitGroundTruth', bool)
            self.testVarConfigFile('chain', 'outputStatistics', bool)
            self.testVarConfigFile('chain', 'cloud_threshold', int)
            self.testVarConfigFile('chain', 'spatialResolution', int)
            self.testVarConfigFile('chain', 'colorTable', str)
            self.testVarConfigFile('chain', 'mode_outside_RegionSplit', float)
            self.testVarConfigFile('chain', 'merge_final_classifications', bool)
            if self.getParam("chain", "merge_final_classifications"):
                self.testVarConfigFile('chain', 'merge_final_classifications_undecidedlabel', int)
                self.testVarConfigFile('chain', 'merge_final_classifications_ratio', float)
                self.testVarConfigFile('chain', 'merge_final_classifications_method',
                                       str, ["majorityvoting", "dempstershafer"])
                self.testVarConfigFile('chain', 'dempstershafer_mob',
                                       str, ["precision", "recall", "accuracy", "kappa"])
                self.testVarConfigFile('chain', 'keep_runs_results', bool)
                self.testVarConfigFile('chain', 'fusionOfClassificationAllSamplesValidation', bool)

            self.testVarConfigFile('argTrain', 'classifier', str)
            self.testVarConfigFile('argTrain', 'options', str)
            self.testVarConfigFile('argTrain', 'cropMix', bool)
            self.testVarConfigFile('argTrain', 'dempster_shafer_SAR_Opt_fusion', bool)
            self.testVarConfigFile('argTrain', 'prevFeatures', str)
            self.testVarConfigFile('argTrain', 'outputPrevFeatures', str)
            self.testVarConfigFile('argTrain', 'annualCrop', Sequence)
            self.testVarConfigFile('argTrain', 'ACropLabelReplacement', Sequence)

            self.testVarConfigFile('argTrain', 'sampleSelection', Mapping)
            self.testVarConfigFile('argTrain', 'samplesClassifMix', bool)
            self.testVarConfigFile('argTrain', 'validityThreshold', int)

            check_sampleSelection()
            check_sampleAugmentation()

            self.testVarConfigFile('argClassification', 'classifMode', str, ["separate", "fusion"])
            self.testVarConfigFile('argClassification', 'noLabelManagement', str, ["maxConfidence", "learningPriority"])

            self.testVarConfigFile('GlobChain', 'proj', str)
            self.testVarConfigFile('GlobChain', 'features', Sequence)
            self.testVarConfigFile('GlobChain', 'autoDate', bool)
            self.testVarConfigFile('GlobChain', 'writeOutputs', bool)
            self.testVarConfigFile('GlobChain', 'useAdditionalFeatures', bool)
            self.testVarConfigFile('GlobChain', 'useGapFilling', bool)

            self.testVarConfigFile('iota2FeatureExtraction', 'copyinput', bool)
            self.testVarConfigFile('iota2FeatureExtraction', 'relrefl', bool)
            self.testVarConfigFile('iota2FeatureExtraction', 'keepduplicates', bool)
            self.testVarConfigFile('iota2FeatureExtraction', 'extractBands', bool)
            self.testVarConfigFile('iota2FeatureExtraction', 'acorfeat', bool)

            self.testVarConfigFile('dimRed', 'dimRed', bool)
            self.testVarConfigFile('dimRed', 'targetDimension', int)
            self.testVarConfigFile('dimRed', 'reductionMode', str)

            self.testVarConfigFile('chain', 'remove_tmp_files', bool)

            if self.cfg.chain.L5Path != "None":
                #L5 variable check
                self.testVarConfigFile('Landsat5', 'temporalResolution', int)
                self.testVarConfigFile('Landsat5', 'keepBands', Sequence)

            if self.cfg.chain.L8Path != "None":
                #L8 variable check
                self.testVarConfigFile('Landsat8', 'temporalResolution', int)
                self.testVarConfigFile('Landsat8', 'keepBands', Sequence)

            if self.cfg.chain.S2Path != "None":
                #S2 variable check
                self.testVarConfigFile('Sentinel_2', 'temporalResolution', int)
                self.testVarConfigFile('Sentinel_2', 'keepBands', Sequence)

            nbTile = len(self.cfg.chain.listTile.split(" "))

            # directory tests
            if self.getParam("chain", "jobsPath"):
                self.testDirectory(self.getParam("chain", "jobsPath"))

            self.testDirectory(self.cfg.chain.pyAppPath)
            self.testDirectory(self.cfg.chain.nomenclaturePath)
            self.testDirectory(self.cfg.chain.groundTruth)
            self.testDirectory(self.cfg.chain.colorTable)
            if self.cfg.chain.S2_output_path:
                self.testDirectory(self.cfg.chain.S2_output_path)
            if self.cfg.chain.S2_S2C_output_path:
                self.testDirectory(self.cfg.chain.S2_S2C_output_path)
            # test of groundTruth file
            Field_FType = []
            dataSource = ogr.Open(self.cfg.chain.groundTruth)
            daLayer = dataSource.GetLayer(0)
            layerDefinition = daLayer.GetLayerDefn()
            for i in range(layerDefinition.GetFieldCount()):
                fieldName = layerDefinition.GetFieldDefn(i).GetName()
                fieldTypeCode = layerDefinition.GetFieldDefn(i).GetType()
                fieldType = layerDefinition.GetFieldDefn(i).GetFieldTypeName(fieldTypeCode)
                Field_FType.append((fieldName, fieldType))
            flag = 0
            for currentField, fieldType in Field_FType:
                if currentField == self.cfg.chain.dataField:
                    flag = 1
                    if "Integer" not in fieldType:
                        raise sErr.fileError("the data's field " +
                                                     currentField + " must be an integer in " +
                                                     self.cfg.chain.groundTruth)
            if flag == 0:
                raise sErr.fileError("field name '" +
                                             self.cfg.chain.dataField + "' doesn't exist in " +
                                             self.cfg.chain.groundTruth)

            # parameters compatibilities check
            if self.getParam("chain", "regionPath") is None and self.cfg.argClassification.classifMode == "fusion":
                raise sErr.configError("you can't chose 'one_region' mode and ask a fusion of classifications\n")
            if self.cfg.chain.merge_final_classifications and self.cfg.chain.runs == 1:
                raise sErr.configError("these parameters are incompatible runs:1 and merge_final_classifications:True")
            if self.cfg.chain.enableCrossValidation and self.cfg.chain.runs == 1:
                raise sErr.configError("these parameters are incompatible runs:1 and enableCrossValidation:True")
            if self.cfg.chain.enableCrossValidation and self.cfg.chain.splitGroundTruth is False:
                raise sErr.configError("these parameters are incompatible splitGroundTruth:False and enableCrossValidation:True")
            if self.cfg.chain.splitGroundTruth is False and self.cfg.chain.runs != 1:
                raise sErr.configError("these parameters are incompatible splitGroundTruth:False and runs different from 1")
            if self.cfg.chain.merge_final_classifications and self.cfg.chain.splitGroundTruth is False:
                raise sErr.configError("these parameters are incompatible merge_final_classifications:True and splitGroundTruth:False")
            if self.cfg.argTrain.dempster_shafer_SAR_Opt_fusion and 'None' in self.cfg.chain.S1Path:
                raise sErr.configError("these parameters are incompatible dempster_shafer_SAR_Opt_fusion : True and S1Path : 'None'")
            if self.cfg.argTrain.dempster_shafer_SAR_Opt_fusion and 'None' in self.cfg.chain.userFeatPath and 'None' in self.cfg.chain.L5Path and 'None' in self.cfg.chain.L8Path and 'None' in self.cfg.chain.S2Path and 'None' in self.cfg.chain.S2_S2C_Path:
                raise sErr.configError("to perform post-classification fusion, optical data must be used")
        # Error managed
        except sErr.configFileError:
            print "Error in the configuration file " + self.pathConf
            raise
        # Warning error not managed !
        except Exception:
            print "Something wrong happened in serviceConfigFile !"
            raise

        return True

    def getAvailableSections(self):
        """
        Return all sections in the configuration file
        :return: list of available section
        """
        return [section for section in self.cfg.iterkeys()]

    def getParam(self, section, variable):
        """
            Return the value of variable in the section from config
            file define in the init phase of the class.
            :param section: string name of the section
            :param variable: string name of the variable
            :return: the value of variable
        """

        if not hasattr(self.cfg, section):
            # not an osoError class because it should NEVER happened
            raise Exception("Section is not in the configuration file: " + str(section))

        objSection = getattr(self.cfg, section)
        if not hasattr(objSection, variable):
            # not an osoError class because it should NEVER happened
            raise Exception("Variable is not in the configuration file: " + str(variable))

        tmpVar = getattr(objSection, variable)

        return tmpVar

    def setParam(self, section, variable, value):
        """
            Set the value of variable in the section from config
            file define in the init phase of the class.
            Mainly used in Unitary test in order to force a value
            :param section: string name of the section
            :param variable: string name of the variable
            :param value: value to set
        """

        if not hasattr(self.cfg, section):
            # not an osoError class because it should NEVER happened
            raise Exception("Section is not in the configuration file: " + str(section))

        objSection = getattr(self.cfg, section)

        if not hasattr(objSection, variable):
            # not an osoError class because it should NEVER happened
            raise Exception("Variable is not in the configuration file: " + str(variable))

        setattr(objSection, variable, value)

    def addParam(self, section, variable, value):
        """
            ADD and set a parameter in an existing section in the config
            file define in the init phase of the class.
            Do nothing if the parameter exist.
            :param section: string name of the section
            :param variable: string name of the variable
            :param value: value to set
        """
        if not hasattr(self.cfg, section):
            raise Exception("Section is not in the configuration file: " + str(section))
        objSection = getattr(self.cfg, section)
        if not hasattr(objSection, variable):
            setattr(objSection, variable, value)

    def forceParam(self, section, variable, value):
        """
            ADD a parameter in an existing section in the config
            file define in the init phase of the class if the parameter
            doesn't exist.
            FORCE the value if the parameter exist.
            Mainly used in Unitary test in order to force a value
            :param section: string name of the section
            :param variable: string name of the variable
            :param value: value to set
        """

        if not hasattr(self.cfg, section):
            # not an osoError class because it should NEVER happened
            raise Exception("Section is not in the configuration file: " + str(section))

        objSection = getattr(self.cfg, section)

        if not hasattr(objSection, variable):
            # It's normal because the parameter should not already exist
            # creation of attribute
            setattr(objSection, variable, value)

        else:
            # It already exist !!
            # setParam instead !!
            self.setParam(section, variable, value)

