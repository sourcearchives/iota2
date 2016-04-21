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
import unittest
import os
import Sensors
import Utils
import filecmp
import fileUtils as fu
from gdalconst import *
from osgeo import gdal
from config import Config

iota2Dir = os.environ.get('IOTA2DIR')

#python -m unittest iota2tests.iota_testSeq

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

def checkSameGroundTruth(shapes,imrefs,datafield,tmpPath = "/mnt/data/home/vincenta/tmp"):
	"""
	IN : 
		shape1 [string] : path to shape
			ex : path/to/myShape.shp
		shape2 [string] : path to shape
			ex : path/to/myShape.shp
		tmpPath [string] : path to a tmp folder
	OUT : 
		return True if shapeFiles are the same
	"""

	rasters = [shapes[0].split(".")[0]+"_raster.tif",shapes[-1].split(".")[0]+"_raster.tif"]
	for raster in rasters:
		if os.path.exists(raster):
			os.remove(raster)

	for shape,imref,raster in zip(shapes,imrefs,rasters):
		cmd = "otbcli_Rasterization -in "+shape+" -out "+raster+" -im "+imref+" -mode attribute -mode.attribute.field "+datafield
		print cmd
		os.system(cmd)

	#difference
	diffRaster = tmpPath+"/diff_raster.tif"
	if os.path.exists(diffRaster):
		os.remove(diffRaster)
	if os.path.exists(diffRaster+".aux.xml"):
		os.remove(diffRaster+".aux.xml")

	cmd = "otbcli_BandMath -il "+rasters[0]+" "+rasters[1]+" -out "+diffRaster+' -exp "abs(im1b1-im2b1)"'
	print cmd 
	os.system(cmd)

	gtif = gdal.Open(diffRaster,GA_ReadOnly)

	srcband = gtif.GetRasterBand(1)
	stats = srcband.GetStatistics(True, True)
	
	for raster in rasters:
		os.remove(raster)

	if stats[0]==stats[1]==0:
		return True
	return False

def checkSameEnvelope(EvRef,EvTest):

	miX_ref,miY_ref,maX_ref,maY_ref = fu.getShapeExtent(EvRef)
	miX_test,miY_test,maX_test,maY_test = fu.getShapeExtent(EvTest)

	if (miX_ref == miX_test) and (miY_test==miY_test) and (maX_ref==maX_test) and (maY_ref==maY_test):
		return True
	return False

class iota_testSeq(unittest.TestCase):

	@classmethod
        def setUpClass(self):
		#get config test
		self.cfg = Config("/mnt/data/home/vincenta/THEIA_OSO/theia_oso/data/config_test/test_4Tiles_seq_L8_Fusion.cfg")
		self.configTest_seq = self.cfg.test.test_config
		self.pyApp = self.cfg.test.test_pyApp
		self.ref_path = iota2Dir+"/"+self.cfg.ref.ref_path
		self.test_path = iota2Dir+"/"+self.cfg.test.test_path
		self.dataField = self.cfg.common.dataField
		self.shp_GT_D0007H0004 = self.cfg.common.shp_GT_D0007H0004
		self.shp_GT_D0007H0003 = self.cfg.common.shp_GT_D0007H0003
		self.shp_GT_D0006H0004 = self.cfg.common.shp_GT_D0006H0004
		self.shp_GT_D0006H0003 = self.cfg.common.shp_GT_D0006H0003

		self.shp_Ev_D0007H0004 = self.cfg.common.shp_Ev_D0007H0004
		self.shp_Ev_D0007H0003 = self.cfg.common.shp_Ev_D0007H0003
		self.shp_Ev_D0006H0004 = self.cfg.common.shp_Ev_D0006H0004
		self.shp_Ev_D0006H0003 = self.cfg.common.shp_Ev_D0006H0003

		self.imRefRef = self.ref_path+"/final/Classif_Seed_0.tif"
		self.imRefTest = self.test_path+"/final/Classif_Seed_0.tif"

		self.cmdFeatures_ref = self.ref_path+"/cmd/features/features.txt"
		self.cmdFeatures_test = self.test_path+"/cmd/features/features.txt"
		self.cmdStats_ref = self.ref_path+"/cmd/stats/stats.txt"
		self.cmdStats_test = self.test_path+"/cmd/stats/stats.txt"
		self.cmdTrain_ref = self.ref_path+"/cmd/train/train.txt"
		self.cmdTrain_test = self.test_path+"/cmd/train/train.txt"
		self.cmdClassif_ref = self.ref_path+"/cmd/cla/class.txt"
		self.cmdClassif_test = self.test_path+"/cmd/cla/class.txt"
		self.cmdConfusion_ref = self.ref_path+"/cmd/confusion/confusion.txt"
		self.cmdConfusion_test = self.test_path+"/cmd/confusion/confusion.txt"
		self.cmdFusion_ref = self.ref_path+"/cmd/fusion/fusion.txt"
		self.cmdFusion_test = self.test_path+"/cmd/fusion/fusion.txt"

		self.region_ref = iota2Dir+"/"+self.cfg.ref.region_ref
		self.region_test = iota2Dir+"/"+self.cfg.test.region_test
		self.regionField = self.cfg.common.regionField
	
		self.tmpDir = self.cfg.common.tmpDir

		print "Launching the chain to test"
        	#os.system("bash "+self.pyApp+"/launchChain.sh "+self.configTest_seq)

	#Test if cmd are the same
	def test_cmdFeatures(self):
		same = filecmp.cmp(self.cmdFeatures_ref,self.cmdFeatures_test)
		self.assertTrue(same)
	def test_cmdStats(self):
		same = checkSameFile([self.cmdStats_ref,self.cmdStats_test])
		self.assertTrue(same)
	def test_cmdTrain(self):
		same = checkSameFile([self.cmdTrain_ref,self.cmdTrain_test])
		self.assertTrue(same)
	def test_cmdClassif(self):
		same = checkSameFile([self.cmdClassif_ref,self.cmdClassif_test])
		self.assertTrue(same)
	def test_cmdConfusion(self):
		same = checkSameFile([self.cmdConfusion_ref,self.cmdConfusion_test])
		self.assertTrue(same)
	def test_cmdFusion(self):
		same = checkSameFile([self.cmdFusion_ref,self.cmdFusion_test])
		self.assertTrue(same)

	#Test if envelopes are the same 
	def test_sameEnvelope_D0007H0004(self):
		EvRef = self.ref_path+self.shp_Ev_D0007H0004
		EvTest = self.test_path+self.shp_Ev_D0007H0004
		same = checkSameEnvelope(EvRef,EvTest)
		self.assertTrue(same)
	
	def test_sameEnvelope_D0007H0003(self):
		EvRef = self.ref_path+self.shp_Ev_D0007H0003
		EvTest = self.test_path+self.shp_Ev_D0007H0003
		same = checkSameEnvelope(EvRef,EvTest)
		self.assertTrue(same)

	def test_sameEnvelope_D0006H0004(self):
		EvRef = self.ref_path+self.shp_Ev_D0006H0004
		EvTest = self.test_path+self.shp_Ev_D0006H0004
		same = checkSameEnvelope(EvRef,EvTest)
		self.assertTrue(same)

	def test_sameEnvelope_D0006H0003(self):
		EvRef = self.ref_path+self.shp_Ev_D0006H0003
		EvTest = self.test_path+self.shp_Ev_D0006H0003
		same = checkSameEnvelope(EvRef,EvTest)
		self.assertTrue(same)

	#Tet if region shape are the same
	def test_regionShape(self):
		reg_ref = self.region_ref
		reg_test = self.region_test
		same = checkSameGroundTruth([reg_ref,reg_test],[self.imRefRef,self.imRefTest],self.regionField,tmpPath = self.tmpDir)
		self.assertTrue(same)

	#Test if the ground truth by tiles are the same
	def test_sameGroundTruth_D0007H0003(self):
		shpRef = self.ref_path+self.shp_GT_D0007H0003
		shpTest = self.test_path+self.shp_GT_D0007H0003
		same = checkSameGroundTruth([shpRef,shpTest],[self.imRefRef,self.imRefTest],self.dataField,tmpPath = self.tmpDir)
		self.assertTrue(same)

	def test_sameGroundTruth_D0006H0003(self):
		shpRef = self.ref_path+self.shp_GT_D0006H0003
		shpTest = self.test_path+self.shp_GT_D0006H0003
		same = checkSameGroundTruth([shpRef,shpTest],[self.imRefRef,self.imRefTest],self.dataField,tmpPath = self.tmpDir)
		self.assertTrue(same)

	def test_sameGroundTruth_D0007H0004(self):
		shpRef = self.ref_path+self.shp_GT_D0007H0004
		shpTest = self.test_path+self.shp_GT_D0007H0004
		same = checkSameGroundTruth([shpRef,shpTest],[self.imRefRef,self.imRefTest],self.dataField,tmpPath = self.tmpDir)
		self.assertTrue(same)

	def test_sameGroundTruth_D0006H0004(self):
		shpRef = self.ref_path+self.shp_GT_D0006H0003
		shpTest = self.test_path+self.shp_GT_D0006H0003
		same = checkSameGroundTruth([shpRef,shpTest],[self.imRefRef,self.imRefTest],self.dataField,tmpPath = self.tmpDir)
		self.assertTrue(same)
	

class iotaTestname(unittest.TestCase):

	def setUp(self):
		pass

    	def tearDown(self):
        	pass

	"""
    	def testLandsat8Name(self):
        	name = Sensors.Landsat8("",Utils.Opath(testDir+"/tsts"),\
        	iota2Dir+"/data/Config_1tile.cfg",0).name
        	self.assertEqual(name, 'Landsat8')
	"""

    	def testLaunchChain(self):
       		import launchChain as lc
        	#lc.launchChain(iota2Dir+"/data/ConfigDummyParallel.cfg", False)
        	""" TODO: valider les fichiers générés, les copier dans data, puis
        	vérifier que ceux qui sont générés à l'exécution du test, sont
        	identiques (test de non régression) """



if __name__ == "__main__":
    unittest.main()
