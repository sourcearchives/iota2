#!/usr/bin/python
#-*- coding: utf-8 -*-

import otbApplication as otb
import fileUtils as fut

"""
def commonPixTypeToOTB(string):
    dico = {\
    "complexDouble":otb.ComplexImagePixelType_double,\
    "complexFloat":otb.ComplexImagePixelType_float,\
    "double":otb.ImagePixelType_double,\
    "float":otb.ImagePixelType_float,\
    "int16":otb.ImagePixelType_int16,\
    "int32":otb.ImagePixelType_int32,\
    "uint16":otb.ImagePixelType_uint16,\
    "uint32":otb.ImagePixelType_uint32,\
    "uint8":otb.ImagePixelType_uint8}
    return dico[string]
"""

def getInputParameterOutput(otbObj):

    listParam = otbObj.GetParametersKeys()
    #check out
    if "out" in listParam : return "out"
    #checkout io.out
    elif "io.out" in listParam : return "io.out"
    else : raise Exception("out parameter not recognize")
    
def unPackFirst(someListOfList):

    for values in someListOfList:
        if isinstance(values,list) or isinstance(values,tuple):yield values[0]
        else : yield values
"""
def CreateSuperimpose(inm,inr,out,eleveDem=None,elevGeoid=None):

    superImpose = otb.Registry.CreateApplication("Superimpose")
    if isinstance(inm,str):superImpose.SetParameterString("inm",inm)
    elif type(inm)==otb.Application:superImpose.SetParameterInputImage("inm",inm.GetParameterOutputImage(getInputParameterOutput(inm)))
    elif isinstance(inm,tuple):superImpose.SetParameterInputImage("inm",inm[0].GetParameterOutputImage(getInputParameterOutput(inm[0])))
    if eleveDem : superImpose.SetParameterString("elev.dem",eleveDem)
    if elevGeoid : superImpose.SetParameterString("elev.geoid",elevGeoid)
    superImpose.SetParameterString("out",out)
    superImpose.SetParameterString("inr",inr)
    return superImpose,inm
"""
def CreateConcatenateImagesApplication(imagesList=None,ram='128',pixType=None,wMode=False,output=None):

    if not isinstance(imagesList,list):imagesList=[imagesList]

    concatenate = otb.Registry.CreateApplication("ConcatenateImages")
    if isinstance(imagesList[0],str):
	concatenate.SetParameterStringList("il",imagesList)
    elif type(imagesList[0])==otb.Application:
        for currentObj in imagesList:
            concatenate.AddImageToParameterInputImageList("il",currentObj.GetParameterOutputImage("out"))
    elif isinstance(imagesList[0],tuple):
        for currentObj in unPackFirst(imagesList):
            concatenate.AddImageToParameterInputImageList("il",currentObj.GetParameterOutputImage("out"))

    concatenate.SetParameterString("out",output)
    concatenate.SetParameterOutputImagePixelType("out",fut.commonPixTypeToOTB(pixType))


    return concatenate

def CreateBandMathApplication(imagesList=None,exp=None,ram='128',pixType=None,output="None",OutParam = "out"):

    if not isinstance(imagesList,list):imagesList=[imagesList]

    bandMath = otb.Registry.CreateApplication("BandMath")
    bandMath.SetParameterString("exp",exp)

    if isinstance(imagesList[0],str):bandMath.SetParameterStringList("il",imagesList)
    elif type(imagesList[0])==otb.Application:
	for currentObj in imagesList:
            bandMath.AddImageToParameterInputImageList("il",currentObj.GetParameterOutputImage(OutParam))
    elif isinstance(imagesList[0],tuple):
        for currentObj in unPackFirst(imagesList):
            bandMath.AddImageToParameterInputImageList("il",currentObj.GetParameterOutputImage(OutParam))
    else : 
        raise Exception(type(imageList[0])+" not available to CreateBandMathApplication function")
    bandMath.SetParameterString("ram",ram)
    bandMath.SetParameterString("out",output)
    bandMath.SetParameterOutputImagePixelType("out",fut.commonPixTypeToOTB(pixType))
    return bandMath

def CreateOrthoRectification(inputImage,outputImage,ram,spx,spy,sx,sy,gridSpacing,\
                             utmZone,utmNorhhem,ulx,uly,dem,geoid):

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
"""
def CreateBinaryMorphologicalOperation(inImg,outImg,ram="2000",pixType='uint8',filter="opening"):
    
    morphoMath = otb.Registry.CreateApplication("BinaryMorphologicalOperation")
    if isinstance(inImg,str):morphoMath.SetParameterString("in",inImg)
    elif type(inImg)==otb.Application:morphoMath.SetParameterInputImage("in",inImg.GetParameterOutputImage("out"))
    elif isinstance(inImg,tuple):morphoMath.SetParameterInputImage("in",inImg[0].GetParameterOutputImage("out"))
    else : raise Exception("input image not recognize")
    morphoMath.SetParameterString("structype","ball")
    morphoMath.SetParameterString("structype.ball.xradius","5")
    morphoMath.SetParameterString("structype.ball.yradius","5")
    morphoMath.SetParameterString("out",outImg)
    morphoMath.SetParameterString("filter",filter)
    morphoMath.SetParameterOutputImagePixelType("out",fut.commonPixTypeToOTB(pixType))

    return morphoMath
"""
def CreateMultitempFilteringFilter(inImg,outcore,winRad,enl,ram="2000",pixType="float",outputStack=None):
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
    SARfilterF.SetParameterOutputImagePixelType("enl",fut.commonPixTypeToOTB(pixType))
    return SARfilterF,inImg,outcore
    
def CreateMultitempFilteringOutcore(inImg,outImg,winRad,ram="2000",pixType="float"):
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
    SARfilter.SetParameterOutputImagePixelType("oc",fut.commonPixTypeToOTB(pixType))
    return SARfilter
 
 
 
