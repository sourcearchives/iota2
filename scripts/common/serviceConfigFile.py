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
from config import Config, Sequence
from fileUtils import getFeatStackName, FileSearch_AND, getRasterNbands


class serviceConfigFile:
    """
    The class serviceConfigFile defines all methods to access to the
    configuration file and to check the variables.
    """

    def __init__(self, pathConf):
        """
            Init class serviceConfigFile
            :param pathConf: string path of the config file
        """

        # self.cfgFile is a class attribute. It is instantiated from Config class.
        #print "Read configuration file: "+ str(pathConf)
        self.pathConf = pathConf
        self.cfg = Config(file(pathConf))

    def testVarConfigFile(self, obj, variable, varType, valeurs="", valDefaut=""):
        """
            This function check if variable is in obj
            and if it has varType type.
            Optionnaly it can check if variable has values in valeurs
            Exit the code if any error are detected
            :param obj: obj name of the obj where to find
            :param variable: string name of the variable
            :param varType: type type of the variable for verification
            :param valeurs: string list of the possible value of variable
            :param valDefaut: value by default if variable is not in the configuration file
        """

        if not hasattr(obj, variable):
            if valDefaut != "":
                setattr(obj, variable, valDefaut)
            else:
                raise Exception("Mandatory variable is missing in the configuration file: "\
                + str(variable))
        else:
            tmpVar = getattr(obj, variable)
    
            if not isinstance(tmpVar, varType):
                message = "Variable " + str(variable) + " has a wrong type\nActual: "\
                + str(type(tmpVar)) + " expected: " + str(varType)
                raise Exception(message)
    
            if valeurs != "":
                ok = 0
                for index in range(len(valeurs)):
                    if tmpVar == valeurs[index]:
                        ok = 1
                if ok == 0:
                    raise Exception("Bad value for " + variable +\
                    " variable. Value accepted: " + str(valeurs) +\
                    " Value read: " + str(tmpVar))


    def checkConfigParameters(self):
        """
            check parameters coherence
            :return: true if ok
        """

        def all_sameBands(items):
            return all(bands == items[0][1] for path, bands in items)

        # test if a list a variable exist.
        self.testVarConfigFile(self.cfg.chain, 'executionMode', str)
        self.testVarConfigFile(self.cfg.chain, 'outputPath', str)
        self.testVarConfigFile(self.cfg.chain, 'jobsPath', str)
        self.testVarConfigFile(self.cfg.chain, 'pyAppPath', str)
        self.testVarConfigFile(self.cfg.chain, 'chainName', str)
        self.testVarConfigFile(self.cfg.chain, 'nomenclaturePath', str)
        self.testVarConfigFile(self.cfg.chain, 'listTile', str)
        self.testVarConfigFile(self.cfg.chain, 'featuresPath', str)
        self.testVarConfigFile(self.cfg.chain, 'L5Path', str)
        self.testVarConfigFile(self.cfg.chain, 'L8Path', str)
        self.testVarConfigFile(self.cfg.chain, 'S2Path', str)
        self.testVarConfigFile(self.cfg.chain, 'S1Path', str)
        self.testVarConfigFile(self.cfg.chain, 'mode', str, ["one_region", "multi_regions", "outside"])
        self.testVarConfigFile(self.cfg.chain, 'regionPath', str)
        self.testVarConfigFile(self.cfg.chain, 'regionField', str)
        self.testVarConfigFile(self.cfg.chain, 'model', str)
        self.testVarConfigFile(self.cfg.chain, 'groundTruth', str)
        self.testVarConfigFile(self.cfg.chain, 'dataField', str)
        self.testVarConfigFile(self.cfg.chain, 'runs', int)
        self.testVarConfigFile(self.cfg.chain, 'ratio', float)
        self.testVarConfigFile(self.cfg.chain, 'cloud_threshold', int)
        self.testVarConfigFile(self.cfg.chain, 'spatialResolution', int)
        self.testVarConfigFile(self.cfg.chain, 'logPath', str)
        self.testVarConfigFile(self.cfg.chain, 'colorTable', str)
        self.testVarConfigFile(self.cfg.chain, 'mode_outside_RegionSplit', str)
        self.testVarConfigFile(self.cfg.chain, 'OTB_HOME', str)

        self.testVarConfigFile(self.cfg.argTrain, 'shapeMode', str, ["polygons", "points"])
        self.testVarConfigFile(self.cfg.argTrain, 'samplesOptions', str)
        self.testVarConfigFile(self.cfg.argTrain, 'classifier', str)
        self.testVarConfigFile(self.cfg.argTrain, 'options', str)
        self.testVarConfigFile(self.cfg.argTrain, 'rearrangeModelTile', bool)
        self.testVarConfigFile(self.cfg.argTrain, 'rearrangeModelTile_out', str)
        self.testVarConfigFile(self.cfg.argTrain, 'cropMix', str, ["True", "False"])
        self.testVarConfigFile(self.cfg.argTrain, 'prevFeatures', str)
        self.testVarConfigFile(self.cfg.argTrain, 'annualCrop', Sequence)
        self.testVarConfigFile(self.cfg.argTrain, 'ACropLabelReplacement', Sequence)

        self.testVarConfigFile(self.cfg.argClassification, 'classifMode', str, ["separate", "fusion"])
        self.testVarConfigFile(self.cfg.argClassification, 'pixType', str)
        self.testVarConfigFile(self.cfg.argClassification, 'confusionModel', bool)
        self.testVarConfigFile(self.cfg.argClassification, 'noLabelManagement', str, ["maxConfidence", "learningPriority"])

        self.testVarConfigFile(self.cfg.GlobChain, 'proj', str)
        self.testVarConfigFile(self.cfg.GlobChain, 'features', Sequence)
        self.testVarConfigFile(self.cfg.GlobChain, 'batchProcessing', str, ["True", "False"])

        if self.cfg.chain.L5Path != "None":
            #L5 variable check
            self.testVarConfigFile(self.cfg.Landsat5, 'nodata_Mask', str, ["True", "False"])
            self.testVarConfigFile(self.cfg.Landsat5, 'nativeRes', int)
            self.testVarConfigFile(self.cfg.Landsat5, 'arbo', str)
            self.testVarConfigFile(self.cfg.Landsat5, 'imtype', str)
            self.testVarConfigFile(self.cfg.Landsat5, 'nuages', str)
            self.testVarConfigFile(self.cfg.Landsat5, 'saturation', str)
            self.testVarConfigFile(self.cfg.Landsat5, 'div', str)
            self.testVarConfigFile(self.cfg.Landsat5, 'nodata', str)
            self.testVarConfigFile(self.cfg.Landsat5, 'arbomask', str)
            self.testVarConfigFile(self.cfg.Landsat5, 'startDate', str)
            self.testVarConfigFile(self.cfg.Landsat5, 'endDate', str)
            self.testVarConfigFile(self.cfg.Landsat5, 'temporalResolution', str)
            self.testVarConfigFile(self.cfg.Landsat5, 'keepBands', Sequence)

        if self.cfg.chain.L8Path != "None":
            #L8 variable check
            self.testVarConfigFile(self.cfg.Landsat8, 'nodata_Mask', str, ["True", "False"])
            self.testVarConfigFile(self.cfg.Landsat8, 'nativeRes', int)
            self.testVarConfigFile(self.cfg.Landsat8, 'arbo', str)
            self.testVarConfigFile(self.cfg.Landsat8, 'imtype', str)
            self.testVarConfigFile(self.cfg.Landsat8, 'nuages', str)
            self.testVarConfigFile(self.cfg.Landsat8, 'saturation', str)
            self.testVarConfigFile(self.cfg.Landsat8, 'div', str)
            self.testVarConfigFile(self.cfg.Landsat8, 'nodata', str)
            self.testVarConfigFile(self.cfg.Landsat8, 'arbomask', str)
            self.testVarConfigFile(self.cfg.Landsat8, 'startDate', str)
            self.testVarConfigFile(self.cfg.Landsat8, 'endDate', str)
            self.testVarConfigFile(self.cfg.Landsat8, 'temporalResolution', str)
            self.testVarConfigFile(self.cfg.Landsat8, 'keepBands', Sequence)

        if self.cfg.chain.S2Path != "None":
            #S2 variable check
            self.testVarConfigFile(self.cfg.Sentinel_2, 'nodata_Mask', str)
            self.testVarConfigFile(self.cfg.Sentinel_2, 'nativeRes', int)
            self.testVarConfigFile(self.cfg.Sentinel_2, 'arbo', str)
            self.testVarConfigFile(self.cfg.Sentinel_2, 'imtype', str)
            self.testVarConfigFile(self.cfg.Sentinel_2, 'nuages', str)
            self.testVarConfigFile(self.cfg.Sentinel_2, 'saturation', str)
            self.testVarConfigFile(self.cfg.Sentinel_2, 'div', str)
            self.testVarConfigFile(self.cfg.Sentinel_2, 'nodata', str)
            self.testVarConfigFile(self.cfg.Sentinel_2, 'nuages_reproj', str)
            self.testVarConfigFile(self.cfg.Sentinel_2, 'saturation_reproj', str)
            self.testVarConfigFile(self.cfg.Sentinel_2, 'div_reproj', str)
            self.testVarConfigFile(self.cfg.Sentinel_2, 'arbomask', str)
            self.testVarConfigFile(self.cfg.Sentinel_2, 'temporalResolution', str)
            self.testVarConfigFile(self.cfg.Sentinel_2, 'keepBands', Sequence)



        nbTile = len(self.cfg.chain.listTile.split(" "))
        # test  if path exist
        error = []

        if "parallel" == self.cfg.chain.executionMode:
            if not os.path.exists(self.cfg.chain.jobsPath):
                error.append(self.cfg.chain.jobsPath+" doesn't exist\n")
            if not os.path.exists(self.cfg.chain.logPath):
                error.append(self.cfg.chain.logPath+" doesn't exist\n")

        if not os.path.exists(self.cfg.chain.pyAppPath):
            error.append(self.cfg.chain.pyAppPath+" doesn't exist\n")
        if not os.path.exists(self.cfg.chain.nomenclaturePath):
            error.append(self.cfg.chain.nomenclaturePath+" doesn't exist\n")
        if "outside" == self.cfg.chain.mode:
            if not os.path.exists(self.cfg.chain.regionPath):
                error.append(self.cfg.chain.regionPath+" doesn't exist\n")
        if "multi_regions" == self.cfg.chain.mode:
            if not os.path.exists(self.cfg.chain.model):
                error.append(self.cfg.chain.model+" doesn't exist\n")

        if not os.path.exists(self.cfg.chain.groundTruth):
            error.append(self.cfg.chain.groundTruth+" doesn't exist\n")
        else:
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
                        error.append("the data's field must be an integer'\n")
            if flag == 0:
                error.append("field name '"+self.cfg.chain.dataField+"' doesn't exist\n")

        if not os.path.exists(self.cfg.chain.colorTable):
            error.append(self.cfg.chain.colorTable+" doesn't exist\n")
        if not os.path.exists(self.cfg.chain.OTB_HOME+"/config_otb.sh"):
            error.append(self.cfg.chain.OTB_HOME+"/config_otb.sh doesn't exist\n")
        if self.cfg.argTrain.cropMix == "True":
            if not os.path.exists(self.cfg.argTrain.prevFeatures):
                error.append(self.cfg.argTrain.prevFeatures+" doesn't exist\n")
            if not self.cfg.argTrain.shapeMode == "points":
                error.append("you must use 'points' mode with 'cropMix' mode\n")
        if (self.cfg.chain.mode != "one_region") and (self.cfg.chain.mode != "multi_regions") and (self.cfg.chain.mode != "outside"):
            error.append("'mode' must be 'one_region' or 'multi_regions' or 'outside'\n")
        if self.cfg.chain.mode == "one_region" and self.cfg.argClassification.classifMode == "fusion":
            error.append("you can't chose 'one_region' mode and ask a fusion of classifications\n")
        if nbTile == 1 and self.cfg.chain.mode == "multi_regions":
            error.append("only one tile detected with mode 'multi_regions'\n")
        if self.cfg.argTrain.shapeMode == "points":
            if ("-sample.mt" or "-sample.mv" or "-sample.bm" or "-sample.vtr") in self.cfg.argTrain.options:
                error.append("wrong options passing in classifier argument see otbcli_TrainVectorClassifier's documentation\n")

        #if features has already compute, check if they have the same number of bands
        if os.path.exists(self.cfg.chain.featuresPath):
            stackName = getFeatStackName(self.pathConf)
            self.cfg.GlobChain.features = FileSearch_AND(self.cfg.chain.featuresPath, True, stackName)
            if self.cfg.GlobChain.features:
                featuresBands = [(currentRaster, getRasterNbands(currentRaster)) for currentRaster in self.cfg.GlobChain.features]
                if not all_sameBands(featuresBands):
                    error.append([currentRaster+" bands : "+str(rasterBands)+"\n" for currentRaster, rasterBands in featuresBands])
        if len(error) >= 1:
            errorList = "".join(error)
            raise Exception("\n"+errorList)

        return True


    def getParam(self, section, variable):
        """
            Return the value of variable in the section from config
            file define in the init phase of the class.
            :param section: string name of the section 
            :param variable: string name of the variable
            :return: the value of variable
        """

        if not hasattr(self.cfg, section):
            raise Exception("Section is not in the configuration file: " + str(section))

        objSection = getattr(self.cfg, section)

        if not hasattr(objSection, variable):
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
            :return: the value of variable
        """

        if not hasattr(self.cfg, section):
            raise Exception("Section is not in the configuration file: " + str(section))

        objSection = getattr(self.cfg, section)

        if not hasattr(objSection, variable):
            raise Exception("Variable is not in the configuration file: " + str(variable))

        setattr(objSection, variable, value)
