#!/usr/bin/python
#-*- coding: utf-8 -*-
# =========================================================================
#   Program:   S1Processor
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
#
# Authors: Thierry KOLECK (CNES)
#
# =========================================================================
# 
# This software build temporal series of S1 images by tiles
# It performs the following steps:
#   1- Download S1 images from PEPS server
#   2- Calibrate the S1 images to gamma0
#   3- Orthorectify S1 images and cut their on geometric tiles
#   4- Concatenante images from the same orbit on the same tile
#   5- Build mask files
#   6- Filter images by using a multiimage filter
#
# Parameters have to be set by the user in the S1Processor.cfg file
#
# =========================================================================

import os
from osgeo import osr
import sys
import S1FileManager
import S1FilteringProcessor
import otbAppli,ast
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from osgeo.gdalconst import *

def getRasterProjectionEPSG(FileName):
	SourceDS = gdal.Open(FileName, GA_ReadOnly)
   	Projection = osr.SpatialReference()
	Projection.ImportFromWkt(SourceDS.GetProjectionRef())
	ProjectionCode = Projection.GetAttrValue("AUTHORITY", 1)
	return ProjectionCode
    
def getRasterExtent(raster_in):
	"""
		Get raster extent of raster_in from GetGeoTransform()
		ARGs:
			INPUT:
				- raster_in: input raster
			OUTPUT
				- ex: extent with [minX,maxX,minY,maxY]
	"""
	if not os.path.isfile(raster_in):
		return []
	raster = gdal.Open(raster_in, GA_ReadOnly)
	if raster is None:
		return []
	geotransform = raster.GetGeoTransform()
	originX = geotransform[0]
	originY = geotransform[3]
	spacingX = geotransform[1]
	spacingY = geotransform[5]
	r, c = raster.RasterYSize, raster.RasterXSize
	
	minX = originX
	maxY = originY
	maxX = minX + c*spacingX
	minY = maxY + r*spacingY
	
	return [minX,maxX,minY,maxY]
    
def FileSearch_AND(PathToFolder,AllPath,*names):

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
			flag=0
			for name in names:
				if files[i].count(name)!=0 and files[i].count(".aux.xml")==0:
					flag+=1
			if flag == len(names):
				if not AllPath:
       					out.append(files[i].split(".")[0])
				else:
					pathOut = path+'/'+files[i]
       					out.append(pathOut)
	return out
    
def getOrigin(manifest):    
    with open(manifest,"r") as saveFile:
        for line in saveFile:
            if "<gml:coordinates>" in line:
                coor = line.replace("                <gml:coordinates>","").replace("</gml:coordinates>","").split(" ")
                coord = [(float(val.replace("\n","").split(",")[0]),float(val.replace("\n","").split(",")[1]))for val in coor]
                return coord[0],coord[1],coord[2],coord[3]
    raise Exception("Coordinates not found in "+str(manifest))

def getOrbitDirection(manifest):
    with open(manifest,"r") as saveFile:
        for line in saveFile:
            if "<s1:pass>" in line:
                if "DESCENDING" in line:
                    return "DES"
                if "ASCENDING" in line:
                    return "ASC"
        return ""
        raise Exception("Orbit Directiction not found in "+str(manifest))

def converCoord(tupleList,inEPSG,OutEPSG):
    
    tupleOut = []
    for inCoord in tupleList:
        lon = inCoord[0]
        lat = inCoord[1]

        inSpatialRef = osr.SpatialReference()
        inSpatialRef.ImportFromEPSG(inEPSG)
        outSpatialRef = osr.SpatialReference()
        outSpatialRef.ImportFromEPSG(OutEPSG)

        coordTrans = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)
        coord = coordTrans.TransformPoint(lon,lat)
        tupleOut.append(coord)
    return tupleOut

def getDateFromS1Raster(PathToRaster):
    return PathToRaster.split("/")[-1].split("-")[4]

def getPolarFromS1Raster(PathToRaster):
    return PathToRaster.split("/")[-1].split("-")[3]

def getPlatformFromS1Raster(PathToRaster):
    return PathToRaster.split("/")[-1].split("-")[0]

    
class Sentinel1_PreProcess(object):

    def __init__(self,configFile):
        import ConfigParser

        config = ConfigParser.ConfigParser()
        config.read(configFile)
        try:
            os.remove("S1ProcessorErr.log.log")
            os.remove("S1ProcessorOut.log")
        except:
           pass
        self.wMode =  ast.literal_eval(config.get('Processing','writeTemporaryFiles'))
        self.wMask = ast.literal_eval(config.get('Processing','getMasks'))
        self.outputGrid= config.get('Processing','TilesShapefile')
        self.raw_directory = config.get('Paths','S1Images')
        self.VH_pattern = "measurement/*vh*-???.tiff"
        self.VV_pattern = "measurement/*vv*-???.tiff"
        self.manifest_pattern = "manifest.safe" 
        self.outputPreProcess = config.get('Paths','Output')
        self.SRTM = config.get('Paths','SRTM')
        self.geoid = config.get('Paths','GeoidFile')

        self.gridSpacing = float(config.get('Processing','Orthorectification_gridspacing'))
        self.borderThreshold = float(config.get('Processing','BorderThreshold'))

        self.outSpacialRes = float(config.get('Processing','OutputSpatialResolution'))
        self.NbProcs=int(config.get('Processing','NbParallelProcesses'))
        self.RAMPerProcess=int(config.get('Processing','RAMPerProcess'))

        self.tilesList=[s.strip() for s in config.get('Processing','Tiles').split(",")]
        self.Filtering_activated=config.getboolean('Filtering','Filtering_activated')
        
        self.ManyProjection = ast.literal_eval(config.get('Processing','ManyProjection'))
        if not self.ManyProjection :
            self.referencesFolder = config.get('Processing','ReferencesFolder')
            self.rasterPattern = config.get('Processing','RasterPattern')
        
        self.stdoutfile=open("/dev/null",'w')
        self.stderrfile=open("S1ProcessorErr.log",'a')
        if "logging" in config.get('Processing','Mode'):
            self.stdoutfile=open("S1ProcessorOut.log",'a')
            self.stderrfile=open("S1ProcessorErr.log",'a')
        if "debug" in config.get('Processing','Mode'):
            self.stdoutfile=None
            self.stderrfile=None
        self.calibrationType=config.get('Processing','Calibration')

        self.pepsdownload=config.getboolean('PEPS','Download')
        if self.pepsdownload==True:
            self.pepscommand=config.get('PEPS','Command')

        

    def generateBorderMask(self,AllOrtho):
            print "Generate Mask ..."
            masks = []
            for currentOrtho,_ in AllOrtho:
                outputParameter = otbAppli.getInputParameterOutput(currentOrtho)
                if "vv" not in currentOrtho.GetParameterValue(outputParameter):continue
                workingDirectory = os.path.split(currentOrtho.GetParameterValue(outputParameter))[0]
                nameBorderMask = os.path.split(currentOrtho.GetParameterValue(outputParameter))[1].replace(".tif","_BorderMask.tif")
                nameBorderMaskTMP = os.path.split(currentOrtho.GetParameterValue(outputParameter))[1].replace(".tif","_BorderMask_TMP.tif")
                bandMathMask = os.path.join(workingDirectory,nameBorderMaskTMP)
                currentOrtho_out = currentOrtho
                if self.wMode : currentOrtho_out.GetParameterValue(outputParameter)
                maskBM = otbAppli.CreateBandMathApplication(imagesList=currentOrtho_out,\
                                                            exp="im1b1==0?1:0",ram=str(self.RAMPerProcess),pixType='uint8',\
                                                            output=bandMathMask)
                if self.wMode : maskBM.ExecuteAndWriteOutput()
                else : maskBM.Execute()
                
                borderMaskOut = os.path.join(workingDirectory,nameBorderMask)
                maskBM_out = maskBM
                if self.wMode : maskBM_out.GetParameterValue("out")
                borderMask = otbAppli.CreateBinaryMorphologicalOperation(maskBM,
                                                                        outImg=borderMaskOut,
                                                                        ram=str(self.RAMPerProcess))
                masks.append((borderMask,maskBM))

            return masks               
                
    def doCalibrationCmd(self,rawRaster):
                
        """
        OUT :
        allCmdOrho [list of otb application list to Execute or ExecuteAndWriteOutput]
        allCmdCalib [all dependence to run ortho]
        """
        allCmdCalib = []
        allCmdOrtho = []
        print "Calibration"

        for i in range(len(rawRaster)):
            for image in rawRaster[i].GetImageList():
                calibrate = image.replace(".tiff","_calibrate.tiff")
                image_OK = image.replace(".tiff","_OrthoReady.tiff")
                if os.path.exists(image_OK)==True:
                    continue
                calib = otbAppli.CreateSarCalibration(image,calibrate,ram=str(self.RAMPerProcess))
                if self.wMode : calib.ExecuteAndWriteOutput()
                else : calib.Execute()
                
                allCmdCalib.append(calib)
                calib_out = calib
                if self.wMode : calib_out = calib.GetParameterValue("out")
                
                expression = 'im1b1<'+str(self.borderThreshold)+'?'+str(self.borderThreshold)+':im1b1 '
                orthoRdy = otbAppli.CreateBandMathApplication(imagesList=calib_out,exp=expression,\
                                                              ram=str(self.RAMPerProcess),pixType="float",\
                                                              output=image_OK)
                allCmdOrtho.append(orthoRdy)
        return allCmdOrtho,allCmdCalib

    def doOrthoByTile(self,rasterList,tileName):

        allOrtho = []
        for i in range(len(rasterList)):
            raster,tileOrigin=rasterList[i]
            manifest = raster.getManifest()
            calibrationApplication = rasterList[i][0].GetCalibrationApplication()
            for calib, dep in calibrationApplication:
                image = calib.GetParameterValue("out")
                currentDate = getDateFromS1Raster(image)
                currentPolar = getPolarFromS1Raster(image)
                currentPlatform = getPlatformFromS1Raster(image)
                currentOrbitDirection=getOrbitDirection(manifest)
                outUTMZone=tileName[0:2]
                outUTMNorthern=str(int(tileName[2]>='N'))
                workingDirectory = os.path.join(self.outputPreProcess,tileName)
                if not os.path.exists(workingDirectory):
                    os.makedirs(workingDirectory)
                inEPSG=4326
                outEPSG=32600+int(outUTMZone)
                if not outUTMNorthern=="0":
                    outEPSG=outEPSG+100
                if self.ManyProjection:
                    [(x,y,dummy)] = converCoord([tileOrigin[0]],inEPSG,outEPSG)
                    [(lrx,lry,dummy)] = converCoord([tileOrigin[2]],inEPSG,outEPSG)
                    uniqueProj=None
                    refRaster = None
                else :
                    refRaster = FileSearch_AND(self.referencesFolder+"/T"+tileName,True,self.rasterPattern)[0]
                    print "reference raster found : "+refRaster
                if self.ManyProjection and outUTMNorthern=="1" and y>0:
                    y=y-10000000.
                    lry=lry-10000000.
                if self.ManyProjection and outUTMNorthern=="0" and y<0:
                    y=y+10000000.
                    lry=lry+10000000.

                orthoImageName = currentPlatform+"_"+\
                                 tileName+"_"+\
                                 currentPolar+"_"+\
                                 currentOrbitDirection+"_"+\
                                 currentDate+".tif"
                                
                inputImage = (calib, dep)
                if self.wMode : inputImage = calib.GetParameterValue("out")
                
                orthoRaster = os.path.join(workingDirectory,orthoImageName)
                
                if self.ManyProjection :
                    sizeX = abs(lrx-x)/self.outSpacialRes
                    sizeY = abs(lry-y)/self.outSpacialRes
                    ortho,ortho_dep = otbAppli.CreateOrthoRectification(inputImage,orthoRaster,\
                                    self.RAMPerProcess,self.outSpacialRes,\
                                    -self.outSpacialRes,sizeX,sizeY,\
                                    self.gridSpacing,\
                                    outUTMZone,outUTMNorthern,\
                                    x,y,self.SRTM,self.geoid)
                else : 
                    
                    ortho,ortho_dep = otbAppli.CreateSuperimposeApplication(refRaster,\
                                                                    inputImage,\
                                                                    pixType="float",\
                                                                    interpolator="bco",\
                                                                    ram=self.RAMPerProcess,\
                                                                    outImg=orthoRaster,\
                                                                    eleveDem=self.SRTM,\
                                                                    elevGeoid=self.geoid)
                allOrtho.append((ortho,ortho_dep))
        return allOrtho

    def concatenateImage(self,orthoList,maskList,tile):

        """
        Concatenate Ortho at the same date
        """
        def sortByFirstElem(MyList):
            from collections import defaultdict
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
                
        def findTilesToConcatenate(applicationList):

            """
            OUT:
            listOfList:
            Example [[r1,r2],[r3,r4],... mean
            r1 and r2 must be concatenates together
            same for r3,r4
            """
            concatenate = []
            names = [(currentName.split("_")[-1].split("t")[0],currentName) for currentName in otbAppli.unPackFirst(applicationList)]
                
            names=sortByFirstElem(names)
            toConcat = [rasterList for currentDate,rasterList in names if len(rasterList)>2]
            for dateToConcat in toConcat : 
                tmp=[ (currentRaster.split("_")[2],currentRaster) for currentRaster in dateToConcat]
                tmp=sortByFirstElem(tmp)
                for pol,rasters in tmp:
                    concatenate.append(rasters)
            print "concatenate"
            print concatenate
            print "-----------"
            Filter = []
            for ToConcat in concatenate :
                sat = [CToConcat.split("_")[0] for CToConcat in ToConcat]
                if not sat.count(sat[0]) == len(sat) : 
                    continue
                Filter.append(ToConcat)
                
            return Filter

        def findMasksToConcatenate(maskList):
            concatenate = []
            names = [os.path.split(mask.GetParameterValue("out"))[-1].split("?")[0] for mask,dep in maskList]
            nameDate = [(name.split("_")[4].split("t")[0],name) for name in names]
            nameDate=sortByFirstElem(nameDate)
            
            for date,maskList in nameDate:
                if len(maskList) > 1 :
                    concatenate.append(maskList)
            
            #check if all masks comes from the same satellite
            maskFilter = []
            for masksToConcat in concatenate :
                sat = [CmasksToConcat.split("_")[0] for CmasksToConcat in masksToConcat]
                if not sat.count(sat[0]) == len(sat) : 
                    continue
                maskFilter.append(masksToConcat)
                
            return maskFilter

        print "concatenate"
        allOrtho = []
        allMasks = []
        imageList=[(os.path.split(currentOrtho.GetParameterValue(otbAppli.getInputParameterOutput(currentOrtho)))[-1].split("?")[0],currentOrtho,_) for currentOrtho,_ in orthoList]
        imageList.sort()
        rastersToConcat = findTilesToConcatenate(imageList)
        
        #fill ortho
        for rasters in rastersToConcat:
            tmp=[]
            name = []
            for pol in rasters:
                name.append(pol.replace(".tif",""))
                for currentOrtho,_ in orthoList:
                    outputParameter = otbAppli.getInputParameterOutput(currentOrtho)
                    if pol in currentOrtho.GetParameterValue(outputParameter):
                        if self.wMode == False : tmp.append((currentOrtho,_))
                        else : 
                            tmp.append(currentOrtho.GetParameterValue(otbAppli.getInputParameterOutput(currentOrtho)))
                            
            name = "_".join(name)+".tif"
            outputImage=os.path.join(self.outputPreProcess,tile,name+"?&writegeom=false")
            concatAppli = otbAppli.CreateBandMathApplication(imagesList=tmp,exp="max(im1b1,im2b1)",\
                                                            ram=str(self.RAMPerProcess),pixType="float",\
                                                            output=outputImage)
            allOrtho.append(concatAppli)
                
        for currentOrtho,_ in orthoList:
            outputParameter = otbAppli.getInputParameterOutput(currentOrtho)
            currentName = os.path.split(currentOrtho.GetParameterValue(outputParameter))[-1].split("?")[0]
            if not currentName in [currentRaster for currentRasters in rastersToConcat for currentRaster in currentRasters]:
                allOrtho.append(currentOrtho)
        
        #fill masks
        if not maskList : return allOrtho,[]
        
        masksToConcat = findMasksToConcatenate(maskList)
        for mask in masksToConcat:
            tmp_m = []
            maskName = []
            for dateMask in mask :
                maskName.append(dateMask)
                for currentMask,_ in maskList:
                    if dateMask in currentMask.GetParameterValue("out"):
                        if self.wMode == False : tmp_m.append((currentMask,_))
                        else : tmp_m.append(currentMask.GetParameterValue("out"))
            maskName = "_".join(maskName)+".tif"
            outputImage=os.path.join(self.outputPreProcess,tile,maskName)
            concatAppliM = otbAppli.CreateBandMathApplication(imagesList=tmp_m,exp="max(im1b1,im2b1)",\
                                                            ram=str(self.RAMPerProcess),pixType="uint8",\
                                                            output=outputImage+"?&writegeom=false")
            allMasks.append((concatAppliM,""))
                
        for currentMask,_ in maskList:
            currentName = os.path.split(currentMask.GetParameterValue("out"))[-1].split("?")[0]
            if not currentName in [currentRaster for currentRasters in masksToConcat for currentRaster in currentRasters]:
                allMasks.append((currentMask,_))
                    
        return allOrtho,allMasks
            
         
def filterRasterByTile(rasterList,calibrations,dependence):
    
    def getCalibrateImage(raster,calib,dep):
        calib_f = []
        dep_f = []
        for currentCal,currentDep in zip(calib,dep):
            rasterName = os.path.split(raster)[-1]
            calibName = os.path.split(currentCal.GetParameterValue("out"))[-1]
            if calibName == rasterName.replace(".tiff","_OrthoReady.tiff"):
                calib_f.append(currentCal)
                dep_f.append(currentDep)
        if len(calib_f)>1:raise Exception("problem in SAR detection")
        return calib_f[0],dep_f[0]

    for i in range(len(rasterList)):
        calibrate = []
        for currentRaster in rasterList[i][0].GetImageList():
            calibrate.append(getCalibrateImage(currentRaster,calibrations,dependence))
        rasterList[i][0].SetCalibrationApplication(calibrate)

# Main code

def S1Processor(cfg):
    
    """
    IN
    cfg [string] : path to a configuration file 
    
    OUT [list of otb's applications need to filter SAR images]
        allFiltered,allDependence,allMasksOut,allTile
    
    Example :
    import S1Processor as s1p
    configurationFile = "/mnt/data/home/vincenta/S1/s1chain/s1tiling/S1Processor.cfg"
    allFiltered,allDependence,allMasks,allTile = s1p.S1Processor(configurationFile)

    for CallFiltered,CallDependence,CallMasks,CallTile in zip(allFiltered,allDependence,allMasks,allTile):
        for SARFiltered,a,b,c,d in CallFiltered : SARFiltered.ExecuteAndWriteOutput()
    """
    import S1FileManager
    import ConfigParser

    config = ConfigParser.ConfigParser()
    config.read(cfg)
    wMode =  ast.literal_eval(config.get('Processing','writeTemporaryFiles'))
    wMasks = ast.literal_eval(config.get('Processing','getMasks'))
    stackFlag = ast.literal_eval(config.get('Processing','outputStack'))
    S1chain = Sentinel1_PreProcess(cfg)
    S1FileManager=S1FileManager.S1FileManager(cfg)

    tilesToProcess = []

    AllRequested = False

    tilesSet=set(S1chain.tilesList)

    for tile in tilesSet:
       if tile == "ALL":
          AllRequested = True
          break
       elif S1FileManager.tileExists(tile):
          tilesToProcess.append(tile)
       else:
          print "Tile "+str(tile)+" does not exist, skipping ..."

    # We can not require both to process all tiles covered by downloaded products and and download all tiles
    if AllRequested :
       if S1FileManager.pepsdownload and "ALL" in S1FileManager.ROIbyTiles:
          print "Can not request to download ROI_by_tiles : ALL if Tiles : ALL. Use ROI_by_coordinates or deactivate download instead"
          sys.exit(1)
       else:
          tilesToProcess = S1FileManager.getTilesCoveredByProducts()
          print "All tiles for which more than "+str(100*S1FileManager.tileToProductOverlapRatio)+"% of the surface is covered by products will be produced: "+str(tilesToProcess)

       
    if len(tilesToProcess) == 0:
       print "No existing tiles found, exiting ..."
       sys.exit(1)



    # Analyse SRTM coverage for MGRS tiles to be processed
    srtm_tiles_check = S1FileManager.checkSRTMCoverage(tilesToProcess)

    needed_srtm_tiles = []
    tilesToProcessChecked = []
    # For each MGRS tile to process
    for tile in tilesToProcess:
            # Get SRTM tiles coverage statistics
            srtm_tiles = srtm_tiles_check[tile]
            current_coverage = 0
            current_needed_srtm_tiles = []
            # Compute global coverage
            for (srtm_tile,coverage) in srtm_tiles:
                    current_needed_srtm_tiles.append(srtm_tile)
                    current_coverage+=coverage
            # If SRTM coverage of MGRS tile is enough, process it
            if current_coverage >= 1.: 
                    needed_srtm_tiles+=current_needed_srtm_tiles
                    tilesToProcessChecked.append(tile)
            else:
                    # Skip it
                    print "Tile "+str(tile)+" has insuficient SRTM coverage ("+str(100*current_coverage)+"%), it will not be processed"

                    
    # Remove duplicates
    needed_srtm_tiles=list(set(needed_srtm_tiles))

    print str(S1FileManager.NbImages)+" images to process on "+str(len(tilesToProcessChecked))+" tiles"

    if len(tilesToProcessChecked) == 0:
            print "No tiles to process, exiting ..."
            sys.exit(1)

    print "Required SRTM tiles: "+str(needed_srtm_tiles)

    srtm_ok = True

    for srtm_tile in needed_srtm_tiles:
            tile_path = os.path.join(S1chain.SRTM,srtm_tile)
            if not os.path.exists(tile_path):
                    srtm_ok = False
                    print tile_path+" is missing"

    if not srtm_ok:
            print "Some SRTM tiles are missing, exiting ..."
            sys.exit(1)

    if not os.path.exists(S1chain.geoid):
            print "Geoid file does not exists ("+S1chain.geoid+"), exiting ..."
            sys.exit(1)

    tilesSet=set(tilesToProcessChecked)

    os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = "10"

    calibrations,_ = S1chain.doCalibrationCmd(S1FileManager.getRasterList())
    
    if wMode :
        for currentCalib in calibrations : currentCalib.ExecuteAndWriteOutput()
    else :
        for currentCalib in calibrations : currentCalib.Execute()

    allFiltered = []
    allDependence = []
    allMasksOut = []
    allTile = []
    for i,tile in enumerate(tilesToProcessChecked):
        allMasks_tmp = []
        print "Tile: "+tile+" ("+str(i+1)+"/"+str(len(tilesSet))+")"
        rasterList = S1FileManager.getS1IntersectByTile(tile)
        if len(rasterList) == 0:
            print "No intersections with tile "+str(tile)
            continue
        filterRasterByTile(rasterList,calibrations,_)
        orthoList = S1chain.doOrthoByTile(rasterList,tile)

        if wMode :
            for orthoRDY,_ in orthoList:orthoRDY.ExecuteAndWriteOutput()
        else :
            for orthoRDY,_ in orthoList:orthoRDY.Execute()
            
        masks = None
        if wMasks :
            masks = S1chain.generateBorderMask(orthoList)
            for border,_ in masks:border.Execute()

        allOrtho,allMasks = S1chain.concatenateImage(orthoList,masks,tile)
        
        if wMasks : 
            for currentM,_ in allMasks : 
                allMasks_tmp.append(currentM.GetParameterValue("out").split("?")[0])
                if not os.path.exists(currentM.GetParameterValue("out").split("?")[0]):
                    print "Creating mask : "+currentM.GetParameterValue("out")
                    currentM.ExecuteAndWriteOutput()
            
        if wMode or not stackFlag: 
            for currentOrtho in allOrtho : currentOrtho.ExecuteAndWriteOutput()
        else : 
            for currentOrtho in allOrtho : currentOrtho.Execute()
        
        if S1chain.Filtering_activated==True:
            filtered = S1FilteringProcessor.main(allOrtho,cfg)
            allFiltered.append(filtered)
            
        allDependence.append((allOrtho,calibrations,_,orthoList))
        allMasksOut.append(allMasks_tmp)
        allTile.append(tile)

    return allFiltered,allDependence,allMasksOut,allTile
        
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Usage: "+sys.argv[0]+" config.cfg"
        sys.exit(1)
    cfg = sys.argv[1]
    S1Processor(cfg)
