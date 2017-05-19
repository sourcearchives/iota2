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
import os,unittest,Sensors,Utils,filecmp,string,random,shutil,sys,osr
import subprocess,RandomInSituByTile,createRegionsByTiles
import fileUtils as fu
import test_genGrid as test_genGrid
import tileEnvelope
from gdalconst import *
from osgeo import gdal
from config import Config
import numpy as np

#export PYTHONPATH=$PYTHONPATH:/mnt/data/home/vincenta/modulePy/config-0.3.9       -> get python Module
#export PYTHONPATH=$PYTHONPATH:/mnt/data/home/vincenta/theia_oso/data/test_scripts -> get scripts needed to test
#export IOTA2DIR=/mnt/data/home/vincenta/theia_oso

#python -m unittest iota2tests

iota2dir = os.environ.get('IOTA2DIR')
iota2_script = os.environ.get('IOTA2DIR')+"/scripts/common"
iota2_dataTest = os.environ.get('IOTA2DIR')+"/data/"

def rasterToArray(InRaster):
        arrayOut = None
        ds = gdal.Open(InRaster)
        myarray = np.array(ds.GetRasterBand(1).ReadAsArray())
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
                self.ref_bandMath = iota2_dataTest+"/references/features/SL_MultiTempGapF_Brightness_NDVI_NDWI__.tif"
                self.ref_config_iota2FeatureExtraction = iota2_dataTest+"/config/test_config_iota2FeatureExtraction.cfg"
                self.ref_iota2FeatureExtraction = iota2_dataTest+"/references/features/SL_MultiTempGapF_Brightness_NDVI_NDWI__.tif"

        def test_Features(self):
                import genCmdFeatures

                if not os.path.exists(self.ref_L8Directory):self.assertTrue(True==False)

                def features_case(configPath,ref,workingDirectory):
                        #features bandMath computed 
                        MyCmd = genCmdFeatures.CmdFeatures("",["D0005H0002"],self.scripts,\
                                                           self.ref_L8Directory,"None","None",\
                                                           configPath,workingDirectory\
                                                           ,None,testMode=True)
                        self.assertTrue(len(MyCmd)==1)
                        subprocess.call(MyCmd[0],shell=True)
                        test_features = fu.FileSearch_AND(workingDirectory,True,"SL_MultiTempGapF_Brightness_NDVI_NDWI__.tif")[0]
                        test_array = rasterToArray(test_features)
                        ref_array = rasterToArray(ref)
                        self.assertTrue(np.array_equal(test_array,ref_array))

                features_case(self.ref_config_featuresBandMath,self.ref_bandMath,self.test_features_bm)
                features_case(self.ref_config_iota2FeatureExtraction,self.ref_iota2FeatureExtraction,self.test_features_iota2)
                
        def test_Confidence(self):
                print " "
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
