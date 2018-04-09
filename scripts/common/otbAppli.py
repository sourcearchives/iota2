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

import re
import os
import ast
import Sensors
import numpy as np
from Utils import Opath
import otbApplication as otb
import fileUtils as fut
import logging

logger = logging.getLogger(__name__)

def getInputParameterOutput(otbObj):

    """
    IN :
    otbObj [otb object]

    OUT :
    output parameter name

    Ex :
    otbBandMath = otb.CreateBandMathApplication(...)
    print getInputParameterOutput(otbBandMath)
    >> out

    /!\ this function is not complete, it must be fill up...
    """
    listParam = otbObj.GetParametersKeys()
    #check out
    if "out" in listParam:
        return "out"
    #check io.out
    elif "io.out" in listParam:
        return "io.out"
    #check mode.raster.out
    elif "mode.raster.out" in listParam:
        return "mode.raster.out"
    elif "outputstack" in listParam:
        return "outputstack"
    else:
        raise Exception("out parameter not recognize")


def unPackFirst(someListOfList):

    """
    python generator
    return first element of a list of list

    Ex:
    myListOfList = [[1,2,3],[4,5,6]]

    for firstValue in unPackFirst(myListOfList):
        print firstValue
    >> 1
    >> 4
    """
    for values in someListOfList:
        if isinstance(values, list) or isinstance(values, tuple):
            yield values[0]
        else:
            yield values


def CreateComputeConfusionMatrixApplication(OtbParameters):
    """
    in parameter could be string
    """
    confusion = otb.Registry.CreateApplication("ComputeConfusionMatrix")
    if not "in" in OtbParameters:
        raise Exception("'in' parameter not found")
    if not "out" in OtbParameters:
        raise Exception("'out' parameter not found")
    if "ref.vector.in" in OtbParameters:
        confusion.SetParameterString("ref.vector.in", str(OtbParameters["ref.vector.in"]))

    confusion.SetParameterString("in", str(OtbParameters["in"]))
    confusion.SetParameterString("out", str(OtbParameters["out"]))
    confusion.UpdateParameters()

    if "format" in OtbParameters:
        confusion.SetParameterString("format", str(OtbParameters["format"]))
    if "ref" in OtbParameters:
        confusion.SetParameterString("ref", str(OtbParameters["ref"]))
    if "ref.raster.in" in OtbParameters:
        confusion.SetParameterString("ref.raster.in", str(OtbParameters["ref.raster.in"]))
    if "ref.raster.nodata" in OtbParameters:
        confusion.SetParameterString("ref.raster.nodata", str(OtbParameters["ref.raster.nodata"]))
    
    if "ref.vector.field" in OtbParameters:
        confusion.SetParameterString("ref.vector.field", str(OtbParameters["ref.vector.field"]))
    if "ref.vector.nodata" in OtbParameters:
        confusion.SetParameterString("ref.vector.nodata", str(OtbParameters["ref.vector.nodata"]))
    if "nodatalabel" in OtbParameters:
        confusion.SetParameterString("nodatalabel", str(OtbParameters["nodatalabel"]))
    if "ram" in OtbParameters:
        confusion.SetParameterString("ram", str(OtbParameters["ram"]))
    
    return confusion


def CreateFusionOfClassificationsApplication(OtbParameters):
    """
    IN:
    parameter consistency are not tested here (done in otb's applications)
    in parameter could be string/OtbApplication/tupleOfOtbApplication
    OtbParameters [dic] dictionnary with otb's parameter keys
                        Example :
                        OtbParameters = {"in":"/image.tif","filter":"lee",\
                                        pixType:"uint8","out":"/out.tif"}
    OUT :
    fusion [otb object ready to Execute]
    """
    fusion = otb.Registry.CreateApplication("FusionOfClassifications")
    
    #Mandatory
    if not "il" in OtbParameters:
        raise Exception("'il' parameter not found")

    imagesList = OtbParameters["il"]
    if not isinstance(imagesList, list):
        imagesList = [imagesList]

    if isinstance(imagesList[0], str):
        fusion.SetParameterStringList("il", imagesList)
    elif isinstance(imagesList[0], otb.Application):
        for currentObj in imagesList:
            inOutParam = getInputParameterOutput(currentObj)
            fusion.AddImageToParameterInputImageList("il",
                                                     currentObj.GetParameterOutputImage(inOutParam))
    elif isinstance(imagesList[0], tuple):
        for currentObj in unPackFirst(imagesList):
            inOutParam = getInputParameterOutput(currentObj)
            fusion.AddImageToParameterInputImageList("il",
                                                     currentObj.GetParameterOutputImage(inOutParam))
    else:
        raise Exception(type(imageList[0]) + " not available to FusionOfClassifications function")
    if "method" in OtbParameters:
        fusion.SetParameterString("method", str(OtbParameters["method"]))
    if "ram" in OtbParameters:
        fusion.SetParameterString("ram", str(OtbParameters["ram"]))
    if "method.dempstershafer.cmfl" in OtbParameters:
        fusion.SetParameterString("method.dempstershafer.cmfl", str(OtbParameters["method.dempstershafer.cmfl"]))
    if "method.dempstershafer.mob" in OtbParameters:
        fusion.SetParameterString("method.dempstershafer.mob", str(OtbParameters["method.dempstershafer.mob"]))
    if "nodatalabel" in OtbParameters:
        fusion.SetParameterString("nodatalabel", str(OtbParameters["nodatalabel"]))
    if "undecidedlabel" in OtbParameters:
        fusion.SetParameterString("undecidedlabel", str(OtbParameters["undecidedlabel"]))
    if "out" in OtbParameters:
        fusion.SetParameterString("out", str(OtbParameters["out"]))
    if "pixType" in OtbParameters:
        fusion.SetParameterOutputImagePixelType("out", fut.commonPixTypeToOTB(OtbParameters["pixType"]))

    return fusion


def CreatePolygonClassStatisticsApplication(OtbParameters):
    """
    IN:
    parameter consistency are not tested here (done in otb's applications)
    in parameter could be string/OtbApplication/tupleOfOtbApplication
    OtbParameters [dic] dictionnary with otb's parameter keys
                        Example :
                        OtbParameters = {"in":"/image.tif","filter":"lee",\
                                        pixType:"uint8","out":"/out.tif"}
    OUT :
    pClassStats [otb object ready to Execute]
    """

    pClassStats = otb.Registry.CreateApplication("PolygonClassStatistics")
    if not "in" in OtbParameters:
        raise Exception("'in' parameter not found")
    if not "out" in OtbParameters:
        raise Exception("'out' parameter not found")
    if not "vec" in OtbParameters:
        raise Exception("'vec' parameter not found")

    #Mandatory
    inputIm = OtbParameters["in"]
    if isinstance(inputIm, str):
        pClassStats.SetParameterString("in", inputIm)
    elif isinstance(inputIm, tuple):
        inOutParam = getInputParameterOutput(inputIm[0])
        pClassStats.SetParameterInputImage("in",
                                           inputIm[0].GetParameterOutputImage(inOutParam))
    elif isinstance(inputIm, otb.Application):
        inOutParam = getInputParameterOutput(inputIm)
        pClassStats.SetParameterInputImage("in",
                                           inputIm.GetParameterOutputImage(inOutParam))
    else:
        raise Exception("input image not recognize")

    pClassStats.SetParameterString("out", OtbParameters["out"])
    pClassStats.SetParameterString("vec", OtbParameters["vec"])
    pClassStats.UpdateParameters()

    #options
    if "mask" in OtbParameters:
        pClassStats.SetParameterString("mask", OtbParameters["mask"])
    if "field" in OtbParameters:
        pClassStats.SetParameterString("field", OtbParameters["field"].lower())
    if "layer" in OtbParameters:
        pClassStats.SetParameterString("layer", OtbParameters["layer"])
    if "elev.dem" in OtbParameters:
        pClassStats.SetParameterString("elev.dem", OtbParameters["elev.dem"])
    if "elev.geoid" in OtbParameters:
        pClassStats.SetParameterString("elev.geoid",
                                       OtbParameters["elev.geoid"])
    if "elev.default" in OtbParameters:
        pClassStats.SetParameterString("elev.default",
                                       OtbParameters["elev.default"])
    if "ram" in OtbParameters:
        pClassStats.SetParameterString("ram", str(OtbParameters["ram"]))

    return pClassStats


def CreateSampleSelectionApplication(OtbParameters):

    """
    IN:
    parameter consistency are not tested here (done in otb's applications)
    in parameter could be string/OtbApplication/tupleOfOtbApplication
    OtbParameters [dic] dictionnary with otb's parameter keys
                        Example :
                        OtbParameters = {"in":"/image.tif","filter":"lee",\
                                        pixType:"uint8","out":"/out.tif"}
    OUT :
    sampleS [otb object ready to Execute]
    """

    sampleS = otb.Registry.CreateApplication("SampleSelection")
    if not "in" in OtbParameters:
        raise Exception("'in' parameter not found")
    if not "out" in OtbParameters:
        raise Exception("'out' parameter not found")
    if not "vec" in OtbParameters:
        raise Exception("'vec' parameter not found")
    if not "instats" in OtbParameters:
        raise Exception("'instats' parameter not found")

    #Mandatory
    inputIm = OtbParameters["in"]
    if isinstance(inputIm, str):
        sampleS.SetParameterString("in", inputIm)
    elif isinstance(inputIm, tuple):
        inOutParam = getInputParameterOutput(inputIm[0])
        sampleS.SetParameterInputImage("in",
                                       inputIm[0].GetParameterOutputImage(inOutParam))
    elif isinstance(inputIm, otb.Application):
        inOutParam = getInputParameterOutput(inputIm)
        sampleS.SetParameterInputImage("in",
                                       inputIm.GetParameterOutputImage(inOutParam))
    else:
        raise Exception("input image not recognize")

    sampleS.SetParameterString("out", OtbParameters["out"])
    sampleS.SetParameterString("vec", OtbParameters["vec"])
    sampleS.SetParameterString("instats", OtbParameters["instats"])
    sampleS.UpdateParameters()

    #options
    if "mask" in OtbParameters:
        sampleS.SetParameterString("mask", OtbParameters["mask"])
    if "outrates" in OtbParameters:
        sampleS.SetParameterString("outrates", OtbParameters["outrates"])
    if "sampler" in OtbParameters:
        sampleS.SetParameterString("sampler", OtbParameters["sampler"])
    if "sampler.periodic.jitter" in OtbParameters:
        sampleS.SetParameterString("sampler.periodic.jitter",
                                   OtbParameters["sampler.periodic.jitter"])
    if "strategy" in OtbParameters:
        sampleS.SetParameterString("strategy", OtbParameters["strategy"])
    if "strategy.byclass.in" in OtbParameters:
        sampleS.SetParameterString("strategy.byclass.in",
                                   str(OtbParameters["strategy.byclass.in"]))
    if "strategy.constant.nb" in OtbParameters:
        sampleS.SetParameterString("strategy.constant.nb",
                                   str(OtbParameters["strategy.constant.nb"]))
    if "strategy.percent.p" in OtbParameters:
        sampleS.SetParameterString("strategy.percent.p",
                                   str(OtbParameters["strategy.percent.p"]))
    if "strategy.total.v" in OtbParameters:
        sampleS.SetParameterString("strategy.total.v",
                                   str(OtbParameters["strategy.total.v"]))
    if "field" in OtbParameters:
        sampleS.SetParameterString("field", OtbParameters["field"].lower())
    if "layer" in OtbParameters:
        sampleS.SetParameterString("layer", OtbParameters["layer"])
    if "elev.dem" in OtbParameters:
        sampleS.SetParameterString("elev.dem", OtbParameters["elev.dem"])
    if "elev.geoid" in OtbParameters:
        sampleS.SetParameterString("elev.geoid", OtbParameters["elev.geoid"])
    if "elev.default" in OtbParameters:
        sampleS.SetParameterString("elev.default",
                                   OtbParameters["elev.default"])
    if "ram" in OtbParameters:
        sampleS.SetParameterString("ram", str(OtbParameters["ram"]))
    if "rand" in OtbParameters:
        sampleS.SetParameterString("rand", str(OtbParameters["rand"]))

    return sampleS


def CreateSampleExtractionApplication(OtbParameters):
    """
    IN:
    parameter consistency are not tested here (done in otb's applications)
    in parameter could be string/OtbApplication/tupleOfOtbApplication
    OtbParameters [dic] dictionnary with otb's parameter keys
                        Example :
                        OtbParameters = {"in":"/image.tif","filter":"lee",\
                                        pixType:"uint8","out":"/out.tif"}
    OUT :
    sampleE [otb object ready to Execute]
    """

    sampleE = otb.Registry.CreateApplication("SampleExtraction")
    if not "in" in OtbParameters:
        raise Exception("'in' parameter not found")
    if not "out" in OtbParameters:
        raise Exception("'out' parameter not found")
    if not "vec" in OtbParameters:
        raise Exception("'vec' parameter not found")

    inputIm = OtbParameters["in"]
    if isinstance(inputIm, str):
        sampleE.SetParameterString("in", inputIm)
    elif isinstance(inputIm, tuple):
        inOutParam = getInputParameterOutput(inputIm[0])
        sampleE.SetParameterInputImage("in",
                                       inputIm[0].GetParameterOutputImage(inOutParam))
    elif isinstance(inputIm, otb.Application):
        inOutParam = getInputParameterOutput(inputIm)
        sampleE.SetParameterInputImage("in",
                                       inputIm.GetParameterOutputImage(inOutParam))
    else:
        raise Exception("input image not recognize")

    sampleE.SetParameterString("out", OtbParameters["out"])
    sampleE.SetParameterString("vec", OtbParameters["vec"])
    sampleE.UpdateParameters()
    if "outfield" in OtbParameters:
        sampleE.SetParameterString("outfield", OtbParameters["outfield"])
    if "outfield.prefix.name" in OtbParameters:
        sampleE.SetParameterString("outfield.prefix.name",
                                   str(OtbParameters["outfield.prefix.name"]))
    if "outfield.list.names" in OtbParameters:
        if not isinstance(OtbParameters["outfield.list.names"], list):
            raise Exception("outfield.list.names must be a list of string")
        sampleE.SetParameterStringList("outfield.list.names",
                                       OtbParameters["outfield.list.names"])
    if "field" in OtbParameters:
        sampleE.SetParameterString("field",
                                   str(OtbParameters["field"]).lower())
    if "layer" in OtbParameters:
        sampleE.SetParameterString("layer", str(OtbParameters["layer"]))
    if "ram" in OtbParameters:
        sampleE.SetParameterString("ram", str(OtbParameters["ram"]))

    return sampleE


def CreateDespeckleApplication(OtbParameters):
    """
    IN:
    parameter consistency are not tested here (done in otb's applications)
    every value could be string
    in parameter could be string/OtbApplication/tupleOfOtbApplication
    OtbParameters [dic] dictionnary with otb's parameter keys
                        Example :
                        OtbParameters = {"in":"/image.tif","filter":"lee",\
                                        pixType:"uint8","out":"/out.tif"}
    OUT :
    despeckle [otb object ready to Execute]
    """

    despeckle = otb.Registry.CreateApplication("Despeckle")
    if not "in" in OtbParameters:
        raise Exception("'in' parameter not found")
    if not "out" in OtbParameters:
        raise Exception("'out' parameter not found")

    inputIm = OtbParameters["in"]
    if isinstance(inputIm, str):
        despeckle.SetParameterString("in", inputIm)
    elif isinstance(inputIm, tuple):
        inOutParam = getInputParameterOutput(inputIm[0])
        despeckle.SetParameterInputImage("in",
                                         inputIm[0].GetParameterOutputImage(inOutParam))
    elif isinstance(inputIm, otb.Application):
        inOutParam = getInputParameterOutput(inputIm)
        despeckle.SetParameterInputImage("in",
                                         inputIm.GetParameterOutputImage(inOutParam))
    else:
        raise Exception("input image not recognize")

    despeckle.SetParameterString("out", OtbParameters["out"])

    if "filter" in OtbParameters:
        despeckle.SetParameterString("filter", OtbParameters["filter"])
    if "filter.lee.rad" in OtbParameters:
        despeckle.SetParameterString("filter.lee.rad",
                                     str(OtbParameters["filter.lee.rad"]))
    if "filter.lee.nblooks" in OtbParameters:
        despeckle.SetParameterString("filter.lee.nblooks",
                                     str(OtbParameters["filter.lee.nblooks"]))
    if "filter.frost.rad" in OtbParameters:
        despeckle.SetParameterString("filter.frost.rad",
                                     str(OtbParameters["filter.frost.rad"]))
    if "filter.frost.deramp" in OtbParameters:
        despeckle.SetParameterString("filter.frost.deramp",
                                     str(OtbParameters["filter.frost.deramp"]))
    if "filter.gammamap.rad" in OtbParameters:
        despeckle.SetParameterString("filter.gammamap.rad",
                                     str(OtbParameters["filter.gammamap.rad"]))
    if "filter.gammamap.nblooks" in OtbParameters:
        despeckle.SetParameterString("filter.gammamap.nblooks",
                                     str(OtbParameters["filter.gammamap.nblooks"]))
    if "filter.kuan.rad" in OtbParameters:
        despeckle.SetParameterString("filter.kuan.rad",
                                     str(OtbParameters["filter.kuan.rad"]))
    if "filter.kuan.nblooks" in OtbParameters:
        despeckle.SetParameterString("filter.kuan.nblooks",
                                     str(OtbParameters["filter.kuan.nblooks"]))
    if "ram" in OtbParameters:
        despeckle.SetParameterString("ram", str(OtbParameters["ram"]))
    if "pixType" in OtbParameters:
        despeckle.SetParameterOutputImagePixelType("out",
                                                   fut.commonPixTypeToOTB(OtbParameters["pixType"]))

    return despeckle


def monoDateDespeckle(allOrtho, tile):
    """
    usage : for each raster in allOrtho apply a despeckle filter and stack
    results by sensor (S1A/S1B) and by mode (ASC/DESC) -> needed to gapFilling
    process

    IN
    allOrtho [list of otb's application]
    tile [string] : current tile to process

    OUT
    SARfiltered [list of tuple] : a tuple contains (concatS1BASC,despeckS1bASC,"","","")
        concatS1BASC [otb application] is the concatenation of all despeckle
        despeckS1bASC [otb application] is all despeckle
    """
    fut.updatePyPath()
    from S1FilteringProcessor import getOrtho, getDatesInOtbOutputName

    s1aDESlist = sorted([currentOrtho for currentOrtho in getOrtho(allOrtho, "s1a(.*)" + tile + "(.*)DES(.*)tif")],
                        key=getDatesInOtbOutputName)
    s1aASClist = sorted([currentOrtho for currentOrtho in getOrtho(allOrtho, "s1a(.*)" + tile + "(.*)ASC(.*)tif")],
                        key=getDatesInOtbOutputName)
    s1bDESlist = sorted([currentOrtho for currentOrtho in getOrtho(allOrtho, "s1b(.*)" + tile + "(.*)DES(.*)tif")],
                        key=getDatesInOtbOutputName)
    s1bASClist = sorted([currentOrtho for currentOrtho in getOrtho(allOrtho, "s1b(.*)" + tile + "(.*)ASC(.*)tif")],
                        key=getDatesInOtbOutputName)

    despeckS1aDES = []
    despeckS1aASC = []
    despeckS1bDES = []
    despeckS1bASC = []

    if s1aDESlist:
        for cOrtho in s1aDESlist:
            cOrtho.Execute()
            inOutParam = getInputParameterOutput(cOrtho)
            despeckParam = {"in": cOrtho, "out": ""}
            despeckle = CreateDespeckleApplication(despeckParam)
            despeckle.Execute()
            despeckS1aDES.append(despeckle)

    if s1aASClist:
        for cOrtho in s1aASClist:
            cOrtho.Execute()
            inOutParam = getInputParameterOutput(cOrtho)
            despeckParam = {"in": cOrtho, "out": ""}
            despeckle = CreateDespeckleApplication(despeckParam)
            despeckle.Execute()
            despeckS1aASC.append(despeckle)

    if s1bDESlist:
        for cOrtho in s1bDESlist:
            cOrtho.Execute()
            inOutParam = getInputParameterOutput(cOrtho)
            despeckParam = {"in": cOrtho, "out": ""}
            despeckle = CreateDespeckleApplication(despeckParam)
            despeckle.Execute()
            despeckS1bDES.append(despeckle)

    if s1bASClist:
        for cOrtho in s1bASClist:
            cOrtho.Execute()
            inOutParam = getInputParameterOutput(cOrtho)
            despeckParam = {"in": cOrtho, "out": ""}
            despeckle = CreateDespeckleApplication(despeckParam)
            despeckle.Execute()
            despeckS1bASC.append(despeckle)

    SARfiltered = []
    concatS1ADES = concatS1AASC = concatS1BDES = concatS1BASC = None
    if despeckS1aDES:
        concatS1ADES = CreateConcatenateImagesApplication({"il": despeckS1aDES,
                                                           "ram": '5000',
                                                           "pixType": "float",
                                                           "out": ""})
        concatS1ADES.Execute()
        SARfiltered.append((concatS1ADES, despeckS1aDES, "", "", ""))

    if despeckS1aASC:
        concatS1AASC = CreateConcatenateImagesApplication({"il": despeckS1aASC,
                                                           "ram": '2000',
                                                           "pixType": "float",
                                                           "out": ""})
        concatS1AASC.Execute()
        SARfiltered.append((concatS1AASC, despeckS1aASC, "", "", ""))

    if despeckS1bDES:
        concatS1BDES = CreateConcatenateImagesApplication({"il": despeckS1bDES,
                                                           "ram": '2000',
                                                           "pixType": "float",
                                                           "out": ""})
        concatS1BDES.Execute()
        SARfiltered.append((concatS1BDES, despeckS1bDES, "", "", ""))

    if despeckS1bASC:
        concatS1BASC = CreateConcatenateImagesApplication({"il": despeckS1bASC,
                                                           "ram": '2000',
                                                           "pixType": "float",
                                                           "out": ""})
        concatS1BASC.Execute()
        SARfiltered.append((concatS1BASC, despeckS1bASC, "", "", ""))

    return SARfiltered


def CreateSarCalibration(OtbParameters):
    """
    IN:
    parameter consistency are not tested here (done in otb's applications)
    every value could be string
    in parameter could be string/OtbApplication
    OtbParameters [dic] dictionnary with otb's parameter keys
                        Example :
                        OtbParameters = {"in":"/image.tif",
                                        pixType:"uint8","out":"/out.tif"}
    OUT :
    calibration [otb object ready to Execute]
    """
    calibration = otb.Registry.CreateApplication("SARCalibration")

    #Mandatory
    if not "in" in OtbParameters:
        raise Exception("'in' parameter not found")

    inputIm = OtbParameters["in"]
    if isinstance(inputIm, str):
        calibration.SetParameterString("in", inputIm)
    elif isinstance(inputIm, otb.Application):
        calibration.SetParameterInputImage("in",
                                           inputIm.GetParameterOutputImage("out"))
    else:
        raise Exception("input image not recognize")

    if "out" in OtbParameters:
        calibration.SetParameterString("out", OtbParameters["out"])
    if "lut" in OtbParameters:
        calibration.SetParameterString("lut", OtbParameters["lut"])
    if "ram" in OtbParameters:
        calibration.SetParameterString("ram", str(OtbParameters["ram"]))
    if "pixType" in OtbParameters:
        calibration.SetParameterOutputImagePixelType("out",
                                                     fut.commonPixTypeToOTB(OtbParameters["pixType"]))
    return calibration


def CreateOrthoRectification(OtbParameters):
    """
    IN:
    parameter consistency are not tested here (done in otb's applications)
    every value could be string
    in parameter could be string/OtbApplication/tuple
    OtbParameters [dic] dictionnary with otb's parameter keys
                        Example :
                        OtbParameters = {"in":"/image.tif",
                                        pixType:"uint8","out":"/out.tif"}
    OUT :
    ortho [otb object ready to Execute]
    """
    #Mandatory
    if not "in" in OtbParameters:
        raise Exception("'in' parameter not found")
    inputImage = OtbParameters["in"]

    #options
    ortho = otb.Registry.CreateApplication("OrthoRectification")
    if isinstance(inputImage, str):
        ortho.SetParameterString("io.in", inputImage)
    elif isinstance(inputImage, otb.Application):
        ortho.SetParameterInputImage("io.in",
                                     inputImage.GetParameterOutputImage("out"))
    elif isinstance(inputImage, tuple):
        ortho.SetParameterInputImage("io.in",
                                     inputImage[0].GetParameterOutputImage("out"))
    else:
        raise Exception("input image not recognize")

    if "io.out" in OtbParameters:
        ortho.SetParameterString("out", str(OtbParameters["out"]))
    if "map" in OtbParameters:
        ortho.SetParameterString("map", str(OtbParameters["map"]))
    if "map.utm.zone" in OtbParameters:
        ortho.SetParameterString("map.utm.zone",
                                 str(OtbParameters["map.utm.zone"]))
    if "map.utm.northhem" in OtbParameters:
        ortho.SetParameterString("map.utm.northhem",
                                 str(OtbParameters["map.utm.northhem"]))
    if "map.epsg.code" in OtbParameters:
        ortho.SetParameterString("map.epsg.code",
                                 str(OtbParameters["map.epsg.code"]))
    if "outputs.mode" in OtbParameters:
        ortho.SetParameterString("outputs.mode",
                                 str(OtbParameters["outputs.mode"]))
    if "outputs.ulx" in OtbParameters:
        ortho.SetParameterString("outputs.ulx",
                                 str(OtbParameters["outputs.ulx"]))
    if "outputs.uly" in OtbParameters:
        ortho.SetParameterString("outputs.uly",
                                 str(OtbParameters["outputs.uly"]))
    if "outputs.sizex" in OtbParameters:
        ortho.SetParameterString("outputs.sizex",
                                 str(OtbParameters["outputs.sizex"]))
    if "outputs.sizey" in OtbParameters:
        ortho.SetParameterString("outputs.sizey",
                                 str(OtbParameters["outputs.sizey"]))
    if "outputs.spacingx" in OtbParameters:
        ortho.SetParameterString("outputs.spacingx",
                                 str(OtbParameters["outputs.spacingx"]))
    if "outputs.spacingy" in OtbParameters:
        ortho.SetParameterString("outputs.spacingy",
                                 str(OtbParameters["outputs.spacingy"]))
    if "outputs.lrx" in OtbParameters:
        ortho.SetParameterString("outputs.lrx",
                                 str(OtbParameters["outputs.lrx"]))
    if "outputs.lry" in OtbParameters:
        ortho.SetParameterString("outputs.lry",
                                 str(OtbParameters["outputs.lry"]))
    if "outputs.ortho" in OtbParameters:
        ortho.SetParameterString("outputs.ortho",
                                 str(OtbParameters["outputs.ortho"]))
    if "outputs.isotropic" in OtbParameters:
        ortho.SetParameterString("outputs.isotropic",
                                 str(OtbParameters["outputs.isotropic"]))
    if "outputs.default" in OtbParameters:
        ortho.SetParameterString("outputs.default",
                                 str(OtbParameters["outputs.default"]))
    if "elev.dem" in OtbParameters:
        ortho.SetParameterString("elev.dem",
                                 str(OtbParameters["elev.dem"]))
    if "elev.geoid" in OtbParameters:
        ortho.SetParameterString("elev.geoid",
                                 str(OtbParameters["elev.geoid"]))
    if "elev.default" in OtbParameters:
        ortho.SetParameterString("elev.default",
                                 str(OtbParameters["elev.default"]))
    if "interpolator" in OtbParameters:
        ortho.SetParameterString("interpolator",
                                 str(OtbParameters["interpolator"]))
    if "interpolator.bco.radius" in OtbParameters:
        ortho.SetParameterString("interpolator.bco.radius",
                                 str(OtbParameters["interpolator.bco.radius"]))
    if "opt.rpc" in OtbParameters:
        ortho.SetParameterString("opt.rpc", str(OtbParameters["opt.rpc"]))
    if "opt.ram" in OtbParameters:
        ortho.SetParameterString("opt.ram", str(OtbParameters["opt.ram"]))
    if "opt.gridspacing" in OtbParameters:
        ortho.SetParameterString("opt.gridspacing",
                                 str(OtbParameters["opt.gridspacing"]))
    if "pixType" in OtbParameters:
        ortho.SetParameterOutputImagePixelType("out",
                                               fut.commonPixTypeToOTB(OtbParameters["pixType"]))
    return ortho, inputImage


def CreateMultitempFilteringFilter(OtbParameters):
    """
    IN:
    parameter consistency are not tested here (done in otb's applications)
    every value could be string
    in parameter could be string/List of OtbApplication/List of tuple
    OtbParameters [dic] dictionnary with otb's parameter keys
                        Example :
                        OtbParameters = {"in":"/image.tif",
                                        pixType:"uint8","out":"/out.tif"}
    OUT :
    SARfilterF [otb object ready to Execute]
    """
    SARfilterF = otb.Registry.CreateApplication("MultitempFilteringFilter")
    if not SARfilterF:
        raise Exception("MultitempFilteringFilter not available")

    #Mandatory
    if not "inl" in OtbParameters:
        raise Exception("'inl' parameter not found")
    if not "wr" in OtbParameters:
        raise Exception("'wr' parameter not found")
    if not "oc" in OtbParameters:
        raise Exception("'oc' parameter not found")
    if not "enl" in OtbParameters:
        raise Exception("'enl' parameter not found")

    inImg = OtbParameters["inl"]
    if not isinstance(inImg, list):
        inImg = [inImg]
    if isinstance(inImg[0], str):
        SARfilterF.SetParameterStringList("inl", inImg)
    elif isinstance(inImg[0], otb.Application):
        for currentObj in inImg:
            outparameterName = getInputParameterOutput(currentObj)
            SARfilterF.AddImageToParameterInputImageList("inl",
                                                         currentObj.GetParameterOutputImage(outparameterName))
    elif isinstance(inImg[0], tuple):
        for currentObj in unPackFirst(inImg):
            outparameterName = getInputParameterOutput(currentObj)
            SARfilterF.AddImageToParameterInputImageList("inl",
                                                         currentObj.GetParameterOutputImage(outparameterName))
    else:
        raise Exception(type(inImg[0]) +
                        " not available to CreateBandMathApplication function")
    SARfilterF.SetParameterString("wr", str(OtbParameters["wr"]))
    outcore = OtbParameters["oc"]
    if isinstance(outcore, str):
        SARfilterF.SetParameterString("oc", outcore)
    else:
        SARfilterF.SetParameterInputImage("oc",
                                          outcore.GetParameterOutputImage("oc"))

    SARfilterF.SetParameterString("enl", str(OtbParameters["enl"]))

    #options
    if "outputstack" in OtbParameters:
        SARfilterF.SetParameterString("outputstack",
                                      OtbParameters["outputstack"])
    if "ram" in OtbParameters:
        SARfilterF.SetParameterString("ram", str(OtbParameters["ram"]))
    if "pixType" in OtbParameters:
        SARfilterF.SetParameterOutputImagePixelType("enl",
                                                    fut.commonPixTypeToOTB(OtbParameters["pixType"]))
    return SARfilterF, inImg, outcore


def CreateMultitempFilteringOutcore(OtbParameters):
    """
    MultitempFilteringOutcore is an External otb module
    git clone http://tully.ups-tlse.fr/vincenta/otb-for-biomass.git -b memChain

    IN:
    parameter consistency are not tested here (done in otb's applications)
    every value could be string
    in parameter could be string/List of OtbApplication/List of tuple
    OtbParameters [dic] dictionnary with otb's parameter keys
                        Example :
                        OtbParameters = {"in":"/image.tif",
                                        pixType:"uint8","out":"/out.tif"}
    OUT :
    SARfilter [otb object ready to Execute]
    """
    SARfilter = otb.Registry.CreateApplication("MultitempFilteringOutcore")
    if not SARfilter:
        raise Exception("MultitempFilteringOutcore not available")

    #Mandatory
    if not "inl" in OtbParameters:
        raise Exception("'inl' parameter not found")
    if not "wr" in OtbParameters:
        raise Exception("'wr' parameter not found")
    if not "oc" in OtbParameters:
        raise Exception("'oc' parameter not found")

    inImg = OtbParameters["inl"]
    if not inImg:
        raise Exception("no input images detected")

    if not isinstance(inImg, list):
        inImg = [inImg]
    if isinstance(inImg[0], str):
        SARfilter.SetParameterStringList("inl", inImg)
    elif isinstance(inImg[0], otb.Application):
        for currentObj in inImg:
            outparameterName = getInputParameterOutput(currentObj)
            SARfilter.AddImageToParameterInputImageList("inl",
                                                        currentObj.GetParameterOutputImage(outparameterName))
    elif isinstance(inImg[0], tuple):
        for currentObj in unPackFirst(inImg):
            outparameterName = getInputParameterOutput(currentObj)
            SARfilter.AddImageToParameterInputImageList("inl",
                                                        currentObj.GetParameterOutputImage(outparameterName))
    else:
        raise Exception(type(inImg[0]) +
                        " not available to CreateBandMathApplication function")
    SARfilter.SetParameterString("wr", OtbParameters["wr"])
    SARfilter.SetParameterString("oc", OtbParameters["oc"])
    if "ram" in OtbParameters:
        SARfilter.SetParameterString("ram", str(OtbParameters["ram"]))
    if "pixType" in OtbParameters:
        SARfilter.SetParameterOutputImagePixelType("oc",
                                                   fut.commonPixTypeToOTB(OtbParameters["pixType"]))

    return SARfilter


def CreateBinaryMorphologicalOperation(OtbParameters):
    """
    IN:
    parameter consistency are not tested here (done in otb's applications)
    every value could be string
    in parameter could be string/OtbApplication/tuple
    OtbParameters [dic] dictionnary with otb's parameter keys
                        Example :
                        OtbParameters = {"in":"/image.tif",
                                        pixType:"uint8","out":"/out.tif"}
    OUT :
    morphoMath [otb object ready to Execute]
    """
    morphoMath = otb.Registry.CreateApplication("BinaryMorphologicalOperation")
    if morphoMath is None:
        raise Exception("Not possible to create 'Binary Morphological \
                        Operation' application, check if OTB is well \
                        configured / installed")

    if not "in" in OtbParameters:
        raise Exception("'in' parameter not found")
    inImg = OtbParameters["in"]

    if isinstance(inImg, str):
        morphoMath.SetParameterString("in", inImg)
    elif isinstance(inImg, otb.Application):
        inOutParam = getInputParameterOutput(inImg)
        morphoMath.SetParameterInputImage("in",
                                          inImg.GetParameterOutputImage(inOutParam))
    elif isinstance(inImg, tuple):
        morphoMath.SetParameterInputImage("in",
                                          inImg[0].GetParameterOutputImage("out"))
    else:
        raise Exception("input image not recognize")

    if "out" in OtbParameters:
        morphoMath.SetParameterString("out", OtbParameters["out"])
    if "channel" in OtbParameters:
        morphoMath.SetParameterString("channel", str(OtbParameters["channel"]))
    if "ram" in OtbParameters:
        morphoMath.SetParameterString("ram", str(OtbParameters["ram"]))
    if "structype" in OtbParameters:
        morphoMath.SetParameterString("structype",
                                      str(OtbParameters["structype"]))
    if "structype.ball.xradius" in OtbParameters:
        morphoMath.SetParameterString("structype.ball.xradius",
                                      str(OtbParameters["structype.ball.xradius"]))
    if "structype.ball.yradius" in OtbParameters:
        morphoMath.SetParameterString("structype.ball.yradius",
                                      str(OtbParameters["structype.ball.yradius"]))
    if "filter" in OtbParameters:
        morphoMath.SetParameterString("filter", str(OtbParameters["filter"]))
    if "filter.dilate.foreval" in OtbParameters:
        morphoMath.SetParameterString("filter.dilate.foreval",
                                      str(OtbParameters["filter.dilate.foreval"]))
    if "filter.dilate.backval" in OtbParameters:
        morphoMath.SetParameterString("filter.dilate.backval",
                                      str(OtbParameters["filter.dilate.backval"]))
    if "filter.erode.foreval" in OtbParameters:
        morphoMath.SetParameterString("filter.erode.foreval",
                                      str(OtbParameters["filter.erode.foreval"]))
    if "filter.erode.backval" in OtbParameters:
        morphoMath.SetParameterString("filter.erode.backval",
                                      str(OtbParameters["filter.erode.backval"]))
    if "filter.opening.foreval" in OtbParameters:
        morphoMath.SetParameterString("filter.opening.foreval",
                                      str(OtbParameters["filter.opening.foreval"]))
    if "filter.opening.backval" in OtbParameters:
        morphoMath.SetParameterString("filter.opening.backval",
                                      str(OtbParameters["filter.opening.backval"]))
    if "filter.closing.foreval" in OtbParameters:
        morphoMath.SetParameterString("filter.closing.foreval",
                                      str(OtbParameters["filter.closing.foreval"]))
    if "pixType" in OtbParameters:
        morphoMath.SetParameterOutputImagePixelType("out",
                                                    fut.commonPixTypeToOTB(OtbParameters["pixType"]))

    return morphoMath


def CreateClumpApplication(OtbParameters):
    """
    IN:
    parameter consistency are not tested here (done in otb's applications)
    every value could be string

    some parameters are missing -> should be added if needed

    in parameter could be string/OtbApplication/tuple
    OtbParameters [dic] dictionnary with otb's parameter keys
                        Example :
                        OtbParameters = {"in":"/image.tif",
                                        pixType:"uint8","out":"/out.tif"}
    OUT :
    seg [otb object ready to Execute]
    """
    seg = otb.Registry.CreateApplication("Segmentation")
    if seg is None:
        raise Exception("Not possible to create 'Segmentation' application, \
                        check if OTB is well configured / installed")
    if not "in" in OtbParameters:
        raise Exception("'in' parameter not found")
    stack = OtbParameters["in"]
    if isinstance(stack, str):
        seg.SetParameterString("in", stack)
    elif isinstance(stack, otb.Application):
        inOutParam = getInputParameterOutput(stack)
        seg.SetParameterInputImage("in", stack.GetParameterOutputImage(inOutParam))
    else:
        raise Exception(type(stack) + " not available to CreateClumpApplication function")

    if "mode" in OtbParameters:
        seg.SetParameterString("mode", OtbParameters["mode"])
    if "filter" in OtbParameters:
        seg.SetParameterString("filter", OtbParameters["filter"])
    if "filter.cc.expr" in OtbParameters:
        seg.SetParameterString("filter.cc.expr", OtbParameters["filter.cc.expr"])
    if "mode.raster.out" in OtbParameters:
        seg.SetParameterString("mode.raster.out", OtbParameters["mode.raster.out"])
    if "pixType" in OtbParameters:
        seg.SetParameterOutputImagePixelType("mode.raster.out", fut.commonPixTypeToOTB(OtbParameters["pixType"]))

    return seg


def CreateConcatenateImagesApplication(OtbParameters):
    """
    IN:
    parameter consistency are not tested here (done in otb's applications)
    every value could be string

    in parameter could be string/List of OtbApplication/List of tuple
    OtbParameters [dic] dictionnary with otb's parameter keys
                        Example :
                        OtbParameters = {"in":"/image.tif",
                                        pixType:"uint8","out":"/out.tif"}
    OUT :
    concatenate [otb object ready to Execute]
    """

    concatenate = otb.Registry.CreateApplication("ConcatenateImages")
    if concatenate is None:
        raise Exception("Not possible to create 'Concatenation' application, \
                        check if OTB is well configured / installed")

    if not "il" in OtbParameters:
        raise Exception("'il' parameter not found")

    imagesList = OtbParameters["il"]
    if not isinstance(imagesList, list):
        imagesList = [imagesList]

    if isinstance(imagesList[0], str):
        concatenate.SetParameterStringList("il", imagesList)
    elif isinstance(imagesList[0], otb.Application):
        for currentObj in imagesList:
            inOutParam = getInputParameterOutput(currentObj)
            concatenate.AddImageToParameterInputImageList("il",
                                                          currentObj.GetParameterOutputImage(inOutParam))
    elif isinstance(imagesList[0], tuple):
        for currentObj in unPackFirst(imagesList):
            inOutParam = getInputParameterOutput(currentObj)
            concatenate.AddImageToParameterInputImageList("il",
                                                          currentObj.GetParameterOutputImage(inOutParam))
    else:
        raise Exception("can't create ConcatenateImagesApplication")

    if "out" in OtbParameters:
        concatenate.SetParameterString("out", OtbParameters["out"])
    if "ram" in OtbParameters:
        concatenate.SetParameterString("ram", OtbParameters["ram"])
    if "pixType" in OtbParameters:
        concatenate.SetParameterOutputImagePixelType("out", fut.commonPixTypeToOTB(OtbParameters["pixType"]))

    return concatenate


def CreateBandMathApplication(OtbParameters):
    """
    IN:
    parameter consistency are not tested here (done in otb's applications)
    every value could be string

    in parameter could be string/List of OtbApplication/List of tuple of OtbApplication
    OtbParameters [dic] dictionnary with otb's parameter keys
                        Example :
                        OtbParameters = {"in":"/image.tif",
                                        pixType:"uint8","out":"/out.tif"}
    OUT :
    bandMath [otb object ready to Execute]
    """

    bandMath = otb.Registry.CreateApplication("BandMath")
    if bandMath is None:
        raise Exception("Not possible to create 'BandMath' application, \
                        check if OTB is well configured / installed")

    #Mandatory
    if not "il" in OtbParameters:
        raise Exception("'il' parameter not found")
    if not "exp" in OtbParameters:
        raise Exception("'exp' parameter not found")
    imagesList = OtbParameters["il"]
    if not isinstance(imagesList, list):
        imagesList = [imagesList]

    if isinstance(imagesList[0], str):
        bandMath.SetParameterStringList("il", imagesList)
    elif isinstance(imagesList[0], otb.Application):
        for currentObj in imagesList:
            inOutParam = getInputParameterOutput(currentObj)
            bandMath.AddImageToParameterInputImageList("il",
                                                       currentObj.GetParameterOutputImage(inOutParam))
    elif isinstance(imagesList[0], tuple):
        for currentObj in unPackFirst(imagesList):
            inOutParam = getInputParameterOutput(currentObj)
            bandMath.AddImageToParameterInputImageList("il",
                                                       currentObj.GetParameterOutputImage(inOutParam))
    else:
        raise Exception(type(imageList[0]) + " not available to CreateBandMathApplication function")

    bandMath.SetParameterString("exp", OtbParameters["exp"])

    #Options
    if "ram" in OtbParameters:
        bandMath.SetParameterString("ram", OtbParameters["ram"])
    if "out" in OtbParameters:
        bandMath.SetParameterString("out", OtbParameters["out"])
    if "pixType" in OtbParameters:
        bandMath.SetParameterOutputImagePixelType("out", fut.commonPixTypeToOTB(OtbParameters["pixType"]))
    return bandMath


def CreateSuperimposeApplication(OtbParameters):
    """
    IN:
    parameter consistency are not tested here (done in otb's applications)
    every value could be string

    in parameters could be string/OtbApplication/tuple of OtbApplication
    OtbParameters [dic] dictionnary with otb's parameter keys
                        Example :
                        OtbParameters = {"in":"/image.tif",
                                        pixType:"uint8","out":"/out.tif"}
    OUT :
    siApp [otb object ready to Execute]
    """
    siApp = otb.Registry.CreateApplication("Superimpose")
    if siApp is None:
        raise Exception("Not possible to create 'Superimpose' application, \
                        check if OTB is well configured / installed")

    #Mandatory
    if not "inr" in OtbParameters:
        raise Exception("'inr' parameter not found")
    if not "inm" in OtbParameters:
        raise Exception("'inm' parameter not found")

    inImg1 = OtbParameters["inr"]
    # First image input
    if isinstance(inImg1, str):
        siApp.SetParameterString("inr", inImg1)
    elif isinstance(inImg1, otb.Application):
        inOutParam = getInputParameterOutput(inImg1)
        siApp.SetParameterInputImage("inr", inImg1.GetParameterOutputImage(inOutParam))
    elif isinstance(inImg1, tuple):
        siApp.SetParameterInputImage("inr", inImg1[0].GetParameterOutputImage(getInputParameterOutput(inImg1[0])))
    else:
        raise Exception("reference input image not recognize")

    inImg2 = OtbParameters["inm"]
    # Second image input
    if isinstance(inImg2, str):
        siApp.SetParameterString("inm", inImg2)
    elif isinstance(inImg2, otb.Application):
        inOutParam = getInputParameterOutput(inImg2)
        siApp.SetParameterInputImage("inm", inImg2.GetParameterOutputImage(inOutParam))
    elif isinstance(inImg2, tuple):
        siApp.SetParameterInputImage("inm", inImg2[0].GetParameterOutputImage(getInputParameterOutput(inImg2[0])))
    else:
        raise Exception("Image to reproject not recognize")

    #Options
    if "elev.dem" in OtbParameters:
        siApp.SetParameterString("elev.dem", OtbParameters["elev.dem"])
    if "elev.geoid" in OtbParameters:
        siApp.SetParameterString("elev.geoid", OtbParameters["elev.geoid"])
    if "elev.default" in OtbParameters:
        siApp.SetParameterString("elev.default", OtbParameters["elev.default"])
    if "lms" in OtbParameters:
        siApp.SetParameterString("lms", OtbParameters["lms"])
    if "fv" in OtbParameters:
        siApp.SetParameterString("fv", OtbParameters["fv"])
    if "elev.dem" in OtbParameters:
        siApp.SetParameterString("elev.dem", OtbParameters["elev.dem"])
    if "out" in OtbParameters:
        siApp.SetParameterString("out", OtbParameters["out"])
    if "mode" in OtbParameters:
        siApp.SetParameterString("mode", OtbParameters["mode"])
    if "interpolator" in OtbParameters:
        siApp.SetParameterString("interpolator", OtbParameters["interpolator"])
    if "interpolator.bco.radius" in OtbParameters:
        siApp.SetParameterString("interpolator.bco.radius",
                                 str(OtbParameters["interpolator.bco.radius"]))
    if "ram" in OtbParameters:
        siApp.SetParameterString("ram", str(OtbParameters["ram"]))
    if "pixType" in OtbParameters:
        siApp.SetParameterOutputImagePixelType("out", fut.commonPixTypeToOTB(OtbParameters["pixType"]))

    return siApp, inImg2


def CreateExtractROIApplication(OtbParameters):
    """
    IN:
    parameter consistency are not tested here (done in otb's applications)
    every value could be string

    in parameters could be string/OtbApplication/tuple of OtbApplications
    OtbParameters [dic] dictionnary with otb's parameter keys
                        Example :
                        OtbParameters = {"in":"/image.tif",
                                        pixType:"uint8","out":"/out.tif"}
    OUT :
    erApp [otb object ready to Execute]
    """
    erApp = otb.Registry.CreateApplication("ExtractROI")
    if erApp is None:
        raise Exception("Not possible to create 'ExtractROI' application, \
                        check if OTB is well configured / installed")

    if not "in" in OtbParameters:
        raise Exception("'in' parameter not found")

    inImg = OtbParameters["in"]

    if isinstance(inImg, str):
        erApp.SetParameterString("in", inImg)
    elif isinstance(inImg, otb.Application):
        inOutParam = getInputParameterOutput(inImg)
        erApp.SetParameterInputImage("in", inImg.GetParameterOutputImage(inOutParam))
    elif isinstance(inImg, tuple):
        erApp.SetParameterInputImage("in", inImg[0].GetParameterOutputImage(getInputParameterOutput(inImg[0])))
    else:
        raise Exception("input image not recognize")

    if "out" in OtbParameters:
        erApp.SetParameterString("out", str(OtbParameters["out"]))
    if "ram" in OtbParameters:
        erApp.SetParameterString("ram", str(OtbParameters["ram"]))
    if "mode" in OtbParameters:
        erApp.SetParameterString("mode", str(OtbParameters["mode"]))
    if "mode.fit.ref" in OtbParameters:
        erApp.SetParameterString("mode.fit.ref",
                                 str(OtbParameters["mode.fit.ref"]))
    if "mode.fit.elev.dem" in OtbParameters:
        erApp.SetParameterString("mode.fit.elev.dem",
                                 str(OtbParameters["mode.fit.elev.dem"]))
    if "mode.fit.elev.geoid" in OtbParameters:
        erApp.SetParameterString("mode.fit.elev.geoid",
                                 str(OtbParameters["mode.fit.elev.geoid"]))
    if "mode.fit.elev.default" in OtbParameters:
        erApp.SetParameterString("mode.fit.elev.default",
                                 str(OtbParameters["mode.fit.elev.default"]))
    if "startx" in OtbParameters:
        erApp.SetParameterString("startx", str(OtbParameters["startx"]))
    if "starty" in OtbParameters:
        erApp.SetParameterString("starty", str(OtbParameters["starty"]))
    if "sizex" in OtbParameters:
        erApp.SetParameterString("sizex", str(OtbParameters["sizex"]))
    if "sizey" in OtbParameters:
        erApp.SetParameterString("sizey", str(OtbParameters["sizey"]))
    if "cl" in OtbParameters:
        if not isinstance(OtbParameters["cl"], list):
            raise Exception("cl parameter must be a list of strings")
        erApp.SetParameterStringList("cl", OtbParameters["cl"])
    if "pixType" in OtbParameters:
        erApp.SetParameterOutputImagePixelType("out",
                                               fut.commonPixTypeToOTB(OtbParameters["pixType"]))
    return erApp


def CreateRasterizationApplication(OtbParameters):
    """
    IN:
    parameter consistency are not tested here (done in otb's applications)
    every value could be string

    in parameters should be string
    OtbParameters [dic] dictionnary with otb's parameter keys
                        Example :
                        OtbParameters = {"in":"/image.tif",
                                        pixType:"uint8","out":"/out.tif"}
    OUT :
    rasterApp [otb object ready to Execute]
    """
    rasterApp = otb.Registry.CreateApplication("Rasterization")
    if rasterApp is None:
        raise Exception("Not possible to create 'Rasterization' application, \
                         check if OTB is well configured / installed")
    #Mandatory
    if not "in" in OtbParameters:
        raise Exception("'in' parameter not found")

    rasterApp.SetParameterString("in", OtbParameters["in"])

    if "out" in OtbParameters:
        rasterApp.SetParameterString("out", OtbParameters["out"])
    if "im" in OtbParameters:
        rasterApp.SetParameterString("im", OtbParameters["im"])
    if "szx" in OtbParameters:
        rasterApp.SetParameterString("szx", str(OtbParameters["szx"]))
    if "szy" in OtbParameters:
        rasterApp.SetParameterString("szy", str(OtbParameters["szy"]))
    if "epsg" in OtbParameters:
        rasterApp.SetParameterString("epsg", str(OtbParameters["epsg"]))
    if "orx" in OtbParameters:
        rasterApp.SetParameterString("orx", str(OtbParameters["orx"]))
    if "ory" in OtbParameters:
        rasterApp.SetParameterString("ory", str(OtbParameters["ory"]))
    if "spx" in OtbParameters:
        rasterApp.SetParameterString("spx", str(OtbParameters["spx"]))
    if "spy" in OtbParameters:
        rasterApp.SetParameterString("spy", str(OtbParameters["spy"]))
    if "background" in OtbParameters:
        rasterApp.SetParameterString("background", str(OtbParameters["background"]))
    if "mode" in OtbParameters:
        rasterApp.SetParameterString("mode", OtbParameters["mode"])
    if "mode.binary.foreground" in OtbParameters:
        rasterApp.SetParameterString("mode.binary.foreground", OtbParameters["mode.binary.foreground"])
    if "mode.attribute.field" in OtbParameters:
        rasterApp.SetParameterString("mode.attribute.field", OtbParameters["mode.attribute.field"])
    if "ram" in OtbParameters:
        rasterApp.SetParameterString("ram", str(OtbParameters["ram"]))
    if "pixType" in OtbParameters:
        rasterApp.SetParameterOutputImagePixelType("out", fut.commonPixTypeToOTB(OtbParameters["pixType"]))

    return rasterApp


def computeUserFeatures(stack, Dates, nbComponent, expressions):
    """
    usage : from a multibands/multitemporal stack of image, compute features
            define by user into configuration file at field 'additionalFeatures'

    IN

    stack [string/otbApplications] : stack of images
    Dates [int] : dates in stack
    nbComponent [int] : number of components by dates
    expressions [string] : user feature

    OUT
    UserFeatures [otbApplication] : otb appli, ready to Execute()
    userFeatureDate : dependance
    stack : dependance
    """
    
    def transformExprToListString(expr):
        """
        Example :
        expr = "(b1+b2)/(b3+b10+b1)"
        print transformExprToListString(expr)
        >> ['(', 'b1', '+', 'b2', ')', '/', '(', 'b3', '+', 'b10', '+', 'b1', ')']
        """
        container = []
        cpt = 0
        while cpt < len(expr):
            currentChar = expr[cpt]
            if currentChar != "b":
                container.append(currentChar)
            else:
                stringDigit = "b"
                for j in range(cpt + 1, len(expr)):
                    try:
                        digit = int(expr[j])
                        cpt += 1
                        stringDigit += expr[j]
                        if cpt == len(expr) - 1:
                            container.append(stringDigit)
                    except:
                        container.append(stringDigit)
                        break
            cpt += 1
        return container

    def checkBands(allBands, nbComp):
        """
        usage : check coherence between allBands in expression and number of component

        IN :
        allBands [set of all bands requested for expression] : example set(['b1', 'b2'])
        nbComp [int] : number of possible bands

        OUT
        ok [bool]
        """
        integerBands = [int(currentBand.split("b")[-1]) for currentBand in allBands]
        return bool(max(integerBands) <= nbComp)

    def computeExpressionDates(expr, nbDate, nbComp):
        """
        from an "bandMath like" expression return bandMath expressions to each dates :

        IN :
        expr [string] : bandMath - like expression
        nbDate [int] : number of dates (in a raster stack)
        nbComp [int] : number of components by dates

        OUT :
        allExpression [list of strings] : bandMath expression by dates

        Example:
        nbDate = 3
        nbComp = 10
        expr = "(b1+b2)/(b3+b10+b1)"
        print computeExpressionDates(expr,nbDate,nbComp)
        >> ['(im1b1+im1b2)/(im1b3+im1b10+im1b1)', '(im1b11+im1b12)/(im1b13+im1b20+im1b11)', '(im1b21+im1b22)/(im1b23+im1b30+im1b21)']
        """
        allBands = set([currentDec for currentDec in re.findall(r'[b]\d+', expr)])
        expressionValid = checkBands(allBands, nbComp)
        if not expressionValid:
            raise Exception("User features expression : '" + expr +
                            "' is not consistent with \
                            sensor's component number : " + str(nbComp))
        expression = transformExprToListString(expr)
        allExpression = []
        for date in range(nbDate):
            expressionDate = [currentChar for currentChar in expression]
            for currentBand in allBands:
                indices = list(np.where(np.array(expression) == currentBand)[0])
                if not indices:
                    raise Exception("Problem in parsing expression : band " + currentBand + " not recognize")
                for ind in indices:
                    bandNumber = expressionDate[ind]
                    bandDate = int(bandNumber.split("b")[-1]) + nbComp * date
                    expressionDate[ind] = "b" + str(bandDate)
            allExpression.append(("".join(expressionDate)).replace("b", "im1b"))

        return allExpression

    nbDates = len(Dates)
    fields = ["USER_Features_" + str(cpt + 1) + "_" + date for cpt in xrange(nbDates) for date in Dates]
    expressionDate = [computeExpressionDates(currentExpression, nbDates, nbComponent) for currentExpression in expressions]
    flatExprDate = [currentExp for currentDate in expressionDate for currentExp in currentDate]

    userFeatureDate = []
    for expression in flatExprDate:
        bandMathApp = CreateBandMathApplication({"il": stack,
                                                 "exp": expression,
                                                 "ram": '2000',
                                                 "pixType": "int16",
                                                 "out": "None"})
        bandMathApp.Execute()
        userFeatureDate.append(bandMathApp)
    UserFeatures = CreateConcatenateImagesApplication({"il": userFeatureDate,
                                                       "ram": '2000',
                                                       "pixType": "int16",
                                                       "out": ""})

    return UserFeatures, fields, userFeatureDate, stack


def gapFilling(cfg, tile, wMode, featuresPath=None, workingDirectory=None,
               testMode=False, testSensorData=None, enable_Copy=False,logger=logger):

    """
    usage : from configuration file, compute gapFilling by sensors to current
            tile

    IN
    cfg [Config object] :
    tile [string] : current tile to compute
    wMode [bool] : write temporary file ?
    featuresPath [string] : features's path
    workingDirectory [string] : path where tmp files will be written
    testMode [bool] : enable test mode
    testSensorData [string] : path to sensor's data -> use if test mode == True

    OUT
    AllgapFill [list of otbApplications] : gapfilling by sensors
    AllRefl [list of otbApplications] : stack of reflectance before gapfilling
    AllMask [list of otbApplications] : input gapFilling masks (by sensors)
    datesInterp [string] : path to interpolation dates
    realDates [string] : path to real sensors date
    dep [list of otbApplication] : dependances
    """

    dep = []
    pathConf = cfg.pathConf

    if fut.onlySAR(cfg):
        return [], [], [], [], [], []
    outFeatures = cfg.getParam('GlobChain', 'features')
    userFeatPath = cfg.getParam('chain', 'userFeatPath')
    if userFeatPath == "None":
        userFeatPath = None
    extractBands = cfg.getParam('iota2FeatureExtraction', 'extractBands')
    if extractBands == False:
        extractBands = None

    ipathL5 = cfg.getParam('chain', 'L5Path')
    if ipathL5 == "None":
        ipathL5 = None
    ipathL8 = cfg.getParam('chain', 'L8Path')
    if ipathL8 == "None":
        ipathL8 = None
    ipathS2 = cfg.getParam('chain', 'S2Path')
    if ipathS2 == "None":
        ipathS2 = None
    autoDate = cfg.getParam('GlobChain', 'autoDate')

    tiles = (cfg.getParam('chain', 'listTile')).split()

    if testMode:
        ipathL8 = testSensorData
    dateB_L5 = dateE_L5 = dateB_L8 = dateE_L8 = dateB_S2 = dateE_S2 = None
    if ipathL5:
        dateB_L5, dateE_L5 = fut.getDateL5(ipathL5, tiles)
    if not autoDate:
        dateB_L5 = cfg.getParam('Landsat5', 'startDate')
        dateE_L5 = cfg.getParam('Landsat5', 'endDate')
    if ipathL8:
        dateB_L8, dateE_L8 = fut.getDateL8(ipathL8, tiles)
        if not autoDate:
            dateB_L8 = cfg.getParam('Landsat8', 'startDate')
            dateE_L8 = cfg.getParam('Landsat8', 'endDate')
    if ipathS2:
        dateB_S2, dateE_S2 = fut.getDateS2(ipathS2, tiles)
        if not autoDate:
            dateB_S2 = cfg.getParam('Sentinel_2', 'startDate')
            dateE_S2 = cfg.getParam('Sentinel_2', 'endDate')

    S2 = Sensors.Sentinel_2(str(ipathS2), Opath("", create=False), pathConf, "", createFolder=None)
    L8 = Sensors.Landsat8(str(ipathL8), Opath("", create=False), pathConf, "", createFolder=None)
    L5 = Sensors.Landsat5(str(ipathL5), Opath("", create=False), pathConf, "", createFolder=None)
    SensorsList = [S2, L8, L5]

    import prepareStack
    AllRefl, AllMask, datesInterp, realDates, commonMask = prepareStack.generateStack(tile, cfg,
                                                                                      featuresPath, wMode,
                                                                                      workingDirectory,
                                                                                      testMode, testSensorData, enable_Copy)


    AllgapFill = []
    reflectanceOutput = [currentRefl.GetParameterValue("out") for currentRefl in AllRefl]
    masksOutput = [currentMask[0].GetParameterValue("out") for currentMask in AllMask]
    datesInterpOutput = [currentDateInterp for currentDateInterp in datesInterp]
    datesRealOutput = [currentDateReal for currentDateReal in realDates]

    logger.info("****** gapFilling to sample script ******")
    logger.info("Reflectances used  : " + " ".join(reflectanceOutput))
    logger.info("masks used : " + " ".join(masksOutput))
    logger.info("interpolation dates : " + " ".join(datesInterpOutput))
    logger.info("real dates : " + " ".join(datesRealOutput))
    logger.info("*****************************************")

    concatSensors = otb.Registry.CreateApplication("ConcatenateImages")
    for refl, mask, currentDatesInterp, currentRealDates in zip(AllRefl, AllMask, datesInterp, realDates):
        if wMode:
            refl.ExecuteAndWriteOutput()
            mask[0].ExecuteAndWriteOutput()
        else:
            refl.Execute()
            mask[0].Execute()

        currentSensor = fut.getCurrentSensor(SensorsList, refl.GetParameterValue("out"))
        reflDirectory, reflName = os.path.split(refl.GetParameterValue("out"))
        outGapFilling = reflDirectory + "/" + reflName.replace(".tif", "_GAP.tif")
        outFeatures = outGapFilling.replace(".tif", "_Features.tif")

        nbDate = fut.getNbDateInTile(currentRealDates)
        gapFill = otb.Registry.CreateApplication("ImageTimeSeriesGapFilling")
        comp = len(currentSensor.bands['BANDS'])

        gapFill.SetParameterInputImage("mask", mask[0].GetParameterOutputImage("out"))
        gapFill.SetParameterString("it", "linear")
        gapFill.SetParameterString("id", currentRealDates)
        gapFill.SetParameterString("od", currentDatesInterp)
        gapFill.SetParameterString("out", outGapFilling)
        gapFill.SetParameterOutputImagePixelType("out", fut.commonPixTypeToOTB('int16'))

        if extractBands:
            bandsToKeep = [bandNumber for bandName, bandNumber in currentSensor.keepBands.items()]
            extract = fut.ExtractInterestBands(refl, nbDate, bandsToKeep,
                                               comp, ram=10000)
            dep.append(extract)
            comp = len(bandsToKeep)
            gapFill.SetParameterInputImage("in", extract.GetParameterOutputImage("out"))

        else:
            gapFill.SetParameterInputImage("in", refl.GetParameterOutputImage("out"))
        gapFill.SetParameterString("comp", str(comp))
        AllgapFill.append(gapFill)

    return AllgapFill, AllRefl, AllMask, datesInterp, realDates, dep


def writeInterpolateDateFile(datesList, outputFolder, timeRes, mode):
    """
    usage : write interpolation date file for SAR sensor using all available dates

    IN
    datesList [list of string] : all available dates
    outputFolder [string] : output interpolation dates folder path
    timeRes [int] : temporal resolution
    mode [string] : sensor mode. Ex 'S1aDES'

    OUT
    outputFile [string] : output path
    """
    outputFile = outputFolder + "/" + mode + "_interpolationDates.txt"

    minDatesInterpol = [currentTileDate[0] for currentTileDate in datesList]
    maxDatesInterpol = [currentTileDate[-1] for currentTileDate in datesList]

    miniInterpol = minDatesInterpol[-1]
    maxiInterpol = maxDatesInterpol[0]

    if not os.path.exists(outputFile):
        outInterDates = "\n".join([str(interpolDate).replace("-", "") for interpolDate in fut.dateInterval(str(miniInterpol), str(maxiInterpol), timeRes)])
        if len(datesList[0]) == 1:
            outInterDates = str(datesList[0][0])
        with open(outputFile, "w") as fileInterp:
            fileInterp.write(outInterDates)
    return outputFile


def writeInputDateFile(allTileMasks, outputFolder, mode):
    """
    usage : write real date file for SAR sensor using all available dates

    IN
    allTileMasks [list of string] : path to all masks which contains dates in
                                    their names
    outputFolder [string] : path to output folder
    mode [string] : sensor mode. Ex 'S1aDES'

    OUT
    outputFile [string] : output path
    """
    outputFile = outputFolder + "/" + mode + "_inputDates.txt"

    if mode == "S1aDES":
        masks = [CCallMasks for CCallMasks in allTileMasks if CCallMasks.split("/")[-1].split("_")[3] == "DES" and CCallMasks.split("/")[-1].split("_")[0] == "s1a"]
    elif mode == "S1aASC":
        masks = [CCallMasks for CCallMasks in allTileMasks if CCallMasks.split("/")[-1].split("_")[3] == "ASC" and CCallMasks.split("/")[-1].split("_")[0] == "s1a"]
    elif mode == "S1bDES":
        masks = [CCallMasks for CCallMasks in allTileMasks if CCallMasks.split("/")[-1].split("_")[3] == "DES" and CCallMasks.split("/")[-1].split("_")[0] == "s1b"]
    elif mode == "S1bASC":
        masks = [CCallMasks for CCallMasks in allTileMasks if CCallMasks.split("/")[-1].split("_")[3] == "ASC" and CCallMasks.split("/")[-1].split("_")[0] == "s1b"]
    else:
        raise Exception("mode not recognize")

    currentTileDate = sorted([int(cTileDate.split("/")[-1].split("_")[4].split("t")[0]) for cTileDate in masks])
    currentTileDate_s = [str(CcurrentTileDate) for CcurrentTileDate in currentTileDate]
    if not os.path.exists(outputFile):
        outInputDates = "\n".join(currentTileDate_s)
        with open(outputFile, "w") as fileDate:
            fileDate.write(outInputDates)

    return outputFile


def sortS1aS1bMasks(masksList):
    """
    usage : sort masks by mode and sensors

    IN
    masksList [list of strings] : names must contains sensor name (s1a or s1b)
                                  and sensor mode (DES or ASC)
    OUT
    sortedMasks [list of list] : masks sorted as : s1aDES,s1aASC,s1bDES,s1bASC
    """
    from S1FilteringProcessor import getDatesInOtbOutputName
    #care about order
    sortedMasks = []
    S1aDES = [CMask for CMask in masksList if CMask.split("/")[-1].split("_")[3] == "DES" and CMask.split("/")[-1].split("_")[0] == "s1a"]
    S1aASC = [CMask for CMask in masksList if CMask.split("/")[-1].split("_")[3] == "ASC" and CMask.split("/")[-1].split("_")[0] == "s1a"]
    S1bDES = [CMask for CMask in masksList if CMask.split("/")[-1].split("_")[3] == "DES" and CMask.split("/")[-1].split("_")[0] == "s1b"]
    S1bASC = [CMask for CMask in masksList if CMask.split("/")[-1].split("_")[3] == "ASC" and CMask.split("/")[-1].split("_")[0] == "s1b"]

    if S1aDES:
        sortedMasks.append(sorted(S1aDES, key=getDatesInOtbOutputName))
    if S1aASC:
        sortedMasks.append(sorted(S1aASC, key=getDatesInOtbOutputName))
    if S1bDES:
        sortedMasks.append(sorted(S1bDES, key=getDatesInOtbOutputName))
    if S1bASC:
        sortedMasks.append(sorted(S1bASC, key=getDatesInOtbOutputName))

    return sortedMasks


def getSARstack(sarConfig, tileName, allTiles):
    """
    usage : for tile 'tileName', using 'sarConfig' compute calibration then
            orthorectification and despeckle filtering
    IN:
    sarConfig [string] : path to SAR configuration file
    tileName [string] : tile name to compute. Ex : T31TCJ
    allTiles [list of strings] : all tiles needed to the current run

    OUT:
    outAllFiltered [list of otbApplications] : all SAR data filtered for current
                                               tile sorted as : s1aDES,s1aASC,
                                               s1bDES,s1bASC
    outAllMasks [list of strings] : SAR masks sorted as :
                                    s1aDES,s1aASC,s1bDES,s1bASC
    outAllDependence [list of otbApplications] : dependances
    interpDateFiles [list of strings] : list of interpolations date files
    inputDateFiles [list of strings] : list of real date files
    """
    import S1Processor as s1p
    import ConfigParser

    config = ConfigParser.ConfigParser()
    config.read(sarConfig)
    outputDirectory = config.get('Paths', 'Output')
    outputDateFolder = outputDirectory + "/" + tileName[1:]
    tr = config.get('Processing', 'TemporalResolution')

    sarTileDateS1aDM = []
    sarTileDateS1aAM = []
    sarTileDateS1bDM = []
    sarTileDateS1bAM = []

    interpDateFiles = []
    inputDateFiles = []

    allFiltered, allDependence, allMasks, allTile = s1p.S1Processor(sarConfig)
    for CallFiltered, CallDependence, CallMasks, CallTile in zip(allFiltered, allDependence, allMasks, allTile):
        if CallTile in tileName:
            outAllFiltered = [CCallFiltered for CCallFiltered in CallFiltered]
            outAllMasks = sortS1aS1bMasks(CallMasks)
            outAllDependence = CallDependence

        if "T" + CallTile in allTiles:

            #get S1a DES masks
            s1aDMasks = [CCallMasks for CCallMasks in CallMasks if CCallMasks.split("/")[-1].split("_")[3] == "DES" and CCallMasks.split("/")[-1].split("_")[0] == "s1a"]
            #get S1a ASC masks
            s1aAMasks = [CCallMasks for CCallMasks in CallMasks if CCallMasks.split("/")[-1].split("_")[3] == "ASC" and CCallMasks.split("/")[-1].split("_")[0] == "s1a"]
            #get S1b DES masks
            s1bDMasks = [CCallMasks for CCallMasks in CallMasks if CCallMasks.split("/")[-1].split("_")[3] == "DES" and CCallMasks.split("/")[-1].split("_")[0] == "s1b"]
            #get S1b ASC masks
            s1bAMasks = [CCallMasks for CCallMasks in CallMasks if CCallMasks.split("/")[-1].split("_")[3] == "ASC" and CCallMasks.split("/")[-1].split("_")[0] == "s1b"]

            if s1aDMasks:
                sarTileDateS1aDM.append(sorted([int(Cs1aDMasks.split("/")[-1].split("_")[4].split("t")[0]) for Cs1aDMasks in s1aDMasks]))
            if s1aAMasks:
                sarTileDateS1aAM.append(sorted([int(Cs1aAMasks.split("/")[-1].split("_")[4].split("t")[0]) for Cs1aAMasks in s1aAMasks]))
            if s1bDMasks:
                sarTileDateS1bDM.append(sorted([int(Cs1bDMasks.split("/")[-1].split("_")[4].split("t")[0]) for Cs1bDMasks in s1bDMasks]))
            if s1bAMasks:
                sarTileDateS1bAM.append(sorted([int(Cs1bDMasks.split("/")[-1].split("_")[4].split("t")[0]) for Cs1bDMasks in s1bAMasks]))

    #Care about list order : must be the same as construct in S1FilteringProcessor.py
    #-> S1aDES,S1aASC,S1bDES and then S1bASC
    tileMasks = [CCoutAllMasks for CoutAllMasks in outAllMasks for CCoutAllMasks in CoutAllMasks]
    if sarTileDateS1aDM:
        interpS1aD = writeInterpolateDateFile(sarTileDateS1aDM,
                                              outputDateFolder,
                                              tr, mode="S1aDES")
        inputS1aD = writeInputDateFile(tileMasks, outputDateFolder,
                                       mode="S1aDES")
        interpDateFiles.append(interpS1aD)
        inputDateFiles.append(inputS1aD)
    if sarTileDateS1aAM:
        interpS1aA = writeInterpolateDateFile(sarTileDateS1aAM,
                                              outputDateFolder,
                                              tr, mode="S1aASC")
        inputS1aA = writeInputDateFile(tileMasks, outputDateFolder,
                                       mode="S1aASC")
        interpDateFiles.append(interpS1aA)
        inputDateFiles.append(inputS1aA)
    if sarTileDateS1bDM:
        interpS1bD = writeInterpolateDateFile(sarTileDateS1bDM,
                                              outputDateFolder,
                                              tr, mode="S1bDES")
        inputS1bD = writeInputDateFile(tileMasks, outputDateFolder,
                                       mode="S1bDES")
        interpDateFiles.append(interpS1bD)
        inputDateFiles.append(inputS1bD)
    if sarTileDateS1bAM:
        interpS1bA = writeInterpolateDateFile(sarTileDateS1bAM,
                                              outputDateFolder,
                                              tr, mode="S1bASC")
        inputS1bA = writeInputDateFile(tileMasks, outputDateFolder,
                                       mode="S1bASC")
        interpDateFiles.append(interpS1bA)
        inputDateFiles.append(inputS1bA)

    return outAllFiltered, outAllMasks, outAllDependence, interpDateFiles, inputDateFiles


def computeSARfeatures(sarConfig, tileToCompute, allTiles, logger=logger):
    """
    IN:
    sarConfig [string] : path to SAR configuration file
    tileToCompute [string] : tile name to compute. Ex : T31TCJ
    allTiles [list of string] : all tiles needed for the run
                                used to compute interpolation dates (gapFilling)
    OUT:
    stackSARFeatures [otb object ready to Execute]
    dep
    fields_names [list of strings] : labels for each feature
    """
    SARstack, SARmasks, SARdep, interpDateFiles, inputDateFiles = getSARstack(sarConfig,
                                                                              tileToCompute,
                                                                              allTiles)
    #number of components per dates VV + VH
    SARcomp = 2
    SARFeatures = []
    Dep = []
    fields_names = []
    features = ["VV","VH"]
    for (currentSarStack, a, b, c, d), CSARmasks, interpDate, inputDate in zip(SARstack, SARmasks, interpDateFiles, inputDateFiles):
        currentSarStack.Execute()
        outName = currentSarStack.GetParameterValue(getInputParameterOutput(currentSarStack))
        if not isinstance(CSARmasks, list):
            CSARmasks = [CSARmasks]
        stackMask = CreateConcatenateImagesApplication({"il": CSARmasks,
                                                        "ram": '5000',
                                                        "pixType": "uint8",
                                                        "out": outName.replace(".tif", "_MASKSTACK.tif")})
        stackMask.Execute()
        Dep.append(stackMask)
        logger.info("SAR gapFilling parameters")
        logger.info("inpute dates file %s"%(inputDate))
        logger.info("output dates file %s"%(interpDate))

        SARgapFill = otb.Registry.CreateApplication("ImageTimeSeriesGapFilling")
        SARgapFill.SetParameterString("it", "linear")
        SARgapFill.SetParameterString("id", inputDate)
        SARgapFill.SetParameterString("od", interpDate)
        SARgapFill.SetParameterString("comp", str(SARcomp))
        SARgapFill.SetParameterInputImage("in", currentSarStack.GetParameterOutputImage(getInputParameterOutput(currentSarStack)))
        SARgapFill.SetParameterOutputImagePixelType("out", fut.commonPixTypeToOTB('float'))
        SARgapFill.SetParameterInputImage("mask", stackMask.GetParameterOutputImage(getInputParameterOutput(stackMask)))

        outName = outName.replace(".tif", "_GAPFIL.tif")
        SARgapFill.SetParameterString("out", outName)
        SARgapFill.Execute()

        Dep.append(SARgapFill)

        SARFeatures.append(SARgapFill)
        SAR_dates = fut.getNbDateInTile(interpDate,display=False, raw_dates=True)
        SAR_mode = os.path.split(outName)[-1].split("_")[1]
        
        for date in SAR_dates:
            for feature in features:
                fields_names.append(SAR_mode + "_" + feature + "_"+ date)
        
    stackSARFeatures = CreateConcatenateImagesApplication({"il": SARFeatures,
                                                           "ram": '5000',
                                                           "pixType": "float",
                                                           "out": "/work/OT/theia/oso/TMP/TMP2/" + tileToCompute + "_STACKGAP.tif"})

    return stackSARFeatures, fields_names, [SARdep, stackMask, SARstack, Dep]


def computeFeatures(cfg, nbDates, tile, stack_dates, AllRefl, AllMask,
                    datesFile_sensor, realDates, logger=logger):
    """
    IN:
    cfg [Config Object]
    nbDates [list of int] : number of component by stack (ApplicationList[0])
    tile [string] : tile to compute ex 'T31TCJ'
    stack_dates [otbObject] : stack to extract features
    AllRefl [list of OTB object] : reflectance by sensors
    AllMask [list of OTB object] : masks by sensors
    datesFile_sensor [list of strings] : path to dates files by sensors
                                         according to stack_dates
    realDates [list of strings] : path to dates before gapFilling
    logger [logging object] : logger

    OUT:
    outputFeatures  [otb object ready to Execute]
    ApplicationList,userDateFeatures,a,b,AllFeatures,SARdep are dependances

    """

    ApplicationList = [stack_dates, AllRefl, AllMask,datesFile_sensor, realDates]
    def fields_names(sensor, datesFile, iota2FeatExtApp, ext_Bands_Flag=None):

        from collections import OrderedDict
        sens_name = sensor.name
        sens_dates = fut.getNbDateInTile(datesFile,
                                         display=False, raw_dates=True)
        #sort by bands number value
        sens_bands_names = [bandName for bandName, bandOrder in sorted(sensor.bands["BANDS"].iteritems(), key=lambda (k,v): (v,k))]

        if ext_Bands_Flag:
            sens_bands_names = [bandName for bandName, bandNumber in currentSensor.keepBands.items()]

        if not iota2FeatExtApp.GetParameterValue("copyinput"):
            sens_bands_names = []

        features = ["NDVI", "NDWI", "Brightness"]
        
        relRef = iota2FeatExtApp.GetParameterValue("relrefl")
        keepDup = iota2FeatExtApp.GetParameterValue("keepduplicates")
        if relRef and not keepDup:
            features = ["NDWI", "Brightness"]
    
        out_fields = []
        for date in sens_dates:
            for band_name in sens_bands_names:
                out_fields.append(sens_name + "_" + band_name + "_" + date)
        for feature in features:
            for date in sens_dates:
                out_fields.append(sens_name + "_" + feature + "_" + date)

        return out_fields

    from config import Config
    pathConf = cfg.pathConf
    userFeatPath = cfg.getParam('chain', 'userFeatPath')

    fut.updatePyPath()

    if userFeatPath == "None":
        userFeatPath = None

    all_fields_sens = []
    useAddFeat = cfg.getParam('GlobChain', 'useAdditionalFeatures')
    extractBands = cfg.getParam('iota2FeatureExtraction', 'extractBands')
    #does not work in operational context (alway empty) -> but test pass...
    #featuresFlag = cfg.getParam('GlobChain', 'features')
    featuresFlag = Config(pathConf).GlobChain.features
    S1Data = cfg.getParam('chain', 'S1Path')
    if S1Data == "None":
        S1Data = None
    if not featuresFlag and userFeatPath is None and not S1Data:
        return ApplicationList

    S2 = Sensors.Sentinel_2(cfg.getParam('chain', 'S2Path'), Opath("", create=False), pathConf, "", createFolder=None)
    L8 = Sensors.Landsat8(cfg.getParam('chain', 'L8Path'), Opath("", create=False), pathConf, "", createFolder=None)
    L5 = Sensors.Landsat5(cfg.getParam('chain', 'L5Path'), Opath("", create=False), pathConf, "", createFolder=None)
    SensorsList = [S2, L8, L5]

    AllFeatures = []
    
    allTiles = (cfg.getParam('chain', 'listTile')).split()
    if S1Data:
        SARfeatures, SAR_fields, SARdep = computeSARfeatures(S1Data, tile, allTiles)
        AllFeatures.append(SARfeatures)
        all_fields_sens.append(SAR_fields)

    for gapFilling, dates, c_datesFile_sensor in zip(stack_dates, nbDates, datesFile_sensor):
        outFeatures = gapFilling.GetParameterValue("out")
        outFeatures = outFeatures.replace(".tif", "_Features.tif")
        featExtr = otb.Registry.CreateApplication("iota2FeatureExtraction")
        currentSensor = fut.getCurrentSensor(SensorsList, gapFilling.GetParameterValue("out"))
        
        comp = len(currentSensor.bands['BANDS'])
        logger.debug("Sensor name found : %s"%(currentSensor.name))
        logger.debug("number of bands for sensor %s : %s"%(currentSensor.name, comp))
        if extractBands:
            bandsToKeep = [bandNumber for bandName, bandNumber in currentSensor.keepBands.items()]
            comp = len(bandsToKeep)
            logger.debug("keepBands flag detected, number of bands to extract %s"%(comp))
        if useAddFeat:
            raw_dates = fut.getNbDateInTile(gapFilling.GetParameterValue("od"), display=False, raw_dates=True)
            userDateFeatures, fields_userFeat, a, b = computeUserFeatures(gapFilling, raw_dates, comp, currentSensor.addFeatures)
            userDateFeatures.Execute()
        else:
            userDateFeatures = a = b = None

        featExtr.SetParameterInputImage("in", gapFilling.GetParameterOutputImage("out"))
        featExtr.SetParameterString("comp", str(comp))
        red = str(currentSensor.red)
        nir = str(currentSensor.nir)
        swir = str(currentSensor.swir)

        featExtr.SetParameterString("red", red)
        featExtr.SetParameterString("nir", nir)
        featExtr.SetParameterString("swir", swir)
        featExtr.SetParameterString("out", outFeatures)
        featExtr.SetParameterOutputImagePixelType("out", fut.commonPixTypeToOTB('int16'))
        fut.iota2FeatureExtractionParameter(featExtr, cfg)
        if featuresFlag:
            logger.info("Add features compute from iota2FeatureExtraction")
            AllFeatures.append(featExtr)
        else:
            AllFeatures.append(gapFilling)
        if useAddFeat:
            AllFeatures.append(userDateFeatures)
            all_fields_sens.append(fields_userFeat)

        fields = fields_names(currentSensor, datesFile=c_datesFile_sensor,
                              iota2FeatExtApp=featExtr, ext_Bands_Flag=extractBands)

        all_fields_sens.append(fields)

    if userFeatPath:
        print "Add user features"
        userFeat_arbo = cfg.getParam('userFeat', 'arbo')
        userFeat_pattern = (cfg.getParam('userFeat', 'patterns')).split(",")
        userFeatures = fut.getUserFeatInTile(userFeatPath, tile, userFeat_arbo, userFeat_pattern)

        concatUserFeatures = CreateConcatenateImagesApplication({"il": userFeatures,
                                                                 "ram": '4000',
                                                                 "pixType": "int16",
                                                                 "out": ""})
        concatUserFeatures.Execute()
        AllFeatures.append(concatUserFeatures)
        all_fields_sens.append(userFeat_pattern)

    if len(AllFeatures) > 1:
        for currentFeat in AllFeatures:
            currentFeat.Execute()
        outFeatures = outFeatures.replace(".tif", "_USERFEAT.tif")
        outPixType = "int16"
        if S1Data:
            outPixType = "float"
        featuresConcatenation = CreateConcatenateImagesApplication({"il": AllFeatures,
                                                                    "ram": '4000',
                                                                    "pixType": outPixType,
                                                                    "out": outFeatures})
        outputFeatures = featuresConcatenation
    else:
        outputFeatures = AllFeatures[0]
    if "S1" in fut.sensorUserList(cfg) and len(fut.sensorUserList(cfg)) == 1:
        userDateFeatures = a = b = None
    elif "S1" not in fut.sensorUserList(cfg):
        SARdep = None
    all_fields_sensors = [feat_name for cFeat in all_fields_sens for feat_name in cFeat]

    sep = " "*63
    logger.debug("Features labels : %s"%(("\n" + sep).join(all_fields_sensors)))

    return outputFeatures, all_fields_sensors, ApplicationList, userDateFeatures, a, b, AllFeatures, SARdep
