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

import sys,os,shutil,glob,math,tarfile,re,Sensors,random
from config import Config, Sequence
import numpy as np
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from osgeo.gdalconst import *
from datetime import timedelta, date
import datetime
from collections import defaultdict
import otbApplication as otb
import errno

def cleanFiles(cfgFile):
    """
    remove files which as to be re-computed
    
    IN
    cfgFile [string] configuration file path
    """
    
    import ConfigParser
    S1Path = Config(file(cfgFile)).chain.S1Path
    if "None" in S1Path : S1Path = None
    features = Config(file(cfgFile)).chain.featuresPath
    
    #Remove nbView.tif 
    """
    validity = FileSearch_AND(features,True,"nbView.tif")
    for Cvalidity in validity : 
        if os.path.exists(Cvalidity) : os.remove(Cvalidity)
    """
    #Remove SAR dates files
    if S1Path:
        config = ConfigParser.ConfigParser()
        config.read(S1Path)
        outputDirectory =  config.get('Paths','Output')
        inDates = FileSearch_AND(outputDirectory,True,"inputDates.txt")
        interpDates = FileSearch_AND(outputDirectory,True,"interpolationDates.txt")
        for cDate in inDates : 
            if os.path.exists(cDate):
                os.remove(cDate)
        for cDate in interpDates : 
            if os.path.exists(cDate):
                os.remove(cDate)
            
def sensorUserList(cfgFile):
    
    """
    """
    L5Path = Config(file(cfgFile)).chain.L5Path
    L8Path = Config(file(cfgFile)).chain.L8Path
    S2Path = Config(file(cfgFile)).chain.S2Path
    S1Path = Config(file(cfgFile)).chain.S1Path
    
    sensorList = []
    
    if not "None" in L5Path : sensorList.append("L5")
    if not "None" in L8Path : sensorList.append("L8")
    if not "None" in S2Path : sensorList.append("S2")
    if not "None" in S1Path : sensorList.append("S1")
    
    return sensorList

    
def onlySAR(cfgFile):
    
    """
    return True if only S1 is set in configuration file
    """
    L5Path = Config(file(cfgFile)).chain.L5Path
    L8Path = Config(file(cfgFile)).chain.L8Path
    S2Path = Config(file(cfgFile)).chain.S2Path
    S1Path = Config(file(cfgFile)).chain.S1Path
    
    if "None" in L5Path : L5Path = None
    if "None" in L8Path : L8Path = None
    if "None" in S2Path : S2Path = None
    if "None" in S1Path : S1Path = None
    
    if L5Path or L8Path or S2Path : return False
    else : return True
    
def getCommonMaskName(cfgFile):
    
    L5Path = Config(file(cfgFile)).chain.L5Path
    L8Path = Config(file(cfgFile)).chain.L8Path
    S2Path = Config(file(cfgFile)).chain.S2Path
    S1Path = Config(file(cfgFile)).chain.S1Path
    
    if "None" in L5Path : L5Path = None
    if "None" in L8Path : L8Path = None
    if "None" in S2Path : S2Path = None
    if "None" in S1Path : S1Path = None
    
    #if L5Path or L8Path or S2Path : return "MaskCommunSL"
    #else : return "SARMask"
    if S1Path : return "SARMask"
    else : return "MaskCommunSL"
    
def dateInterval(dateMin,dataMax,tr):
	
    """
    dateMin [string] : Ex -> 20160101
    dateMax [string] > dateMin
    tr [int/string] -> temporal resolution
    """
    start = datetime.date(int(dateMin[0:4]),int(dateMin[4:6]),int(dateMin[6:8]))
    end = datetime.date(int(dataMax[0:4]),int(dataMax[4:6]),int(dataMax[6:8]))
    delta = timedelta(days=int(tr))
    curr = start
    while curr < end:
        yield curr
        curr += delta
        
def updatePyPath():
    moduleDirectoryName = ["SAR"]
    currentDirectory = os.path.dirname(os.path.realpath(__file__))
    for currentModule in moduleDirectoryName : 
        modPath = currentDirectory+"/"+currentModule
        if not modPath in sys.path:
            sys.path.append(modPath)
	
def updateDirectory(src, dst):

    content = os.listdir(src)
    for currentContent in content:
        if os.path.isfile(src+"/"+currentContent):
            if not os.path.exists(dst+"/"+currentContent):
                shutil.copy(src+"/"+currentContent,dst+"/"+currentContent)
        if os.path.isdir(src+"/"+currentContent):
            if not os.path.exists(dst+"/"+currentContent):
                try:
                    shutil.copytree(src+"/"+currentContent, dst+"/"+currentContent)
                except OSError as exc: # python >2.5
                    if exc.errno == errno.ENOTDIR:
                        shutil.copy(src, dst)
                    else: raise

def copyanything(src, dst):
    try:
        shutil.copytree(src, dst)
    except OSError as exc: # python >2.5
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else: raise

def getDateLandsat(pathLandsat,tiles,sensor="Landsat8"):
	"""
        Get the min and max dates for the given tile.
	"""
	dateMin = 30000000000
	dateMax = 0 #JC
	for tile in tiles:

		folder = os.listdir(pathLandsat+"/"+sensor+"_"+tile)
		
   		for i in range(len(folder)):
			if folder[i].count(".tgz")==0 and folder[i].count(".jpg")==0 and folder[i].count(".xml")==0:				
				contenu = os.listdir(pathLandsat+"/"+sensor+"_"+tile+"/"+folder[i])
				for i in range(len(contenu)):
					if contenu[i].count(".TIF")!=0:
						Date = int(contenu[i].split("_")[3])
						if Date > dateMax:
							dateMax = Date
						if Date < dateMin:
							dateMin = Date
	return str(dateMin),str(dateMax)

def getDateL5(pathL5,tiles):
    return getDateLandsat(pathL5, tiles, "Landsat5")

def getDateL8(pathL8,tiles):
    return getDateLandsat(pathL8, tiles, "Landsat8")

def getDateS2(pathS2,tiles):
	"""
        Get the min and max dates for the given tile.
	"""
	datePos = 2
	if "T" in tiles[0]:datePos = 1
	dateMin = 30000000000
	dateMax = 0 #JC
	for tile in tiles:

		folder = os.listdir(pathS2+"/"+tile)
		
   		for i in range(len(folder)):
			if folder[i].count(".tgz")==0 and folder[i].count(".jpg")==0 and folder[i].count(".xml")==0:
				Date = int(folder[i].split("_")[datePos].split("-")[0])
				if Date > dateMax:
					dateMax = Date
				if Date < dateMin:
					dateMin = Date

	return str(dateMin),str(dateMax)

	
def unPackFirst(someListOfList):

    for values in someListOfList:
        if isinstance(values,list) or isinstance(values,tuple):yield values[0]
        else : yield values

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
    try : 
        return dico[string]
    except :
        raise Exception("Error in commonPixTypeToOTB function input parameter : "+string+" not available, choices are :"+\
                        "'complexDouble','complexFloat','double','float','int16','int32','uint16','uint32','uint8'")

def AddStringToFile(myString,writtingFile):

	with open(writtingFile,"a") as f:
		f.write(myString)

def splitList(InList,nbSplit):
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
    		leftovers= ys[size*n:]
    		for c in xrange(n):
       	 		if leftovers:
           			extra= [ leftovers.pop() ] 
        		else:
           			extra= []
        		yield ys[c*size:(c+1)*size] + extra

	splitList = list(chunk(InList,nbSplit))

	#check empty content (if nbSplit > len(Inlist)) 
	All = []
	for splits in splitList:
		for split in splits:
			if not split in All:
				All.append(split)

	for i in range(len(splitList)):
		if len(splitList[i])==0:
			randomChoice = random.sample(All,1)[0]
			splitList[i].append(randomChoice)

	return splitList

def getCurrentSensor(SensorsList,refl):
	for currentSensor in SensorsList:
                if currentSensor.name in refl:
			return currentSensor

def getIndex(listOfTuple,keyVal):
	try : 
		return [item for key,item in listOfTuple].index(keyVal)+1
	except :
		print keyVal+" not in list of bands"
		return []
	

def ExtractInterestBands(stack,nbDates,SPbandsList,comp,ram = 128):

	SB_ToKeep = [ "Channel"+str(int(currentBand)+i*comp) for i in range(nbDates) for currentBand in SPbandsList]
	extract = otb.Registry.CreateApplication("ExtractROI")
	extract.SetParameterString("in",stack)
	if isinstance(stack,str):extract.SetParameterString("in",stack)
    	elif type(stack)==otb.Application:extract.SetParameterInputImage("in",stack.GetParameterOutputImage("out"))

	extract.SetParameterString("ram",str(ram))
	extract.UpdateParameters()
	extract.SetParameterStringList("cl",SB_ToKeep)
	extract.Execute()

	return extract

def iota2FeatureExtractionParameter(otbObject,configPath):

	copyinput = Config(file(configPath)).iota2FeatureExtraction.copyinput
	relrefl = Config(file(configPath)).iota2FeatureExtraction.relrefl
	keepduplicates = Config(file(configPath)).iota2FeatureExtraction.keepduplicates

	if copyinput == "True" : 
		otbObject.SetParameterEmpty("copyinput",True)
	if relrefl == "True" : 
		otbObject.SetParameterEmpty("relrefl",True)
	if keepduplicates == "True" : 
		otbObject.SetParameterEmpty("keepduplicates",True)

	#return otbObject

def keepBiggestArea(shpin,shpout):
	print "compute : "+shpin
	def addPolygon(feat, simplePolygon, in_lyr, out_lyr):
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

def findCurrentTileInString(string,allTiles):
	"""
		IN:
		string [string]: string where we want to found a string in the string list 'allTiles' 
		allTiles [list of strings]

		OUT:
		if there is a unique occurence of a string in allTiles, return this occurence. else, return Exception
	"""
	tileList = [currentTile for currentTile in allTiles if currentTile in string]#must contain same element
	if len(set(tileList))==1:return tileList[0]
	else : raise Exception("more than one tile found into the string :'"+string+"'")

def getUserFeatInTile(userFeat_path,tile,userFeat_arbo,userFeat_pattern):
    """
    IN :
    userFeat_path [string] : path to user features
    tile [string] : current tile
    userFeat_arbo [string] : tree to find features from userFeat_path/tile
    userFeat_pattern [list of strings] : lis of features to find

    OUT :
    list of all features finding in userFeat_path/tile
    """
    allFeat = []
    for currentPattern in userFeat_pattern:
        allFeat+=fileSearchRegEx(userFeat_path+"/"+tile+"/"+userFeat_arbo+currentPattern+"*")
    return allFeat

def getFieldElement(shape,driverName="ESRI Shapefile",field = "CODE",mode = "all",elemType = "int"):
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
	def getElem(elem,elemType):
		if elemType == "int" : return int(elem)
		elif elemType == "str" : return str(elem)
		else:
			raise Exception("elemType must be 'int' or 'str'")
	driver = ogr.GetDriverByName(driverName)
	dataSource = driver.Open(shape, 0)
	layer = dataSource.GetLayer()
	if mode == "all" : return [ getElem(currentFeat.GetField(field),elemType) for currentFeat in layer]
	elif mode == "unique" : return list(set([ getElem(currentFeat.GetField(field),elemType) for currentFeat in layer]))
	else:
		raise Exception("mode parameter must be 'all' or 'unique'")

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

def readRaster(name, data = False, band = 1):

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

    #convert raster to an array
    datas = raster_band.ReadAsArray()

    if data:
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
        raise Exception("can't open "+rasterIn)
    geotransform = raster.GetGeoTransform()
    spacingX = geotransform[1]
    spacingY = geotransform[5]
    return spacingX,spacingY

def assembleTile_Merge(AllRaster,spatialResolution,out,ot="Int16"):
    """
        IN : 
        AllRaster [string] : 
        spatialResolution [int] : 
        out [string] : output path
    
        OUT:
        a mosaic of all images in AllRaster.
        0 values are considered as noData. Usefull for pixel superposition.
    """
    AllRaster = " ".join(AllRaster)
    cmd = "gdal_merge.py -ps "+str(spatialResolution)+" -"+str(spatialResolution)+" -o "+out+" -ot "+ot+" -n 0 "+AllRaster
    print cmd 
    os.system(cmd)

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
    Y = int(vardate[0:4])
    M = int(vardate[4:6])
    D = int(vardate[6:len(vardate)])
    return Y,M,D

def getNbDateInTile(dateInFile,display = True):
    with open(dateInFile) as f:
        for i, l in enumerate(f):
            vardate = l.rstrip()
            try:
                Y,M,D = getDateFromString(vardate)
                validDate = datetime.datetime(int(Y),int(M),int(D))
                if display : print validDate
            except ValueError:
                raise Exception("unvalid date in : "+dateInFile+" -> '"+str(vardate)+"'")
        return i + 1

def getGroundSpacing(pathToFeat,ImgInfo):
    os.system("otbcli_ReadImageInfo -in "+pathToFeat+">"+ImgInfo)
    info = open(ImgInfo,"r")
    while True :
        data = info.readline().rstrip('\n\r')
        if data.count("spacingx: ")!=0:
            spx = data.split("spacingx: ")[-1]
        elif data.count("spacingy:")!=0:
            spy = data.split("spacingy: ")[-1]
            break
    info.close()
    os.remove(ImgInfo)
    return spx,spy

def getRasterProjectionEPSG(FileName):
    SourceDS = gdal.Open(FileName, GA_ReadOnly)
    Projection = osr.SpatialReference()
    Projection.ImportFromWkt(SourceDS.GetProjectionRef())
    ProjectionCode = Projection.GetAttrValue("AUTHORITY", 1)
    return ProjectionCode

def getRasterNbands(raster):
    
    src_ds = gdal.Open(raster)
    if src_ds is None:
        raise Exception(raster+" doesn't exist")
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
    
    if not (isinstance(tmpVar,varType)):
        message = "Variable " + str(variable) + " has a wrong type\nActual: "\
        + str(type(tmpVar)) + " expected: " + str(varType)
        raise Exception (message)
        
    if valeurs != "":
        ok = 0
        for index in range(len(valeurs)):
            if (tmpVar == valeurs[index]):
                ok = 1
        if ok == 0:
            raise Exception("Bad value for " + variable + " variable. Value accepted : " + str(valeurs))

def checkConfigParameters(pathConf):

    """
    IN:
        pathConf [string] : path to a iota2's configuration file.

    check parameters coherence 
    """
    def all_sameBands(items):
        return all(bands == items[0][1] for path,bands in items)

    cfg = Config(file(pathConf))
    # test if a list a variable exist.
    testVarConfigFile(cfg.chain, 'executionMode', str)
    testVarConfigFile(cfg.chain, 'outputPath', str)
    testVarConfigFile(cfg.chain, 'jobsPath', str)
    testVarConfigFile(cfg.chain, 'pyAppPath', str)
    testVarConfigFile(cfg.chain, 'chainName', str)
    testVarConfigFile(cfg.chain, 'nomenclaturePath', str)
    testVarConfigFile(cfg.chain, 'listTile', str)
    testVarConfigFile(cfg.chain, 'featuresPath', str)
    testVarConfigFile(cfg.chain, 'L5Path', str)
    testVarConfigFile(cfg.chain, 'L8Path', str)
    testVarConfigFile(cfg.chain, 'S2Path', str)
    testVarConfigFile(cfg.chain, 'S1Path', str)
    testVarConfigFile(cfg.chain, 'mode', str, ["one_region", "multi_regions", "outside"])
    testVarConfigFile(cfg.chain, 'regionPath', str)
    testVarConfigFile(cfg.chain, 'regionField', str)
    testVarConfigFile(cfg.chain, 'model', str)
    testVarConfigFile(cfg.chain, 'groundTruth', str)
    testVarConfigFile(cfg.chain, 'dataField', str)
    testVarConfigFile(cfg.chain, 'runs', int)
    testVarConfigFile(cfg.chain, 'ratio', float)
    testVarConfigFile(cfg.chain, 'cloud_threshold', int)
    testVarConfigFile(cfg.chain, 'spatialResolution', int)
    testVarConfigFile(cfg.chain, 'logPath', str)
    testVarConfigFile(cfg.chain, 'colorTable', str)
    testVarConfigFile(cfg.chain, 'mode_outside_RegionSplit', str)
    testVarConfigFile(cfg.chain, 'OTB_HOME', str)
    
    testVarConfigFile(cfg.argTrain, 'shapeMode', str, ["polygons", "points"])
    testVarConfigFile(cfg.argTrain, 'samplesOptions', str)
    testVarConfigFile(cfg.argTrain, 'classifier', str)
    testVarConfigFile(cfg.argTrain, 'options', str)
    testVarConfigFile(cfg.argTrain, 'rearrangeModelTile', bool)
    testVarConfigFile(cfg.argTrain, 'rearrangeModelTile_out', str)
    testVarConfigFile(cfg.argTrain, 'cropMix', str, ["True", "False"])
    testVarConfigFile(cfg.argTrain, 'prevFeatures', str)
    testVarConfigFile(cfg.argTrain, 'annualCrop', Sequence)
    testVarConfigFile(cfg.argTrain, 'ACropLabelReplacement', Sequence)
    
    testVarConfigFile(cfg.argClassification, 'classifMode', str, ["separate", "fusion"])
    testVarConfigFile(cfg.argClassification, 'pixType', str)
    testVarConfigFile(cfg.argClassification, 'confusionModel', bool)
    testVarConfigFile(cfg.argClassification, 'noLabelManagement', str, ["maxConfidence", "learningPriority"])
    
    testVarConfigFile(cfg.GlobChain, 'proj', str)
    testVarConfigFile(cfg.GlobChain, 'features', Sequence)
    testVarConfigFile(cfg.GlobChain, 'batchProcessing', str, ["True", "False"])
    
    if cfg.chain.L5Path != "None":
        #L5 variable check
        testVarConfigFile(cfg.Landsat5, 'nodata_Mask', str, ["True", "False"])
        testVarConfigFile(cfg.Landsat5, 'nativeRes', int)
        testVarConfigFile(cfg.Landsat5, 'arbo', str)
        testVarConfigFile(cfg.Landsat5, 'imtype', str)
        testVarConfigFile(cfg.Landsat5, 'nuages', str)
        testVarConfigFile(cfg.Landsat5, 'saturation', str)
        testVarConfigFile(cfg.Landsat5, 'div', str)
        testVarConfigFile(cfg.Landsat5, 'nodata', str)
        testVarConfigFile(cfg.Landsat5, 'arbomask', str)
        testVarConfigFile(cfg.Landsat5, 'startDate', str)
        testVarConfigFile(cfg.Landsat5, 'endDate', str)
        testVarConfigFile(cfg.Landsat5, 'temporalResolution', str)
        testVarConfigFile(cfg.Landsat5, 'keepBands', Sequence)

    if cfg.chain.L8Path != "None":
        #L8 variable check
        testVarConfigFile(cfg.Landsat8, 'nodata_Mask', str, ["True", "False"])
        testVarConfigFile(cfg.Landsat8, 'nativeRes', int)
        testVarConfigFile(cfg.Landsat8, 'arbo', str)
        testVarConfigFile(cfg.Landsat8, 'imtype', str)
        testVarConfigFile(cfg.Landsat8, 'nuages', str)
        testVarConfigFile(cfg.Landsat8, 'saturation', str)
        testVarConfigFile(cfg.Landsat8, 'div', str)
        testVarConfigFile(cfg.Landsat8, 'nodata', str)
        testVarConfigFile(cfg.Landsat8, 'arbomask', str)
        testVarConfigFile(cfg.Landsat8, 'startDate', str)
        testVarConfigFile(cfg.Landsat8, 'endDate', str)
        testVarConfigFile(cfg.Landsat8, 'temporalResolution', str)
        testVarConfigFile(cfg.Landsat8, 'keepBands', Sequence)

    if cfg.chain.S2Path != "None":
        #S2 variable check
        testVarConfigFile(cfg.Sentinel_2, 'nodata_Mask', str)
        testVarConfigFile(cfg.Sentinel_2, 'nativeRes', int)
        testVarConfigFile(cfg.Sentinel_2, 'arbo', str)
        testVarConfigFile(cfg.Sentinel_2, 'imtype', str)
        testVarConfigFile(cfg.Sentinel_2, 'nuages', str)
        testVarConfigFile(cfg.Sentinel_2, 'saturation', str)
        testVarConfigFile(cfg.Sentinel_2, 'div', str)
        testVarConfigFile(cfg.Sentinel_2, 'nodata', str)
        testVarConfigFile(cfg.Sentinel_2, 'nuages_reproj', str)
        testVarConfigFile(cfg.Sentinel_2, 'saturation_reproj', str)
        testVarConfigFile(cfg.Sentinel_2, 'div_reproj', str)
        testVarConfigFile(cfg.Sentinel_2, 'arbomask', str)
        testVarConfigFile(cfg.Sentinel_2, 'temporalResolution', str)
        testVarConfigFile(cfg.Sentinel_2, 'keepBands', Sequence)


    nbTile = len(cfg.chain.listTile.split(" "))
    # test  if path exist
    error=[]
    """
    if "parallel" in cfg.chain.executionMode:
    	if not os.path.exists(cfg.chain.jobsPath):
    		error.append(cfg.chain.jobsPath+" doesn't exist\n")
    	if not os.path.exists(cfg.chain.logPath):
    		error.append(cfg.chain.logPath+" doesn't exist\n")
    """
    if not os.path.exists(cfg.chain.pyAppPath):
        error.append(cfg.chain.pyAppPath+" doesn't exist\n")
    if not os.path.exists(cfg.chain.nomenclaturePath):
        error.append(cfg.chain.nomenclaturePath+" doesn't exist\n")
    if "outside" == cfg.chain.mode :
        if not os.path.exists(cfg.chain.regionPath):
            error.append(cfg.chain.regionPath+" doesn't exist\n")
    if "multi_regions" == cfg.chain.mode :
        if not os.path.exists(cfg.chain.model):
            error.append(cfg.chain.model+" doesn't exist\n")
    
    if not os.path.exists(cfg.chain.groundTruth):
        error.append(cfg.chain.groundTruth+" doesn't exist\n")
    else:
        Field_FType = []
        dataSource = ogr.Open(cfg.chain.groundTruth)
        daLayer = dataSource.GetLayer(0)
        layerDefinition = daLayer.GetLayerDefn()
        for i in range(layerDefinition.GetFieldCount()):
            fieldName =  layerDefinition.GetFieldDefn(i).GetName()
            fieldTypeCode = layerDefinition.GetFieldDefn(i).GetType()
            fieldType = layerDefinition.GetFieldDefn(i).GetFieldTypeName(fieldTypeCode)
            Field_FType.append((fieldName,fieldType))
        flag = 0
        for currentField,fieldType in Field_FType:
            if currentField == cfg.chain.dataField:
                flag = 1
                if not "Integer" in fieldType:
                    error.append("the data's field must be an integer'\n")
        if flag == 0:
            error.append("field name '"+cfg.chain.dataField+"' doesn't exist\n")

    if not os.path.exists(cfg.chain.colorTable):
        error.append(cfg.chain.colorTable+" doesn't exist\n")
    if not os.path.exists(cfg.chain.OTB_HOME+"/config_otb.sh"):
        error.append(cfg.chain.OTB_HOME+"/config_otb.sh doesn't exist\n")
    if cfg.argTrain.cropMix == "True":
        if not os.path.exists(cfg.argTrain.prevFeatures):
            error.append(cfg.argTrain.prevFeatures+" doesn't exist\n")
        if not cfg.argTrain.shapeMode == "points":
            error.append("you must use 'points' mode with 'cropMix' mode\n")
    if (cfg.chain.mode != "one_region") and (cfg.chain.mode != "multi_regions") and (cfg.chain.mode != "outside"):
        error.append("'mode' must be 'one_region' or 'multi_regions' or 'outside'\n")
    if cfg.chain.mode == "one_region" and cfg.argClassification.classifMode == "fusion":
        error.append("you can't chose 'one_region' mode and ask a fusion of classifications\n")
    if nbTile == 1 and cfg.chain.mode == "multi_regions":
        error.append("only one tile detected with mode 'multi_regions'\n")
    if cfg.argTrain.shapeMode == "points":
        if ("-sample.mt" or "-sample.mv" or "-sample.bm" or "-sample.vtr") in cfg.argTrain.options:
            error.append("wrong options passing in classifier argument see otbcli_TrainVectorClassifier's documentation\n")

    #if features has already compute, check if they have the same number of bands
    if os.path.exists(cfg.chain.featuresPath ):
        stackName = getFeatStackName(pathConf)
        cfg.GlobChain.features = FileSearch_AND(cfg.chain.featuresPath,True,stackName)
        if cfg.GlobChain.features:
            featuresBands = [(currentRaster,getRasterNbands(currentRaster)) for currentRaster in cfg.GlobChain.features]
            if not all_sameBands(featuresBands):
                error.append([ currentRaster+" bands : "+str(rasterBands)+"\n" for currentRaster,rasterBands in featuresBands])
    if len(error)>=1:
        errorList = "".join(error)
        raise Exception("\n"+errorList)

def multiSearch(shp,ogrDriver='ESRI Shapefile'):
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
    for in_feat in in_lyr:
        geom = in_feat.GetGeometryRef()
        if geom.GetGeometryName() == 'MULTIPOLYGON':
        return True
    return False

def getAllFieldsInShape(vector,driver='ESRI Shapefile'):

	"""
		IN :
		vector [string] : path to vector file
		driver [string] : gdal driver

		OUT :
		[list of string] : all fields in vector
	"""
	driver = ogr.GetDriverByName(driver)
	dataSource = driver.Open(vector, 0)
	if dataSource is None: raise Exception("Could not open "+vector)
	layer = dataSource.GetLayer()
	layerDefinition = layer.GetLayerDefn()
	return [layerDefinition.GetFieldDefn(i).GetName() for i in range(layerDefinition.GetFieldCount())]

def multiPolyToPoly(shpMulti,shpSingle):

	"""
	IN:
		shpMulti [string] : path to an input vector
		shpSingle [string] : output vector

	OUT:
		convert all multipolygon to polygons. Add all single polygon into shpSingle
	"""
	def addPolygon(feat, simplePolygon, in_lyr, out_lyr):
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

def CreateNewLayer(layer, outShapefile,AllFields):

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
      out_lyr_name = os.path.splitext( os.path.split( outShapefile )[1] )[0]
      srsObj = layer.GetSpatialRef()
      outLayer = outDataSource.CreateLayer( out_lyr_name, srsObj, geom_type=ogr.wkbMultiPolygon )
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
	AllModel =  cfg.AllModel
	modelFind = []
	for i in range(len(AllModel)):
		currentModel = cfg.AllModel[i].modelName
		try :
			ind = modelFind.index(currentModel)
			raise Exception("Model "+currentModel+" already exist")
		except ValueError :
			modelFind.append(currentModel)
	return modelFind

def mergeSQLite_cmd(outname, opath,*files):
	filefusion = opath+"/"+outname+".sqlite"
	if os.path.exists(filefusion):
		os.remove(filefusion)
	first = files[0]
	cmd = 'ogr2ogr -f SQLite '+filefusion+' '+first
	print cmd 
	os.system(cmd)
	if len(files)>1:
		for f in range(1,len(files)):
			fusion = 'ogr2ogr -f SQLite -update -append '+filefusion+' '+files[f]
			print fusion
			os.system(fusion)

	if os.path.exists(filefusion):
		for currentShape in files:
			os.remove(currentShape)

def mergeSQLite(outname, opath,files):
	filefusion = opath+"/"+outname+".sqlite"
	if os.path.exists(filefusion):
		os.remove(filefusion)
	first = files[0]
	cmd = 'ogr2ogr -f SQLite '+filefusion+' '+first
	print cmd 
	os.system(cmd)
	if len(files)>1:
		for f in range(1,len(files)):
			fusion = 'ogr2ogr -f SQLite -update -append '+filefusion+' '+files[f]
			print fusion
			os.system(fusion)

def mergeVectors(outname, opath,files,ext="shp"):
   	"""
   	Merge a list of vector files in one 
   	"""
	outType = ''
	if ext == 'sqlite':
		outType = ' -f SQLite '
	file1 = files[0]
  	nbfiles = len(files)
  	filefusion = opath+"/"+outname+"."+ext
	if os.path.exists(filefusion):
		os.remove(filefusion)
  	fusion = 'ogr2ogr '+filefusion+' '+file1+' '+outType
	print fusion
  	os.system(fusion)

	for f in range(1,nbfiles):
		fusion = 'ogr2ogr -update -append '+filefusion+' '+files[f]+' -nln '+outname+' '+outType
		print fusion
		os.system(fusion)

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

def ResizeImage(imgIn,imout,spx,spy,imref,proj,pixType):

	minX,maxX,minY,maxY = getRasterExtent(imref)

	#Resize = 'gdalwarp -of GTiff -r cubic -tr '+spx+' '+spy+' -te '+str(minX)+' '+str(minY)+' '+str(maxX)+' '+str(maxY)+' -t_srs "EPSG:'+proj+'" '+imgIn+' '+imout
	Resize = 'gdalwarp -of GTiff -tr '+spx+' '+spy+' -te '+str(minX)+' '+str(minY)+' '+str(maxX)+' '+str(maxY)+' -t_srs "EPSG:'+proj+'" '+imgIn+' '+imout
	print Resize
	os.system(Resize)

def gen_confusionMatrix(csv_f,AllClass):

	"""
	
	IN:
		csv_f [list of list] : comes from confCoordinatesCSV function.
		AllClass [list of strings] : all class
	OUT : 
		confMat [numpy array] : generate a numpy array representing a confusion matrix
	"""
	NbClasses = len(AllClass)

	confMat = [[0]*NbClasses]*NbClasses
	confMat = np.asarray(confMat)
	
	row = 0
	for classRef in AllClass:
		flag = 0#in order to manage the case "this reference label was never classified"
		for classRef_csv in csv_f:
			if classRef_csv[0] == classRef:
				col = 0
				for classProd in AllClass:
					for classProd_csv in classRef_csv[1]:
						if classProd_csv[0] == classProd:
							confMat[row][col] = confMat[row][col] + classProd_csv[1]
					col+=1
				#row +=1
		row+=1
		#if flag == 0:
		#	row+=1

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
		FileMat = open(csvPath,"r")
		while 1:
			data = FileMat.readline().rstrip('\n\r')
			if data == "":
				FileMat.close()
				break
			if data.count('#Reference labels (rows):')!=0:
				ref = data.split(":")[-1].split(",")
			elif data.count('#Produced labels (columns):')!=0:
				prod = data.split(":")[-1].split(",")
			else:
				y = ref[cpty]
				line = data.split(",")
				cptx = 0
				for val in line:
					x = prod[cptx]
					out.append([int(y),[int(x),float(val)]])
					cptx+=1
				cpty +=1
	return out

def findAndReplace(InFile,Search,Replace):

	"""
	IN:
	InFile [string] : path to a file
	Search [string] : pattern to find in InFile
	Replace [string] : replace pattern by Replace
	
	OUT:
	replace a string by an other one in a file
	"""
	f1 = open(InFile, 'r')
	f2Name = InFile.split("/")[-1].split(".")[0]+"_tmp."+InFile.split("/")[-1].split(".")[1]
	f2path = "/".join(InFile.split("/")[0:len(InFile.split("/"))-1])
	f2 = open(f2path+"/"+f2Name, 'w')
	for line in f1:
    		f2.write(line.replace(Search,Replace))
	f1.close()
	f2.close()

	os.remove(InFile)
	shutil.copyfile(f2path+"/"+f2Name, InFile)
	os.remove(f2path+"/"+f2Name)

def bigDataTransfert(pathOut,folderList): 
	"""
	IN : 
		pathOut [string] path to output folder
		folderList [list of string path]

		copy datas through zip (use with HPC)
	"""
	
	TAR = pathOut+"/TAR.tar"
	tarFile = tarfile.open(TAR, mode='w')
	for feat in folderList:
		tarFile.add(feat,arcname=feat.split("/")[-1])
	tarFile.close()

	t = tarfile.open(TAR, 'r')
	t.extractall(pathOut)
	os.remove(TAR)
	
	
def erodeOrDilateShapeFile(infile,outfile,buffdist):

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
	try:
       		ds=ogr.Open(infile)
        	drv=ds.GetDriver()
        	if os.path.exists(outfile):
            		drv.DeleteDataSource(outfile)
        	drv.CopyDataSource(ds,outfile)
        	ds.Destroy()
        
       		ds=ogr.Open(outfile,1)
        	lyr=ds.GetLayer(0)
        	for i in range(0,lyr.GetFeatureCount()):
            		feat=lyr.GetFeature(i)
            		lyr.DeleteFeature(i)
            		geom=feat.GetGeometryRef()
            		feat.SetGeometry(geom.Buffer(float(buffdist)))
            		lyr.CreateFeature(feat)
        	ds.Destroy()
    	except:return False
    	return True

def erodeShapeFile(infile,outfile,buffdist):
    return erodeOrDilateShapeFile(infile,outfile,-math.fabs(buffdist))

def dilateShapeFile(infile,outfile,buffdist):
    return erodeOrDilateShapeFile(infile,outfile,math.fabs(buffdist))

def getListTileFromModel(modelIN,pathToConfig):

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
	return [f for f in glob.glob(Pathfile)]

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
	return env[0],env[2],env[1],env[3]

def getFeatStackName(pathConf):
	cfg = Config(pathConf)
	listIndices = cfg.GlobChain.features
	try:
		userFeatPath = Config(file(pathConf)).chain.userFeatPath
		if userFeatPath == "None" : userFeatPath = None
	except:
		userFeatPath = None
		print "WARNING : missing field chain.userFeatPath in "+pathConf

	userFeat_pattern = ""
	if userFeatPath : userFeat_pattern = "_".join((Config(file(pathConf)).userFeat.patterns).split(","))
		
	if len(listIndices)>1:
		listIndices = list(listIndices)
		listIndices = sorted(listIndices)
		listFeat = "_".join(listIndices)
	elif len(listIndices) == 1 :
		listFeat = listIndices[0]
	else:
		return "SL_MultiTempGapF"+userFeat_pattern+".tif"

	Stack_ind = "SL_MultiTempGapF_"+listFeat+"_"+userFeat_pattern+"_.tif"
	return Stack_ind

def writeCmds(path,cmds,mode="w"):

	cmdFile = open(path,mode)
	for i in range(len(cmds)):
		if i == 0:
			cmdFile.write("%s"%(cmds[i]))
		else:
			cmdFile.write("\n%s"%(cmds[i]))
	cmdFile.close()

def removeShape(shapePath,extensions):
	"""
	IN:
		shapePath : path to the shapeFile without extension. 
			ex : /path/to/myShape where /path/to/myShape.* exists
		extensions : all extensions to delete
			ex : extensions = [".prj",".shp",".dbf",".shx"]
	"""
	for ext in extensions:
		os.remove(shapePath+ext)

def cpShapeFile(inpath,outpath,extensions,spe=False):

	for ext in extensions:
		if not spe:
			shutil.copy(inpath+ext,outpath+ext)
		else:
			shutil.copy(inpath+ext,outpath)
	

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

def renameShapefile(inpath,filename,old_suffix,new_suffix,outpath=None):
    if not outpath:
        outpath = inpath
    os.system("cp "+inpath+"/"+filename+old_suffix+".shp "+outpath+"/"+filename+new_suffix+".shp")
    os.system("cp "+inpath+"/"+filename+old_suffix+".shx "+outpath+"/"+filename+new_suffix+".shx")
    os.system("cp "+inpath+"/"+filename+old_suffix+".dbf "+outpath+"/"+filename+new_suffix+".dbf")
    os.system("cp "+inpath+"/"+filename+old_suffix+".prj "+outpath+"/"+filename+new_suffix+".prj")

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
       outname = opath+"/"+nameVF+"_"+nameCF+".shp"
   else:
       outname = opath+"/"+nameOut+".shp"    

   if os.path.exists(outname):
      os.remove(outname)
   Clip = "ogr2ogr -clipsrc "+cutFile+" "+outname+" "+vectorFile+" -progress"
   print Clip
   os.system(Clip)
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
         chname = chname+feature+"_"
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
     ch = ch+serie+" "
   return ch

def ConcatenateAllData(opath, pathConf,workingDirectory,wOut,name,*SerieList):
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
   print Concatenation
   os.system(Concatenation)


