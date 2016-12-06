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

def buildExpression_cloud(Path_Mask):
	
	ds = gdal.Open(Path_Mask, GA_ReadOnly)
	bands = ds.RasterCount

	exp = "-".join(["im1b"+str(band+1) for band in range(bands)])
	return str(bands)+"-"+exp
	
def genNbView(TilePath,maskOut,nbview,workingDirectory = None):
	"""
	"""

	nameNbView = "nbView.tif"
	wd = TilePath
	if workingDirectory:wd = workingDirectory
	tmp1 = wd+"/"+nameNbView

	if not os.path.exists(TilePath+"/"+nameNbView):
		#build stack
		MaskStack = "AllSensorMask.tif"
		maskList = fu.FileSearch_AND(TilePath,True,"_ST_MASK.tif")
		maskList = " ".join(maskList)

		#cmd = "gdalbuildvrt "+TilePath+"/"+MaskStack+" "+maskList
		cmd = "otbcli_ConcatenateImages -il "+maskList+" -out "+TilePath+"/"+MaskStack+" int16"
		print cmd
		os.system(cmd)
	
		exp = buildExpression_cloud(TilePath+"/"+MaskStack)
		tmp2 = maskOut.replace(".shp","_tmp_2.tif").replace(TilePath,wd)

		cmd = 'otbcli_BandMath -il '+TilePath+"/"+MaskStack+' -out '+tmp1+' uint16 -exp "'+exp+'"'
		print cmd
		os.system(cmd)
	
		cmd = 'otbcli_BandMath -il '+tmp1+' -out '+tmp2+' -exp "im1b1>='+str(nbview)+'?1:0"'
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
			shutil.copy(tmp1,TilePath)
			fu.cpShapeFile(wd+"/"+maskOut.split("/")[-1].replace(".shp",""),TilePath,[".prj",".shp",".dbf",".shx"],spe=True)

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This funtion compute a shapeFile which is the representation of availaible pixels")
	parser.add_argument("-path.features",help ="path to the folder which contains features (mandatory)",dest = "tileMaskPath",required=True)
	parser.add_argument("-out",help ="output shapeFile",dest = "maskOut",required=True)
	parser.add_argument("-nbview",help ="nbview threshold",dest = "nbview",required=True)
	parser.add_argument("--wd",dest = "workingDirectory",help ="path to the working directory",default=None,required=False)
	args = parser.parse_args()

	genNbView(args.tileMaskPath,args.maskOut,args.nbview,args.workingDirectory)










































