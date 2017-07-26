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
import sys,os,shutil
from config import Config
import fileUtils as fu
from osgeo import gdal
from osgeo.gdalconst import *

def compareRef(shapeRef,shapeLearn,classif,diff,footprint,workingDirectory, cfg):

    minX,maxX,minY,maxY = fu.getRasterExtent(classif)
    shapeRaster_val=workingDirectory+"/"+shapeRef.split("/")[-1].replace(".shp",".tif")
    shapeRaster_learn=workingDirectory+"/"+shapeLearn.split("/")[-1].replace(".shp",".tif")

    dataField = cfg.getParam('chain', 'dataField')
    spatialRes = int(cfg.getParam('chain', 'spatialResolution'))
    executionMode = cfg.getParam('chain', 'executionMode')

    #Rasterise val
    cmd = "gdal_rasterize -a "+dataField+" -init 0 -tr "+str(spatialRes)+" "+str(spatialRes)+" "+shapeRef+" "+shapeRaster_val+" -te "+str(minX)+" "+str(minY)+" "+str(maxX)+" "+str(maxY)
    print cmd
    os.system(cmd)
    #Rasterise learn
    cmd = "gdal_rasterize -a "+dataField+" -init 0 -tr "+str(spatialRes)+" "+str(spatialRes)+" "+shapeLearn+" "+shapeRaster_learn+" -te "+str(minX)+" "+str(minY)+" "+str(maxX)+" "+str(maxY)
    print cmd
    os.system(cmd)

    #diff val
    diff_val = workingDirectory+"/"+diff.split("/")[-1].replace(".tif","_val.tif")
    cmd_val = 'otbcli_BandMath -il '+shapeRaster_val+' '+classif+' -out '+diff_val+' uint8 -exp "im1b1==0?0:im1b1==im2b1?2:1"'#reference identique -> 2  | reference != -> 1 | pas de reference -> 0
    print cmd_val
    os.system(cmd_val)
    os.remove(shapeRaster_val)

    #diff learn
    diff_learn = workingDirectory+"/"+diff.split("/")[-1].replace(".tif","_learn.tif")
    cmd_learn = 'otbcli_BandMath -il '+shapeRaster_learn+' '+classif+' -out '+diff_learn+' uint8 -exp "im1b1==0?0:im1b1==im2b1?4:3"'#reference identique -> 4  | reference != -> 3 | pas de reference -> 0
    print cmd_learn
    os.system(cmd_learn)
    os.remove(shapeRaster_learn)

    #sum diff val + learn
    diff_tmp = workingDirectory+"/"+diff.split("/")[-1]
    cmd_sum = 'otbcli_BandMath -il '+diff_val+' '+diff_learn+' -out '+diff_tmp+' uint8 -exp "im1b1+im2b1"'
    print cmd_sum
    os.system(cmd_sum)
    os.remove(diff_val)
    os.remove(diff_learn)

    if executionMode == "parallel": 
        shutil.copy(diff_tmp,diff)
        os.remove(diff_tmp)

    return diff

def genConfMatrix(pathClassif, pathValid, N, dataField, pathToCmdConfusion,
                  cfg, pathWd):

    AllCmd = []
    pathTMP = pathClassif+"/TMP"

    pathTest = cfg.getParam('chain', 'outputPath')
    spatialRes = cfg.getParam('chain', 'spatialRes')

    workingDirectory = pathClassif+"/TMP"
    if pathWd:
        workingDirectory = os.getenv('TMPDIR').replace(":","")

    AllTiles = []
    validationFiles = fu.FileSearch_AND(pathValid,True,"_val.shp")
    for valid in validationFiles:
        currentTile = valid.split("/")[-1].split("_")[0]
        try:
            ind = AllTiles.index(currentTile)
        except ValueError:
            AllTiles.append(currentTile)

    for seed in range(N):
        #recherche de tout les shapeFiles par seed, par tuiles pour les fusionner
        for tile in AllTiles:		
            valTile = fu.FileSearch_AND(pathValid,True,tile,"_seed"+str(seed)+"_val.shp")
            fu.mergeVectors("ShapeValidation_"+tile+"_seed_"+str(seed), pathTMP,valTile)
            learnTile = fu.FileSearch_AND(pathValid,True,tile,"_seed"+str(seed)+"_learn.shp")
            fu.mergeVectors("ShapeLearning_"+tile+"_seed_"+str(seed), pathTMP,learnTile)
            pathDirectory = pathTMP
            if pathWd != None:
                pathDirectory = "$TMPDIR"
            cmd = 'otbcli_ComputeConfusionMatrix -in '+pathClassif+'/Classif_Seed_'+str(seed)+'.tif -out '+pathDirectory+'/'+tile+'_seed_'+str(seed)+'.csv -ref.vector.field '+dataField+' -ref vector -ref.vector.in '+pathTMP+'/ShapeValidation_'+tile+'_seed_'+str(seed)+'.shp'
            AllCmd.append(cmd)
            classif = pathTMP+"/"+tile+"_seed_"+str(seed)+".tif"
            diff = pathTMP+"/"+tile+"_seed_"+str(seed)+"_CompRef.tif"
            footprint=pathTest+"/final/Classif_Seed_0.tif"
            compareRef(pathTMP+'/ShapeValidation_'+tile+'_seed_'+str(seed)+'.shp',
                       pathTMP+'/ShapeLearning_'+tile+'_seed_'+str(seed)+'.shp',
                       classif, diff, footprint, workingDirectory, cfg)

    fu.writeCmds(pathToCmdConfusion+"/confusion.txt",AllCmd)

    for seed in range(N):
        AllDiff = fu.FileSearch_AND(pathTMP,True,"_seed_"+str(seed)+"_CompRef.tif")
        diff_seed = pathTest+"/final/diff_seed_"+str(seed)+".tif"
        if pathWd:
            diff_seed = workingDirectory+"/diff_seed_"+str(seed)+".tif"
        fu.assembleTile_Merge(AllDiff,spatialRes,diff_seed,ot="Byte")
        if pathWd:
            shutil.copy(workingDirectory+"/diff_seed_"+str(seed)+".tif",pathTest+"/final/diff_seed_"+str(seed)+".tif")

    return(AllCmd)

if __name__ == "__main__":

    import serviceConfigFile as SCF
    parser = argparse.ArgumentParser(description = "this function create a confusion matrix")
    parser.add_argument("-path.classif",help ="path to the folder which contains classification images (mandatory)",dest = "pathClassif",required=True)
    parser.add_argument("-path.valid",help ="path to the folder which contains validation samples (with priority) (mandatory)",dest = "pathValid",required=True)
    parser.add_argument("-N",dest = "N",help ="number of random sample(mandatory)",required=True,type = int)
    parser.add_argument("-data.field",dest = "dataField",help ="data's field into data shape (mandatory)",required=True)
    parser.add_argument("-confusion.out.cmd",dest = "pathToCmdConfusion",help ="path where all confusion cmd will be stored in a text file(mandatory)",required=True)	
    parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
    parser.add_argument("-conf",help ="path to the configuration file which describe the classification (mandatory)",dest = "pathConf",required=False)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)

    genConfMatrix(args.pathClassif, args.pathValid, args.N, args.dataField,
                  args.pathToCmdConfusion, cfg, args.pathWd)



















































