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
from osgeo import ogr
from config import Config, Sequence, Mapping
from fileUtils import getFeatStackName, FileSearch_AND, getRasterNbands
import serviceError
import sys

# this is a pointer to the module object instance itself.
this = sys.modules[__name__]

# declaration of pathConf and cfg variables
this.pathConf = None
this.cfg = None

def initializeConfig(pathConf_name):
    if this.pathConf is None:
        # first set of pathConf and cfg
        if pathConf_name is None:
            raise Exception("First call to serviceConfigFile: pathConf_name is not define")
        this.pathConf = pathConf_name
        this.cfg = Config(file(pathConf_name))

def clearConfig():
    if not this.pathConf is None:
        # also in local function scope. no scope specifier like global is needed
        this.pathConf = None
        this.cfg = None

class serviceConfigFile:
    """
    The class serviceConfigFile defines all methods to access to the
    configuration file and to check the variables.
    """

    def __init__(self, pathConf, checkConfig=True):
        """
            Init class serviceConfigFile
            :param pathConf: string path of the config file
        """
        #initializeConfig(pathConf)
        #self.cfg = this.cfg
        #self.pathConf = this.pathConf
        self.pathConf = pathConf
        self.cfg = Config(file(pathConf))
        
        # COMPATIBILITY with old version of config files
        # Test if logFile, logLevel, logFileLevel, logConsoleLevel and logConsole exist.
        if checkConfig:
            try:
                self.testVarConfigFile('chain', 'logFile', str)
            except serviceError.configFileError:
                self.addParam('chain', 'logFile', 'iota2LogFile.log')
            try:
                self.testVarConfigFile('chain', 'logFileLevel', str)
            except serviceError.configFileError:
                # set logFileLevel to INFO by default
                self.addParam('chain', 'logFileLevel', "INFO")
            try:
                self.testVarConfigFile('chain', 'logConsoleLevel', str)
            except serviceError.configFileError:
                # set logConsoleLevel to INFO by default
                self.addParam('chain', 'logConsoleLevel', "INFO")
            try:
                self.testVarConfigFile('chain', 'logConsole', bool)
            except serviceError.configFileError:
                # set logConcole to true
                self.addParam('chain', 'logConsole', True)
            try:
                self.testVarConfigFile('chain', 'enableConsole', bool)
            except serviceError.configFileError:
                # set logConcole to true
                self.addParam('chain', 'enableConsole', False)

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
            raise serviceError.configFileError("Section '" + str(section)
                    + "' is not in the configuration file")

        objSection = getattr(self.cfg, section)

        if not hasattr(objSection, variable):
            if valDefaut != "":
                setattr(objSection, variable, valDefaut)
            else:
                raise serviceError.parameterError(section,
                "mandatory variable '" + str(variable) +
                "' is missing in the configuration file")
        else:
            tmpVar = getattr(objSection, variable)

            if not isinstance(tmpVar, varType):
                message = "variable '" + str(variable) +\
                "' has a wrong type\nActual: " + str(type(tmpVar)) +\
                " expected: " + str(varType)
                raise serviceError.parameterError(section, message)

            if valeurs != "":
                ok = 0
                for index in range(len(valeurs)):
                    if tmpVar == valeurs[index]:
                        ok = 1
                if ok == 0:
                    message = "bad value for '" + variable +\
                    "' variable. Value accepted: " + str(valeurs) +\
                    " Value read: " + str(tmpVar)
                    raise serviceError.parameterError(section, message)
    
    def testDirectory(self, directory):
        if not os.path.exists(directory):
            raise serviceError.dirError(directory)

    def checkConfigParameters(self):
        """
            check parameters coherence
            :return: true if ok
        """

        def check_sampleSelection():
            """
            """
            def check_parameters(sampleSel):
                
                not_allowed_p = ["outrates", "in", "mask", "vec", "out", "instats", "field", "layer", "rand", "inxml"]
                strats = ["byclass", "constant", "percent", "total", "smallest", "all"]
                for p in not_allowed_p:
                    if p in sampleSel:
                        raise serviceError.configError("'{}' parameter must not be set in argTrain.sampleSelection".format(p))
                    
                if "sampler" in sampleSel:
                    sampler = sampleSel["sampler"]
                    if not sampler in ["periodic", "random"]:
                        raise serviceError.configError("sampler must be 'periodic' or 'random'")
                if "sampler.periodic.jitter" in sampleSel:
                    jitter = sampleSel["sampler.periodic.jitter"]
                    if not isinstance(jitter, int):
                        raise serviceError.configError("jitter must an integer")
                if "strategy" in sampleSel:
                    strategy = sampleSel["strategy"]
                    if not strategy in strats:
                        raise serviceError.configError("strategy must be {}".format(' or '.join(["'{}'".format(elem) for elem in strats])))
                if "strategy.byclass.in" in sampleSel:
                    byclass = sampleSel["strategy.byclass.in"]
                    if not isinstance(byclass, str):
                        raise serviceError.configError("strategy.byclass.in must a string")
                if "strategy.constant.nb" in sampleSel:
                    constant = sampleSel["strategy.constant.nb"]
                    if not isinstance(constant, int):
                        raise serviceError.configError("strategy.constant.nb must an integer")
                if "strategy.percent.p" in sampleSel:
                    percent = sampleSel["strategy.percent.p"]
                    if not isinstance(percent, float):
                        raise serviceError.configError("strategy.percent.p must a float")
                if "strategy.total.v" in sampleSel:
                    total = sampleSel["strategy.total.v"]
                    if not isinstance(total, int):
                        raise serviceError.configError("strategy.total.v must an integer")
                if "elev.dem" in sampleSel:
                    dem = sampleSel["elev.dem"]
                    if not isinstance(dem, str):
                        raise serviceError.configError("elev.dem must a string")
                if "elev.geoid" in sampleSel:
                    geoid = sampleSel["elev.geoid"]
                    if not isinstance(geoid, str):
                        raise serviceError.configError("elev.geoid must a string")
                if "elev.default" in sampleSel:
                    default = sampleSel["elev.default"]
                    if not isinstance(default, float):
                        raise serviceError.configError("elev.default must a float")
                if "ram" in sampleSel:
                    ram = sampleSel["ram"]
                    if not isinstance(ram, int):
                        raise serviceError.configError("ram must a float")
                if "target_model" in sampleSel:
                    target_model = sampleSel["target_model"]
                    if not isinstance(target_model, int):
                        raise serviceError.configError("target_model must an integer")
        
            sampleSel = dict(self.cfg.argTrain.sampleSelection)
            check_parameters(sampleSel)
            if "per_model" in sampleSel:
                for model in sampleSel["per_model"]:
                    check_parameters(dict(model))

        def check_region_vector(cfg):
            """
            """
            region_path = cfg.chain.regionPath
            region_field = cfg.chain.regionField
            if cfg.chain.mode == "outside":
                driver = ogr.GetDriverByName("ESRI Shapefile")
                dataSource = driver.Open(region_path, 0)
                if dataSource is None:
                    raise Exception("Could not open " + region_path)
                layer = dataSource.GetLayer()
                field_index = layer.FindFieldIndex(region_field, False)
                layerDefinition = layer.GetLayerDefn()
                fieldTypeCode = layerDefinition.GetFieldDefn(field_index).GetType()
                fieldType = layerDefinition.GetFieldDefn(field_index).GetFieldTypeName(fieldTypeCode)
                if not fieldType == "String":
                    raise serviceError.configError("the region field must be a string")

        
        def all_sameBands(items):
            return all(bands == items[0][1] for path, bands in items)

        try:
            #self.cfg.chain.nomenclaturePath
            check_region_vector(self.cfg)
            
            # test of variable
            self.testVarConfigFile('chain', 'executionMode', str)
            self.testVarConfigFile('chain', 'outputPath', str)
            self.testVarConfigFile('chain', 'jobsPath', str)
            self.testVarConfigFile('chain', 'pyAppPath', str)
            self.testVarConfigFile('chain', 'chainName', str)
            self.testVarConfigFile('chain', 'nomenclaturePath', str)
            self.testVarConfigFile('chain', 'listTile', str)
            self.testVarConfigFile('chain', 'featuresPath', str)
            self.testVarConfigFile('chain', 'L5Path', str)
            self.testVarConfigFile('chain', 'L8Path', str)
            self.testVarConfigFile('chain', 'S2Path', str)
            self.testVarConfigFile('chain', 'S1Path', str)
            self.testVarConfigFile('chain', 'mode', str, ["one_region", "multi_regions", "outside"])
            self.testVarConfigFile('chain', 'firstStep', str, ["init", "sampling", "learning", "classification", "mosaic", "validation"])
            self.testVarConfigFile('chain', 'lastStep', str, ["init", "sampling", "learning", "classification", "mosaic", "validation"])
            self.testVarConfigFile('chain', 'regionPath', str)
            self.testVarConfigFile('chain', 'regionField', str)
            self.testVarConfigFile('chain', 'model', str)
            self.testVarConfigFile('chain', 'groundTruth', str)
            self.testVarConfigFile('chain', 'dataField', str)
            self.testVarConfigFile('chain', 'runs', int)
            self.testVarConfigFile('chain', 'ratio', float)
            self.testVarConfigFile('chain', 'outputStatistics', bool)
            self.testVarConfigFile('chain', 'cloud_threshold', int)
            self.testVarConfigFile('chain', 'spatialResolution', int)
            self.testVarConfigFile('chain', 'logPath', str)
            self.testVarConfigFile('chain', 'colorTable', str)
            self.testVarConfigFile('chain', 'mode_outside_RegionSplit', float)

            self.testVarConfigFile('argTrain', 'classifier', str)
            self.testVarConfigFile('argTrain', 'options', str)
            self.testVarConfigFile('argTrain', 'cropMix', bool)
            self.testVarConfigFile('argTrain', 'prevFeatures', str)
            self.testVarConfigFile('argTrain', 'outputPrevFeatures', str)
            self.testVarConfigFile('argTrain', 'annualCrop', Sequence)
            self.testVarConfigFile('argTrain', 'ACropLabelReplacement', Sequence)
            self.testVarConfigFile('argTrain', 'sampleSelection', Mapping)
            self.testVarConfigFile('argTrain', 'samplesClassifMix', bool)
            self.testVarConfigFile('argTrain', 'validityThreshold', int)

            check_sampleSelection()

            self.testVarConfigFile('argClassification', 'classifMode', str, ["separate", "fusion"])
            self.testVarConfigFile('argClassification', 'pixType', str)
            self.testVarConfigFile('argClassification', 'noLabelManagement', str, ["maxConfidence", "learningPriority"])

            self.testVarConfigFile('GlobChain', 'proj', str)
            self.testVarConfigFile('GlobChain', 'features', Sequence)

            if self.cfg.chain.L5Path != "None":
                #L5 variable check
                self.testVarConfigFile('Landsat5', 'nodata_Mask', str, ["True", "False"])
                self.testVarConfigFile('Landsat5', 'nativeRes', int)
                self.testVarConfigFile('Landsat5', 'arbo', str)
                self.testVarConfigFile('Landsat5', 'imtype', str)
                self.testVarConfigFile('Landsat5', 'nuages', str)
                self.testVarConfigFile('Landsat5', 'saturation', str)
                self.testVarConfigFile('Landsat5', 'div', str)
                self.testVarConfigFile('Landsat5', 'nodata', str)
                self.testVarConfigFile('Landsat5', 'arbomask', str)
                self.testVarConfigFile('Landsat5', 'startDate', str)
                self.testVarConfigFile('Landsat5', 'endDate', str)
                self.testVarConfigFile('Landsat5', 'temporalResolution', str)
                self.testVarConfigFile('Landsat5', 'keepBands', Sequence)

            if self.cfg.chain.L8Path != "None":
                #L8 variable check
                self.testVarConfigFile('Landsat8', 'nodata_Mask', str, ["True", "False"])
                self.testVarConfigFile('Landsat8', 'nativeRes', int)
                self.testVarConfigFile('Landsat8', 'arbo', str)
                self.testVarConfigFile('Landsat8', 'imtype', str)
                self.testVarConfigFile('Landsat8', 'nuages', str)
                self.testVarConfigFile('Landsat8', 'saturation', str)
                self.testVarConfigFile('Landsat8', 'div', str)
                self.testVarConfigFile('Landsat8', 'nodata', str)
                self.testVarConfigFile('Landsat8', 'arbomask', str)
                self.testVarConfigFile('Landsat8', 'startDate', str)
                self.testVarConfigFile('Landsat8', 'endDate', str)
                self.testVarConfigFile('Landsat8', 'temporalResolution', str)
                self.testVarConfigFile('Landsat8', 'keepBands', Sequence)

            if self.cfg.chain.S2Path != "None":
                #S2 variable check
                self.testVarConfigFile('Sentinel_2', 'nodata_Mask', str)
                self.testVarConfigFile('Sentinel_2', 'nativeRes', int)
                self.testVarConfigFile('Sentinel_2', 'arbo', str)
                self.testVarConfigFile('Sentinel_2', 'imtype', str)
                self.testVarConfigFile('Sentinel_2', 'nuages', str)
                self.testVarConfigFile('Sentinel_2', 'saturation', str)
                self.testVarConfigFile('Sentinel_2', 'div', str)
                self.testVarConfigFile('Sentinel_2', 'nodata', str)
                self.testVarConfigFile('Sentinel_2', 'nuages_reproj', str)
                self.testVarConfigFile('Sentinel_2', 'saturation_reproj', str)
                self.testVarConfigFile('Sentinel_2', 'div_reproj', str)
                self.testVarConfigFile('Sentinel_2', 'arbomask', str)
                self.testVarConfigFile('Sentinel_2', 'temporalResolution', str)
                self.testVarConfigFile('Sentinel_2', 'keepBands', Sequence)

            nbTile = len(self.cfg.chain.listTile.split(" "))

            # directory tests
            if "parallel" == self.cfg.chain.executionMode:
                self.testDirectory(self.cfg.chain.jobsPath)
                self.testDirectory(self.cfg.chain.logPath)

            self.testDirectory(self.cfg.chain.pyAppPath)
            self.testDirectory(self.cfg.chain.nomenclaturePath)
            if "outside" == self.cfg.chain.mode:
                self.testDirectory(self.cfg.chain.regionPath)
            if "multi_regions" == self.cfg.chain.mode:
                self.testDirectory(self.cfg.chain.model)
            self.testDirectory(self.cfg.chain.groundTruth)

            self.testDirectory(self.cfg.chain.colorTable)

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
                    if not "Integer" in fieldType:
                        raise serviceError.fileError("the data's field " +
                                currentField + " must be an integer in " +
                                self.cfg.chain.groundTruth)
            if flag == 0:
                raise serviceError.fileError("field name '" +
                        self.cfg.chain.dataField + "' doesn't exist in " +
                        self.cfg.chain.groundTruth)

            # parameters compatibilities check
            if (self.cfg.chain.mode != "one_region") and (self.cfg.chain.mode != "multi_regions") and (self.cfg.chain.mode != "outside"):
                raise serviceError.configError("'mode' must be 'one_region' or 'multi_regions' or 'outside'\n")
            if self.cfg.chain.mode == "one_region" and self.cfg.argClassification.classifMode == "fusion":
                raise serviceError.configError("you can't chose 'one_region' mode and ask a fusion of classifications\n")
            if nbTile == 1 and self.cfg.chain.mode == "multi_regions":
                raise serviceError.configError("only one tile detected with mode 'multi_regions'\n")

            #if features has already compute, check if they have the same number of bands
            if os.path.exists(self.cfg.chain.featuresPath):
                stackName = getFeatStackName(self.pathConf)
                self.cfg.GlobChain.features = FileSearch_AND(self.cfg.chain.featuresPath, True, stackName)
                if self.cfg.GlobChain.features:
                    featuresBands = [(currentRaster, getRasterNbands(currentRaster)) for currentRaster in self.cfg.GlobChain.features]
                    if not all_sameBands(featuresBands):
                        raise serviceError.configError([currentRaster+" bands : "+str(rasterBands)+"\n" for currentRaster, rasterBands in featuresBands])

        # Error managed
        except serviceError.configFileError:
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
            ADD a parameter in an existing section in the config
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
            # It's normal because the parameter should not already exist
            # creation of attribute
            setattr(objSection, variable, value)

        else:
            # It already exist !!
            # setParam instead !!
            self.setParam(section, variable, value)

