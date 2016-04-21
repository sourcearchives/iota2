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

testDir = "/tmp/"
iota2Dir = os.environ.get('IOTA2DIR')

#python -m unittest iota2tests.iota_testSeq
configTest_seq = "/mnt/data/home/vincenta/THEIA_OSO/theia_oso/data/Config_4Tiles_L8.cfg"
pyApp = "/mnt/data/home/vincenta/THEIA_OSO/theia_oso/scripts/common"

res_ref_seq = "/mnt/data/home/vincenta/THEIA_OSO/theia_oso/data/res_ref/res_L8_seq"
res_test_seq = "/mnt/data/home/vincenta/THEIA_OSO/theia_oso/data/res_test/res_L8_seq"

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

def checkSameShapeFile(shapes,imrefs,datafield,tmpPath = "/mnt/data/home/vincenta/tmp"):
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

class iota_testSeq(unittest.TestCase):

	@classmethod
        def setUpClass(self):
		print "Lancement de la chaine test"
        	#os.system("bash "+pyApp+"/launchChain.sh "+configTest_seq)

	#Test if cmd are the same
	def test_cmdFeatures(self):
		same = filecmp.cmp(res_ref_seq+"/cmd/features/features.txt",res_test_seq+"/cmd/features/features.txt")
		self.assertTrue(same)
	def test_cmdStats(self):
		same = checkSameFile([res_ref_seq+"/cmd/stats/stats.txt",res_test_seq+"/cmd/stats/stats.txt"])
		self.assertTrue(same)
	def test_cmdTrain(self):
		same = checkSameFile([res_ref_seq+"/cmd/train/train.txt",res_test_seq+"/cmd/train/train.txt"])
		self.assertTrue(same)
	def test_cmdClassif(self):
		same = checkSameFile([res_ref_seq+"/cmd/cla/class.txt",res_test_seq+"/cmd/cla/class.txt"])
		self.assertTrue(same)
	def test_cmdConfusion(self):
		same = checkSameFile([res_ref_seq+"/cmd/confusion/confusion.txt",res_test_seq+"/cmd/confusion/confusion.txt"])
		self.assertTrue(same)
	def test_cmdFusion(self):
		same = checkSameFile([res_ref_seq+"/cmd/fusion/fusion.txt",res_test_seq+"/cmd/fusion/fusion.txt"])
		self.assertTrue(same)

	#Test if envelopes are the same 
		
	#Test if the ground truth by tiles are the same
	def test_sameGroundTruth_D0007H0003(self):
		shp1 = res_ref_seq+"/dataRegion/FakeData_France_MaskCommunSL_regionTestL8_region_1_D0007H0003.shp"
		shp2 =  res_test_seq+"/dataRegion/FakeData_France_MaskCommunSL_regionTestL8_region_1_D0007H0003.shp"
		imref1 = res_ref_seq+"/final/Classif_Seed_0.tif"
		imref2 = res_test_seq+"/final/Classif_Seed_0.tif"
		dataField = "CODE"
		same = checkSameShapeFile([shp1,shp2],[imref1,imref2],dataField)
		self.assertTrue(same)

	def test_sameGroundTruth_D0006H0003(self):
		shp1 = res_ref_seq+"/dataRegion/FakeData_France_MaskCommunSL_regionTestL8_region_1_D0006H0003.shp"
		shp2 =  res_test_seq+"/dataRegion/FakeData_France_MaskCommunSL_regionTestL8_region_1_D0006H0003.shp"
		imref1 = res_ref_seq+"/final/Classif_Seed_0.tif"
		imref2 = res_test_seq+"/final/Classif_Seed_0.tif"
		dataField = "CODE"
		same = checkSameShapeFile([shp1,shp2],[imref1,imref2],dataField)
		self.assertTrue(same)

	def test_sameGroundTruth_D0007H0004(self):
		shp1 = res_ref_seq+"/dataRegion/FakeData_France_MaskCommunSL_regionTestL8_region_2_D0007H0004.shp"
		shp2 =  res_test_seq+"/dataRegion/FakeData_France_MaskCommunSL_regionTestL8_region_2_D0007H0004.shp"
		imref1 = res_ref_seq+"/final/Classif_Seed_0.tif"
		imref2 = res_test_seq+"/final/Classif_Seed_0.tif"
		dataField = "CODE"
		same = checkSameShapeFile([shp1,shp2],[imref1,imref2],dataField)
		self.assertTrue(same)

	def test_sameGroundTruth_D0006H0004(self):
		shp1 = res_ref_seq+"/dataRegion/FakeData_France_MaskCommunSL_regionTestL8_region_2_D0006H0004.shp"
		shp2 =  res_test_seq+"/dataRegion/FakeData_France_MaskCommunSL_regionTestL8_region_2_D0006H0004.shp"
		imref1 = res_ref_seq+"/final/Classif_Seed_0.tif"
		imref2 = res_test_seq+"/final/Classif_Seed_0.tif"
		dataField = "CODE"
		same = checkSameShapeFile([shp1,shp2],[imref1,imref2],dataField)
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
