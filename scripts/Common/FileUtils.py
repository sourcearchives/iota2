# !/usr/bin/python
# -*- coding: utf-8 -*-

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

import sys
import os
import shutil
import glob
import math
import tarfile
import re
import random
import logging
from collections import defaultdict
from datetime import timedelta, date
import datetime
import errno
import warnings
import numpy as np
from config import Config, Sequence
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from osgeo.gdalconst import *
import otbApplication as otb
from Common.Utils import run


def ensure_dir(dirname):
    """
    Ensure that a named directory exists; if it does not, attempt to create it.
    """
    import errno
    try:
        os.makedirs(dirname)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise


def getOutputPixType(nomencalture_path):
    """use to deduce de classifications pixels type
    
    Parameters
    ----------
    nomencalture_path : string
        path to the nomenclature
    
    Return
    ------
    string
        "uint8" or "uint16"
    """
    label_max = 0
    dico_format = {"uint8":256,
                   "uint16":65536}

    with open(nomencalture_path, "r") as nomencalture_path_f:
        for line in nomencalture_path_f:
            label = int(line.rstrip().split(":")[-1].replace(" ",""))
            if label < 0:
                raise Exception ("labels must be > 0")
            if label > label_max:
                label_max = label

    if label <= dico_format["uint8"]:
        output_format = "uint8"
    elif label > dico_format["uint8"] and label < dico_format["uint16"]:
        output_format = "uint16"
    elif label_max > dico_format["uint16"]:
        raise Exception ("label must inferior of 65536")
    return output_format


def WriteNewFile(newFile, fileContent):
    """
    """
    with open(newFile, "w") as new_f:
        new_f.write(fileContent)


def memory_usage_psutil(unit="MB"):
    # return the memory usage in MB
    import resource
    if unit == "MB":
        coeff = 1000.0
    elif unit == "GB":
        coeff = 1000.0*1000.0
    mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / coeff
    #print 'Memory usage: %s (MB)' % (mem)
    return mem


def parseClassifCmd(cmdPath):

    """
    IN
    OUT
    list of list
    """
    from Common import ServiceConfigFile as SCF
    import argparse
    import shlex

    parser = argparse.ArgumentParser(description="Performs a classification of the input image (compute in RAM) according to a model file, ")
    parser.add_argument("-in", dest="tempFolderSerie", help="path to the folder which contains temporal series", default=None, required=True)
    parser.add_argument("-mask", dest="mask", help="path to classification's mask", default=None, required=True)
    parser.add_argument("-pixType", dest="pixType", help="pixel format", default=None, required=True)
    parser.add_argument("-model", dest="model", help="path to the model", default=None, required=True)
    parser.add_argument("-imstat", dest="stats", help="path to statistics", default=None, required=False)
    parser.add_argument("-out", dest="outputClassif", help="output classification's path", default=None, required=True)
    parser.add_argument("-confmap", dest="confmap", help="output classification confidence map", default=None, required=True)
    parser.add_argument("-ram", dest="ram", help="pipeline's size", default=128, required=False)
    parser.add_argument("--wd", dest="pathWd", help="path to the working directory", default=None, required=False)
    parser.add_argument("-conf", help="path to the configuration file (mandatory)", dest="pathConf", required=True)
    parser.add_argument("-maxCPU", help="True : Class all the image and after apply mask",
                        dest="MaximizeCPU", default="False", choices=["True", "False"], required=False)
    parameters = []

    with open(cmdPath, "r") as cmd_f:
        for line_cmd in cmd_f:
            argsString = shlex.split(" ".join(line_cmd.rstrip().split(" ")[2::]))
            args = parser.parse_args(argsString)
            workingDirectory = None
            if args.pathWd:
                workingDirectory = os.getenv("TMPDIR")
                args.tempFolderSerie = args.tempFolderSerie.replace("$TMPDIR", workingDirectory)
                args.mask = args.mask.replace("$TMPDIR", workingDirectory)
                args.outputClassif = args.outputClassif.replace("$TMPDIR", workingDirectory)
                args.confmap = args.confmap.replace("$TMPDIR", workingDirectory)

            parameters.append([args.tempFolderSerie, args.mask, args.model,
                               args.stats, args.outputClassif, args.confmap,
                               workingDirectory, args.pathConf, args.pixType,
                               args.MaximizeCPU, args.ram])

    return parameters


def commonMaskSARgeneration(cfg, tile, cMaskName):
    """
    generate SAR common mask
    """
    import ConfigParser
    from Common import ServiceConfigFile as SCF
    S1Path = cfg.getParam('chain', 'S1Path')
    featureFolder = os.path.join(cfg.getParam('chain', 'outputPath'),
                                 "features")
    config = ConfigParser.ConfigParser()
    config.read(S1Path)
    referenceFolder = config.get('Processing', 'ReferencesFolder') + "/" + tile
    stackPattern = config.get('Processing', 'RasterPattern')
    if not os.path.exists(referenceFolder):
        raise Exception(referenceFolder + "does not exists")
    refRaster = FileSearch_AND(referenceFolder, True, stackPattern)[0]
    cMaskPath = featureFolder + "/" + tile + "/tmp/" + cMaskName + ".tif"
    if not os.path.exists(featureFolder + "/" + tile):
        os.mkdir(featureFolder + "/" + tile)
        os.mkdir(featureFolder + "/" + tile + "/tmp/")

    cmd = "otbcli_BandMath -il " + refRaster + " -out " + cMaskPath + ' uint8 -exp "1"'
    if not os.path.exists(cMaskPath):
        os.system(cmd)
    cMaskPathVec = featureFolder + "/" + tile + "/tmp/" + cMaskName + ".shp"
    VectorMask = "gdal_polygonize.py -f \"ESRI Shapefile\" -mask " + cMaskPath + " " + cMaskPath +\
                 " " + cMaskPathVec
    print VectorMask
    if not os.path.exists(cMaskPathVec):
        os.system(VectorMask)
    os.system(VectorMask)
    return cMaskPath


def commonMaskUserFeatures(cfg, tile, cMaskName):
    """compute the common masks if only user features is selected
    
    Parameters
    ----------
    
    cfg : serviceConfig object
        configuration object
    tile : string
        tile to compute
    cMaskName : string
        mask's name
    """
    from Common import ServiceConfigFile as SCF
    from Common import OtbAppBank

    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    featuresPath = os.path.join(cfg.getParam('chain', 'outputPath'),
                                "features")
    userFeatPath = cfg.getParam('chain', 'userFeatPath')
    userFeat_arbo = cfg.getParam('userFeat', 'arbo')
    userFeat_patterns = (cfg.getParam('userFeat', 'patterns')).split(",")

    for dir_user in os.listdir(userFeatPath):
        if tile in dir_user and os.path.isdir(os.path.join(userFeatPath, dir_user)):
            ref_raster = FileSearch_AND(os.path.join(userFeatPath, dir_user),
                                        True, userFeat_patterns[0].replace(" ",""))[0]
    ref_raster_out = os.path.join(featuresPath, tile, "tmp", cMaskName + ".tif")
    ref_raster_app = OtbAppBank.CreateBandMathApplication({"il": ref_raster,
                                                           "out": ref_raster_out,
                                                           "exp": "1",
                                                           "pixType": "uint8"})
    if not os.path.exists(ref_raster_out):
        ref_raster_app.ExecuteAndWriteOutput()

    cMaskPathVec = ref_raster_out.replace(".tif", ".shp")
    if not os.path.exists(cMaskPathVec):
        VectorMask = "gdal_polygonize.py -f \"ESRI Shapefile\" -mask {} {} {}".format(ref_raster_out,
                                                                                      ref_raster_out,
                                                                                      cMaskPathVec)
        run(VectorMask)


def getCommonMasks(tile, cfg, workingDirectory=None):
    """
    usage : get common mask (sensors common area) for one tile

    IN
    tile [string]
    cfg [serviceConfig obj]
    workingDirectory [string]

    OUT
    commonMask [string] : common mask path
    """

    from Sensors import TimeSeriesStacks
    from Common import ServiceConfigFile as SCF

    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    outputDirectory = os.path.join(cfg.getParam('chain', 'outputPath'),
                                   "features")
    out_dir = os.path.join(outputDirectory, tile)

    if not os.path.exists(out_dir):
        try:
            os.mkdir(out_dir)
            os.mkdir(os.path.join(out_dir, "tmp"))
        except OSError:
            pass

    cMaskName = getCommonMaskName(cfg)

    #check if mask allready exists. If it exists, remove it
    maskCommun = FileSearch_AND(out_dir, True, cMaskName, ".tif")
    if len(maskCommun) == 1:
        os.remove(maskCommun[0])
    elif len(maskCommun) > 1:
        raise Exception("too many common masks found")
    if cMaskName == "SARMask":
        commonMask = commonMaskSARgeneration(cfg, tile, cMaskName)
    elif cMaskName == "UserFeatmask":
        commonMask = commonMaskUserFeatures(cfg, tile, cMaskName)
    else:
        tileFeaturePath = outputDirectory + "/" + tile
        if not os.path.exists(tileFeaturePath):
            os.mkdir(tileFeaturePath)
        _, _, _, _, commonMask = TimeSeriesStacks.generateStack(tile, cfg,
                                                                outputDirectory=tileFeaturePath, writeOutput=False,
                                                                workingDirectory=workingDirectory,
                                                                testMode=False, testSensorData=None)

    return commonMask


def cleanFiles(cfg):
    """
    remove files which as to be re-computed

    IN
    cfgFile [string] configuration file path
    """

    import ConfigParser
    S1Path = cfg.getParam('chain', 'S1Path')
    if "None" in S1Path:
        S1Path = None

    #Remove nbView.tif
    """
    features = cfg.getParam('chain', 'featuresPath')
    validity = FileSearch_AND(features,True,"nbView.tif")
    for Cvalidity in validity:
        if os.path.exists(Cvalidity):
            os.remove(Cvalidity)
    """
    #Remove SAR dates files
    if S1Path:
        config = ConfigParser.ConfigParser()
        config.read(S1Path)
        outputDirectory = config.get('Paths', 'Output')
        inDates = FileSearch_AND(outputDirectory, True, "inputDates.txt")
        interpDates = FileSearch_AND(outputDirectory, True, "interpolationDates.txt")
        for cDate in inDates:
            if os.path.exists(cDate):
                os.remove(cDate)
        for cDate in interpDates:
            if os.path.exists(cDate):
                os.remove(cDate)


def sensorUserList(cfg):

    """
        Construct list of sensor used
        :param cfg: class serviceConfigFile
        :return sensorList: The list of sensor used
    """
    from Common import ServiceConfigFile as SCF

    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)
    L5Path = cfg.getParam('chain', 'L5Path')
    L8Path = cfg.getParam('chain', 'L8Path')
    S2Path = cfg.getParam('chain', 'S2Path')
    S2_S2C_Path = cfg.getParam('chain', 'S2_S2C_Path')
    S1Path = cfg.getParam('chain', 'S1Path')

    sensorList = []

    if "None" not in L5Path:
        sensorList.append("L5")
    if "None" not in L8Path:
        sensorList.append("L8")
    if "None" not in S2Path:
        sensorList.append("S2")
    if "None" not in S2_S2C_Path:
        sensorList.append("S2_S2C_Path")
    if "None" not in S1Path:
        sensorList.append("S1")

    return sensorList


def onlySAR(cfg):

    """
        Test if only SAR data is available
        :param cfg: class serviceConfigFile
        :return retour: bool True if only S1 is set in configuration file
    """
    from Common import ServiceConfigFile as SCF
    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)
    # TODO refactoring de la fonction à faire : gestion des erreurs en particulier
    L5Path = cfg.getParam('chain', 'L5Path')
    L8Path = cfg.getParam('chain', 'L8Path')
    S2Path = cfg.getParam('chain', 'S2Path')
    S1Path = cfg.getParam('chain', 'S1Path')

    if "None" in L5Path:
        L5Path = None
    if "None" in L8Path:
        L8Path = None
    if "None" in S2Path:
        S2Path = None
    if "None" in S1Path:
        S1Path = None

    retour = False

    if L5Path or L8Path or S2Path:
        retour = False
    elif not L5Path and not L8Path and not S2Path and not S1Path:
        warnings.warn("No sensors path found")
    else:
        retour = True

    return retour


def getCommonMaskName(cfg):
    """
        Test if only SAR data is available
        :param cfg: class serviceConfigFile
        :return retour: string name of the mask
    """
    from Common import ServiceConfigFile as SCF

    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)
    L5Path = cfg.getParam('chain', 'L5Path')
    L8Path = cfg.getParam('chain', 'L8Path')
    S2Path = cfg.getParam('chain', 'S2Path')
    S1Path = cfg.getParam('chain', 'S1Path')
    userFeatPath = cfg.getParam('chain', 'userFeatPath')

    if "None" in L5Path:
        L5Path = None
    if "None" in L8Path:
        L8Path = None
    if "None" in S2Path:
        S2Path = None
    if "None" in S1Path:
        S1Path = None
    if "None" in userFeatPath:
        userFeatPath = None

    if onlySAR(cfg):
        mask_name = "SARMask"
    elif not L5Path and not L8Path and not S2Path and not S1Path and userFeatPath:
        mask_name = "UserFeatmask"
    else:
        mask_name = "MaskCommunSL"
    return mask_name


def dateInterval(dateMin, dataMax, tr):
    """
    dateMin [string] : Ex -> 20160101
    dateMax [string] > dateMin
    tr [int/string] -> temporal resolution
    """
    start = datetime.date(int(dateMin[0:4]), int(dateMin[4:6]), int(dateMin[6:8]))
    end = datetime.date(int(dataMax[0:4]), int(dataMax[4:6]), int(dataMax[6:8]))
    delta = timedelta(days=int(tr))
    curr = start
    while curr < end:
        yield curr
        curr += delta


def updatePyPath():
    """
    usage : add some child/parent directories to PYTHONPATH needed en IOTA2
    warning : this script depend of IOTA2 architecture
    """
    ext_mod = ["vector-tools"]
    parent = "/".join(os.path.abspath(os.path.join(os.path.realpath(__file__), os.pardir)).split("/")[0:-2])
    for currentModule in ext_mod:
        ext_mod_path = os.path.join(parent, currentModule)
        if ext_mod_path not in sys.path:
            sys.path.append(ext_mod_path)


def updateDirectory(src, dst):

    content = os.listdir(src)
    for currentContent in content:
        if os.path.isfile(src + "/" + currentContent):
            if not os.path.exists(dst + "/" + currentContent):
                shutil.copy(src + "/" + currentContent, dst + "/" + currentContent)
        if os.path.isdir(src + "/" + currentContent):
            if not os.path.exists(dst + "/" + currentContent):
                try:
                    shutil.copytree(src + "/" + currentContent, dst + "/" + currentContent)
                # python >2.5
                except OSError as exc:
                    if exc.errno == errno.ENOTDIR:
                        shutil.copy(src, dst)
                    else:
                        raise


def copyanything(src, dst):
    try:
        shutil.copytree(src, dst)
    # python >2.5
    except OSError as exc:
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else:
            raise


def getDateLandsat(pathLandsat, tiles, sensor="Landsat8"):
    """
    Get the min and max dates for the given tile.
    """
    dateMin = 30000000000
    dateMax = 0
    for tile in tiles:
        folder = os.listdir(pathLandsat + "/" + sensor + "_" + tile)
        for i in range(len(folder)):
            if folder[i].count(".tgz") == 0 and folder[i].count(".jpg") == 0 and folder[i].count(".xml") == 0:
                contenu = os.listdir(pathLandsat + "/" + sensor + "_" + tile + "/" + folder[i])
                for i in range(len(contenu)):
                    if contenu[i].count(".TIF") != 0:
                        Date = int(contenu[i].split("_")[3])
                        if Date > dateMax:
                            dateMax = Date
                        if Date < dateMin:
                            dateMin = Date
    return str(dateMin), str(dateMax)


def getDateL5(pathL5, tiles):
    return getDateLandsat(pathL5, tiles, "Landsat5")


def getDateL8(pathL8, tiles):
    return getDateLandsat(pathL8, tiles, "Landsat8")


def getDateS2(pathS2, tiles):
    """
    Get the min and max dates for the given tile.
    """
    datePos = 2
    if "T" in tiles[0]:
        datePos = 1
    dateMin = 30000000000
    dateMax = 0
    for tile in tiles:
        folder = os.listdir(pathS2 + "/" + tile)
        for i in range(len(folder)):
            if folder[i].count(".tgz") == 0 and folder[i].count(".jpg") == 0 and folder[i].count(".xml") == 0:
                Date = int(folder[i].split("_")[datePos].split("-")[0])
                if Date > dateMax:
                    dateMax = Date
                if Date < dateMin:
                    dateMin = Date
    return str(dateMin), str(dateMax)


def getDateS2_S2C(pathS2, tiles):
    """
    Get the min and max dates for the given tile.
    """
    datePos = 2
    dateMin = 30000000000
    dateMax = 0
    for tile in tiles:
        folder = os.listdir(pathS2 + "/" + tile)
        for i in range(len(folder)):
            if folder[i].count(".tgz") == 0 and folder[i].count(".jpg") == 0 and folder[i].count(".xml") == 0:
                Date = int(folder[i].split("_")[datePos].split("T")[0])
                if Date > dateMax:
                    dateMax = Date
                if Date < dateMin:
                    dateMin = Date
    return str(dateMin), str(dateMax)


def unPackFirst(someListOfList):
    """
    python generator
    return first element of an iterable

    Example:
    ListOfLists = [[1, 2], [6], [0, 1, 2]]
    for first in unPackFirst(ListOfLists):
        print first
    >> 1
    >> 6
    >> 0
    """
    for values in someListOfList:
        if isinstance(values, list) or isinstance(values, tuple):
            yield values[0]
        else:
            yield values


def commonPixTypeToOTB(string):
    dico = {"complexDouble": otb.ComplexImagePixelType_double,
            "complexFloat": otb.ComplexImagePixelType_float,
            "double": otb.ImagePixelType_double,
            "float": otb.ImagePixelType_float,
            "int16": otb.ImagePixelType_int16,
            "int32": otb.ImagePixelType_int32,
            "uint16": otb.ImagePixelType_uint16,
            "uint32": otb.ImagePixelType_uint32,
            "uint8": otb.ImagePixelType_uint8}
    try:
        return dico[string]
    except:
        raise Exception("Error in commonPixTypeToOTB function input parameter : " + string + " not available, choices are :"
                        "'complexDouble','complexFloat','double','float','int16','int32','uint16','uint32','uint8'")


def AddStringToFile(myString, writtingFile):

    with open(writtingFile, "a") as f:
        f.write(myString)


def splitList(InList, nbSplit):
    """
    IN :
    InList [list]
    nbSplit [int] : number of output fold

    OUT :
    splitList [list of nbSplit list]

    Examples :
        foo = ['a', 'b', 'c', 'd', 'e']
        print splitList(foo,4)
        >> [['e', 'c'], ['d'], ['a'], ['b']]

        print splitList(foo,8)
        >> [['b'], ['d'], ['c'], ['e'], ['a'], ['d'], ['a'], ['b']]
    """
    def chunk(xs, n):
        ys = list(xs)
        random.shuffle(ys)
        size = len(ys) // n
        leftovers = ys[size * n:]
        for c in xrange(n):
            if leftovers:
                extra = [leftovers.pop()]
            else:
                extra = []
            yield ys[c * size:(c + 1) * size] + extra

    splitList = list(chunk(InList, nbSplit))

    #check empty content (if nbSplit > len(Inlist))
    All = []
    for splits in splitList:
        for split in splits:
            if split not in All:
                All.append(split)

    for i in range(len(splitList)):
        if len(splitList[i]) == 0:
            randomChoice = random.sample(All, 1)[0]
            splitList[i].append(randomChoice)

    return splitList


def getCurrentSensor(SensorsList, refl):
    """
    get current sensor from reflectance raster
    SensorsList [list of Sensors Object]
    refl [string]
    """
    for currentSensor in SensorsList:
        sensorName = os.path.basename(refl).split("_")[0]
        if currentSensor.name == sensorName:
            return currentSensor


def getIndex(listOfTuple, keyVal):
    """
    usage :
    """

    retour = None
    try:
        retour = [item for key, item in listOfTuple].index(keyVal) + 1
    except:
        print keyVal + " not in list of bands"
        retour = []
    return retour


def ExtractInterestBands(stack, nbDates, SPbandsList, comp, ram=128):
    """
    usage : extract bands according to 'SPbandsList' parameter
    """
    SB_ToKeep = ["Channel" + str(int(currentBand) + i * comp) for i in range(nbDates) for currentBand in SPbandsList]
    extract = otb.Registry.CreateApplication("ExtractROI")

    if isinstance(stack, str):
        extract.SetParameterString("in", stack)
    elif type(stack) == otb.Application:
        extract.SetParameterInputImage("in", stack.GetParameterOutputImage("out"))

    extract.SetParameterString("ram", str(ram))
    extract.UpdateParameters()
    extract.SetParameterStringList("cl", SB_ToKeep)
    extract.Execute()
    return extract


def keepBiggestArea(shpin, shpout):
    """
    usage : from shpin, keep biggest polygon and save it in shpout
    logger = logging.getLogger(__name__)
    logger.debug("Processing {}".format(shpin))
    """

    def addPolygon(feat, simplePolygon, in_lyr, out_lyr):
        """
        usage : add polygon
        """
        featureDefn = in_lyr.GetLayerDefn()
        polygon = ogr.CreateGeometryFromWkb(simplePolygon)
        out_feat = ogr.Feature(featureDefn)
        for field in field_name_list:
            inValue = feat.GetField(field)
            out_feat.SetField(field, inValue)
        out_feat.SetGeometry(polygon)
        out_lyr.CreateFeature(out_feat)
        out_lyr.SetFeature(out_feat)

    gdal.UseExceptions()
    driver = ogr.GetDriverByName('ESRI Shapefile')
    field_name_list = getAllFieldsInShape(shpin)
    in_ds = driver.Open(shpin, 0)
    in_lyr = in_ds.GetLayer()
    inLayerDefn = in_lyr.GetLayerDefn()
    srsObj = in_lyr.GetSpatialRef()
    if os.path.exists(shpout):
        driver.DeleteDataSource(shpout)
    out_ds = driver.CreateDataSource(shpout)
    out_lyr = out_ds.CreateLayer('poly', srsObj, geom_type=ogr.wkbPolygon)
    for i in range(0, len(field_name_list)):
        fieldDefn = inLayerDefn.GetFieldDefn(i)
        fieldName = fieldDefn.GetName()
        if fieldName not in field_name_list:
            continue
        out_lyr.CreateField(fieldDefn)

    area = []
    allGeom = []
    for in_feat in in_lyr:
        geom = in_feat.GetGeometryRef()
        area.append(geom.GetArea())
        allGeom.append(geom.ExportToWkb())

    indexMax = np.argmax(np.array(area))
    addPolygon(in_lyr[indexMax], allGeom[indexMax], in_lyr, out_lyr)


def findCurrentTileInString(string, allTiles):
    """
    IN:
    string [string]: string where we want to found a string in the string list 'allTiles'
    allTiles [list of strings]

    OUT:
    if there is a unique occurence of a string in allTiles, return this occurence. else, return Exception
    """
    #must contain same element
    tileList = [currentTile for currentTile in allTiles if currentTile in string]
    if len(set(tileList)) == 1:
        return tileList[0]
    else:
        raise Exception("more than one tile found into the string :'" + string + "'")


def getUserFeatInTile(userFeat_path, tile, userFeat_arbo, userFeat_pattern):
    """
    IN :
    userFeat_path [string] : path to user features
    tile [string] : current tile
    userFeat_arbo [string] : tree to find features from userFeat_path/tile
    userFeat_pattern [list of strings] : lis of features to find

    OUT :
    
    allFeat : list 
        all features finding in userFeat_path/tile
        
    """
    allFeat = []
    fields = []
    for currentPattern in userFeat_pattern:
        allFeat += fileSearchRegEx(userFeat_path + "/" + tile + "/" + userFeat_arbo + currentPattern.replace(" ","") + "*")
        for band_num in range(getRasterNbands(allFeat[-1])):
            fields.append("userFeature_Band{}_{}".format(band_num + 1,
                                                         currentPattern.replace(" ","")))
    return allFeat, fields


def getFieldElement(shape, driverName="ESRI Shapefile", field="CODE", mode="all",
                    elemType="int"):
    """
    IN :
    shape [string] : shape to compute
    driverName [string] : ogr driver to read the shape
    field [string] : data's field
    mode [string] : "all" or "unique"

    OUT :
    [list] containing all/unique element in shape's field

    Example :
        getFieldElement("./MyShape.sqlite","SQLite","CODE",mode = "all")
        >> [1,2,2,2,2,3,4]
        getFieldElement("./MyShape.sqlite","SQLite","CODE",mode = "unique")
        >> [1,2,3,4]
    """
    def getElem(elem, elemType):
        
        retourElem = None
        if elemType == "int":
            retourElem = int(elem)
        elif elemType == "str":
            retourElem = str(elem)
        else:
            raise Exception("elemType must be 'int' or 'str'")
        return retourElem
        
    driver = ogr.GetDriverByName(driverName)
    dataSource = driver.Open(shape, 0)
    layer = dataSource.GetLayer()
    
    retourMode = None
    if mode == "all":
        retourMode = [getElem(currentFeat.GetField(field), elemType) for currentFeat in layer]
    elif mode == "unique":
        retourMode = list(set([getElem(currentFeat.GetField(field), elemType) for currentFeat in layer]))
    else:
        raise Exception("mode parameter must be 'all' or 'unique'")
    return retourMode


def sortByFirstElem(MyList):
    """
    Example 1:
        MyList = [(1,2),(1,1),(6,1),(1,4),(6,7)]
        print sortByElem(MyList)
        >> [(1, [2, 1, 4]), (6, [1, 7])]

    Example 2:
        MyList = [((1,6),2),((1,6),1),((1,2),1),((1,6),4),((1,2),7)]
        print sortByElem(MyList)
        >> [((1, 2), [1, 7]), ((1, 6), [2, 1, 4])]
    """
    d = defaultdict(list)
    for k, v in MyList:
        d[k].append(v)
    return list(d.items())


def readRaster(name, data=False, band=1):

    """
    Open raster and return metadate information about it.

    in :
        name : raster name
    out :
        [datas] : numpy array from raster dataset
        xsize : xsize of raster dataset
        ysize : ysize of raster dataset
        projection : projection of raster dataset
        transform : coordinates and pixel size of raster dataset
    """
    try:
        raster = gdal.Open(name, 0)
    except:
        print "Problem on raster file path"
        sys.exit()

    raster_band = raster.GetRasterBand(band)

    #property of raster
    projection = raster.GetProjectionRef()
    transform = raster.GetGeoTransform()
    xsize = raster.RasterXSize
    ysize = raster.RasterYSize

    if data:
        # convert raster to an array
        datas = raster_band.ReadAsArray()
        return datas, xsize, ysize, projection, transform
    else:
        return xsize, ysize, projection, transform


def getRasterResolution(rasterIn):
    """
    IN :
    rasterIn [string]:path to raster

    OUT :
    return pixelSizeX, pixelSizeY
    """
    raster = gdal.Open(rasterIn, GA_ReadOnly)
    if raster is None:
        raise Exception("can't open " + rasterIn)
    geotransform = raster.GetGeoTransform()
    spacingX = geotransform[1]
    spacingY = geotransform[5]
    return spacingX, spacingY


def assembleTile_Merge(AllRaster, spatialResolution, out, ot="Int16", co=None):
    """
    usage : function use to mosaic rasters

    IN :
    AllRaster [list of strings] : rasters path
    spatialResolution [int] :
    out [string] : output path
    ot [string] (not mandatory) : output pixelType (gdal format)
    co [dictionary] gdal rasters creation options (not mandatory)

    OUT:
    a mosaic of all images in AllRaster.
    0 values are considered as noData. Usefull for pixel superposition.
    """

    gdal_co = ""
    if co:
        gdal_co = " -co " + " -co ".join(["{}={}".format(co_name, co_value) for co_name, co_value in co.items()])


    AllRaster = " ".join(AllRaster)
    if os.path.exists(out):
        os.remove(out)

    cmd = "gdal_merge.py {} -ps {} -{} -o {} -ot {} -n 0 {}".format(gdal_co, spatialResolution,
                                                                    spatialResolution, out,
                                                                    ot, AllRaster)
    run(cmd)

def getVectorFeatures(InputShape):
    """
    IN :
    InputShape [string] : path to a vector (otbcli_SampleExtraction output)

    OUT :
    AllFeat : [lsit of string] : list of all feature fought in InputShape. This vector must
    contains field with pattern 'value_N' N:[0,int(someInt)]
    """
    dataSource = ogr.Open(InputShape)
    daLayer = dataSource.GetLayer(0)
    layerDefinition = daLayer.GetLayerDefn()

    AllFeat = []
    for i in range(layerDefinition.GetFieldCount()):
        if "value_" in layerDefinition.GetFieldDefn(i).GetName():
            AllFeat.append(layerDefinition.GetFieldDefn(i).GetName())
    return AllFeat


def getDateFromString(vardate):
    """
    usage get date from string date
    vardate [string] : ex : 20160101
    """
    Y = int(vardate[0:4])
    M = int(vardate[4:6])
    D = int(vardate[6:len(vardate)])
    return Y, M, D


def getNbDateInTile(dateInFile, display=True, raw_dates=False):
    """
    usage : get available dates in file
    dateInFile [string] : path to txt containing one date per line
    raw_dates [bool] flag use to return all available dates
    """
    allDates = []
    with open(dateInFile) as f:
        for i, l in enumerate(f):
            vardate = l.rstrip()
            try:
                Y, M, D = getDateFromString(vardate)
                validDate = datetime.datetime(int(Y), int(M), int(D))
                allDates.append(vardate)
                if display:
                    print validDate
            except ValueError:
                raise Exception("unvalid date in : "+dateInFile+" -> '"+str(vardate)+"'")
    if raw_dates:
        output = allDates
    else:
        output = i + 1
    return output


def getGroundSpacing(pathToFeat, ImgInfo):
    run("otbcli_ReadImageInfo -in "+pathToFeat+">"+ImgInfo)
    info = open(ImgInfo, "r")
    while True:
        data = info.readline().rstrip('\n\r')
        if data.count("spacingx: ") != 0:
            spx = data.split("spacingx: ")[-1]
        elif data.count("spacingy:") != 0:
            spy = data.split("spacingy: ")[-1]
            break
    info.close()
    os.remove(ImgInfo)
    return spx, spy


def getRasterProjectionEPSG(FileName):
    """
    usage get raster EPSG projection code
    """
    SourceDS = gdal.Open(FileName, GA_ReadOnly)
    Projection = osr.SpatialReference()
    Projection.ImportFromWkt(SourceDS.GetProjectionRef())
    ProjectionCode = Projection.GetAttrValue("AUTHORITY", 1)
    return ProjectionCode


def getRasterNbands(raster):
    """
    usage get raster's number of bands
    """
    src_ds = gdal.Open(raster)
    if src_ds is None:
        raise Exception(raster + " doesn't exist")
    return int(src_ds.RasterCount)


def testVarConfigFile(obj, variable, varType, valeurs=""):
    """
    This function check if variable is in obj
    and if it has varType type.
    Optionnaly it can check if variable has values in valeurs
    Exit the code if any error are detected
    @param
    """

    if not hasattr(obj, variable):
        raise Exception("Mandatory variable is missing in the configuration file: " + str(variable))

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
            raise Exception("Bad value for " + variable + " variable. Value accepted : " + str(valeurs))


def multiSearch(shp, ogrDriver='ESRI Shapefile'):
    """
    usage : return true if shp contains one or more 'MULTIPOLYGON'
    IN
    shp [string] path to a shapeFile
    ogrDriver [string] ogr driver name

    OUT
    [bool]
    """
    driver = ogr.GetDriverByName(ogrDriver)
    in_ds = driver.Open(shp, 0)
    in_lyr = in_ds.GetLayer()

    retour = False
    for in_feat in in_lyr:
        geom = in_feat.GetGeometryRef()
        if geom.GetGeometryName() == 'MULTIPOLYGON':
            retour = True
    return retour


def getAllFieldsInShape(vector, driver='ESRI Shapefile'):

    """
    IN :
    vector [string] : path to vector file
    driver [string] : gdal driver

    OUT :
    [list of string] : all fields in vector
    """
    driver = ogr.GetDriverByName(driver)
    dataSource = driver.Open(vector, 0)
    if dataSource is None:
        raise Exception("Could not open " + vector)
    layer = dataSource.GetLayer()
    layerDefinition = layer.GetLayerDefn()
    return [layerDefinition.GetFieldDefn(i).GetName() for i in range(layerDefinition.GetFieldCount())]


def multiPolyToPoly(shpMulti, shpSingle):
    """
    IN:
    shpMulti [string] : path to an input vector
    shpSingle [string] : output vector

    OUT:
    convert all multipolygon to polygons. Add all single polygon into shpSingle
    """
    def addPolygon(feat, simplePolygon, in_lyr, out_lyr):
        """
        add polygon
        """
        featureDefn = in_lyr.GetLayerDefn()
        polygon = ogr.CreateGeometryFromWkb(simplePolygon)
        out_feat = ogr.Feature(featureDefn)
        for field in field_name_list:
            inValue = feat.GetField(field)
            out_feat.SetField(field, inValue)
        out_feat.SetGeometry(polygon)
        out_lyr.CreateFeature(out_feat)
        out_lyr.SetFeature(out_feat)

    def multipoly2poly(in_lyr, out_lyr):
        for in_feat in in_lyr:
            geom = in_feat.GetGeometryRef()
            if geom.GetGeometryName() == 'MULTIPOLYGON':
                for geom_part in geom:
                    addPolygon(in_feat, geom_part.ExportToWkb(), in_lyr, out_lyr)
            else:
                addPolygon(in_feat, geom.ExportToWkb(), in_lyr, out_lyr)

    gdal.UseExceptions()
    driver = ogr.GetDriverByName('ESRI Shapefile')
    field_name_list = getAllFieldsInShape(shpMulti)
    in_ds = driver.Open(shpMulti, 0)
    in_lyr = in_ds.GetLayer()
    inLayerDefn = in_lyr.GetLayerDefn()
    srsObj = in_lyr.GetSpatialRef()
    if os.path.exists(shpSingle):
        driver.DeleteDataSource(shpSingle)
    out_ds = driver.CreateDataSource(shpSingle)
    out_lyr = out_ds.CreateLayer('poly', srsObj, geom_type=ogr.wkbPolygon)
    for i in range(0, len(field_name_list)):
        fieldDefn = inLayerDefn.GetFieldDefn(i)
        fieldName = fieldDefn.GetName()
        if fieldName not in field_name_list:
            continue
        out_lyr.CreateField(fieldDefn)
    multipoly2poly(in_lyr, out_lyr)


def createPolygonShapefile(name, epsg, driver):

    outDriver = ogr.GetDriverByName(driver)
    if os.path.exists(name):
        os.remove(name)
    out_coordsys = osr.SpatialReference()
    out_coordsys.ImportFromEPSG(epsg)
    outDataSource = outDriver.CreateDataSource(name)
    outLayer = outDataSource.CreateLayer(name, srs=out_coordsys, geom_type=ogr.wkbPolygon)
    outDataSource.Destroy()


def CreateNewLayer(layer, outShapefile, AllFields):

    """
    IN:
    layer [ogrLayer] : layer to create
    outShapefile [string] : out ogr vector
    AllFields [list of strings] : fields to copy from layer to outShapefile

    """
    outDriver = ogr.GetDriverByName("ESRI Shapefile")
    if os.path.exists(outShapefile):
        outDriver.DeleteDataSource(outShapefile)
    outDataSource = outDriver.CreateDataSource(outShapefile)
    out_lyr_name = os.path.splitext(os.path.split(outShapefile)[1])[0]
    srsObj = layer.GetSpatialRef()
    outLayer = outDataSource.CreateLayer(out_lyr_name, srsObj, geom_type=ogr.wkbMultiPolygon)
    # Add input Layer Fields to the output Layer if it is the one we want
    inLayerDefn = layer.GetLayerDefn()
    for i in range(0, inLayerDefn.GetFieldCount()):
        fieldDefn = inLayerDefn.GetFieldDefn(i)
        fieldName = fieldDefn.GetName()
        if fieldName not in AllFields:
            continue
        outLayer.CreateField(fieldDefn)
    # Get the output Layer's Feature Definition
    outLayerDefn = outLayer.GetLayerDefn()

    # Add features to the ouput Layer
    for inFeature in layer:
        # Create output Feature
        outFeature = ogr.Feature(outLayerDefn)

        # Add field values from input Layer
        for i in range(0, outLayerDefn.GetFieldCount()):
            fieldDefn = outLayerDefn.GetFieldDefn(i)
            fieldName = fieldDefn.GetName()
            if fieldName not in AllFields:
                continue
            outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(),
                                inFeature.GetField(i))
        # Set geometry as centroid
        geom = inFeature.GetGeometryRef()
        if geom:
            outFeature.SetGeometry(geom.Clone())
            outLayer.CreateFeature(outFeature)


def getAllModels(PathconfigModels):
    """
    return All models in PathconfigModels file
    """
    f = file(PathconfigModels)
    cfg = Config(f)
    AllModel = cfg.AllModel
    modelFind = []
    for i in range(len(AllModel)):
        currentModel = cfg.AllModel[i].modelName
        try:
            ind = modelFind.index(currentModel)
            raise Exception("Model " + currentModel + " already exist")
        except ValueError:
            modelFind.append(currentModel)
    return modelFind


def mergeSQLite(outname, opath, files):
    filefusion = opath+"/"+outname+".sqlite"
    if os.path.exists(filefusion):
        os.remove(filefusion)
    if len(files) > 1:
        first = files[0]
        cmd = 'ogr2ogr -f SQLite '+filefusion+' '+first
        run(cmd)
        if len(files) > 1:
            for f in range(1, len(files)):
                fusion = 'ogr2ogr -f SQLite -update -append '+filefusion+' '+files[f]
                print fusion
                run(fusion)
    else:
        shutil.copy(files[0], filefusion)


def mergeSqlite(vectorList, outputVector):
    """
    IN
    vectorList [list of strings] : vector's path to merge

    OUT
    outputVector [string] : output path
    """
    import sqlite3

    vectorList_cpy = [elem for elem in vectorList]

    def cleanSqliteDatabase(db, table):

        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        res = cursor.fetchall()
        res = [x[0] for x in res]
        if len(res) > 0:
            if table in res:
                cursor.execute("DROP TABLE %s;"%(table))
        conn.commit()
        cursor = conn = None

    if os.path.exists(outputVector):
        os.remove(outputVector)

    shutil.copy(vectorList_cpy[0], outputVector)

    if len(outputVector) > 1:
        del vectorList_cpy[0]

        conn = sqlite3.connect(outputVector)
        cursor = conn.cursor()
        for cpt, currentVector in enumerate(vectorList_cpy):
            cursor.execute("ATTACH '%s' as db%s;"%(currentVector, str(cpt)))
            cursor.execute("CREATE TABLE output2 AS SELECT * FROM db"+str(cpt)+".output;")
            cursor.execute("INSERT INTO output SELECT * FROM output2;")
            conn.commit()
            cleanSqliteDatabase(outputVector, "output2")
        cursor = conn = None


def mergeVectors(outname, opath, files, ext="shp", out_Tbl_name=None):
    """
    Merge a list of vector files in one
    """
    done = []

    outType = ''
    if ext == 'sqlite':
        outType = ' -f SQLite '
    file1 = files[0]
    nbfiles = len(files)
    filefusion = opath + "/" + outname + "." + ext
    if os.path.exists(filefusion):
        os.remove(filefusion)

    table_name = outname
    if out_Tbl_name:
        table_name = out_Tbl_name
    fusion = 'ogr2ogr '+filefusion+' '+file1+' '+outType+' -nln '+table_name
    run(fusion)

    done.append(file1)
    for f in range(1, nbfiles):
        fusion = 'ogr2ogr -update -append '+filefusion+' '+files[f]+' -nln '+table_name+' '+outType
        run(fusion)
        done.append(files[f])

    return filefusion


def getRasterExtent(raster_in):
    """
    Get raster extent of raster_in from GetGeoTransform()
    ARGs:
    INPUT:
        - raster_in: input raster
    OUTPUT
        - ex: extent with [minX,maxX,minY,maxY]
    """
    
    retour = []
    if not os.path.isfile(raster_in):
        pass
    else:
        raster = gdal.Open(raster_in, GA_ReadOnly)
        if raster is None:
            pass
        else:
            geotransform = raster.GetGeoTransform()
            originX = geotransform[0]
            originY = geotransform[3]
            spacingX = geotransform[1]
            spacingY = geotransform[5]
            r, c = raster.RasterYSize, raster.RasterXSize
        
            minX = originX
            maxY = originY
            maxX = minX + c * spacingX
            minY = maxY + r * spacingY
        
            retour = [minX, maxX, minY, maxY]
    return retour


def ResizeImage(imgIn, imout, spx, spy, imref, proj, pixType):
    """
    re-sample raster thanks to gdalwarp api
    """
    minX, maxX, minY, maxY = getRasterExtent(imref)

    #Resize = 'gdalwarp -of GTiff -r cubic -tr '+spx+' '+spy+' -te '+str(minX)+' '+str(minY)+' '+str(maxX)+' '+str(maxY)+' -t_srs "EPSG:'+proj+'" '+imgIn+' '+imout
    Resize = 'gdalwarp -of GTiff -tr '+spx+' '+spy+' -te '+str(minX)+' '+str(minY)+' '+str(maxX)+' '+str(maxY)+' -t_srs "EPSG:'+proj+'" '+imgIn+' '+imout
    run(Resize)


def gen_confusionMatrix(csv_f, AllClass):
    """
    IN:
    csv_f [list of list] : comes from confCoordinatesCSV function.
    AllClass [list of strings] : all class
    OUT :
    confMat [numpy array] : generate a numpy array representing a confusion matrix
    """
    NbClasses = len(AllClass)

    confMat = [[0] * NbClasses] * NbClasses
    confMat = np.asarray(confMat)
    row = 0
    for classRef in AllClass:
        #in order to manage the case "this reference label was never classified"
        flag = 0
        for classRef_csv in csv_f:
            if classRef_csv[0] == classRef:
                col = 0
                for classProd in AllClass:
                    for classProd_csv in classRef_csv[1]:
                        if classProd_csv[0] == classProd:
                            confMat[row][col] = confMat[row][col] + classProd_csv[1]
                    col += 1
                #row +=1
        row += 1
        #if flag == 0:
        #   row+=1

    return confMat


def confCoordinatesCSV(csvPaths):
    """
    IN :
    csvPaths [string] : list of path to csv files
        ex : ["/path/to/file1.csv","/path/to/file2.csv"]
    OUT :
    out [list of lists] : containing csv's coordinates

    ex : file1.csv
        #Reference labels (rows):11
        #Produced labels (columns):11,12
        14258,52

         file2.csv
        #Reference labels (rows):12
        #Produced labels (columns):11,12
        38,9372

    out = [[12,[11,38]],[12,[12,9372]],[11,[11,14258]],[11,[12,52]]]
    """
    out = []
    for csvPath in csvPaths:
        cpty = 0
        FileMat = open(csvPath, "r")
        while 1:
            data = FileMat.readline().rstrip('\n\r')
            if data == "":
                FileMat.close()
                break
            if data.count('#Reference labels (rows):') != 0:
                ref = data.split(":")[-1].split(",")
            elif data.count('#Produced labels (columns):') != 0:
                prod = data.split(":")[-1].split(",")
            else:
                y = ref[cpty]
                line = data.split(",")
                cptx = 0
                for val in line:
                    x = prod[cptx]
                    out.append([int(y), [int(x), float(val)]])
                    cptx += 1
                cpty += 1
    return out


def findAndReplace(InFile, Search, Replace):
    """
    IN:
    InFile [string] : path to a file
    Search [string] : pattern to find in InFile
    Replace [string] : replace pattern by Replace

    OUT:
    replace a string by an other one in a file
    """
    f1 = open(InFile, 'r')
    f2Name = InFile.split("/")[-1].split(".")[0] + "_tmp." + InFile.split("/")[-1].split(".")[1]
    f2path = "/".join(InFile.split("/")[0:len(InFile.split("/")) - 1])
    f2 = open(f2path + "/" + f2Name, 'w')
    for line in f1:
        f2.write(line.replace(Search, Replace))
    f1.close()
    f2.close()

    os.remove(InFile)
    shutil.copyfile(f2path + "/" + f2Name, InFile)
    os.remove(f2path + "/" + f2Name)


def bigDataTransfert(pathOut, folderList):
    """
    IN :
    pathOut [string] path to output folder
    folderList [list of string path]

    copy datas through zip (use with HPC)
    """
    TAR = pathOut + "/TAR.tar"
    tarFile = tarfile.open(TAR, mode='w')
    for feat in folderList:
        tarFile.add(feat, arcname=feat.split("/")[-1])
    tarFile.close()

    t = tarfile.open(TAR, 'r')
    t.extractall(pathOut)
    os.remove(TAR)


def erodeOrDilateShapeFile(infile, outfile, buffdist):
    """
    dilate or erode all features in the shapeFile In

    IN :
    - infile : the shape file
            ex : /xxx/x/x/x/x/yyy.shp
    - outfile : the resulting shapefile
            ex : /x/x/x/x/x.shp
    - buffdist : the distance of dilatation or erosion
            ex : -10 for erosion
                 +10 for dilatation

    OUT :
    - the shapeFile outfile
    """
    
    retour = True
    try:
        ds = ogr.Open(infile)
        drv = ds.GetDriver()
        if os.path.exists(outfile):
            drv.DeleteDataSource(outfile)
        drv.CopyDataSource(ds, outfile)
        ds.Destroy()

        ds = ogr.Open(outfile, 1)
        lyr = ds.GetLayer(0)
        for i in range(0, lyr.GetFeatureCount()):
            feat = lyr.GetFeature(i)
            lyr.DeleteFeature(i)
            geom = feat.GetGeometryRef()
            feat.SetGeometry(geom.Buffer(float(buffdist)))
            lyr.CreateFeature(feat)
        ds.Destroy()
    except:
        retour = False
    return retour


def erodeShapeFile(infile, outfile, buffdist):
    return erodeOrDilateShapeFile(infile, outfile, -math.fabs(buffdist))


def dilateShapeFile(infile, outfile, buffdist):
    return erodeOrDilateShapeFile(infile, outfile, math.fabs(buffdist))


def getListTileFromModel(modelIN, pathToConfig):
    """
    IN :
        modelIN [string] : model name (generally an integer)
        pathToConfig [string] : path to the configuration file which link a model and all tiles uses to built him.
    OUT :
        list of tiles uses to built "modelIN"

    Exemple
    $cat /path/to/myConfigFile.cfg
    AllModel:
    [
        {
        modelName:'1'
        tilesList:'D0005H0001 D0005H0002'
        }
        {
        modelName:'22'
        tilesList:'D0004H0004 D0005H0008'
        }
    ]
    tiles = getListTileFromModel('22',/path/to/myConfigFile.cfg)
    print tiles
    >>tiles = ['D0004H0004','D0005H0008']
    """
    f = file(pathToConfig)
    cfg = Config(f)
    AllModel = cfg.AllModel

    for model in AllModel:
        if model.modelName == modelIN:
            return model.tilesList.split("_")


def fileSearchRegEx(Pathfile):
    """
    get files by regEx
    """
    return [f for f in glob.glob(Pathfile.replace("[", "[[]"))]


def getShapeExtent(shape_in):
    """
        Get shape extent of shape_in. The shape must have only one geometry
    """

    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(shape_in, 0)
    layer = dataSource.GetLayer()

    for feat in layer:
        geom = feat.GetGeometryRef()
    env = geom.GetEnvelope()
    return env[0], env[2], env[1], env[3]


def getFeatStackName(pathConf):
    """
    usage : get Feature Stack name
    """
    from Common import ServiceConfigFile as SCF
    if not isinstance(pathConf, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(pathConf)
    listIndices = cfg.getParam("GlobChain", "features")
    userFeatPath = cfg.getParam("chain", "userFeatPath")
    if "None" in userFeatPath:
        userFeatPath = None
    userFeat_pattern = ""
    if userFeatPath:
        userFeat_pattern = "_".join((cfg.getParam("userFeat", "patterns")).split(","))

    Stack_ind = "SL_MultiTempGapF" + userFeat_pattern + ".tif"
    retourListFeat = True
    if len(listIndices) > 1:
        listIndices = list(listIndices)
        listIndices = sorted(listIndices)
        listFeat = "_".join(listIndices)
    elif len(listIndices) == 1:
        listFeat = listIndices[0]
    else:
        retourListFeat = False

    if retourListFeat is True:
        Stack_ind = "SL_MultiTempGapF_" + listFeat + "_" + userFeat_pattern + "_.tif"
    return Stack_ind


def writeCmds(path, cmds, mode="w"):

    cmdFile = open(path, mode)
    for i in range(len(cmds)):
        if i == 0:
            cmdFile.write("%s" % (cmds[i]))
        else:
            cmdFile.write("\n%s" % (cmds[i]))
    cmdFile.close()


def getCmd(path):
    with open(path, "r") as f:
        All_cmd = [line for line in f]
    return All_cmd


def removeShape(shapePath, extensions):
    """
    IN:
        shapePath : path to the shapeFile without extension.
            ex : /path/to/myShape where /path/to/myShape.* exists
        extensions : all extensions to delete
            ex : extensions = [".prj",".shp",".dbf",".shx"]
    """
    for ext in extensions:
        os.remove(shapePath + ext)


def cpShapeFile(inpath, outpath, extensions, spe=False):

    for ext in extensions:
        if not spe:
            shutil.copy(inpath + ext, outpath + ext)
        else:
            shutil.copy(inpath + ext, outpath)


def FileSearch_AND(PathToFolder, AllPath, *names):

    """
        search all files in a folder or sub folder which contains all names in their name

        IN :
            - PathToFolder : target folder
                    ex : /xx/xxx/xx/xxx
            - *names : target names
                    ex : "target1","target2"
        OUT :
            - out : a list containing all file name (without extension) which are containing all name
    """
    out = []
    for path, dirs, files in os.walk(PathToFolder):
        for i in range(len(files)):
            flag = 0
            for name in names:
                if files[i].count(name) != 0 and files[i].count(".aux.xml") == 0:
                    flag += 1
            if flag == len(names):
                if not AllPath:
                    out.append(files[i].split(".")[0])
                else:
                    pathOut = path + '/' + files[i]
                    out.append(pathOut)
    return out


def renameShapefile(inpath, filename, old_suffix, new_suffix, outpath=None):
    if not outpath:
        outpath = inpath
    run("cp "+inpath+"/"+filename+old_suffix+".shp "+outpath+"/"+filename+new_suffix+".shp")
    run("cp "+inpath+"/"+filename+old_suffix+".shx "+outpath+"/"+filename+new_suffix+".shx")
    run("cp "+inpath+"/"+filename+old_suffix+".dbf "+outpath+"/"+filename+new_suffix+".dbf")
    run("cp "+inpath+"/"+filename+old_suffix+".prj "+outpath+"/"+filename+new_suffix+".prj")
    return outpath+"/"+filename+new_suffix+".shp"

def ClipVectorData(vectorFile, cutFile, opath, nameOut=None):
    """
    Cuts a shapefile with another shapefile
    ARGs:
       INPUT:
            -vectorFile: the shapefile to be cut
            -shpMask: the other shapefile
       OUTPUT:
            -the vector file clipped
    """
    if not nameOut:
        nameVF = vectorFile.split("/")[-1].split(".")[0]
        nameCF = cutFile.split("/")[-1].split(".")[0]
        outname = opath + "/" + nameVF + "_" + nameCF + ".shp"
    else:
        outname = opath + "/" + nameOut + ".shp"

    if os.path.exists(outname):
        os.remove(outname)

    Clip = "ogr2ogr -clipsrc "+cutFile+" "+outname+" "+vectorFile+" -progress"
    run(Clip)
    return outname


def BuildName(opath, *SerieList):
    """
    Returns a name for an output using as input several images series.
    ARGs:
       INPUT:
            -SerieList:  the list of different series
            -opath : output path
    """

    chname = ""
    for serie in SerieList:
        feat = serie.split(' ')
        for f in feat:
            dernier = f.split('/')
            name = dernier[-1].split('.')
            feature = name[0]
            chname = chname + feature + "_"
    return chname


def GetSerieList(*SerieList):
    """
    Returns a list of images likes a character chain.
    ARGs:
        INPUT:
            -SerieList: the list of different series
        OUTPUT:
    """
    ch = ""
    for serie in SerieList:
        name = serie.split('.')
        ch = ch + serie + " "
    return ch


def ConcatenateAllData(opath, pathConf, workingDirectory, wOut, name, *SerieList):
    """
    Concatenates all data: Reflectances, NDVI, NDWI, Brightness
    ARGs:
       INPUT:
            -SerieList: the list of different series
            -opath : output path
       OUTPUT:
            - The concatenated data
    """
    pixelo = "int16"
    ch = GetSerieList(*SerieList)
    ConcFile = opath+"/"+name
    Concatenation = "otbcli_ConcatenateImages -il "+ch+" -out "+ConcFile+" "+pixelo
    run(Concatenation)

class serviceCompareImageFile:
    """
    The class serviceCompareImageFile provides methods to compare
    two images file with gdal
    Code inspired from gdalCompare.py
    """

    #######################################################
    def __compare_metadata(self, file1_md, file2_md, id, options=[]):
        if file1_md is None and file2_md is None:
            return 0

        found_diff = 0

        if len(list(file1_md.keys())) != len(list(file2_md.keys())):
            print('Difference in %s metadata key count' % id)
            print('  file1 Keys: ' + str(list(file1_md.keys())))
            print('  file2 Keys: ' + str(list(file2_md.keys())))
            found_diff += 1

        for key in list(file1_md.keys()):
            if key not in file2_md:
                print('file2 %s metadata lacks key \"%s\"' % (id, key))
                found_diff += 1
            elif file2_md[key] != file1_md[key]:
                print('Metadata value difference for key "' + key + '"')
                print('  file1: "' + file1_md[key] + '"')
                print('  file2:    "' + file2_md[key] + '"')
                found_diff += 1

        return found_diff

    #######################################################
    # Review and report on the actual image pixels that differ.
    def __compare_image_pixels(self, file1_band, file2_band, id, options=[]):
        diff_count = 0
        max_diff = 0

        for line in range(file1_band.YSize):
            file1_line = file1_band.ReadAsArray(0, line, file1_band.XSize, 1)[0]
            file2_line = file2_band.ReadAsArray(0, line, file1_band.XSize, 1)[0]
            diff_line = file1_line.astype(float) - file2_line.astype(float)
            max_diff = max(max_diff, abs(diff_line).max())
            diff_count += len(diff_line.nonzero()[0])

        print('  Pixels Differing: ' + str(diff_count))
        print('  Maximum Pixel Difference: ' + str(max_diff))

    #######################################################
    def __compare_band(self, file1_band, file2_band, id, options=[]):
        found_diff = 0

        if file1_band.DataType != file2_band.DataType:
            print('Band %s pixel types differ.' % id)
            print('  file1: ' + gdal.GetDataTypeName(file1_band.DataType))
            print('  file2:    ' + gdal.GetDataTypeName(file2_band.DataType))
            found_diff += 1

        if file1_band.GetNoDataValue() != file2_band.GetNoDataValue():
            print('Band %s nodata values differ.' % id)
            print('  file1: ' + str(file1_band.GetNoDataValue()))
            print('  file2:    ' + str(file2_band.GetNoDataValue()))
            found_diff += 1

        if file1_band.GetColorInterpretation() != file2_band.GetColorInterpretation():
            print('Band %s color interpretation values differ.' % id)
            print('  file1: ' + gdal.GetColorInterpretationName(file1_band.GetColorInterpretation()))
            print('  file2:    ' + gdal.GetColorInterpretationName(file2_band.GetColorInterpretation()))
            found_diff += 1

        if file1_band.Checksum() != file2_band.Checksum():
            print('Band %s checksum difference:' % id)
            print('  file1: ' + str(file1_band.Checksum()))
            print('  file2:    ' + str(file2_band.Checksum()))
            found_diff += 1
            self.__compare_image_pixels(file1_band, file2_band, id, options)

        # Check overviews
        if file1_band.GetOverviewCount() != file2_band.GetOverviewCount():
            print('Band %s overview count difference:' % id)
            print('  file1: ' + str(file1_band.GetOverviewCount()))
            print('  file2:    ' + str(file2_band.GetOverviewCount()))
            found_diff += 1
        else:
            for i in range(file1_band.GetOverviewCount()):
                found_diff += self.__compare_band(file1_band.GetOverview(i),
                                                  file2_band.GetOverview(i),
                                                  id + ' overview ' + str(i),
                                                  options)

        # Metadata
        if 'SKIP_METADATA' not in options:
            found_diff += self.__compare_metadata(file1_band.GetMetadata(),
                                                  file2_band.GetMetadata(),
                                                  'Band ' + id, options)

        # TODO: Color Table, gain/bias, units, blocksize, mask, min/max

        return found_diff

    #######################################################
    def __compare_srs(self, file1_wkt, file2_wkt):
        retour = 1        
        if file1_wkt == file2_wkt:
            retour = 0
        else:
            print('Difference in SRS!')

            file1_srs = osr.SpatialReference(file1_wkt)
            file2_srs = osr.SpatialReference(file2_wkt)

            if file1_srs.IsSame(file2_srs):
                print('  * IsSame() reports them as equivalent.')
            else:
                print('  * IsSame() reports them as different.')

            print('  file1:')
            print('  ' + file1_srs.ExportToPrettyWkt())
            print('  file2:')
            print('  ' + file2_srs.ExportToPrettyWkt())

        return retour

    #######################################################
    def __compareGdal(self, file1_gdal, file2_gdal, options=[]):
        found_diff = 0

        # SRS
        if 'SKIP_SRS' not in options:
            found_diff += self.__compare_srs(file1_gdal.GetProjection(),
                                             file2_gdal.GetProjection())

        # GeoTransform
        if 'SKIP_GEOTRANSFORM' not in options:
            file1_gt = file1_gdal.GetGeoTransform()
            file2_gt = file2_gdal.GetGeoTransform()
            if file1_gt != file2_gt:
                print('GeoTransforms Differ:')
                print('  file1: ' + str(file1_gt))
                print('  file2:    ' + str(file2_gt))
                found_diff += 1

        # Metadata
        if 'SKIP_METADATA' not in options:
            found_diff += self.__compare_metadata(file1_gdal.GetMetadata(),
                                                  file2_gdal.GetMetadata(),
                                                  'Dataset', options)

        # Bands
        if file1_gdal.RasterCount != file2_gdal.RasterCount:
            print('Band count mismatch (file1=%d, file2=%d)'
                  % (file1_gdal.RasterCount, file2_gdal.RasterCount))
            found_diff += 1

        # Dimensions
        for i in range(file1_gdal.RasterCount):
            gSzX = file1_gdal.GetRasterBand(i + 1).XSize
            nSzX = file2_gdal.GetRasterBand(i + 1).XSize
            gSzY = file1_gdal.GetRasterBand(i + 1).YSize
            nSzY = file2_gdal.GetRasterBand(i + 1).YSize

            if gSzX != nSzX or gSzY != nSzY:
                print('Band size mismatch (band=%d file1=[%d,%d], file2=[%d,%d])' %
                      (i, gSzX, gSzY, nSzX, nSzY))
                found_diff += 1

        # If so-far-so-good, then compare pixels
        if found_diff == 0:
            for i in range(file1_gdal.RasterCount):
                found_diff += self.__compare_band(file1_gdal.GetRasterBand(i + 1),
                                                  file2_gdal.GetRasterBand(i + 1),
                                                  str(i + 1),
                                                  options)

        return found_diff

    #######################################################
    def __compareGdalSDS(self, file1_db, file2_db, options=[]):
        found_diff = 0

        file1_sds = file1_db.GetMetadata('SUBDATASETS')
        file2_sds = file2_db.GetMetadata('SUBDATASETS')

        count = len(list(file1_sds.keys())) / 2
        for i in range(count):
            key = 'SUBDATASET_%d_NAME' % (i + 1)

            sub_file1_db = gdal.Open(file1_sds[key])
            sub_file2_db = gdal.Open(file2_sds[key])

            sds_diff = self.__compareGdal(sub_file1_db, sub_file2_db, options)
            found_diff += sds_diff
            if sds_diff > 0:
                print('%d differences found between:\n  %s\n  %s'
                      % (sds_diff, file1_sds[key], file2_sds[key]))

        return found_diff

    #######################################################
    def gdalFileCompare(self, file1, file2):
        """
        Compares the two files in input and return the number of differences
        @param:
            file1: string first file
            file2: string second file
        @return:
            The number of differences
        """
        try:
            os.stat(file1)
        except:
            raise Exception("Could not open " + file1)
        try:
            os.stat(file2)
        except:
            raise Exception("Could not open " + file2)

        file1_gdal = gdal.Open(file1)
        file2_gdal = gdal.Open(file2)

        checkSubDataSet = False

        difference = 0

        difference += self.__compareGdal(file1_gdal, file2_gdal)

        if checkSubDataSet:
            difference += self.__compareGdalSDS(file1_gdal, file2_gdal)

        return difference


# Error class definition
class DifferenceError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class serviceCompareVectorFile:
    """
    The class serviceCompareShapeFile provides methods to compare
    two vector file
    """

    def testSameShapefiles(self, vector1, vector2, driver='ESRI Shapefile'):
        """
            IN :
                vector [string] : path to shapefile 1
                vector [string] : path to shapefile 2
                driver [string] : gdal driver
            OUT :
                retour [bool] : True if same file False if different
        """

        def isEqual(in1, in2):
            if in1 != in2:
                raise DifferenceError("Files are not identical")

        # Output of the function
        retour = False

        try:
            driver = ogr.GetDriverByName(driver)
            # Openning of files
            data1 = driver.Open(vector1, 0)
            data2 = driver.Open(vector2, 0)

            if data1 is None:
                raise Exception("Could not open " + vector1)
            if data2 is None:
                raise Exception("Could not open " + vector2)

            layer1 = data1.GetLayer()
            layer2 = data2.GetLayer()
            featureCount1 = layer1.GetFeatureCount()
            featureCount2 = layer2.GetFeatureCount()
            # check if number of element is equal
            isEqual(featureCount1, featureCount2)

            # check if type of geometry is same
            isEqual(layer1.GetGeomType(), layer2.GetGeomType())

            # check features
            for i in range(featureCount1):
                feature1 = layer1.GetFeature(i)
                feature2 = layer2.GetFeature(i)

                geom1 = feature1.GetGeometryRef()
                geom2 = feature2.GetGeometryRef()
                print geom1
                print geom2
                # check if coordinates are equal
                isEqual(str(geom1), str(geom2))

            layerDefinition1 = layer1.GetLayerDefn()
            layerDefinition2 = layer2.GetLayerDefn()
            # check if number of fiels is equal
            isEqual(layerDefinition1.GetFieldCount(),
                    layerDefinition2.GetFieldCount())

            # check fields for layer definition
            for i in range(layerDefinition1.GetFieldCount()):
                isEqual(layerDefinition1.GetFieldDefn(i).GetName(),
                        layerDefinition2.GetFieldDefn(i).GetName())
                fieldTypeCode = layerDefinition1.GetFieldDefn(i).GetType()
                isEqual(layerDefinition1.GetFieldDefn(i).GetFieldTypeName(fieldTypeCode),
                        layerDefinition2.GetFieldDefn(i).GetFieldTypeName(fieldTypeCode))
                isEqual(layerDefinition1.GetFieldDefn(i).GetWidth(),
                        layerDefinition2.GetFieldDefn(i).GetWidth())
                isEqual(layerDefinition1.GetFieldDefn(i).GetPrecision(),
                        layerDefinition2.GetFieldDefn(i).GetPrecision())

        # TODO Voir si ces tests sont suffisants.

        except DifferenceError:
            # DifferenceError : retour set to false
            retour = False
        except:
            # other error : retour set to false and raise
            retour = False
            raise
        else:
            # no error : files are identical retour set to true
            retour = True

        return retour

