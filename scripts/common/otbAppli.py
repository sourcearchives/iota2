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
import numpy as np
import os
import Sensors
from Utils import Opath
import otbApplication as otb
import fileUtils as fut
from config import Config
import ast


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
    sampleE [otb object ready to Execute]
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
    elif type(inputIm) == otb.Application:
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
    elif type(inputIm) == otb.Application:
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
    elif type(inputIm) == otb.Application:
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
    if not OtbParameters.has_key("in"):
        raise Exception("'in' parameter not found")
    if not OtbParameters.has_key("out"):
        raise Exception("'out' parameter not found")

    inputIm = OtbParameters["in"]
    if isinstance(inputIm,str): despeckle.SetParameterString("in",inputIm)
    elif isinstance(inputIm,tuple):
        inOutParam = getInputParameterOutput(inputIm[0])
        despeckle.SetParameterInputImage("in",inputIm[0].GetParameterOutputImage(inOutParam))
    elif type(inputIm)==otb.Application:
        inOutParam = getInputParameterOutput(inputIm)
        despeckle.SetParameterInputImage("in",inputIm.GetParameterOutputImage(inOutParam))
    else : raise Exception("input image not recognize")


    despeckle.SetParameterString("out",OtbParameters["out"])

    if OtbParameters.has_key("filter"):
        despeckle.SetParameterString("filter",OtbParameters["filter"])
    if OtbParameters.has_key("filter.lee.rad"):
        despeckle.SetParameterString("filter.lee.rad",str(OtbParameters["filter.lee.rad"]))
    if OtbParameters.has_key("filter.lee.nblooks"):
        despeckle.SetParameterString("filter.lee.nblooks",str(OtbParameters["filter.lee.nblooks"]))
    if OtbParameters.has_key("filter.frost.rad"):
        despeckle.SetParameterString("filter.frost.rad",str(OtbParameters["filter.frost.rad"]))
    if OtbParameters.has_key("filter.frost.deramp"):
        despeckle.SetParameterString("filter.frost.deramp",str(OtbParameters["filter.frost.deramp"]))
    if OtbParameters.has_key("filter.gammamap.rad"):
        despeckle.SetParameterString("filter.gammamap.rad",str(OtbParameters["filter.gammamap.rad"]))
    if OtbParameters.has_key("filter.gammamap.nblooks"):
        despeckle.SetParameterString("filter.gammamap.nblooks",str(OtbParameters["filter.gammamap.nblooks"]))
    if OtbParameters.has_key("filter.kuan.rad"):
        despeckle.SetParameterString("filter.kuan.rad",str(OtbParameters["filter.kuan.rad"]))
    if OtbParameters.has_key("filter.kuan.nblooks"):
        despeckle.SetParameterString("filter.kuan.nblooks",str(OtbParameters["filter.kuan.nblooks"]))
    if OtbParameters.has_key("ram"):
        despeckle.SetParameterString("ram",str(OtbParameters["ram"]))
    if OtbParameters.has_key("pixType"):
        despeckle.SetParameterOutputImagePixelType("out",fut.commonPixTypeToOTB(OtbParameters["pixType"]))

    return despeckle

def monoDateDespeckle(allOrtho,tile):

    fut.updatePyPath()
    from S1FilteringProcessor import getOrtho,getDatesInOtbOutputName

    s1aDESlist = sorted([currentOrtho for currentOrtho in getOrtho(allOrtho,"s1a(.*)"+tile+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
    s1aASClist = sorted([currentOrtho for currentOrtho in getOrtho(allOrtho,"s1a(.*)"+tile+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)
    s1bDESlist = sorted([currentOrtho for currentOrtho in getOrtho(allOrtho,"s1b(.*)"+tile+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
    s1bASClist = sorted([currentOrtho for currentOrtho in getOrtho(allOrtho,"s1b(.*)"+tile+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)

    despeckS1aDES = []
    despeckS1aASC = []
    despeckS1bDES = []
    despeckS1bASC = []

    if s1aDESlist :
        for cOrtho in s1aDESlist :
            cOrtho.Execute()
            inOutParam = getInputParameterOutput(cOrtho)
            despeckParam = {"in":cOrtho,"out":""}
            despeckle = CreateDespeckleApplication(despeckParam)
            despeckle.Execute()
            despeckS1aDES.append(despeckle)

    if s1aASClist :
        for cOrtho in s1aASClist :
            cOrtho.Execute()
            inOutParam = getInputParameterOutput(cOrtho)
            despeckParam = {"in":cOrtho,"out":""}
            despeckle = CreateDespeckleApplication(despeckParam)
            despeckle.Execute()
            despeckS1aASC.append(despeckle)

    if s1bDESlist :
        for cOrtho in s1bDESlist :
            cOrtho.Execute()
            inOutParam = getInputParameterOutput(cOrtho)
            despeckParam = {"in":cOrtho,"out":""}
            despeckle = CreateDespeckleApplication(despeckParam)
            despeckle.Execute()
            despeckS1bDES.append(despeckle)

    if s1bASClist :
        for cOrtho in s1bASClist :
            cOrtho.Execute()
            inOutParam = getInputParameterOutput(cOrtho)
            despeckParam = {"in":cOrtho,"out":""}
            despeckle = CreateDespeckleApplication(despeckParam)
            despeckle.Execute()
            despeckS1bASC.append(despeckle)

    SARfiltered = []
    concatS1ADES=concatS1AASC=concatS1BDES=concatS1BASC=None
    if despeckS1aDES :
        concatS1ADES = CreateConcatenateImagesApplication(imagesList=despeckS1aDES,\
                                                          ram='5000',pixType="float",\
                                                          output="")
        concatS1ADES.Execute()
        SARfiltered.append((concatS1ADES,despeckS1aDES,"","",""))

    if despeckS1aASC :
        concatS1AASC = CreateConcatenateImagesApplication(imagesList=despeckS1aASC,\
                                                          ram='2000',pixType="float",\
                                                          output="")
        concatS1AASC.Execute()
        SARfiltered.append((concatS1AASC,despeckS1aASC,"","",""))

    if despeckS1bDES :
        concatS1BDES = CreateConcatenateImagesApplication(imagesList=despeckS1bDES,\
                                                          ram='2000',pixType="float",\
                                                          output="")
        concatS1BDES.Execute()
        SARfiltered.append((concatS1BDES,despeckS1bDES,"","",""))

    if despeckS1bASC :
        concatS1BASC = CreateConcatenateImagesApplication(imagesList=despeckS1bASC,\
                                                          ram='2000',pixType="float",\
                                                          output="")
        concatS1BASC.Execute()
        SARfiltered.append((concatS1BASC,despeckS1bASC,"","",""))

    return SARfiltered

def CreateSarCalibration(inputIm,outputIm,pixelType="float",ram="2000",wMode=False):

    """
    IN:
    inputIm [string/otbObject]
    outputIm [string] : output path
    pixelType [string] : output pixel type, according to commonPixTypeToOTB
                         function in fileUtils
    ram [string] : pipe's size

    wMode unused

    OUT :
    calibration [otb object ready to Execute]
    """
    calibration = otb.Registry.CreateApplication("SARCalibration")
    calibration.SetParameterString("out",outputIm)
    calibration.SetParameterString("lut","gamma")
    calibration.SetParameterString("ram",str(ram))
    calibration.SetParameterOutputImagePixelType("out",fut.commonPixTypeToOTB(pixelType))
    if isinstance(inputIm,str): calibration.SetParameterString("in",inputIm)
    elif type(inputIm)==otb.Application:calibration.SetParameterInputImage("in",inputIm.GetParameterOutputImage("out"))
    else : raise Exception("input image not recognize")
    return calibration

def CreateOrthoRectification(inputImage,outputImage,ram,spx,spy,sx,sy,gridSpacing,\
                             utmZone,utmNorhhem,ulx,uly,dem,geoid):

    """
    IN :
    inputImage [string/otbObject]
    outputImage [string]
    ram [string/int] pipe's size
    spx [string/int] spacingx
    spy [string/int] spacingy
    sx [string/int] sizex
    sy [string/int] sizey
    gridSpacing [string/int] gridSpacing
    utmZone [string/int] utmZone
    utmNorhhem [string/int] utmNorhhem
    ulx [string/int] upper left x coordinate
    uly [string/int] upper left y coordinate
    dem [string] path to DEM
    geoid [string] path to geoid shape file

    OUT :
    ortho [otb object ready to Execute]
    """
    ortho = otb.Registry.CreateApplication("OrthoRectification")
    if isinstance(inputImage,str):ortho.SetParameterString("io.in",inputImage)
    elif type(inputImage)==otb.Application:ortho.SetParameterInputImage("io.in",inputImage.GetParameterOutputImage("out"))
    elif isinstance(inputImage,tuple):ortho.SetParameterInputImage("io.in",inputImage[0].GetParameterOutputImage("out"))
    else : raise Exception("input image not recognize")

    ortho.SetParameterString("opt.ram",str(ram))
    ortho.SetParameterString("io.out",outputImage+"?&writegeom=false")
    ortho.SetParameterString("outputs.spacingx",str(spx))
    ortho.SetParameterString("outputs.spacingy",str(spy))
    ortho.SetParameterString("outputs.sizex",str(sx))
    ortho.SetParameterString("outputs.sizey",str(sy))
    ortho.SetParameterString("opt.gridspacing",str(gridSpacing))

    ortho.SetParameterString("outputs.ulx",str(ulx))
    ortho.SetParameterString("outputs.uly",str(uly))
    ortho.SetParameterString("elev.dem",dem)
    ortho.SetParameterString("elev.geoid",geoid)

    ortho.SetParameterString("map","utm")
    ortho.SetParameterString("map.utm.zone",str(utmZone))
    ortho.SetParameterString("map.utm.northhem",str(utmNorhhem))

    return ortho,inputImage

def CreateMultitempFilteringFilter(inImg,outcore,winRad,enl,ram="2000",pixType="float",outputStack=None):
    """
    MultitempFilteringFilter is an External otb module
    git clone http://tully.ups-tlse.fr/vincenta/otb-for-biomass.git -b memChain

    IN:

    inImg [string/listOfString/listofOtbObject/listOfTupleOfOtbObject]
    outcore [string/otbObject] outcore path (application input)
    winRad [string/int] window radius
    enl [int] equivalent number of look
    ram [string/int] pipe's size
    pixType [string] : output pixel type, according to commonPixTypeToOTB
                       function in fileUtils
    outputStack [bool] output format stack / N images (application output)

    OUT:
    SARfilterF [otb object ready to Execute]
    inImg,outcore are dependances
    """
    SARfilterF = otb.Registry.CreateApplication("MultitempFilteringFilter")
    if not SARfilterF:
        raise Exception("MultitempFilteringFilter not available")
    if not inImg : raise Exception("no input images detected")

    if not isinstance(inImg,list):inImg=[inImg]
    if isinstance(inImg[0],str):SARfilterF.SetParameterStringList("inl",inImg)
    elif type(inImg[0])==otb.Application:
        for currentObj in inImg:
            outparameterName = getInputParameterOutput(currentObj)
            SARfilterF.AddImageToParameterInputImageList("inl",currentObj.GetParameterOutputImage(outparameterName))
    elif isinstance(inImg[0],tuple):
        for currentObj in unPackFirst(inImg):
            outparameterName = getInputParameterOutput(currentObj)
            SARfilterF.AddImageToParameterInputImageList("inl",currentObj.GetParameterOutputImage(outparameterName))
    else :
        raise Exception(type(inImg[0])+" not available to CreateBandMathApplication function")
    SARfilterF.SetParameterString("wr",str(winRad))

    if isinstance(outcore,str):
        SARfilterF.SetParameterString("oc",outcore)
    else :
        SARfilterF.SetParameterInputImage("oc",outcore.GetParameterOutputImage("oc"))

    SARfilterF.SetParameterString("enl",enl)
    if outputStack:
        SARfilterF.SetParameterString("outputstack",outputStack)
    SARfilterF.SetParameterString("ram",str(ram))
    SARfilterF.SetParameterOutputImagePixelType("enl",fut.commonPixTypeToOTB(pixType))
    return SARfilterF,inImg,outcore

def CreateMultitempFilteringOutcore(inImg,outImg,winRad,ram="2000",pixType="float"):
    """
    MultitempFilteringOutcore is an External otb module
    git clone http://tully.ups-tlse.fr/vincenta/otb-for-biomass.git -b memChain

    IN:

    inImg [string/listOfString/listofOtbObject/listOfTupleOfOtbObject]
    outImg [string] output outcore path
    winRad [string/int] window radius
    ram [string/int] pipe's size
    pixType [string] : output pixel type, according to commonPixTypeToOTB
                       function in fileUtils
    OUT:
    SARfilter [otb object ready to Execute]
    """
    SARfilter = otb.Registry.CreateApplication("MultitempFilteringOutcore")
    if not SARfilter:
        raise Exception("MultitempFilteringOutcore not available")
    if not inImg : raise Exception("no input images detected")

    if not isinstance(inImg,list):inImg=[inImg]
    if isinstance(inImg[0],str):SARfilter.SetParameterStringList("inl",inImg)
    elif type(inImg[0])==otb.Application:
        for currentObj in inImg:
            outparameterName = getInputParameterOutput(currentObj)
            SARfilter.AddImageToParameterInputImageList("inl",currentObj.GetParameterOutputImage(outparameterName))
    elif isinstance(inImg[0],tuple):
        for currentObj in unPackFirst(inImg):
            outparameterName = getInputParameterOutput(currentObj)
            SARfilter.AddImageToParameterInputImageList("inl",currentObj.GetParameterOutputImage(outparameterName))
    else :
        raise Exception(type(inImg[0])+" not available to CreateBandMathApplication function")
    SARfilter.SetParameterString("wr",str(winRad))
    SARfilter.SetParameterString("oc",outImg)
    SARfilter.SetParameterString("ram",str(ram))
    SARfilter.SetParameterOutputImagePixelType("oc",fut.commonPixTypeToOTB(pixType))
    return SARfilter

def CreateBinaryMorphologicalOperation(inImg, ram="2000", pixType='uint8',\
                                       filter="opening", ballxradius = '5',\
                                       ballyradius = '5', outImg = ""):
    """
    IN

    inImg [string/OtbObject/TupleOfOtbObject]
    ram [string/int] pipe's size
    pixType [string] : output pixel type, according to commonPixTypeToOTB
                       function in fileUtils
    filter [string] filter type dilate/erode/opening/closing
    ballxradius [string/int]
    ballyradius [string/int]
    outImg [string] output path

    OUT
    morphoMath [otb object ready to Execute]
    """
    morphoMath = otb.Registry.CreateApplication("BinaryMorphologicalOperation")
    if morphoMath is None:
        raise Exception("Not possible to create 'Binary Morphological Operation' application, check if OTB is well configured / installed")

    if isinstance(inImg,str):morphoMath.SetParameterString("in", inImg)
    elif type(inImg)==otb.Application:
        inOutParam = getInputParameterOutput(inImg)
        morphoMath.SetParameterInputImage("in", inImg.GetParameterOutputImage(inOutParam))
    elif isinstance(inImg,tuple):morphoMath.SetParameterInputImage("in", inImg[0].GetParameterOutputImage("out"))
    else : raise Exception("input image not recognize")
    morphoMath.SetParameterString("filter", filter)
    morphoMath.SetParameterString("structype", "ball")
    morphoMath.SetParameterString("structype.ball.xradius", str(ballxradius))
    morphoMath.SetParameterString("structype.ball.yradius", str(ballyradius))
    morphoMath.SetParameterString("out", outImg)
    morphoMath.SetParameterOutputImagePixelType("out", fut.commonPixTypeToOTB(pixType))

    return morphoMath

def CreateClumpApplication(stack, exp, ram='128', pixType="uint8", output=""):

    """
    IN
    stack [string/OtbObject]
    exp [string] filter expression
    ram [string/int] pipe's size
    pixType [string] : output pixel type, according to commonPixTypeToOTB
                       function in fileUtils
    output [string] output path

    OUT
    seg [otb object ready to Execute]
    """
    seg = otb.Registry.CreateApplication("Segmentation")
    if seg is None:
        raise Exception("Not possible to create 'Segmentation' application, check if OTB is well configured / installed")
    if not stack :
        raise Exception("no input image detected")
    if isinstance(stack, str):seg.SetParameterString("in", stack)
    elif type(stack) == otb.Application:
        inOutParam = getInputParameterOutput(stack)
        seg.SetParameterInputImage("in", stack.GetParameterOutputImage(inOutParam))
    else:
        raise Exception(type(stack)+" not available to CreateClumpApplication function")

    seg.SetParameterString("mode","raster")
    seg.SetParameterString("filter","cc")
    seg.SetParameterString("filter.cc.expr", exp)
    seg.SetParameterString("mode.raster.out", output)
    seg.SetParameterOutputImagePixelType("mode.raster.out", fut.commonPixTypeToOTB(pixType))

    return seg

def CreateConcatenateImagesApplication(imagesList=None,ram='128',pixType="uint8",output=""):
    """
    IN
    imagesList [string/listOfString/listofOtbObject/listOfTupleOfOtbObject]
    ram [string/int] pipe's size
    pixType [string] : output pixel type, according to commonPixTypeToOTB
                       function in fileUtils
    output [string] output path

    OUT
    concatenate [otb object ready to Execute]
    """
    if not isinstance(imagesList,list):imagesList=[imagesList]

    concatenate = otb.Registry.CreateApplication("ConcatenateImages")
    if concatenate is None:
        raise Exception("Not possible to create 'Concatenation' application, check if OTB is well configured / installed")

    if isinstance(imagesList[0],str):
        concatenate.SetParameterStringList("il",imagesList)
    elif type(imagesList[0])==otb.Application:
        for currentObj in imagesList:
            inOutParam = getInputParameterOutput(currentObj)
            concatenate.AddImageToParameterInputImageList("il",currentObj.GetParameterOutputImage(inOutParam))
    elif isinstance(imagesList[0],tuple):
        for currentObj in unPackFirst(imagesList):
            inOutParam = getInputParameterOutput(currentObj)
            concatenate.AddImageToParameterInputImageList("il",currentObj.GetParameterOutputImage(inOutParam))
    else : raise Exception("can't create ConcatenateImagesApplication")

    concatenate.SetParameterString("out",output)
    concatenate.SetParameterOutputImagePixelType("out", fut.commonPixTypeToOTB(pixType))

    return concatenate

def CreateBandMathApplication(imagesList=None,exp=None,ram='128',pixType="uint8",output=""):
    """
    IN
    imagesList [string/listOfString/listofOtbObject/listOfTupleOfOtbObject]
    exp [string] bandMath expression
    ram [string/int] pipe's size
    pixType [string] : output pixel type, according to commonPixTypeToOTB
                       function in fileUtils
    output [string] output path

    OUT
    bandMath [otb object ready to Execute]
    """
    if not isinstance(imagesList,list):imagesList=[imagesList]

    bandMath = otb.Registry.CreateApplication("BandMath")
    if bandMath is None:
        raise Exception("Not possible to create 'BandMath' application, check if OTB is well configured / installed")

    bandMath.SetParameterString("exp",exp)

    if isinstance(imagesList[0],str):bandMath.SetParameterStringList("il",imagesList)
    elif type(imagesList[0])==otb.Application:
        for currentObj in imagesList:
            inOutParam = getInputParameterOutput(currentObj)
            bandMath.AddImageToParameterInputImageList("il",currentObj.GetParameterOutputImage(inOutParam))
    elif isinstance(imagesList[0],tuple):
        for currentObj in unPackFirst(imagesList):
            inOutParam = getInputParameterOutput(currentObj)
            bandMath.AddImageToParameterInputImageList("il",currentObj.GetParameterOutputImage(inOutParam))
    else :
        raise Exception(type(imageList[0])+" not available to CreateBandMathApplication function")
    bandMath.SetParameterString("ram",ram)
    bandMath.SetParameterString("out",output)
    bandMath.SetParameterOutputImagePixelType("out",fut.commonPixTypeToOTB(pixType))
    return bandMath


def CreateSuperimposeApplication(inImg1, inImg2, ram="2000",
                                 pixType='uint8', lms=None,
                                 outImg="", interpolator="nn",
                                 eleveDem=None,elevGeoid=None):
    """
    IN

    inImg1 [string/OtbObject/tupleOfOtbObject] input reference image
    inImg2 [string/OtbObject/tupleOfOtbObject] input image to reproject
    ram [string/int] pipe's size
    pixType [string] : output pixel type, according to commonPixTypeToOTB
                       function in fileUtils
    lms [string/int]
    interpolator [string] interpolator type
    eleveDem [string] path to DEM
    elevGeoid [string] path to geoid
    output [string] output path

    OUT
    siApp [otb object ready to Execute]
    """
    siApp = otb.Registry.CreateApplication("Superimpose")
    if siApp  is None:
        raise Exception("Not possible to create 'Superimpose' application, check if OTB is well configured / installed")

    # First image input
    if isinstance(inImg1, str):siApp.SetParameterString("inr", inImg1)
    elif type(inImg1) == otb.Application:
        inOutParam = getInputParameterOutput(inImg1)
        siApp.SetParameterInputImage("inr", inImg1.GetParameterOutputImage(inOutParam))
    elif isinstance(inImg1, tuple):siApp.SetParameterInputImage("inr", inImg1[0].GetParameterOutputImage(getInputParameterOutput(inImg1[0])))
    else : raise Exception("reference input image not recognize")

    # Second image input
    if isinstance(inImg2, str):siApp.SetParameterString("inm", inImg2)
    elif type(inImg2) == otb.Application:
        inOutParam = getInputParameterOutput(inImg2)
        siApp.SetParameterInputImage("inm", inImg2.GetParameterOutputImage(inOutParam))
    elif isinstance(inImg2, tuple):siApp.SetParameterInputImage("inm", inImg2[0].GetParameterOutputImage(getInputParameterOutput(inImg2[0])))
    else : raise Exception("Image to reproject not recognize")

    siApp.SetParameterString("ram", str(ram))
    siApp.SetParameterString("interpolator", interpolator)
    siApp.SetParameterString("out", outImg)
    if eleveDem : siApp.SetParameterString("elev.dem",eleveDem)
    if elevGeoid : siApp.SetParameterString("elev.geoid",elevGeoid)
    if lms : siApp.SetParameterString("lms",lms)
    siApp.SetParameterOutputImagePixelType("out", fut.commonPixTypeToOTB(pixType))

    return siApp,inImg2

def CreateExtractROIApplication(inImg, startx, starty, sizex, sizey, ram="2000", pixType='uint8', outImg = ""):

    erApp = otb.Registry.CreateApplication("ExtractROI")
    if erApp is None:
        raise Exception("Not possible to create 'ExtractROI' application, check if OTB is well configured / installed")

    if isinstance(inImg, str):erApp.SetParameterString("in", inImg)
    elif type(inImg) == otb.Application:
        inOutParam = getInputParameterOutput(inImg)
        erApp.SetParameterInputImage("in", inImg.GetParameterOutputImage(inOutParam))
    elif isinstance(inImg, tuple):erApp.SetParameterInputImage("in", inImg[0].GetParameterOutputImage("out"))
    else : raise Exception("input image not recognize")

    erApp.SetParameterString("ram", str(ram))
    erApp.SetParameterString("startx", str(startx))
    erApp.SetParameterString("starty", str(starty))
    erApp.SetParameterString("sizex", str(sizex))
    erApp.SetParameterString("sizey", str(sizey))
    erApp.SetParameterString("out", outImg)
    erApp.SetParameterOutputImagePixelType("out", fut.commonPixTypeToOTB(pixType))

    return erApp

def CreateRasterizationApplication(inVect, inRefImg, background, outImg=""):

    rasterApp = otb.Registry.CreateApplication("Rasterization")
    if rasterApp is None:
        raise Exception("Not possible to create 'Rasterization' application, check if OTB is well configured / installed")

    rasterApp.SetParameterString("in", inVect)
    rasterApp.SetParameterString("out", outImg)
    rasterApp.SetParameterString("im", inRefImg)
    rasterApp.SetParameterString("background", str(background))

    return rasterApp

def computeUserFeatures(stack,nbDates,nbComponent,expressions):

    def transformExprToListString(expr):
        """
        Example :
        expr = "(b1+b2)/(b3+b10+b1)"
        print transformExprToListString(expr)
        >> ['(', 'b1', '+', 'b2', ')', '/', '(', 'b3', '+', 'b10', '+', 'b1', ')']
        """
        container = []
        cpt=0
        while cpt <len(expr):
            currentChar = expr[cpt]
            if currentChar != "b" : container.append(currentChar)
            else:
                stringDigit = "b"
                for j in range(cpt+1,len(expr)):
                    try :
                        digit = int(expr[j])
                        cpt+=1
                        stringDigit+=expr[j]
                        if cpt == len(expr)-1: container.append(stringDigit)
                    except :
                        container.append(stringDigit)
                        break
            cpt+=1
        return container

    def checkBands(allBands,nbComp):
        """
        usage : check coherence between allBands in expression and number of component

        IN :
        allBands [set of all bands requested for expression] : example set(['b1', 'b2'])
        nbComp [int] : number of possible bands

        OUT
        ok [bool]
        """
        integerBands = [int(currentBand.split("b")[-1]) for currentBand in allBands]
        if max(integerBands)<=nbComp : return True
        else : return False

    def computeExpressionDates(expr,nbDate,nbComp):

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
        allBands = set([ currentDec for currentDec in re.findall(r'[b]\d+',expr)])
        expressionValid = checkBands(allBands,nbComp)
        if not expressionValid : raise Exception("User features expression : '"+expr+\
                                                  "' is not consistent with sensor's component number : "+str(nbComp))
        expression = transformExprToListString(expr)
        allExpression = []
        for date in range(nbDate):
            expressionDate = [currentChar for currentChar in expression]
            for currentBand in allBands :
                indices = list(np.where(np.array(expression) == currentBand)[0])
                if not indices:
                    raise Exception("Problem in parsing expression : band "+currentBand+" not recognize")
                for ind in indices :
                    bandNumber = expressionDate[ind]
                    bandDate = int(bandNumber.split("b")[-1])+nbComp*date
                    expressionDate[ind] = "b"+str(bandDate)
            allExpression.append(("".join(expressionDate)).replace("b","im1b"))

        return allExpression

    expressionDate = [computeExpressionDates(currentExpression,nbDates,nbComponent) for currentExpression in expressions]
    flatExprDate = [currentExp for currentDate in expressionDate for currentExp in currentDate]

    userFeatureDate = []
    for expression in flatExprDate:
        bandMathApp = CreateBandMathApplication(imagesList=stack,exp=expression,\
                                                ram='2000',pixType="int16",\
                                                output="None")
        bandMathApp.Execute()
        userFeatureDate.append(bandMathApp)
    UserFeatures = CreateConcatenateImagesApplication(imagesList=userFeatureDate,ram='2000',\
                                                      pixType="int16",output="")

    return UserFeatures,userFeatureDate,stack

def gapFilling(pathConf,tile,wMode,featuresPath=None,workingDirectory=None,testMode=False,testSensorData=None):

    dep = []
    if fut.onlySAR(pathConf) : return [],[],[],[],[],[]
    outFeatures = Config(file(pathConf)).GlobChain.features
    userFeatPath = Config(file(pathConf)).chain.userFeatPath
    if userFeatPath == "None" : userFeatPath = None
    extractBands = Config(file(pathConf)).iota2FeatureExtraction.extractBands
    if extractBands == "False" : extractBands = None

    ipathL5=Config(file(pathConf)).chain.L5Path
    if ipathL5 == "None" : ipathL5=None
    ipathL8=Config(file(pathConf)).chain.L8Path
    if ipathL8 == "None" : ipathL8=None
    ipathS2=Config(file(pathConf)).chain.S2Path
    if ipathS2 == "None" : ipathS2=None
    autoDate = ast.literal_eval(Config(file(pathConf)).GlobChain.autoDate)
    gapL5=Config(file(pathConf)).Landsat5.temporalResolution
    gapL8=Config(file(pathConf)).Landsat8.temporalResolution
    gapS2=Config(file(pathConf)).Sentinel_2.temporalResolution
    tiles=(Config(file(pathConf)).chain.listTile).split()

    if testMode : ipathL8 = testSensorData
    dateB_L5=dateE_L5=dateB_L8=dateE_L8=dateB_S2=dateE_S2 = None
    if ipathL5 :
        dateB_L5,dateE_L5=fut.getDateL5(ipathL5,tiles)
    if not autoDate :
        dateB_L5 = Config(file(pathConf)).Landsat5.startDate
        dateE_L5 = Config(file(pathConf)).Landsat5.endDate
    if ipathL8 :
        dateB_L8,dateE_L8=fut.getDateL8(ipathL8,tiles)
        if not autoDate :
            dateB_L8 = Config(file(pathConf)).Landsat8.startDate
            dateE_L8 = Config(file(pathConf)).Landsat8.endDate
    if ipathS2 :
        dateB_S2,dateE_S2=fut.getDateS2(ipathS2,tiles)
        if not autoDate :
            dateB_S2 = Config(file(pathConf)).Sentinel_2.startDate
            dateE_S2 = Config(file(pathConf)).Sentinel_2.endDate

    S2 = Sensors.Sentinel_2("",Opath("",create = False),pathConf,"",createFolder = None)
    L8 = Sensors.Landsat8("",Opath("",create = False),pathConf,"",createFolder = None)
    L5 = Sensors.Landsat5("",Opath("",create = False),pathConf,"",createFolder = None)
    SensorsList = [S2,L8,L5]

    workingDirectoryFeatures = workingDirectory+"/"+tile
    if not os.path.exists(workingDirectoryFeatures):os.mkdir(workingDirectoryFeatures)
    import prepareStack
    AllRefl,AllMask,datesInterp,realDates = prepareStack.generateStack(tile,pathConf,\
                                                                       featuresPath,ipathL5=ipathL5,ipathL8=ipathL8,\
                                                                       ipathS2=ipathS2,dateB_L5=dateB_L5,dateE_L5=dateE_L5,\
                                                                       dateB_L8=dateB_L8,dateE_L8=dateE_L8,dateB_S2=dateB_S2,\
                                                                       dateE_S2=dateE_S2,gapL5=gapL5,gapL8=gapL8,\
                                                                       gapS2=gapS2,writeOutput=wMode,\
                                                                       workingDirectory=workingDirectoryFeatures)

    AllgapFill = []
    reflectanceOutput = [currentRefl.GetParameterValue("out") for currentRefl in AllRefl]
    masksOutput = [currentMask[0].GetParameterValue("out") for currentMask in AllMask]
    datesInterpOutput = [currentDateInterp for currentDateInterp in datesInterp]
    datesRealOutput = [currentDateReal for currentDateReal in realDates]

    print "\n****** gapFilling to sample script ******"
    print "Reflectances used  : "+" ".join(reflectanceOutput)
    print "masks used : "+" ".join(masksOutput)
    print "interpolation dates : "+" ".join(datesInterpOutput)
    print "real dates : "+" ".join(datesRealOutput)
    print "*****************************************\n"

    features = []
    concatSensors= otb.Registry.CreateApplication("ConcatenateImages")
    for refl,mask,currentDatesInterp,currentRealDates in zip(AllRefl,AllMask,datesInterp,realDates):
        if wMode :
            refl.ExecuteAndWriteOutput()
            mask[0].ExecuteAndWriteOutput()
        else :
            refl.Execute()
            mask[0].Execute()

        currentSensor = fut.getCurrentSensor(SensorsList,refl.GetParameterValue("out"))
        reflDirectory,reflName =  os.path.split(refl.GetParameterValue("out"))
        outGapFilling=reflDirectory+"/"+reflName.replace(".tif","_GAP.tif")
        outFeatures=outGapFilling.replace(".tif","_Features.tif")

        nbDate = fut.getNbDateInTile(currentRealDates)
        gapFill = otb.Registry.CreateApplication("ImageTimeSeriesGapFilling")
        comp = len(currentSensor.bands['BANDS'])

        gapFill.SetParameterInputImage("mask",mask[0].GetParameterOutputImage("out"))
        gapFill.SetParameterString("it","linear")
        gapFill.SetParameterString("id",currentRealDates)
        gapFill.SetParameterString("od",currentDatesInterp)
        gapFill.SetParameterString("out",outGapFilling)
        gapFill.SetParameterOutputImagePixelType("out",fut.commonPixTypeToOTB('int16'))

        if extractBands :
            bandsToKeep = [bandNumber for bandNumber,bandName in currentSensor.keepBands]
            extract = fut.ExtractInterestBands(refl,nbDate,bandsToKeep,comp,ram = 10000)
            dep.append(extract)
            comp = len(bandsToKeep)
            gapFill.SetParameterInputImage("in",extract.GetParameterOutputImage("out"))

        else : gapFill.SetParameterInputImage("in",refl.GetParameterOutputImage("out"))
        gapFill.SetParameterString("comp",str(comp))
        AllgapFill.append(gapFill)

    return AllgapFill,AllRefl,AllMask,datesInterp,realDates,dep

def writeInterpolateDateFile(datesList,outputFolder,timeRes,mode):
    outputFile = outputFolder+"/"+mode+"_interpolationDates.txt"

    minDatesInterpol = [currentTileDate[0] for currentTileDate in datesList]
    maxDatesInterpol = [currentTileDate[-1] for currentTileDate in datesList]

    miniInterpol = minDatesInterpol[-1]
    maxiInterpol = maxDatesInterpol[0]

    if not os.path.exists(outputFile):
        outInterDates = "\n".join([str(interpolDate).replace("-","") for interpolDate in fut.dateInterval(str(miniInterpol),str(maxiInterpol),timeRes)])
        if len(datesList[0])==1:outInterDates=str(datesList[0][0])
        with open(outputFile,"w") as fileInterp: fileInterp.write(outInterDates)
    return outputFile

def writeInputDateFile(allTileMasks,outputFolder,mode):

    outputFile = outputFolder+"/"+mode+"_inputDates.txt"

    if mode == "S1aDES":
        masks = [CCallMasks for CCallMasks in allTileMasks if CCallMasks.split("/")[-1].split("_")[3]=="DES" and CCallMasks.split("/")[-1].split("_")[0]=="s1a"]
    elif mode == "S1aASC":
        masks = [CCallMasks for CCallMasks in allTileMasks if CCallMasks.split("/")[-1].split("_")[3]=="ASC" and CCallMasks.split("/")[-1].split("_")[0]=="s1a"]
    elif mode == "S1bDES":
        masks = [CCallMasks for CCallMasks in allTileMasks if CCallMasks.split("/")[-1].split("_")[3]=="DES" and CCallMasks.split("/")[-1].split("_")[0]=="s1b"]
    elif mode == "S1bASC":
        masks = [CCallMasks for CCallMasks in allTileMasks if CCallMasks.split("/")[-1].split("_")[3]=="ASC" and CCallMasks.split("/")[-1].split("_")[0]=="s1b"]
    else : raise Exception("mode not recognize")

    currentTileDate = sorted([int(cTileDate.split("/")[-1].split("_")[4].split("t")[0]) for cTileDate in masks])
    currentTileDate_s = [str(CcurrentTileDate) for CcurrentTileDate in currentTileDate]
    if not os.path.exists(outputFile):
        outInputDates = "\n".join(currentTileDate_s)
        with open(outputFile,"w") as fileDate:
            fileDate.write(outInputDates)

    return outputFile

def sortS1aS1bMasks(masksList):
    from S1FilteringProcessor import getDatesInOtbOutputName
    sortedMasks = []#care about order
    S1aDES = [CMask for CMask in masksList if CMask.split("/")[-1].split("_")[3]=="DES" and CMask.split("/")[-1].split("_")[0]=="s1a"]
    S1aASC = [CMask for CMask in masksList if CMask.split("/")[-1].split("_")[3]=="ASC" and CMask.split("/")[-1].split("_")[0]=="s1a"]
    S1bDES = [CMask for CMask in masksList if CMask.split("/")[-1].split("_")[3]=="DES" and CMask.split("/")[-1].split("_")[0]=="s1b"]
    S1bASC = [CMask for CMask in masksList if CMask.split("/")[-1].split("_")[3]=="ASC" and CMask.split("/")[-1].split("_")[0]=="s1b"]

    if S1aDES : sortedMasks.append(sorted(S1aDES,key=getDatesInOtbOutputName))
    if S1aASC : sortedMasks.append(sorted(S1aASC,key=getDatesInOtbOutputName))
    if S1bDES : sortedMasks.append(sorted(S1bDES,key=getDatesInOtbOutputName))
    if S1bASC : sortedMasks.append(sorted(S1bASC,key=getDatesInOtbOutputName))

    return sortedMasks

def getSARstack(sarConfig,tileName,allTiles):
    """
    IN:
    sarConfig [string] : path to SAR configuration file
    tileName [string] : tile name to compute. Ex : T31TCJ
    OUT:
    """
    import S1Processor as s1p
    import ConfigParser

    config = ConfigParser.ConfigParser()
    config.read(sarConfig)
    outputDirectory =  config.get('Paths','Output')
    outputDateFolder = outputDirectory+"/"+tileName[1:]
    tr =  config.get('Processing','TemporalResolution')

    sarTileDateS1aDM = []
    sarTileDateS1aAM = []
    sarTileDateS1bDM = []
    sarTileDateS1bAM = []

    interpDateFiles = []
    inputDateFiles = []

    allFiltered,allDependence,allMasks,allTile = s1p.S1Processor(sarConfig)
    for CallFiltered,CallDependence,CallMasks,CallTile in zip(allFiltered,allDependence,allMasks,allTile):
        if CallTile in tileName :
            outAllFiltered = [CCallFiltered for CCallFiltered in CallFiltered]
            outAllMasks = sortS1aS1bMasks(CallMasks)
            outAllDependence = CallDependence

        if "T"+CallTile in allTiles:

            #get S1a DES masks
            s1aDMasks = [CCallMasks for CCallMasks in CallMasks if CCallMasks.split("/")[-1].split("_")[3]=="DES" and CCallMasks.split("/")[-1].split("_")[0]=="s1a"]
            #get S1a ASC masks
            s1aAMasks = [CCallMasks for CCallMasks in CallMasks if CCallMasks.split("/")[-1].split("_")[3]=="ASC" and CCallMasks.split("/")[-1].split("_")[0]=="s1a"]
            #get S1b DES masks
            s1bDMasks = [CCallMasks for CCallMasks in CallMasks if CCallMasks.split("/")[-1].split("_")[3]=="DES" and CCallMasks.split("/")[-1].split("_")[0]=="s1b"]
            #get S1b ASC masks
            s1bAMasks = [CCallMasks for CCallMasks in CallMasks if CCallMasks.split("/")[-1].split("_")[3]=="ASC" and CCallMasks.split("/")[-1].split("_")[0]=="s1b"]

            if s1aDMasks :
                sarTileDateS1aDM.append(sorted([int(Cs1aDMasks.split("/")[-1].split("_")[4].split("t")[0]) for Cs1aDMasks in s1aDMasks]))
            if s1aAMasks :
                sarTileDateS1aAM.append(sorted([int(Cs1aAMasks.split("/")[-1].split("_")[4].split("t")[0]) for Cs1aAMasks in s1aAMasks]))
            if s1bDMasks :
                sarTileDateS1bDM.append(sorted([int(Cs1bDMasks.split("/")[-1].split("_")[4].split("t")[0]) for Cs1bDMasks in s1bDMasks]))
            if s1bAMasks :
                sarTileDateS1bAM.append(sorted([int(Cs1bDMasks.split("/")[-1].split("_")[4].split("t")[0]) for Cs1bDMasks in s1bAMasks]))

    #Care about list order : must be the same as construct in S1FilteringProcessor.py
    #-> S1aDES,S1aASC,S1bDES and then S1bASC
    tileMasks = [CCoutAllMasks for CoutAllMasks in outAllMasks for CCoutAllMasks in CoutAllMasks]
    if sarTileDateS1aDM :
        interpS1aD = writeInterpolateDateFile(sarTileDateS1aDM,outputDateFolder,tr,mode="S1aDES")
        inputS1aD = writeInputDateFile(tileMasks,outputDateFolder,mode="S1aDES")
        interpDateFiles.append(interpS1aD)
        inputDateFiles.append(inputS1aD)
    if sarTileDateS1aAM :
        interpS1aA = writeInterpolateDateFile(sarTileDateS1aAM,outputDateFolder,tr,mode="S1aASC")
        inputS1aA = writeInputDateFile(tileMasks,outputDateFolder,mode="S1aASC")
        interpDateFiles.append(interpS1aA)
        inputDateFiles.append(inputS1aA)
    if sarTileDateS1bDM :
        interpS1bD = writeInterpolateDateFile(sarTileDateS1bDM,outputDateFolder,tr,mode="S1bDES")
        inputS1bD = writeInputDateFile(tileMasks,outputDateFolder,mode="S1bDES")
        interpDateFiles.append(interpS1bD)
        inputDateFiles.append(inputS1bD)
    if sarTileDateS1bAM :
        interpS1bA = writeInterpolateDateFile(sarTileDateS1bAM,outputDateFolder,tr,mode="S1bASC")
        inputS1bA = writeInputDateFile(tileMasks,outputDateFolder,mode="S1bASC")
        interpDateFiles.append(interpS1bA)
        inputDateFiles.append(inputS1bA)

    return outAllFiltered,outAllMasks,outAllDependence,interpDateFiles,inputDateFiles

def computeSARfeatures(sarConfig,tileToCompute,allTiles):

    """
    IN:
    sarConfig [string] : path to SAR configuration file
    tileToCompute [string] : tile name to compute. Ex : T31TCJ
    allTiles [list of string] : all tiles needed for the run
                                used to compute interpolation dates (gapFilling)
    OUT:
    stackSARFeatures [otb object ready to Execute]
    """
    from S1FilteringProcessor import getDatesInOtbOutputName

    SARstack,SARmasks,SARdep,interpDateFiles,inputDateFiles = getSARstack(sarConfig,tileToCompute,allTiles)
    SARcomp = 2 #number of components per dates VV + VH
    SARFeatures = []
    Dep = []
    for (currentSarStack,a,b,c,d),CSARmasks,interpDate,inputDate in zip(SARstack,SARmasks,interpDateFiles,inputDateFiles):

        currentSarStack.Execute()
        outName = currentSarStack.GetParameterValue(getInputParameterOutput(currentSarStack))
        if not isinstance(CSARmasks,list):CSARmasks=[CSARmasks]
        stackMask = CreateConcatenateImagesApplication(imagesList=CSARmasks,ram='5000',pixType="uint8",output=outName.replace(".tif","_MASKSTACK.tif"))
        stackMask.Execute()
        Dep.append(stackMask)
        print "-------------------------------------------"
        print "SAR gapFilling parameters"
        print "id "+inputDate
        print "od "+interpDate
        print stackMask.GetParameterValue("out")

        SARgapFill = otb.Registry.CreateApplication("ImageTimeSeriesGapFilling")
        SARgapFill.SetParameterString("it","linear")
        SARgapFill.SetParameterString("id",inputDate)
        SARgapFill.SetParameterString("od",interpDate)
        SARgapFill.SetParameterString("comp",str(SARcomp))
        SARgapFill.SetParameterInputImage("in",currentSarStack.GetParameterOutputImage(getInputParameterOutput(currentSarStack)))
        SARgapFill.SetParameterOutputImagePixelType("out",fut.commonPixTypeToOTB('float'))
        SARgapFill.SetParameterInputImage("mask",stackMask.GetParameterOutputImage(getInputParameterOutput(stackMask)))

        outName = outName.replace(".tif","_GAPFIL.tif")
        SARgapFill.SetParameterString("out",outName)
        SARgapFill.Execute()

        Dep.append(SARgapFill)

        SARFeatures.append(SARgapFill)

    stackSARFeatures = CreateConcatenateImagesApplication(imagesList=SARFeatures,ram='5000',pixType="float",output="/work/OT/theia/oso/TMP/TMP2/"+tileToCompute+"_STACKGAP.tif")
    return stackSARFeatures,[SARdep,stackMask,SARstack,Dep]

def computeFeatures(pathConf,nbDates,tile,*ApplicationList,**testVariables):
    """
    IN:
    pathConf [string] : path to the configuration file
    *ApplicationList [list of list of OTB's application] : only first content of list is used to produce features
    nbDates [list of int] : number of component by stack (ApplicationList[0])

    OUT:
    outputFeatures  [otb object ready to Execute]
    ApplicationList,userDateFeatures,a,b,AllFeatures,SARdep are dependances

    """
    testMode = testVariables.get('testMode')
    testUserFeatures = testVariables.get('testUserFeatures')
    userFeatPath = Config(file(pathConf)).chain.userFeatPath

    fut.updatePyPath()

    if testMode : userFeatPath = testUserFeatures
    if userFeatPath == "None" : userFeatPath = None
    useAddFeat = ast.literal_eval(Config(file(pathConf)).GlobChain.useAdditionalFeatures)
    extractBands = ast.literal_eval(Config(file(pathConf)).iota2FeatureExtraction.extractBands)
    featuresFlag = Config(file(pathConf)).GlobChain.features
    S1Data = Config(file(pathConf)).chain.S1Path
    if S1Data == "None" : S1Data = None

    if not featuresFlag and userFeatPath == None and not S1Data: return ApplicationList

    S2 = Sensors.Sentinel_2("",Opath("",create = False),pathConf,"",createFolder = None)
    L8 = Sensors.Landsat8("",Opath("",create = False),pathConf,"",createFolder = None)
    L5 = Sensors.Landsat5("",Opath("",create = False),pathConf,"",createFolder = None)
    SensorsList = [S2,L8,L5]

    AllGapFilling = ApplicationList[0]
    AllFeatures = []

    allTiles = (Config(file(pathConf)).chain.listTile).split()
    if S1Data :
        SARfeatures,SARdep = computeSARfeatures(S1Data,tile,allTiles)
        AllFeatures.append(SARfeatures)

    for gapFilling,dates in zip(AllGapFilling,nbDates):
        outFeatures=gapFilling.GetParameterValue("out")
        outFeatures=outFeatures.replace(".tif","_Features.tif")
        featExtr = otb.Registry.CreateApplication("iota2FeatureExtraction")
        currentSensor = fut.getCurrentSensor(SensorsList,gapFilling.GetParameterValue("out"))
        comp = len(currentSensor.bands['BANDS'])

        if extractBands :
            bandsToKeep = [bandNumber for bandNumber,bandName in currentSensor.keepBands]
            comp = len(bandsToKeep)
        if useAddFeat :
            userDateFeatures,a,b = computeUserFeatures(gapFilling,dates,comp,currentSensor.addFeatures)
            userDateFeatures.Execute()
        else :
            userDateFeatures=a=b=None

        featExtr.SetParameterInputImage("in",gapFilling.GetParameterOutputImage("out"))
        featExtr.SetParameterString("comp",str(comp))
        red = str(currentSensor.bands["BANDS"]["red"])
        nir = str(currentSensor.bands["BANDS"]["NIR"])
        swir = str(currentSensor.bands["BANDS"]["SWIR"])
        if extractBands :
            red = str(fut.getIndex(currentSensor.keepBands,"red"))
            nir = str(fut.getIndex(currentSensor.keepBands,"NIR"))
            swir = str(fut.getIndex(currentSensor.keepBands,"SWIR"))

        featExtr.SetParameterString("red",red)
        featExtr.SetParameterString("nir",nir)
        featExtr.SetParameterString("swir",swir)
        featExtr.SetParameterString("out",outFeatures)
        featExtr.SetParameterOutputImagePixelType("out",fut.commonPixTypeToOTB('int16'))
        fut.iota2FeatureExtractionParameter(featExtr,pathConf)
        if featuresFlag :
            print "Add features compute from iota2FeatureExtraction"
            AllFeatures.append(featExtr)
        else :
            AllFeatures.append(gapFilling)
        if useAddFeat : AllFeatures.append(userDateFeatures)

    if userFeatPath :
        print "Add user features"
        userFeat_arbo = Config(file(pathConf)).userFeat.arbo
        userFeat_pattern = (Config(file(pathConf)).userFeat.patterns).split(",")
        userFeatures = fut.getUserFeatInTile(userFeatPath,tile,userFeat_arbo,userFeat_pattern)

        concatUserFeatures = CreateConcatenateImagesApplication(imagesList=userFeatures,\
                                                                ram='4000',pixType="int16",output="")
        concatUserFeatures.Execute()
        AllFeatures.append(concatUserFeatures)
    if len(AllFeatures)>1:
        for currentFeat in AllFeatures : currentFeat.Execute()
        outFeatures=outFeatures.replace(".tif","_USERFEAT.tif")
        outPixType = "int16"
        if S1Data : outPixType = "float"
        featuresConcatenation = CreateConcatenateImagesApplication(imagesList=AllFeatures,\
                                                                   ram='4000',pixType=outPixType,output=outFeatures)
        outputFeatures = featuresConcatenation
    else :
        outputFeatures = AllFeatures[0]
    if "S1" in fut.sensorUserList(pathConf) and len(fut.sensorUserList(pathConf))==1:
        userDateFeatures=a=b=None
    elif not "S1" in fut.sensorUserList(pathConf):
        SARdep = None
    return outputFeatures,ApplicationList,userDateFeatures,a,b,AllFeatures,SARdep
