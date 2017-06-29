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
import os,argparse
from osgeo import gdal
from osgeo.gdalconst import *
import fileUtils as fu
import shutil
from config import Config

from vectorSampler import gapFillingToSample

def buildExpression_cloud(Path_Mask):
	
	ds = gdal.Open(Path_Mask, GA_ReadOnly)
	bands = ds.RasterCount

	exp = "-".join(["im1b"+str(band+1) for band in range(bands)])
	return str(bands)+"-"+exp
	
def getLineNumberInFiles(fileList):
        
    nbLine = 0
    for currentFile in fileList :
        with open(currentFile,'r') as currentF:
                for line in currentF:
                        nbLine+=1
    return nbLine

def computeNbView(tile,workingDirectory,pathConf,outputRaster,tilePath):
    
    print "Computing pixel validity by tile"
    tilesStackDirectory = workingDirectory+"/"+tile+"_STACK"
    if not os.path.exists(tilesStackDirectory) : os.mkdir(tilesStackDirectory)
    AllRefl,AllMask,datesInterp,realDates = gapFillingToSample("trainShape","samplesOptions",\
                                                               tilesStackDirectory,"samples",\
                                                               "dataField",tilesStackDirectory,tile,\
                                                               pathConf,wMode=False,onlySensorsMasks=True)
    if not os.path.exists(tilePath+"/tmp") : 
        fu.copyanything(tilesStackDirectory+"/"+tile+"/tmp",tilePath+"/tmp")
    if not os.path.exists(tilePath+"/Final") :
        fu.copyanything(tilesStackDirectory+"/"+tile+"/Final",tilePath+"/Final")

    for currentMask in AllMask : currentMask[0].Execute()
    concat = fu.CreateConcatenateImagesApplication(AllMask,pixType='uint8',wMode=False,output="")
    concat.Execute()
    nbRealDates = getLineNumberInFiles(realDates)
    print "Number of real dates : "+str(nbRealDates)
    expr = str(nbRealDates)+"-"+"-".join(["im1b"+str(band+1) for band in range(nbRealDates)])
    nbView = fu.CreateBandMathApplication(imagesList=(concat,AllMask),exp=expr,ram='2500',pixType='uint8',wMode=True,output=outputRaster)
    nbView.ExecuteAndWriteOutput()

def genNbView(TilePath,maskOut,nbview,pathConf,workingDirectory = None):
	"""
	"""
        allTiles = (Config(file(pathConf)).chain.listTile).split()
        tile = fu.findCurrentTileInString(TilePath,allTiles)

	nameNbView = "nbView.tif"
	wd = TilePath
	if workingDirectory:wd = workingDirectory
	tilePixVal = wd+"/"+nameNbView

        if not os.path.exists(TilePath):os.mkdir(TilePath)

	if not os.path.exists(TilePath+"/"+nameNbView):

		tmp2 = maskOut.replace(".shp","_tmp_2.tif").replace(TilePath,wd)
                computeNbView(tile,workingDirectory,pathConf,tilePixVal,TilePath)
		cmd = 'otbcli_BandMath -il '+tilePixVal+' -out '+tmp2+' -exp "im1b1>='+str(nbview)+'?1:0"'
		print cmd
		os.system(cmd)
	
		maskOut_tmp = maskOut.replace(".shp","_tmp.shp").replace(TilePath,wd)
		cmd = "gdal_polygonize.py -mask "+tmp2+" "+tmp2+" -f \"ESRI Shapefile\" "+maskOut_tmp
		print cmd
		os.system(cmd)
		fu.erodeShapeFile(maskOut_tmp,wd+"/"+maskOut.split("/")[-1],0.1)
	
		os.remove(tmp2)
		fu.removeShape(maskOut_tmp.replace(".shp",""),[".prj",".shp",".dbf",".shx"])
	
		if workingDirectory:
			shutil.copy(tilePixVal,TilePath)
			fu.cpShapeFile(wd+"/"+maskOut.split("/")[-1].replace(".shp",""),TilePath,[".prj",".shp",".dbf",".shx"],spe=True)

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This funtion compute a shapeFile which is the representation of availaible pixels")
	parser.add_argument("-path.features",help ="path to the folder which contains features (mandatory)",dest = "tileMaskPath",required=True)
	parser.add_argument("-out",help ="output shapeFile",dest = "maskOut",required=True)
	parser.add_argument("-nbview",help ="nbview threshold",dest = "nbview",required=True)
	parser.add_argument("--wd",dest = "workingDirectory",help ="path to the working directory",default=None,required=False)
	args = parser.parse_args()

	genNbView(args.tileMaskPath,args.maskOut,args.nbview,args.workingDirectory)










































