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

import argparse
import os
import shutil
from config import Config
import fileUtils as fu
import serviceConfigFile as SCF
from Utils import run

def getModelinClassif(item):
    return item.split("_")[-3]

def getModelinMASK(item):
    return item.split("_")[-2]

def gen_MaskRegionByTile(fieldRegion, Stack_ind, workingDir, currentTile, AllModel, shpRName, pathToImg, pathTest, pathWd, pathToConfig):
    modelTile = []
    for path in AllModel:
        #tiles = path.replace(".txt","").split("/")[-1].split("_")[2:len(path.split("/")[-1].split("_"))-2]
        currentModel = path.split("/")[-1].split("_")[1]
        tiles = fu.getListTileFromModel(currentModel, pathToConfig)
        model = path.split("/")[-1].split("_")[1]
        seed = path.split("/")[-1].split("_")[-1].replace(".txt", "")
        for tile in tiles:
            #get the model which learn the current tile
            if tile == currentTile:
                modelTile.append(model)
            pathToFeat = pathToImg+"/"+tile+"/Final/"+Stack_ind
            maskSHP = pathTest+"/shapeRegion/"+shpRName+"_region_"+model+"_"+tile+".shp"
            maskTif = workingDir+"/"+shpRName+"_region_"+model+"_"+tile+"_NODATA.tif"
            maskTif_f = pathTest+"/classif/MASK/"+shpRName+"_region_"+model+"_"+tile+"_NODATA.tif"
            #Création du mask
            if not os.path.exists(maskTif_f):
                cmdRaster = "otbcli_Rasterization -in "+maskSHP+" -mode attribute -mode.attribute.field "+fieldRegion+" -im "+pathToFeat+" -out "+maskTif

                run(cmdRaster)
                if pathWd != None:
                    cmd = "cp "+maskTif+" "+pathTest+"/classif/MASK"
                    run(cmd)
    return modelTile

def concatClassifs_OneTile(pathWd, seed, currentTile, pathTest, modelTile, concatOut):

    classifFusion = []

    for model in modelTile:
        classifFusion.append(pathTest+"/classif/Classif_"+currentTile+"_model_"+model+"_seed_"+str(seed)+".tif")

    if len(classifFusion) == 1:
        cmd = "cp "+classifFusion[0]+" "+concatOut
        run(cmd)
    else:
        classifFusion_sort = sorted(classifFusion, key=getModelinClassif)#in order to match images and their mask
        stringClFus = " ".join(classifFusion_sort)
        pathToDirectory = pathTest+"/classif/"
        if pathWd != None:
            pathToDirectory = pathWd

        cmd = "otbcli_ConcatenateImages -ram 128 -il "+stringClFus+" -out "+pathToDirectory+"/"+concatOut.split("/")[-1]
        run(cmd)

        if not os.path.exists(concatOut):
            cmd = "cp "+pathWd+"/"+concatOut.split("/")[-1]+" "+pathTest+"/classif"
            run(cmd)

    return concatOut

def concatRegion_OneTile(currentTile, pathTest, classifFusion_mask, pathWd, TileMask_concat):

    #TileMask_concat = pathTest+"/classif/"+currentTile+"_MASK.tif"
    if len(classifFusion_mask) == 1 and not os.path.exists(TileMask_concat):
        shutil.copy(classifFusion_mask[0], TileMask_concat)
    elif len(classifFusion_mask) != 1 and not os.path.exists(TileMask_concat):
        classifFusion_MASK_sort = sorted(classifFusion_mask, key=getModelinMASK)#in order to match images and their mask
        stringClFus = " ".join(classifFusion_MASK_sort)

        pathDirectory = pathTest+"/classif"
        if pathWd != None:
            pathDirectory = pathWd
        cmd = "otbcli_ConcatenateImages -ram 128 -il "+stringClFus+" -out "+pathDirectory+"/"+TileMask_concat.split("/")[-1]
        run(cmd)

        if pathWd != None:
            cmd = "cp "+pathWd+"/"+TileMask_concat.split("/")[-1]+" "+pathTest+"/classif"
            run(cmd)
    return TileMask_concat

def buildConfidenceExp(imgClassif_FUSION, imgConfidence, imgClassif):
    """
    IN :
        imgClassif_FUSION [string] : path to the classification merged with or without pixels with no label
        imgConfidence [list string] : paths to confidence map
        imgClassif [list string] : paths to images of classifications

    OUT :
        exp [string] : Mathematical expression
        il [string] : input img list to give to otbcli_BandMath

    /!\ the list of images of classifications and the list of confidence map must have the same order.
        example :
            classif = ["cl1","cl2","cl3","cl4"]
            confidences = ["c1","c2","c3","c4"]

            'c1' must be the confidence map of the classification 'cl1' etc...
    """

    if len(imgConfidence) != len(imgClassif):
        raise Exception("Error, the list of classification and the list of confidence map must have the same length")
    im_conf = []
    im_class = []
    im_ref = "im"+str(2*len(imgConfidence)+1)+"b1"

    for i in range(len(imgConfidence)):
        im_conf.append("im"+str(i+1)+"b1")
    for i in range(len(imgConfidence), 2*len(imgConfidence)):
        im_class.append("im"+str(i+1)+"b1")

    #(c1>c2 and c1>c3 and c1>c4)?cl1:(c2>c1 and c2>c3 and c2>c4)?cl2:etc...
    #(c1>c2)?cl1:(c2>c1)?:cl2:0
    exp = im_ref+"!=0?"+im_ref+":"
    for i in range(len(im_conf)):
        tmp = []
        for j in range(len(im_conf)):
            if (im_conf[i] != im_conf[j]):
                tmp.append(im_conf[i]+">"+im_conf[j])
        exp_tmp = " and ".join(tmp)
        exp += "("+exp_tmp+")?"+im_class[i]+":"

    exp += im_class[0]

    #build images list
    il = ""
    for i in range(len(imgConfidence)):
        il += " "+imgConfidence[i]
    for i in range(len(imgClassif)):
        il += " "+imgClassif[i]
    il += " "+imgClassif_FUSION

    return exp, il

def getNbsplitShape(model, configModelPath):

    """
    allShape = fu.fileSearchRegEx(pathToShapes+"/*_region_"+model+"f*.shp")
    splits = []
    for shape in allShape:
        split = shape.split("/")[-1].split("_")[2].split("f")[-1]
        splits.append(split)
    return int(max(splits))
    """
    from config import Config
    cfg = Config(configModelPath)
    fold = []
    for model_tile in cfg.AllModel:
        model_name = model_tile.modelName
        if model_name.split("f")[0] == model and len(model_name.split("f")) > 1:
            fold.append(int(model_name.split("f")[-1]))
    return max(fold)

def noData(pathTest, pathFusion, fieldRegion, pathToImg, pathToRegion, N, cfg, pathWd):

    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    pathConf = cfg.pathConf
    Stack_ind = fu.getFeatStackName(pathConf)

    noLabelManagement = cfg.getParam('argClassification', 'noLabelManagement')
    outputPath = cfg.getParam('chain', 'outputPath')
    modeClassif = cfg.getParam('chain', 'mode')
    pixType = cfg.getParam('argClassification', 'pixType')

    if modeClassif == "outside":
        currentmodel = pathFusion.split("/")[-1].split("_")[3]
        config_model = os.path.join(outputPath, "config_model", "configModel.cfg")
        Nfold = getNbsplitShape(currentmodel, config_model)

    pathDirectory = pathTest+"/classif"
    if pathWd != None:
        workingDir = pathWd
        pathDirectory = pathWd
    else:
        workingDir = pathTest+"/classif/MASK"

    currentTile = pathFusion.split("/")[-1].split("_")[0]

    shpRName = pathToRegion.split("/")[-1].replace(".shp", "")
    AllModel = fu.FileSearch_AND(pathTest+"/model", True, "model", ".txt")
    if modeClassif != "outside":
        modelTile = gen_MaskRegionByTile(fieldRegion, Stack_ind, workingDir, currentTile, AllModel, shpRName, pathToImg, pathTest, pathWd, outputPath+"/config_model/configModel.cfg")
    elif modeClassif == "outside" and noLabelManagement == "maxConfidence":
        modelTile = pathFusion.split("/")[-1].split("_")[3]
    elif modeClassif == "outside" and noLabelManagement == "learningPriority":
        modelTile_tmp = pathFusion.split("/")[-1].split("_")[3]
        modelTile = []
        for i in range(Nfold):
            modelTile.append(modelTile_tmp+"f"+str(i+1))

    if len(modelTile) == 0 or noLabelManagement == "maxConfidence":
        seed = os.path.split(pathFusion)[-1].split("_")[-1].split(".")[0]
        imgConfidence = fu.FileSearch_AND(pathTest+"/classif", True, "confidence_seed_"+str(seed)+".tif", currentTile)
        imgClassif = fu.FileSearch_AND(pathTest+"/classif", True, "Classif_"+currentTile, "seed_"+str(seed))
        imgData = pathDirectory+"/"+currentTile+"_FUSION_NODATA_seed"+str(seed)+".tif"
        if modeClassif == "outside":
            imgConfidence = fu.fileSearchRegEx(pathTest+"/classif/"+currentTile+"_model_"+modelTile+"f*_confidence_seed_"+str(seed)+".tif")
            imgClassif = fu.fileSearchRegEx(pathTest+"/classif/Classif_"+currentTile+"_model_"+modelTile+"f*_seed_"+str(seed)+".tif")
            imgData = pathDirectory+"/Classif_"+currentTile+"_model_"+modelTile+"_seed_"+str(seed)+".tif"
        imgConfidence.sort()
        imgClassif.sort()
        exp, il = buildConfidenceExp(pathFusion, imgConfidence, imgClassif)
        cmd = "otbcli_BandMath -il "+il+" -out "+imgData+' '+pixType+' -exp "'+exp+'"'
        run(cmd)
        if pathWd != None:
            run("cp "+imgData+" "+pathTest+"/classif")

    elif len(modelTile) != 0 and noLabelManagement == "learningPriority":
        #Concaténation des classifications pour une tuile (qui a ou non plusieurs régions) et Concaténation des masques de régions pour une tuile (qui a ou non plusieurs régions)
        seed = os.path.split(pathFusion)[-1].split("_")[-1].split(".")[0]
        concatOut = pathTest+"/classif/"+currentTile+"_FUSION_concat_seed"+str(seed)+".tif"
        if modeClassif == "outside":
            concatOut = pathTest+"/classif/"+currentTile+"_FUSION_model_"+modelTile[0].split("f")[0]+"concat_seed"+str(seed)+".tif"
        pathToClassifConcat = concatClassifs_OneTile(pathWd, seed, currentTile, pathTest, modelTile, concatOut)

        pattern_mask = "*region_*_"+currentTile+"_NODATA.tif"
        classifFusion_mask = fu.fileSearchRegEx(pathTest+"/classif/MASK/"+pattern_mask)
        outConcat_mask = pathTest+"/classif/"+currentTile+"_MASK.tif"
        if modeClassif == "outside":
            pattern_mask = "*region_"+modelTile[0].split("f")[0]+"_"+currentTile+".tif"
            classifFusion_mask_tmp = fu.fileSearchRegEx(pathTest+"/classif/MASK/"+pattern_mask)
            outConcat_mask = pathTest+"/classif/"+currentTile+"_MASK_model_"+modelTile[0].split("f")[0]+".tif"
            classifFusion_mask = []
            for i in range(Nfold):
                classifFusion_mask.append(classifFusion_mask_tmp[0])

        pathToRegionMaskConcat = concatRegion_OneTile(currentTile, pathTest, classifFusion_mask, pathWd, outConcat_mask)

        #construction de la commande
        exp = ""
        im1 = pathFusion
        im2 = pathToRegionMaskConcat
        im3 = pathToClassifConcat

        for i in range(len(classifFusion_mask)):
            if i+1 < len(classifFusion_mask):
                exp = exp+"im2b"+str(i+1)+">=1?im3b"+str(i+1)+":"
            else:
                exp = exp+"im2b"+str(i+1)+">=1?im3b"+str(i+1)+":0"
        exp = "im1b1!=0?im1b1:("+exp+")"

        imgData = pathDirectory+"/"+currentTile+"_FUSION_NODATA_seed"+str(seed)+".tif"
        if modeClassif == "outside":
            imgData = pathDirectory+"/Classif_"+currentTile+"_model_"+modelTile[0].split("f")[0]+"_seed_"+str(seed)+".tif"

        cmd = 'otbcli_BandMath -il '+im1+' '+im2+' '+im3+' -out '+imgData+' '+pixType+' -exp '+'"'+exp+'"'
        run(cmd)

        if pathWd != None:
            run("cp "+imgData+" "+pathTest+"/classif")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="This function creates the jobArray.pbs for extractData")
    parser.add_argument("-test.path", help="Test's path", dest="pathTest", required=True)
    parser.add_argument("-tile.fusion.path", help="path to the classification's images (with fusion)", dest="pathFusion", required=True)
    parser.add_argument("-region.field", dest="fieldRegion", help="region field into region shape", required=True)
    parser.add_argument("-path.img", dest="pathToImg", help="path where all images are stored", required=True)
    parser.add_argument("-path.region", dest="pathToRegion", help="path to the global region shape", required=True)
    parser.add_argument("-N", dest="N", help="number of random sample(mandatory)", type=int, required=True)
    parser.add_argument("-conf", help="path to the configuration file which describe the learning method (mandatory)", dest="pathConf", required=True)
    parser.add_argument("--wd", dest="pathWd", help="path to the working directory", default=None, required=False)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)

    noData(args.pathTest, args.pathFusion, args.fieldRegion, args.pathToImg,
           args.pathToRegion, args.N, cfg, args.pathWd)
