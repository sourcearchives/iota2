#!/usr/bin/python
#-*- coding: utf-8 -*-


import os
import shutil
import logging
import dill
from osgeo import osr
import sys
import ast
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from osgeo.gdalconst import *

from Common import OtbAppBank
import S1FileManager
import S1FilteringProcessor

logger = logging.getLogger(__name__)


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
        self.RAMPerProcess=int(config.get('Processing','RAMPerProcess'))

        self.tilesList=[s.strip() for s in config.get('Processing','Tiles').split(",")]

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


    def generateBorderMask(self,AllOrtho):
            print "Generate Mask ..."
            masks = []
            for currentOrtho,_ in AllOrtho:
                outputParameter = OtbAppBank.getInputParameterOutput(currentOrtho)
                if "vv" not in currentOrtho.GetParameterValue(outputParameter):continue
                workingDirectory = os.path.split(currentOrtho.GetParameterValue(outputParameter))[0]
                nameBorderMask = os.path.split(currentOrtho.GetParameterValue(outputParameter))[1].replace(".tif","_BorderMask.tif")
                nameBorderMaskTMP = os.path.split(currentOrtho.GetParameterValue(outputParameter))[1].replace(".tif","_BorderMask_TMP.tif")
                bandMathMask = os.path.join(workingDirectory,nameBorderMaskTMP)
                currentOrtho_out = currentOrtho
                if self.wMode : currentOrtho_out.GetParameterValue(outputParameter)
                maskBM = OtbAppBank.CreateBandMathApplication({"il": currentOrtho_out,
                                                               "exp": "im1b1<0.0011?1:0",
                                                               "ram": str(self.RAMPerProcess),
                                                               "pixType": 'uint8',
                                                               "out": bandMathMask})
                if self.wMode : maskBM.ExecuteAndWriteOutput()
                else : maskBM.Execute()

                borderMaskOut = os.path.join(workingDirectory,nameBorderMask)
                maskBM_out = maskBM
                if self.wMode : maskBM_out.GetParameterValue("out")
                borderMask = OtbAppBank.CreateBinaryMorphologicalOperation({"in" : maskBM,
                                                                            "out" : borderMaskOut,
                                                                            "ram" : str(self.RAMPerProcess),
                                                                            "pixType" : "uint8",
                                                                            "filter" : "opening",
                                                                            "ballxradius" : 5,
                                                                            "ballyradius" : 5})
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

        for i in range(len(rawRaster)):
            for image in rawRaster[i].GetImageList():
                calibrate = image.replace(".tiff","_calibrate.tiff")
                image_OK = image.replace(".tiff","_OrthoReady.tiff")
                if os.path.exists(image_OK)==True:
                    continue

                calib = OtbAppBank.CreateSarCalibration({"in" : image,
                                                         "out" : calibrate,
                                                         "lut" : "gamma",
                                                         "ram" : str(self.RAMPerProcess)})
                if self.wMode : calib.ExecuteAndWriteOutput()
                else : calib.Execute()

                allCmdCalib.append(calib)
                calib_out = calib
                if self.wMode : calib_out = calib.GetParameterValue("out")

                expression = 'im1b1<'+str(self.borderThreshold)+'?'+str(self.borderThreshold)+':im1b1 '
                orthoRdy = OtbAppBank.CreateBandMathApplication({"il": calib_out,
                                                                 "exp": expression,
                                                                 "ram": str(self.RAMPerProcess),
                                                                 "pixType": "float",
                                                                 "out": image_OK})
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

                    ortho,ortho_dep = OtbAppBank.CreateOrthoRectification({"in" : inputImage,
                                                                           "out" : orthoRaster,
                                                                           "ram" : self.RAMPerProcess,
                                                                           "outputs.spacingx" :self.outSpacialRes,
                                                                           "outputs.spacingy" :-self.outSpacialRes,
                                                                           "outputs.sizex" : sizeX,
                                                                           "outputs.sizey" : sizeY,
                                                                           "opt.gridspacing" : self.gridSpacing,
                                                                           "map.utm.zone" : outUTMZone,
                                                                           "map.utm.northhem" : outUTMNorthern,
                                                                           "outputs.ulx" : x,
                                                                           "outputs.uly" : y,
                                                                           "elev.dem" : self.SRTM,
                                                                           "elev.geoid" : self.geoid,
                                                                           "map" : "utm"})
                else:
                    ortho,ortho_dep = OtbAppBank.CreateSuperimposeApplication({"inr": refRaster,
                                                                               "inm": inputImage,
                                                                               "pixType": "float",
                                                                               "interpolator": "bco",
                                                                               "ram": self.RAMPerProcess,
                                                                               "io.out": orthoRaster,
                                                                               "elev.dem": self.SRTM,
                                                                               "elev.geoid": self.geoid})
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
            names = [(currentName.split("_")[-1].split("t")[0],currentName) for currentName in OtbAppBank.unPackFirst(applicationList)]
            names=sortByFirstElem(names)
            toConcat = [rasterList for currentDate,rasterList in names if len(rasterList)>2]

            for dateToConcat in toConcat :
                tmp=[ (currentRaster.split("_")[2],currentRaster) for currentRaster in dateToConcat]
                tmp=sortByFirstElem(tmp)[::-1]#VV first then VH
                for pol,rasters in tmp:
                    concatenate.append(rasters)
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
        imageList=[(os.path.split(currentOrtho.GetParameterValue(OtbAppBank.getInputParameterOutput(currentOrtho)))[-1].split("?")[0],currentOrtho,_) for currentOrtho,_ in orthoList]
        imageList.sort()
        rastersToConcat = findTilesToConcatenate(imageList)

        #fill ortho
        for rasters in rastersToConcat:
            tmp=[]
            name = []
            for pol in rasters:
                name.append(pol.replace(".tif",""))
                for currentOrtho,_ in orthoList:
                    outputParameter = OtbAppBank.getInputParameterOutput(currentOrtho)
                    if pol in currentOrtho.GetParameterValue(outputParameter):
                        if self.wMode == False : tmp.append((currentOrtho,_))
                        else :
                            tmp.append(currentOrtho.GetParameterValue(OtbAppBank.getInputParameterOutput(currentOrtho)))

            name = "_".join(name)+".tif"
            outputImage=os.path.join(self.outputPreProcess,tile,name+"?&writegeom=false")
            concatAppli = OtbAppBank.CreateBandMathApplication({"il": tmp,
                                                                "exp": "max(im1b1,im2b1)",
                                                                "ram": str(self.RAMPerProcess),
                                                                "pixType": "float",
                                                                "out": outputImage})
            allOrtho.append(concatAppli)
        for currentOrtho,_ in orthoList:
            outputParameter = OtbAppBank.getInputParameterOutput(currentOrtho)
            currentName = os.path.split(currentOrtho.GetParameterValue(outputParameter))[-1].split("?")[0]
            if not currentName in [currentRaster for currentRasters in rastersToConcat for currentRaster in currentRasters]:
                allOrtho.append(currentOrtho)

        #fill masks
        if not maskList:
            return allOrtho,[]

        masksToConcat = findMasksToConcatenate(maskList)

        for mask in masksToConcat:
            tmp_m = []
            maskName = []
            for dateMask in mask :
                maskName.append(dateMask)
                for currentMask,_ in maskList:
                    if dateMask in currentMask.GetParameterValue("out"):
                        if self.wMode == False:
                            tmp_m.append((currentMask,_))
                        else:
                            tmp_m.append(currentMask.GetParameterValue("out"))
            maskName = "_".join([elem.replace(".tif","").replace("_BorderMask", "") for elem in maskName])+"_BorderMask.tif"
            outputImage = os.path.join(self.outputPreProcess, tile, maskName)

            concatAppliM = OtbAppBank.CreateBandMathApplication({"il": tmp_m,
                                                                 "exp": "max(im1b1,im2b1)",
                                                                 "ram": str(self.RAMPerProcess),
                                                                 "pixType": "uint8",
                                                                 "out": outputImage+"?&writegeom=false"})
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
        if len(calib_f)>1:
            print("more than one calibration file found")
        return calib_f[0],dep_f[0]

    for i in range(len(rasterList)):
        calibrate = []
        for currentRaster in rasterList[i][0].GetImageList():
            calibrate.append(getCalibrateImage(currentRaster,calibrations,dependence))
        rasterList[i][0].SetCalibrationApplication(calibrate)

def getS1DateFromMaskName(MaskName):
    """
    """
    posDate = 4
    return os.path.basename(MaskName).split("_")[posDate]


def getDateFromFile(dateFile):
    """
    """
    all_dates = []
    with open(dateFile, "r") as df:
        for line in df:
            all_dates.append(line.rstrip())
    return all_dates


def writeDateFile(out_stack_date, dateList):
    """
    """
    with open(out_stack_date, "w") as new_dateFile:
        for date in dateList:
            new_dateFile.write(date + "\n")


def SAR_floatToInt(filterApplication, nb_bands, RAMPerProcess,
                   outputFormat="uint16", db_min=-25, db_max=3):
    """transform float SAR values to integer
    """
    import math
    from Common import OtbAppBank as otbApp
    min_val = str(10.0 ** (db_min / 10.0))
    max_val = str(10.0 ** (db_max / 10.0))

    min_val_scale = 0
    max_val_scale = "((2^16)-1)"
    if outputFormat  == "uint8":
        max_val_scale = "((2^8)-1)"

    #build expression
    to_db_expression = "10*log10(im1bX)"
    scale_expression = "(({}-{})/({}-{}))*({})+({}-(({}-{})*{})/({}-{}))".format(max_val_scale,
                                                                                 min_val_scale,
                                                                                 db_max, db_min,
                                                                                 to_db_expression,
                                                                                 min_val_scale,
                                                                                 max_val_scale,
                                                                                 min_val_scale,
                                                                                 db_min,
                                                                                 db_max,
                                                                                 db_min)
    scale_max_val = (2 ** 16)-1
    scale_min_val = 0
    threshold_expression = "{0}>{1}?{3}:{0}<{2}?{4}:{5}".format(to_db_expression,
                                                                db_max, db_min,
                                                                scale_max_val,
                                                                scale_min_val,
                                                                scale_expression)


    expression = ";".join([threshold_expression.replace("X", str(i+1)) for i in range(nb_bands)])

    outputPath = filterApplication.GetParameterValue(otbApp.getInputParameterOutput(filterApplication))

    convert = OtbAppBank.CreateBandMathXApplication({"il": filterApplication,
                                                     "out": outputPath,
                                                     "exp": expression,
                                                     "ram": str(RAMPerProcess),
                                                     "pixType": outputFormat})
    return convert


def writeOutputRaster(OTB_App, overwrite=True, workingDirectory=None, logger=logger):
    """
    """
    import shutil
    from Common import OtbAppBank as otbApp

    out_param = otbApp.getInputParameterOutput(OTB_App)
    out_raster = OTB_App.GetParameterValue(out_param)

    launch_write = True
    if os.path.exists(out_raster.split("?")[0]) and not overwrite:
        launch_write = False

    if workingDirectory is None and launch_write:
        OTB_App.ExecuteAndWriteOutput()

    elif launch_write:
        out_raster_dir, out_raster_name = os.path.split(out_raster)
        out_workingDir = os.path.join(workingDirectory, out_raster_name)
        out_workingDir = out_workingDir.split("?")[0]
        OTB_App.SetParameterString(out_param, out_workingDir)
        OTB_App.ExecuteAndWriteOutput()
        shutil.copy(out_workingDir, out_raster.split("?")[0])
        if os.path.exists(out_workingDir.replace(".tif",".geom")):
            shutil.copy(out_workingDir.replace(".tif",".geom"),
                        out_raster.replace(".tif",".geom").split("?")[0])
    if not launch_write:
        logger.info("{} already exists and will not be overwrited".format(out_raster))

    OTB_App = None
    return out_raster


def generateBorderMask(data_img, out_mask, RAMPerProcess=4000):
    """
    """

    threshold = 0.0011
    mask = OtbAppBank.CreateBandMathApplication({"il": data_img,
                                                 "exp": "im1b1<{}?1:0".format(threshold),
                                                 "ram": str(RAMPerProcess),
                                                 "pixType": 'uint8'})
    mask.Execute()
    borderMask = OtbAppBank.CreateBinaryMorphologicalOperation({"in" : mask,
                                                                "out" : out_mask,
                                                                "ram" : str(RAMPerProcess),
                                                                "pixType" : "uint8",
                                                                "filter" : "opening",
                                                                "ballxradius" : 5,
                                                                "ballyradius" : 5})
    dep = mask
    return borderMask, dep


def LaunchSARreprojection(rasterList, refRaster=None, tileName=None, SRTM=None, geoid=None,
                          output_directory=None, RAMPerProcess=None, workingDirectory=None):
    """must be use with multiprocessing.Pool
    """

    def writeOutputRaster_2(OTB_App, overwrite=True, workingDirectory=None, dep=None, logger=logger):
        """
        """
        import shutil
        from Common import OtbAppBank as otbApp

        out_param = otbApp.getInputParameterOutput(OTB_App)
        out_raster = OTB_App.GetParameterValue(out_param)

        launch_write = True
        if os.path.exists(out_raster.split("?")[0]) and not overwrite:
            launch_write = False

        if workingDirectory is None and launch_write:
            OTB_App.ExecuteAndWriteOutput()

        elif launch_write:
            out_raster_dir, out_raster_name = os.path.split(out_raster)
            out_workingDir = os.path.join(workingDirectory, out_raster_name)
            out_workingDir = out_workingDir.split("?")[0]
            OTB_App.SetParameterString(out_param, out_workingDir)
            OTB_App.ExecuteAndWriteOutput()
            shutil.copy(out_workingDir, out_raster.split("?")[0])
            if os.path.exists(out_workingDir.replace(".tif",".geom")):
                shutil.copy(out_workingDir.replace(".tif",".geom"),
                            out_raster.replace(".tif",".geom").split("?")[0])
        if not launch_write:
            logger.info("{} already exists and will not be overwrited".format(out_raster))

        OTB_App = None
        return out_raster

    date_position = 4

    all_superI_vv = []
    all_superI_vh = []
    all_acquisition_date_vv = []
    all_acquisition_date_vh = []
    dates = []
    all_dep = []
    for date_to_Concatenate in rasterList:
        #Calibration + Superimpose
        vv, vh = date_to_Concatenate.GetImageList()
        SAR_directory, SAR_name = os.path.split(vv)
        currentPlatform = getPlatformFromS1Raster(vv)
        manifest = date_to_Concatenate.getManifest()
        currentOrbitDirection = getOrbitDirection(manifest)
        acquisition_date = SAR_name.split("-")[date_position]
        dates.append(acquisition_date)
        calib_vv = OtbAppBank.CreateSarCalibration({"in" : vv,
                                                    "lut" : "gamma",
                                                    "ram" : str(RAMPerProcess)})
        calib_vh = OtbAppBank.CreateSarCalibration({"in" : vh,
                                                    "lut" : "gamma",
                                                    "ram" : str(RAMPerProcess)})
        calib_vv.Execute()
        calib_vh.Execute()
        all_dep.append(calib_vv)
        all_dep.append(calib_vh)
        orthoImageName_vv = "{}_{}_{}_{}_{}".format(currentPlatform,
                                                    tileName,
                                                    "vv",
                                                    currentOrbitDirection,
                                                    acquisition_date)

        super_vv, super_vv_dep = OtbAppBank.CreateSuperimposeApplication({"inr": refRaster,
                                                                          "inm": calib_vv,
                                                                          "pixType": "float",
                                                                          "interpolator": "bco",
                                                                          "ram": RAMPerProcess,
                                                                          "elev.dem": SRTM,
                                                                          "elev.geoid": geoid})
        orthoImageName_vh = "{}_{}_{}_{}_{}".format(currentPlatform,
                                                    tileName,
                                                    "vh",
                                                    currentOrbitDirection,
                                                    acquisition_date)

        super_vh, super_vh_dep = OtbAppBank.CreateSuperimposeApplication({"inr": refRaster,
                                                                          "inm": calib_vh,
                                                                          "pixType": "float",
                                                                          "interpolator": "bco",
                                                                          "ram": RAMPerProcess,
                                                                          "elev.dem": SRTM,
                                                                          "elev.geoid": geoid})
        super_vv.Execute()
        super_vh.Execute()
        all_dep.append(super_vv)
        all_dep.append(super_vh)
        all_superI_vv.append(super_vv)
        all_superI_vh.append(super_vh)

        all_acquisition_date_vv.append(orthoImageName_vv)
        all_acquisition_date_vh.append(orthoImageName_vh)

    all_acquisition_date_vv = "_".join(sorted(all_acquisition_date_vv))
    all_acquisition_date_vh = "_".join(sorted(all_acquisition_date_vh))
    #Concatenate thanks to a BandMath
    vv_exp = ",".join(["im{}b1".format(i+1) for i in range(len(all_superI_vv))])
    vv_exp = "max({})".format(vv_exp)
    SAR_vv = os.path.join(output_directory, all_acquisition_date_vv + ".tif")
    concatAppli_vv = OtbAppBank.CreateBandMathApplication({"il": all_superI_vv,
                                                           "exp": vv_exp,
                                                           "out": SAR_vv,
                                                           "ram": str(RAMPerProcess),
                                                           "pixType": "float"})
    vh_exp = ",".join(["im{}b1".format(i+1) for i in range(len(all_superI_vh))])
    vh_exp = "max({})".format(vh_exp)
    SAR_vh = os.path.join(output_directory, all_acquisition_date_vh + ".tif")
    concatAppli_vh = OtbAppBank.CreateBandMathApplication({"il": all_superI_vh,
                                                           "exp": vh_exp,
                                                           "out": SAR_vh,
                                                           "ram": str(RAMPerProcess),
                                                           "pixType": "float"})

    ortho_path = writeOutputRaster_2(concatAppli_vv, overwrite=False,
                                   workingDirectory=workingDirectory, dep=all_dep)
    ortho_path = writeOutputRaster_2(concatAppli_vh, overwrite=False,
                                   workingDirectory=workingDirectory, dep=all_dep)

    #from the results generate a mask
    super_vv = os.path.join(output_directory, all_acquisition_date_vv + ".tif")
    border_mask = super_vv.replace(".tif", "_BorderMask.tif")
    mask_app, _ = generateBorderMask(super_vv,
                                     border_mask,
                                     RAMPerProcess=RAMPerProcess)
    mask_path = writeOutputRaster(mask_app, overwrite=False,
                                  workingDirectory=workingDirectory)
    mask_path_geom = mask_path.replace(".tif", ".geom")
    if os.path.exists(mask_path_geom):
        os.remove(mask_path_geom)

    return (SAR_vv, SAR_vh)

def concatenateDates(rasterList):
    """from a list of raster, find raster to concatenates (same acquisition date)
    """
    from Common import FileUtils as fut

    date_position = 4
    date_SAR = []
    for raster in rasterList:
        vv, vh = raster.imageFilenamesList
        SAR_directory, SAR_name = os.path.split(vv)
        acquisition_date = SAR_name.split("-")[date_position].split("t")[0]
        date_SAR.append((acquisition_date, raster))
    date_SAR = fut.sortByFirstElem(date_SAR)
    return [tuple(listOfConcatenation) for date, listOfConcatenation in date_SAR]

def splitByMode(rasterList):
    """
    """
    modes = {"s1a":{"ASC":[], "DES":[]},
             "s1b":{"ASC":[], "DES":[]}}
    for raster, coordinates in rasterList:
        manifest = raster.getManifest()
        currentOrbitDirection = getOrbitDirection(manifest)
        currentPlatform = getPlatformFromS1Raster(raster.imageFilenamesList[0])
        modes[currentPlatform][currentOrbitDirection].append(raster)
    return modes["s1a"]["ASC"], modes["s1a"]["DES"], modes["s1b"]["ASC"], modes["s1b"]["DES"]


def getSARDates(rasterList):
    """
    """
    date_position = 4
    dates = []
    for raster in rasterList:
        vv, vh = raster.imageFilenamesList
        SAR_directory, SAR_name = os.path.split(vv)
        acquisition_date = SAR_name.split("-")[date_position]
        dates.append(acquisition_date)
    dates = sorted(dates)
    return dates


def S1PreProcess(cfg, process_tile, workingDirectory=None, getFiltered=False):

    """
    IN
    cfg [string] : path to a configuration file
    process_tile [list] : list of tiles to be processed
    workingDirectory [string] : path to a working directory

    OUT [list of otb's applications need to filter SAR images]
        allFiltered,allDependence,allMasksOut,allTile
    """
    import multiprocessing
    from functools import partial
    import ConfigParser

    import S1FileManager
    from Common import FileUtils as fut

    if process_tile and not isinstance(process_tile, list):
        process_tile = [process_tile]

    config = ConfigParser.ConfigParser()
    config.read(cfg)
    wMode =  ast.literal_eval(config.get('Processing','writeTemporaryFiles'))
    wMasks = ast.literal_eval(config.get('Processing','getMasks'))
    stackFlag = ast.literal_eval(config.get('Processing','outputStack'))
    RAMPerProcess=int(config.get('Processing','RAMPerProcess'))
    S1chain = Sentinel1_PreProcess(cfg)
    S1FileManager = S1FileManager.S1FileManager(cfg)
    try :
        fMode = config.get('Processing','FilteringMode')
    except :
        fMode = "multi"
    tilesToProcess = []

    convert_to_interger = False

    tilesToProcess = [cTile[1:] for cTile in process_tile]

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

    tilesSet=list(tilesToProcessChecked)
    rasterList = [elem for elem, coordinates in S1FileManager.getS1IntersectByTile(tilesSet[0])]
    
    comp_per_date = 2#VV / VH

    tile = tilesToProcessChecked[0]

    allMasks = []
    if workingDirectory:
        workingDirectory = os.path.join(workingDirectory, tile)
        if not os.path.exists(workingDirectory):
            try:
                os.mkdir(workingDirectory)
            except:
                pass

    refRaster = fut.FileSearch_AND(S1chain.referencesFolder+"/T"+tile ,True, S1chain.rasterPattern)[0]

    #get SAR rasters which intersection the tile
    rasterList = S1FileManager.getS1IntersectByTile(tile)
    #split SAR rasters in different groups
    rasterList_s1aASC, rasterList_s1aDES,rasterList_s1bASC, rasterList_s1bDES = splitByMode(rasterList)
    #get detected dates by acquisition mode
    s1_ASC_dates = getSARDates(rasterList_s1aASC + rasterList_s1bASC)
    s1_DES_dates = getSARDates(rasterList_s1aDES + rasterList_s1bDES)

    #find which one as to be concatenate (acquisitions dates are the same)
    rasterList_s1aASC = concatenateDates(rasterList_s1aASC)
    rasterList_s1aDES = concatenateDates(rasterList_s1aDES)
    rasterList_s1bASC = concatenateDates(rasterList_s1bASC)
    rasterList_s1bDES = concatenateDates(rasterList_s1bDES)

    output_directory = os.path.join(S1chain.outputPreProcess, tile)
    if not os.path.exists(output_directory):
        try:
            os.mkdir(output_directory)
        except:
            print "{} already exists".format(output_directory)
    LaunchSARreprojection_prod = partial(LaunchSARreprojection, refRaster=refRaster,
                                         tileName=tile,
                                         geoid=S1chain.geoid,
                                         SRTM=S1chain.SRTM,
                                         output_directory=output_directory,
                                         RAMPerProcess=RAMPerProcess,
                                         workingDirectory=workingDirectory)
    rasterList_s1aASC_reproj = []
    p = multiprocessing.Pool(1)
    rasterList_s1aASC_reproj.append(p.map(LaunchSARreprojection_prod,
                                          rasterList_s1aASC))
    p.terminate()
    p.join()

    rasterList_s1aDES_reproj = []
    p = multiprocessing.Pool(1)
    rasterList_s1aDES_reproj.append(p.map(LaunchSARreprojection_prod,
                                          rasterList_s1aDES))
    p.terminate()
    p.join()

    rasterList_s1bASC_reproj = []
    p = multiprocessing.Pool(1)
    rasterList_s1bASC_reproj.append(p.map(LaunchSARreprojection_prod,
                                          rasterList_s1bASC))
    p.terminate()
    p.join()

    rasterList_s1bDES_reproj = []
    p = multiprocessing.Pool(1)
    rasterList_s1bDES_reproj.append(p.map(LaunchSARreprojection_prod,
                                          rasterList_s1bDES))
    p.terminate()
    p.join()

    rasterList_s1aASC_reproj_flat = [pol for SAR_date in rasterList_s1aASC_reproj[0] for pol in SAR_date]
    rasterList_s1aDES_reproj_flat = [pol for SAR_date in rasterList_s1aDES_reproj[0] for pol in SAR_date]
    rasterList_s1bASC_reproj_flat = [pol for SAR_date in rasterList_s1bASC_reproj[0] for pol in SAR_date]
    rasterList_s1bDES_reproj_flat = [pol for SAR_date in rasterList_s1bDES_reproj[0] for pol in SAR_date]

    allOrtho_path = rasterList_s1aASC_reproj_flat + rasterList_s1aDES_reproj_flat + rasterList_s1bASC_reproj_flat + rasterList_s1bDES_reproj_flat
    
    s1aASC_masks = [s1aASC.replace(".tif", "_BorderMask.tif") for s1aASC in rasterList_s1aASC_reproj_flat if "_vv_" in s1aASC]
    s1aDES_masks = [s1aDES.replace(".tif", "_BorderMask.tif") for s1aDES in rasterList_s1aDES_reproj_flat if "_vv_" in s1aDES]
    s1bASC_masks = [s1bASC.replace(".tif", "_BorderMask.tif") for s1bASC in rasterList_s1bASC_reproj_flat if "_vv_" in s1bASC]
    s1bDES_masks = [s1bDES.replace(".tif", "_BorderMask.tif") for s1bDES in rasterList_s1bDES_reproj_flat if "_vv_" in s1bDES]
    allMasks = s1aASC_masks + s1aDES_masks + s1bASC_masks + s1bDES_masks

    date_tile = {'s1_ASC': s1_ASC_dates,
                 's1_DES': s1_DES_dates}

    #sort detected dates
    for k, v in date_tile.items():
        v.sort()

    #launch outcore generation and prepare mulitemporal filtering
    filtered = S1FilteringProcessor.main(allOrtho_path, cfg,
                                         date_tile, tile)
    allFiltered = []
    allMasksOut = []

    for S1_filtered, a, b in filtered:
        if convert_to_interger:
            S1_filtered.Execute()
            convert = SAR_floatToInt(S1_filtered, comp_per_date * len(date_tile[mode]), RAMPerProcess)
            allFiltered.append(convert)
        else:
            allFiltered.append(S1_filtered)

    allMasksOut.append(allMasks)

    #In order to avoid "TypeError: can't pickle SwigPyObject objects"
    if getFiltered:
        return allFiltered, allMasksOut  
