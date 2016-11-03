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

import sys,os,shutil,glob,math,tarfile,re
from config import Config
import numpy as np
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from osgeo.gdalconst import *
from datetime import timedelta, date
import datetime

def assembleTile_Merge(AllRaster,spatialResolution,out):
	AllRaster = " ".join(AllRaster)
	cmd = "gdal_merge.py -ps "+str(spatialResolution)+" -"+str(spatialResolution)+" -o "+out+" -ot Int16 -n 0 "+AllRaster
	print cmd 
	os.system(cmd)

def getVectorFeatures(InputShape):

    dataSource = ogr.Open(InputShape)
    daLayer = dataSource.GetLayer(0)
    layerDefinition = daLayer.GetLayerDefn()

    AllFeat = []
    for i in range(layerDefinition.GetFieldCount()):
        if "value_" in layerDefinition.GetFieldDefn(i).GetName():
            AllFeat.append(layerDefinition.GetFieldDefn(i).GetName())
    return AllFeat

def getDateFromString(date):
        Y = int(date[0:4])
        M = int(date[4:6])
        D = int(date[6:len(date)])
        return Y,M,D

def getNbDateInTile(dateInFile):
    with open(dateInFile) as f:
        for i, l in enumerate(f):
            date = l.rstrip()
            try:
                Y,M,D = getDateFromString(date)
                validDate = datetime.datetime(int(Y),int(M),int(D))
                print validDate
            except ValueError:
                raise Exception("unvalid date in : "+dateInFile+" -> '"+str(date)+"'")
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

def getRasterProjectionEPSG(raster):
	src_ds = gdal.Open(raster)
	if src_ds is None:
   		raise Exception(raster+" doesn't exist")
	proj = src_ds.GetProjectionRef()
	EPSG_Code = re.findall(r'\b\d+\b', proj.split(",")[-1])
	if len(EPSG_Code) != 1:
		raise Exception("Can't determine projection")
	else:
		return int(EPSG_Code[0])

def getRasterNbands(raster):
	
	src_ds = gdal.Open(raster)
	if src_ds is None:
   		raise Exception(raster+" doesn't exist")
	return int(src_ds.RasterCount)

def checkConfigParameters(pathConf):

	def all_sameBands(items):
    		return all(bands == items[0][1] for path,bands in items)

	executionMode = Config(file(pathConf)).chain.executionMode
	outputPath = Config(file(pathConf)).chain.outputPath
	jobsPath = Config(file(pathConf)).chain.jobsPath
	pyAppPath = Config(file(pathConf)).chain.pyAppPath
	chainName = Config(file(pathConf)).chain.chainName
	nomenclaturePath = Config(file(pathConf)).chain.nomenclaturePath
	listTile = Config(file(pathConf)).chain.listTile
	featuresPath = Config(file(pathConf)).chain.featuresPath
	L5Path = Config(file(pathConf)).chain.L5Path
	L8Path = Config(file(pathConf)).chain.L8Path
	S2Path = Config(file(pathConf)).chain.S2Path
	S1Path = Config(file(pathConf)).chain.S1Path
	mode = Config(file(pathConf)).chain.mode
	regionPath = Config(file(pathConf)).chain.regionPath
	regionField = Config(file(pathConf)).chain.regionField
	model = Config(file(pathConf)).chain.model
	groundTruth = Config(file(pathConf)).chain.groundTruth
	dataField = Config(file(pathConf)).chain.dataField
	runs = Config(file(pathConf)).chain.runs
	ratio = Config(file(pathConf)).chain.ratio
	cloud_threshold = Config(file(pathConf)).chain.cloud_threshold
	spatialResolution = Config(file(pathConf)).chain.spatialResolution
	logPath = Config(file(pathConf)).chain.logPath
	colorTable = Config(file(pathConf)).chain.colorTable
	mode_outside_RegionSplit = Config(file(pathConf)).chain.mode_outside_RegionSplit
	OTB_HOME = Config(file(pathConf)).chain.OTB_HOME
	nbTile = len(listTile.split(" "))
	
	shapeMode = Config(file(pathConf)).argTrain.shapeMode
	samplesOptions = Config(file(pathConf)).argTrain.samplesOptions
	classifier = Config(file(pathConf)).argTrain.classifier
	options = Config(file(pathConf)).argTrain.options
	rearrangeModelTile = Config(file(pathConf)).argTrain.rearrangeModelTile
	rearrangeModelTile_out = Config(file(pathConf)).argTrain.rearrangeModelTile_out
	cropMix = Config(file(pathConf)).argTrain.cropMix
	prevFeatures = Config(file(pathConf)).argTrain.prevFeatures
	annualCrop = Config(file(pathConf)).argTrain.annualCrop
	ACropLabelReplacement = Config(file(pathConf)).argTrain.ACropLabelReplacement

	classifMode = Config(file(pathConf)).argClassification.classifMode
	fusionOptions = Config(file(pathConf)).argClassification.fusionOptions
	pixType = Config(file(pathConf)).argClassification.pixType
	confusionModel = Config(file(pathConf)).argClassification.confusionModel
	noLabelManagement = Config(file(pathConf)).argClassification.noLabelManagement

	proj = Config(file(pathConf)).GlobChain.proj
	features = Config(file(pathConf)).GlobChain.features
	temporalResolution = Config(file(pathConf)).GlobChain.temporalResolution
	batchProcessing = Config(file(pathConf)).GlobChain.batchProcessing
	
	error=[]
	"""
	if "parallel" in executionMode:
		if not os.path.exists(jobsPath):
			error.append(jobsPath+" doesn't exist\n")
		if not os.path.exists(logPath):
			error.append(logPath+" doesn't exist\n")
	"""
	if not os.path.exists(pyAppPath):
		error.append(pyAppPath+" doesn't exist\n")
	if not os.path.exists(nomenclaturePath):
		error.append(nomenclaturePath+" doesn't exist\n")
	if "outside" == mode :
		if not os.path.exists(regionPath):
			error.append(regionPath+" doesn't exist\n")
	if "mutli_regions" == mode :
		if not os.path.exists(model):
			error.append(model+" doesn't exist\n")
	if not os.path.exists(groundTruth):
		error.append(groundTruth+" doesn't exist\n")
	else:
		Field_FType = []
		dataSource = ogr.Open(groundTruth)
		daLayer = dataSource.GetLayer(0)
		layerDefinition = daLayer.GetLayerDefn()
		for i in range(layerDefinition.GetFieldCount()):
			fieldName =  layerDefinition.GetFieldDefn(i).GetName()
			fieldTypeCode = layerDefinition.GetFieldDefn(i).GetType()
    			fieldType = layerDefinition.GetFieldDefn(i).GetFieldTypeName(fieldTypeCode)
			Field_FType.append((fieldName,fieldType))
		flag = 0
		for currentField,fieldType in Field_FType:
			if currentField == dataField:
				flag = 1
				if not "Integer" in fieldType:
					error.append("the data's field must be an integer'\n")
		if flag == 0:
			error.append("field name '"+dataField+"' doesn't exist\n")

	if not os.path.exists(colorTable):
		error.append(colorTable+" doesn't exist\n")
	if not os.path.exists(OTB_HOME+"/config_otb.sh"):
		error.append(OTB_HOME+"/config_otb.sh doesn't exist\n")
	if cropMix == "True":
		if not os.path.exists(prevFeatures):
			error.append(prevFeatures+" doesn't exist\n")
		if not shapeMode == "points":
			error.append("you must use 'points' mode with 'cropMix' mode\n")
	if (mode != "one_region") and (mode != "multi_regions") and (mode != "outside"):
		error.append("'mode' must be 'one_region' or 'multi_regions' or 'outside'\n")
	if mode == "one_region" and classifMode == "fusion":
		error.append("you can't chose 'one_region' mode and ask a fusion of classifications\n")
	if nbTile == 1 and mode == "multi_regions":
		error.append("only one tile detected with mode 'multi_regions'\n")
	if shapeMode == "points":
		if ("-sample.mt" or "-sample.mv" or "-sample.bm" or "-sample.vtr") in options:
			error.append("wrong options passing in classifier argument see otbcli_TrainVectorClassifier's documentation\n")

	#if features has already compute, check if they have the same number of bands
	if os.path.exists(featuresPath ):
		stackName = getFeatStackName(pathConf)
		features = FileSearch_AND(featuresPath,True,stackName)
		if features:
			featuresBands = [(currentRaster,getRasterNbands(currentRaster)) for currentRaster in features]
			if not all_sameBands(featuresBands):
				error.append([ currentRaster+" bands : "+str(rasterBands)+"\n" for currentRaster,rasterBands in featuresBands])
	if len(error)>=1:
		errorList = "".join(error)
		raise Exception("\n"+errorList)

def multiSearch(shp):
	driver = ogr.GetDriverByName('ESRI Shapefile')
	in_ds = driver.Open(shp, 0)
	in_lyr = in_ds.GetLayer()
	for in_feat in in_lyr:
        	geom = in_feat.GetGeometryRef()
       		if geom.GetGeometryName() == 'MULTIPOLYGON':
			return True
	return False

def getFields(shp):
   """
   Returns the list of fields of a shapefile
   """
   driver = ogr.GetDriverByName("ESRI Shapefile")
   if driver.Open(shp, 0):
	ds = driver.Open(shp, 0)
   else:
	print "Not possible to open the file "+shp
	sys.exit(1)

   layer = ds.GetLayer()
   inLayerDefn = layer.GetLayerDefn()
   field_name_list = []
   for i in range(inLayerDefn.GetFieldCount()):
      field =  inLayerDefn.GetFieldDefn(i).GetName()
      field_name_list.append(field)
   return field_name_list

def multiPolyToPoly(shpMulti,shpSingle):

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
	field_name_list = getFields(shpMulti)
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

def getAllClassInShape(shapeExemple,datafield):
	
	driver = ogr.GetDriverByName("ESRI Shapefile")
	dataSource = driver.Open(shapeExemple, 0)
	layer = dataSource.GetLayer()

	AllClass = []
	for feature in layer:
		currentFeat = feature.GetField(datafield)
		try:
			ind = AllClass.index(str(currentFeat))
		except ValueError:
    			AllClass.append(str(currentFeat))
	return AllClass

def getAllModels(PathconfigModels):
	"""
	return All models
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
	if len(listIndices)>1:
		listIndices = list(listIndices)
		listIndices = sorted(listIndices)
		listFeat = "_".join(listIndices)
	elif len(listIndices) == 1 :
		listFeat = listIndices[0]
	else:
		return "SL_MultiTempGapF.tif"

	Stack_ind = "SL_MultiTempGapF_"+listFeat+"__.tif"
	#Stack_ind = "SL_MultiTempGapF_"+listFeat+"__.vrt"
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
