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
import os,argparse,otbAppli
from osgeo import gdal
from osgeo.gdalconst import *
import fileUtils as fu
import shutil
from config import Config
from Utils import run


from vectorSampler import gapFillingToSample

def buildExpression_cloud(Path_Mask):

    ds = gdal.Open(Path_Mask, GA_ReadOnly)
    bands = ds.RasterCount

    exp = "-".join(["im1b"+str(band+1) for band in range(bands)])
    return str(bands)+"-"+exp
	
def getLineNumberInFiles(fileList):

    nbLine = 0
    for currentFile in fileList:
        with open(currentFile,'r') as currentF:
            for line in currentF:
                nbLine+=1
    return nbLine

def computeNbView(tile, workingDirectory, cfg, outputRaster, tilePath):
    
    print "Computing pixel validity by tile"
    tilesStackDirectory = workingDirectory+"/"+tile+"_STACK"
    if not os.path.exists(tilesStackDirectory):
        os.mkdir(tilesStackDirectory)
    AllRefl,AllMask,datesInterp,realDates = gapFillingToSample("trainShape","samplesOptions",\
                                                               tilesStackDirectory,"samples",\
                                                               "dataField",tilesStackDirectory,tile,\
                                                               cfg, wMode=False,onlySensorsMasks=True)

    if not os.path.exists(tilePath+"/tmp"): 
        os.mkdir(tilePath+"/tmp")
        fu.updateDirectory(tilesStackDirectory+"/"+tile+"/tmp",tilePath+"/tmp")
    if not os.path.exists(tilePath+"/Final"):
        os.mkdir(tilePath+"/Final")
        fu.updateDirectory(tilesStackDirectory+"/"+tile+"/Final",tilePath+"/Final")


    for currentMask in AllMask : currentMask[0].Execute()
    concat = otbAppli.CreateConcatenateImagesApplication({"il" : AllMask,
                                                          "pixType" : 'uint8',
                                                          "out" : ""})
    concat.Execute()
    nbRealDates = getLineNumberInFiles(realDates)
    print "Number of real dates : "+str(nbRealDates)
    expr = str(nbRealDates)+"-"+"-".join(["im1b"+str(band+1) for band in range(nbRealDates)])
    print expr

    nbView = otbAppli.CreateBandMathApplication({"il": (concat,AllMask),
                                                 "exp": expr,
                                                 "ram": '2500',
                                                 "pixType": 'uint8',
                                                 "out": outputRaster})

    dep = [AllRefl,AllMask,datesInterp,realDates,concat]
    return nbView,tilesStackDirectory,dep

def nbViewSAR(tile, cfg, outputRaster):
    
    import otbAppli
    fu.updatePyPath()
    S1Data = cfg.getParam('chain', 'S1Path')
    allTiles = (cfg.getParam('chain', 'listTile')).split()
    
    #launch SAR masks generation
    a,SARmasks,b,c,d = otbAppli.getSARstack(S1Data, tile, allTiles)
    flatMasks = [CCSARmasks for CSARmasks in SARmasks for CCSARmasks in CSARmasks]    
    bmExp = str(len(flatMasks))+"-"+"-".join(["im"+str(date+1)+"b1" for date in range(len(flatMasks))])
    nbView = otbAppli.CreateBandMathApplication({"il": flatMasks,
                                                 "exp": bmExp,
                                                 "ram": '2500',
                                                 "pixType": 'uint8',
                                                 "out": outputRaster})
    dep=[a,b,c,d]
    return nbView,dep

def nbViewOpticalAndSAR(tile, workingDirectory, cfg, outputRaster, tilePath):
    
    
    sarView,sar_ = nbViewSAR(tile, cfg, outputRaster)
    sarView.Execute()
    nbViewOpt,tilesStackDirectory,opt_ = nbViewOptical(tile, workingDirectory,
                                            cfg, outputRaster, tilePath)
    nbViewOpt.Execute()
    
    nbViewSarOpt = otbAppli.CreateBandMathApplication({"il": [(nbViewOpt,opt_),(sarView,sar_)],
                                                       "exp" :"im1b1+im2b1",
                                                       "ram": '2500',
                                                       "pixType": 'uint8',
                                                       "out": outputRaster})
    dep=[opt_,sar_,sarView,nbViewOpt]
    return nbViewSarOpt,tilesStackDirectory,dep
    
def computeNbView(tile, workingDirectory, cfg, outputRaster, tilePath):
    
    print "Computing pixel validity by tile"
    
    sensorList = fu.sensorUserList(cfg)
    
    if not "S1" in sensorList:
        nbView,tilesStackDirectory,_ = nbViewOptical(tile, workingDirectory,
                                         cfg, outputRaster, tilePath)
        nbView.ExecuteAndWriteOutput()
        return tilesStackDirectory
    elif "S1" in sensorList and (len(sensorList)>1):
        nbViewOptSAR,tilesStackDirectory,_ = nbViewOpticalAndSAR(tile,
                                workingDirectory, cfg, outputRaster, tilePath)
        nbViewOptSAR.ExecuteAndWriteOutput()
        return tilesStackDirectory
    else :
        sarView,_ = nbViewSAR(tile, cfg, outputRaster)
        sarView.ExecuteAndWriteOutput()
        return None

def genNbView(TilePath, maskOut, nbview, cfg, workingDirectory = None):
    """
    """
    allTiles = (cfg.getParam('chain', 'listTile')).split()
    tile = fu.findCurrentTileInString(TilePath,allTiles)
    nameNbView = "nbView.tif"
    wd = TilePath
    if workingDirectory:
        wd = workingDirectory
    tilePixVal = wd+"/"+nameNbView
    if not os.path.exists(TilePath):
        os.mkdir(TilePath)
    if not os.path.exists(TilePath+"/"+nameNbView):
        tmp2 = maskOut.replace(".shp","_tmp_2.tif").replace(TilePath,wd)
        tilesStackDirectory = computeNbView(tile, wd, cfg, tilePixVal, TilePath)
        cmd = 'otbcli_BandMath -il '+tilePixVal+' -out '+tmp2+' -exp "im1b1>='+str(nbview)+'?1:0"'
        run(cmd)
        maskOut_tmp = maskOut.replace(".shp","_tmp.shp").replace(TilePath,wd)
        cmd = "gdal_polygonize.py -mask "+tmp2+" "+tmp2+" -f \"ESRI Shapefile\" "+maskOut_tmp
        run(cmd)
        fu.erodeShapeFile(maskOut_tmp,wd+"/"+maskOut.split("/")[-1],0.1)
        os.remove(tmp2)
        fu.removeShape(maskOut_tmp.replace(".shp",""),[".prj",".shp",".dbf",".shx"])
        if workingDirectory:
            shutil.copy(tilePixVal,TilePath)
            fu.cpShapeFile(wd+"/"+maskOut.split("/")[-1].replace(".shp",""),TilePath,[".prj",".shp",".dbf",".shx"],spe=True)
        if tilesStackDirectory:
            shutil.rmtree(tilesStackDirectory)

if __name__ == "__main__":

    import serviceConfigFile as SCF
    parser = argparse.ArgumentParser(description = "This funtion compute a shapeFile which is the representation of availaible pixels")
    parser.add_argument("-path.features",help ="path to the folder which contains features (mandatory)",dest = "tileMaskPath",required=True)
    parser.add_argument("-out",help ="output shapeFile",dest = "maskOut",required=True)
    parser.add_argument("-nbview",help ="nbview threshold",dest = "nbview",required=True)
    parser.add_argument("-conf",help ="path to the configuration file",dest = "pathConf",required=False)
    parser.add_argument("--wd",dest = "workingDirectory",help ="path to the working directory",default=None,required=False)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)
    
    genNbView(args.tileMaskPath, args.maskOut, args.nbview, cfg,
              args.workingDirectory)
