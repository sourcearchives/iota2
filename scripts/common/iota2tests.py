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
import os,unittest,Sensors,Utils,filecmp,string,random,shutil,sys,osr,ogr
import subprocess,RandomInSituByTile,createRegionsByTiles,vectorSampler
import fileUtils as fu
import test_genGrid as test_genGrid
import tileEnvelope
from gdalconst import *
from osgeo import gdal
from config import Config
import numpy as np
import otbApplication as otb

#export PYTHONPATH=$PYTHONPATH:/mnt/data/home/vincenta/modulePy/config-0.3.9       -> get python Module
#export PYTHONPATH=$PYTHONPATH:/mnt/data/home/vincenta/IOTA2/theia_oso/data/test_scripts -> get scripts needed to test
#export IOTA2DIR=/mnt/data/home/vincenta/IOTA2/theia_oso

#python -m unittest iota2tests

iota2dir = os.environ.get('IOTA2DIR')
iota2_script = os.environ.get('IOTA2DIR')+"/scripts/common"
iota2_dataTest = os.environ.get('IOTA2DIR')+"/data/"

def rasterToArray(InRaster):
        arrayOut = None
        ds = gdal.Open(InRaster)
        arrayOut = ds.ReadAsArray()
        return arrayOut

def arrayToRaster(inArray,outRaster):
        rows = inArray.shape[0]
        cols = inArray.shape[1]
        originX = 777225.58
        originY = 6825084.53
        pixSize = 30
        driver = gdal.GetDriverByName('GTiff')
        outRaster = driver.Create(outRaster, cols, rows, 1, gdal.GDT_UInt16)
        if not outRaster : raise Exception("can not create : "+outRaster)
        outRaster.SetGeoTransform((originX, pixSize, 0, originY, 0, pixSize))
        outband = outRaster.GetRasterBand(1)
        outband.WriteArray(inArray)
        outRasterSRS = osr.SpatialReference()
        outRasterSRS.ImportFromEPSG(2154)
        outRaster.SetProjection(outRasterSRS.ExportToWkt())
        outband.FlushCache()

def generateRandomString(size):
	return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(size))

def checkSameFile(files,patterns = ["res_ref","res_test"]):
	
	replacedBy = "XXXX"

	Alltmp = []
	for file_ in files:
		file_tmp = file_.split(".")[0]+"_tmp."+file_.split(".")[-1]
		if os.path.exists(file_tmp):
			os.remove(file_tmp)
		Alltmp.append(file_tmp)
		with open(file_,"r") as f1:
			for line in f1:
				line_tmp = line
				for patt in patterns:
					if patt in line:
						line_tmp = line.replace(patt,replacedBy)
				with open(file_tmp,"a") as f2:
					f2.write(line_tmp)
	same = filecmp.cmp(Alltmp[0],Alltmp[1])
	
	for fileTmp in Alltmp:
		os.remove(fileTmp)
	
	return same

def checkSameEnvelope(EvRef,EvTest):

	miX_ref,miY_ref,maX_ref,maY_ref = fu.getShapeExtent(EvRef)
	miX_test,miY_test,maX_test,maY_test = fu.getShapeExtent(EvTest)

	if (miX_ref == miX_test) and (miY_test==miY_test) and (maX_ref==maX_test) and (maY_ref==maY_test):
		return True
	return False

def prepareAnnualFeatures(workingDirectory,referenceDirectory,*rasters):
        """
        double all pixels of rasters
        """
        shutil.copytree(referenceDirectory,workingDirectory)

        for raster in rasters:
                rasterPath = fu.FileSearch_AND(workingDirectory,True,raster)[0]
                cmd = 'otbcli_BandMathX -il '+rasterPath+' -out '+rasterPath+' -exp "im1+im1"'
                print cmd
                os.system(cmd)

class iota_testStringManipulations(unittest.TestCase):
	
	@classmethod
        def setUpClass(self):
		self.AllL8Tiles = "D00005H0010 D0002H0007 D0003H0006 D0004H0004 D0005H0002 D0005H0009 D0006H0006 D0007H0003 D0007H0010 D0008H0008 D0009H0007 D0010H0006 D0000H0001 D0002H0008 D0003H0007 D0004H0005 D0005H0003 D0005H0010 D0006H0007 D0007H0004 D0008H0002 D0008H0009 D0009H0008 D0010H0007 D0000H0002 D0003H0001 D0003H0008 D0004H0006 D0005H0004 D0006H0001 D0006H0008 D0007H0005 D0008H0003 D0009H0002 D0009H0009 D0010H0008 D00010H0005 D0003H0002 D0003H0009 D0004H0007 D0005H0005 D0006H0002 D0006H0009 D0007H0006 D0008H0004 D0009H0003 D0010H0002 D0001H0007 D0003H0003 D0004H0001 D0004H0008 D0005H0006 D0006H0003 D0006H0010 D0007H0007 D0008H0005 D0009H0004 D0010H0003 D0001H0008 D0003H0004 D0004H0002 D0004H0009 D0005H0007 D0006H0004 D0007H0001 D0007H0008 D0008H0006 D0009H0005 D0010H0004 D0002H0006 D0003H0005 D0004H0003 D0005H0001 D0005H0008 D0006H0005 D0007H0002 D0007H0009 D0008H0007 D0009H0006 D0010H0005 ".split()
		self.AllS2Tiles = "T30TVT T30TXP T30TYN T30TYT T30UWU T30UYA T31TCK T31TDJ T31TEH T31TEN T31TFM T31TGL T31UCR T31UDS T31UFP T32TLP T32TMN T32ULV T30TWP T30TXQ T30TYP T30UUU T30UWV T30UYU T31TCL T31TDK T31TEJ T31TFH T31TFN T31TGM T31UCS T31UEP T31UFQ T32TLQ T32TNL T32UMU T30TWS T30TXR T30TYQ T30UVU T30UXA T30UYV T31TCM T31TDL T31TEK T31TFJ T31TGH T31TGN T31UDP T31UEQ T31UFR T32TLR T32TNM T32UMV T30TWT T30TXS T30TYR T30UVV T30UXU T31TCH T31TCN T31TDM T31TEL T31TFK T31TGJ T31UCP T31UDQ T31UER T31UGP T32TLT T32TNN T30TXN T30TXT T30TYS T30UWA T30UXV T31TCJ T31TDH T31TDN T31TEM T31TFL T31TGK T31UCQ T31UDR T31UES T31UGQ T32TMM T32ULU".split()
		self.dateFile = iota2_dataTest+"/references/dates.txt"
		self.fakeDateFile = iota2_dataTest+"/references/fakedates.txt"

	def test_getTile(self):
		rString_head = generateRandomString(100)
		rString_tail = generateRandomString(100)
	
		S2 = True
		for currentTile in self.AllS2Tiles:
			try : fu.findCurrentTileInString(rString_head+currentTile+rString_tail,self.AllS2Tiles)
			except : S2 = False
		self.assertTrue(S2)
		L8 = True
		for currentTile in self.AllL8Tiles:
			try : fu.findCurrentTileInString(rString_head+currentTile+rString_tail,self.AllL8Tiles)
			except : L8 = False
		self.assertTrue(L8)

	def test_getDates(self):

		try:
			nbDates = fu.getNbDateInTile(self.dateFile,display = False)
			self.assertTrue(nbDates==35)
		except:
			self.assertTrue(True==False)

		try:
			fu.getNbDateInTile(self.fakeDateFile,display = False)
			self.assertTrue(True==False)
		except:self.assertTrue(True==True)

def compareSQLite(vect_1,vect_2,mode='table'):

        '''
        compare SQLite, table mode is faster but does not work with 
        connected OTB applications.

        return true if vectors are the same
        '''

        def getFieldValue(feat,fields):
                return dict([(currentField,feat.GetField(currentField)) for currentField in fields])
        def priority(item):
                return (item[0],item[1])
        def getValuesSortedByCoordinates(vector):
                values = []
                driver = ogr.GetDriverByName("SQLite")
                ds = driver.Open(vector,0)
                lyr = ds.GetLayer()
                fields = fu.getAllFieldsInShape(vector,'SQLite')
                for feature in lyr:
                        x,y= feature.GetGeometryRef().GetX(),feature.GetGeometryRef().GetY()
                        fields_val = getFieldValue(feature,fields)
                        values.append((x,y,fields_val))

                values = sorted(values,key=priority)
                return values

        fields_1 = fu.getAllFieldsInShape(vect_1,'SQLite') 
        fields_2 = fu.getAllFieldsInShape(vect_2,'SQLite')

        if len(fields_1) != len(fields_2): return False
        elif cmp(fields_1,fields_2) != 0 : return False
        
        if mode == 'table':
                import sqlite3 as lite
                import pandas as pad
                connection_1 = lite.connect(vect_1)
                df_1 = pad.read_sql_query("SELECT * FROM output", connection_1)

                connection_2 = lite.connect(vect_2)
                df_2 = pad.read_sql_query("SELECT * FROM output", connection_2)

                try: 
                        table = (df_1 != df_2).any(1)
                        if True in table.tolist():return False
                        else:return True
                except ValueError:
                        return False

        elif mode == 'coordinates':
                values_1 = getValuesSortedByCoordinates(vect_1)
                values_2 = getValuesSortedByCoordinates(vect_2)
                sameFeat = [cmp(val_1,val_2) == 0 for val_1,val_2 in zip(values_1,values_2)]
                if False in sameFeat:return False
                return True
        else:
                raise Exception("mode parameter must be 'table' or 'coordinates'")
        

class iota_testSamplerApplications(unittest.TestCase):
        
        @classmethod
        def setUpClass(self):
                self.test_vector = iota2_dataTest+"/test_vector"
                if not os.path.exists(self.test_vector):os.mkdir(self.test_vector)

                self.referenceShape = iota2_dataTest+"/references/sampler/D0005H0002_polygons_To_Sample.shp"
                self.configSimple_NO_bindings = iota2_dataTest+"/config/test_config.cfg"
                self.configSimple_bindings = iota2_dataTest+"/config/test_config_bindings.cfg"
                self.configCropMix_NO_bindings = iota2_dataTest+"/config/test_config_cropMix.cfg"
                self.configCropMix_bindings = iota2_dataTest+"/config/test_config_cropMix_bindings.cfg"
                self.configClassifCropMix_NO_bindings = iota2_dataTest+"/config/test_config_classifCropMix.cfg"
                self.configClassifCropMix_bindings = iota2_dataTest+"/config/test_config_classifCropMix_bindings.cfg"
                self.configPrevClassif = iota2_dataTest+"/config/prevClassif.cfg"

                self.regionShape = iota2_dataTest+"/references/region_need_To_env.shp"
                self.features = iota2_dataTest+"/references/features/D0005H0002/Final/SL_MultiTempGapF_Brightness_NDVI_NDWI__.tif"
                self.expectedFeatures = {11:74,12:34,42:19,51:147}
        
        def test_samplerSimple(self):
                reference = iota2_dataTest+"/references/sampler/D0005H0002_polygons_To_Sample_Samples_ref.sqlite"
                workingDirectory = self.test_vector+"/simpleSampler"
                if os.path.exists(workingDirectory):shutil.rmtree(workingDirectory)
                os.mkdir(workingDirectory)
                vectorTest = vectorSampler.generateSamples(self.referenceShape,workingDirectory,self.configSimple_NO_bindings,\
                                                           testMode=True,features=self.features)
     
                self.assertTrue(compareSQLite(vectorTest,reference))
        
        def test_samplerSimple_bindings(self):
                reference = iota2_dataTest+"/references/sampler/D0005H0002_polygons_To_Sample_Samples_ref_bindings.sqlite"
                workingDirectory = self.test_vector+"/simpleSampler_bindings"
                if os.path.exists(workingDirectory):shutil.rmtree(workingDirectory)
                os.mkdir(workingDirectory)
                data_folder = iota2_dataTest+"/references/features"
                vectorTest = vectorSampler.generateSamples(self.referenceShape,workingDirectory,self.configSimple_bindings,\
                                                           testMode=True,features=self.features,testFeaturePath=data_folder)

                self.assertTrue(compareSQLite(vectorTest,reference,mode='coordinates'))
        
        def test_samplerCropMix(self):
                reference = iota2_dataTest+"/references/sampler/D0005H0002_polygons_To_Sample_Samples_CropMix.sqlite"
                workingDirectory = self.test_vector+"/cropMixSampler/"
                if os.path.exists(workingDirectory):shutil.rmtree(workingDirectory)
                os.mkdir(workingDirectory)
                featuresPath = iota2_dataTest+"/references/features/"
                annualFeaturesPath = workingDirectory+"/annualFeatures"
                prepareAnnualFeatures(annualFeaturesPath,featuresPath,"Landsat8_ST_REFL.tif","SL_MultiTempGapF_Brightness_NDVI_NDWI__.tif")

                vectorTest = vectorSampler.generateSamples(self.referenceShape,workingDirectory,self.configCropMix_NO_bindings,\
                                                           testMode=True,features=None,testFeaturePath=featuresPath,\
                                                           testAnnualFeaturePath=annualFeaturesPath)

                self.assertTrue(compareSQLite(vectorTest,reference))
        
        def test_samplerCropMix_bindings(self):
                reference = iota2_dataTest+"/references/sampler/D0005H0002_polygons_To_Sample_Samples_CropMix_bindings.sqlite"
                workingDirectory = self.test_vector+"/cropMixSampler_bindings/"
                if os.path.exists(workingDirectory):shutil.rmtree(workingDirectory)
                os.mkdir(workingDirectory)
   
                featuresPath = iota2_dataTest+"/references/features/"
                annualFeaturesPath = workingDirectory+"/annualFeatures"
                prepareAnnualFeatures(annualFeaturesPath,featuresPath,"Landsat8_ST_REFL.tif","SL_MultiTempGapF_Brightness_NDVI_NDWI__.tif")

                vectorTest = vectorSampler.generateSamples(self.referenceShape,workingDirectory,self.configCropMix_bindings,\
                                                           testMode=True,features=None,testFeaturePath=featuresPath,\
                                                           testAnnualFeaturePath=annualFeaturesPath)

                self.assertTrue(compareSQLite(vectorTest,reference,mode='coordinates'))
        
        def test_samplerClassifCropMix(self):
                """
                random part in this script could not be control, no reference vector can be done.
                Only number of features can be control.
                """
                prevClassif = iota2_dataTest+"/references/sampler/"
                workingDirectory = self.test_vector+"/classifCropMixSampler/"
                if os.path.exists(workingDirectory):shutil.rmtree(workingDirectory)
                os.mkdir(workingDirectory)
   
                vectorTest = vectorSampler.generateSamples(self.referenceShape,workingDirectory,self.configClassifCropMix_NO_bindings,\
                                                           testMode=True,features=self.features,testFeaturePath=None,\
                                                           testAnnualFeaturePath=prevClassif,testPrevConfig=self.configPrevClassif,\
                                                           testShapeRegion=self.regionShape)
                same = []
                for key,val in self.expectedFeatures.iteritems():
                        if len(fu.getFieldElement(vectorTest,'SQLite','code','all')) != self.expectedFeatures[key]:
                                same.append(True)
                        else:
                                same.append(False)
                if False in same: self.assertTrue(False)
                else : self.assertTrue(True)
        
        def test_samplerClassifCropMix_bindings(self):
                """
                random part in this script could not be control, no reference vector can be done.
                Only number of features can be control.
                """
                prevClassif = iota2_dataTest+"/references/sampler/"
                workingDirectory = self.test_vector+"/classifCropMixSampler_bindings/"
                if os.path.exists(workingDirectory):shutil.rmtree(workingDirectory)
                os.mkdir(workingDirectory)
                featuresPath = iota2_dataTest+"/references/features/"
                vectorTest = vectorSampler.generateSamples(self.referenceShape,workingDirectory,self.configClassifCropMix_bindings,\
                                                           testMode=True,features=self.features,testFeaturePath=featuresPath,\
                                                           testAnnualFeaturePath=prevClassif,testPrevConfig=self.configPrevClassif,\
                                                           testShapeRegion=self.regionShape)
                same = []
                for key,val in self.expectedFeatures.iteritems():
                        if len(fu.getFieldElement(vectorTest,'SQLite','code','all')) != self.expectedFeatures[key]: same.append(True)
                        else:same.append(False)

                if False in same: self.assertTrue(False)
                else : self.assertTrue(True)
        
                        


class iota_testRasterManipulations(unittest.TestCase):

	@classmethod
        def setUpClass(self):
                self.scripts = iota2dir+"/scripts/common"
                self.test_RasterDirectory = iota2_dataTest+"/test_raster/"
                self.test_features_bm = self.test_RasterDirectory+"/test_features_bm/"
                self.test_features_iota2 = self.test_RasterDirectory+"/test_features_iota2"
                if not os.path.exists(self.test_RasterDirectory):os.mkdir(self.test_RasterDirectory)

                if os.path.exists(self.test_features_bm):shutil.rmtree(self.test_features_bm)
                os.mkdir(self.test_features_bm)
                if os.path.exists(self.test_features_iota2):shutil.rmtree(self.test_features_iota2)
                os.mkdir(self.test_features_iota2)

                self.ref_L8Directory = iota2_dataTest+"/L8_50x50/"

                self.ref_config_featuresBandMath = iota2_dataTest+"/config/test_config.cfg"
                self.ref_features = iota2_dataTest+"/references/features/D0005H0002/Final/SL_MultiTempGapF_Brightness_NDVI_NDWI__.tif"
                self.ref_config_iota2FeatureExtraction = iota2_dataTest+"/config/test_config_iota2FeatureExtraction.cfg"

        def test_Features(self):
                import genCmdFeatures

                if not os.path.exists(self.ref_L8Directory):self.assertTrue(True==False)

                ref_array = rasterToArray(self.ref_features)

                def features_case(configPath,workingDirectory):
                        #features bandMath computed 
                        MyCmd = genCmdFeatures.CmdFeatures("",["D0005H0002"],self.scripts,\
                                                           self.ref_L8Directory,"None","None",\
                                                           configPath,workingDirectory\
                                                           ,None,testMode=True)
 
                        self.assertTrue(len(MyCmd)==1)
                        subprocess.call(MyCmd[0],shell=True)
                        test_features = fu.FileSearch_AND(workingDirectory,True,"SL_MultiTempGapF_Brightness_NDVI_NDWI__.tif")[0]
                        return test_features

                def sortData(iotaFeatures):
                        workingDirectory,name =  os.path.split(iotaFeatures)

                        reflOut = workingDirectory+"/"+name.replace(".tif","_refl.tif")
                        refl = " ".join(["Channel"+str(i+1) for i in range(14)])
                        cmd = "otbcli_ExtractROI -cl "+refl+" -in "+iotaFeatures+" -out "+reflOut
                        print cmd 
                        os.system(cmd)

                        featSample_1 = workingDirectory+"/"+name.replace(".tif","_featSample1.tif")
                        cmd = "otbcli_ExtractROI -cl Channel19 Channel20 -in "+iotaFeatures+" -out "+featSample_1
                        print cmd 
                        os.system(cmd)

                        featSample_2 = workingDirectory+"/"+name.replace(".tif","_featSample2.tif")
                        refl = " ".join(["Channel"+str(i) for i in np.arange(15,19,1)])
                        cmd = "otbcli_ExtractROI -cl "+refl+" -in "+iotaFeatures+" -out "+featSample_2
                        print cmd 
                        os.system(cmd)
                        
                        cmd = "otbcli_ConcatenateImages -il "+reflOut+" "+featSample_1+" "+featSample_2+" -out "+iotaFeatures
                        print cmd
                        os.system(cmd)

                        os.remove(reflOut)
                        os.remove(featSample_1)
                        os.remove(featSample_2)

                test_feat_bm = features_case(self.ref_config_featuresBandMath,self.test_features_bm)
                test_array = rasterToArray(test_feat_bm)

                self.assertTrue(np.array_equal(test_array,ref_array))

                test_feat_iota = features_case(self.ref_config_iota2FeatureExtraction,self.test_features_iota2)
                sortData(test_feat_iota)
                test_array_iota = rasterToArray(test_feat_iota)
                self.assertTrue(np.array_equal(test_array_iota,ref_array))
 
class iota_testShapeManipulations(unittest.TestCase):

	@classmethod
        def setUpClass(self):
		self.referenceShape = iota2_dataTest+"/references/D5H2_groundTruth_samples.shp"
                self.nbFeatures = 28
		self.fields = ['ID', 'LC', 'CODE', 'AREA_HA']
                self.dataField = 'CODE'
                self.epsg = 2154
                self.typeShape = iota2_dataTest+"/references/typo.shp"
                self.regionField = "DN"
                self.priorityEnvelope_ref = iota2_dataTest+"/references/priority_ref"
                self.splitRatio = 0.5               

		self.test_vector = iota2_dataTest+"/test_vector"
                if os.path.exists(self.test_vector):shutil.rmtree(self.test_vector)
                os.mkdir(self.test_vector)     

	def test_CountFeatures(self):
		features = fu.getFieldElement(self.referenceShape,driverName="ESRI Shapefile",field = "CODE",mode = "all",elemType = "int")
		self.assertTrue(len(features)==self.nbFeatures)

	def test_MultiPolygons(self):
		detectMulti = fu.multiSearch(self.referenceShape)
		single = iota2_dataTest+"/test_MultiToSinglePoly.shp"
		fu.multiPolyToPoly(self.referenceShape,single)
		detectNoMulti = fu.multiSearch(single)
		self.assertTrue(detectMulti)
		self.assertFalse(detectNoMulti)

		testFiles = fu.fileSearchRegEx(iota2_dataTest+"/test_*")
		for testFile in testFiles : 
			if os.path.isfile(testFile) : 
				os.remove(testFile)

	def test_getField(self):
		allFields = fu.getAllFieldsInShape(self.referenceShape,"ESRI Shapefile")
		self.assertTrue(self.fields == allFields)

	def test_Envelope(self):

                self.test_envelopeDir = iota2_dataTest+"/test_vector/test_envelope"
                if os.path.exists(self.test_envelopeDir):
                        shutil.rmtree(self.test_envelopeDir)
                os.mkdir(self.test_envelopeDir)

                self.priorityEnvelope_test = self.test_envelopeDir+"/priority_test"
                if os.path.exists(self.priorityEnvelope_test):
                        shutil.rmtree(self.priorityEnvelope_test)
                os.mkdir(self.priorityEnvelope_test)

		#Create a 3x3 grid (9 vectors shapes). Each tile are 110.010 km with 10 km overlaping to fit L8 datas.
		test_genGrid.genGrid(self.test_envelopeDir,X=3,Y=3,overlap=10,size=110.010,raster = "True",pixSize = 30)

		tilesPath = fu.fileSearchRegEx(self.test_envelopeDir+"/*.tif")
		ObjListTile = [tileEnvelope.Tile(currentTile,currentTile.split("/")[-1].split(".")[0]) for currentTile in tilesPath]
		ObjListTile_sort = sorted(ObjListTile,key=tileEnvelope.priorityKey)
                
		tileEnvelope.genTileEnvPrio(ObjListTile_sort,self.priorityEnvelope_test,self.priorityEnvelope_test,self.epsg)
                
                envRef = fu.fileSearchRegEx(self.priorityEnvelope_ref+"/*.shp")
                cmpEnv = [checkSameEnvelope(currentRef,currentRef.replace(self.priorityEnvelope_ref,self.priorityEnvelope_test)) for currentRef in envRef]
                self.assertTrue(all(cmpEnv))
        
        def test_regionsByTile(self):
                
                self.test_regionsByTiles = iota2_dataTest+"/test_vector/test_regionsByTiles"
                if os.path.exists(self.test_regionsByTiles):
                        shutil.rmtree(self.test_regionsByTiles)
                os.mkdir(self.test_regionsByTiles)

                createRegionsByTiles.createRegionsByTiles(self.typeShape, self.regionField,self.priorityEnvelope_ref,self.test_regionsByTiles,None)

        def test_SplitVector(self):

                self.test_split = iota2_dataTest+"/test_vector/test_splitVector"
                if os.path.exists(self.test_split):
                        shutil.rmtree(self.test_split)
                os.mkdir(self.test_split)

                AllTrain, AllValid = RandomInSituByTile.RandomInSituByTile(self.referenceShape,self.dataField,1,self.test_split,\
                                                                           self.splitRatio,None,None,test=True)

                featuresTrain = fu.getFieldElement(AllTrain[0],driverName="ESRI Shapefile",field = "CODE",mode = "all",elemType = "int")
		self.assertTrue(len(featuresTrain)==self.nbFeatures*self.splitRatio)
                featuresValid = fu.getFieldElement(AllValid[0],driverName="ESRI Shapefile",field = "CODE",mode = "all",elemType = "int")
		self.assertTrue(len(featuresValid)==self.nbFeatures*(1-self.splitRatio))


if __name__ == "__main__":
    unittest.main()
