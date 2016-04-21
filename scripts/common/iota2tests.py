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
from osgeo import ogr

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

def checkSameShapeFile(shape1,shape2,tmpPath = "/mnt/data/home/vincenta/tmp"):
	"""
	IN : 
		shape1 [string] : path to shape
			ex : path/to/myShape.shp
		shape2 [string] : path to shape
			ex : path/to/myShape.shp
	OUT : 
		return True if shapeFiles are the same
	"""

	#check fields

	pathToClip = fu.ClipVectorData(shape1, shape2, tmpPath)
	
	driver = ogr.GetDriverByName("ESRI Shapefile")
	dataSource = driver.Open(pathToClip, 0)
	layer = dataSource.GetLayer()

	Nbfeat = 0
	for feature in layer:
    		Nbfeat+=1
	if Nbfeat !=0:
		return False
	
	return True
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

	def test_sameGroundTruth(self):
		same = checkSameShapeFile(res_ref_seq+"/dataRegion/FakeData_France_MaskCommunSL_regionTestL8_region_1_D0007H0003.shp",res_test_seq+"/dataRegion/FakeData_France_MaskCommunSL_regionTestL8_region_1_D0006H0003.shp")
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
