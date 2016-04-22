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

import glob,argparse,sys,os,gdal,osr,ogr

def CreateColorTable(fileLUT):
	"""
	IN : 
		fileLUT [string] : path to the color file table
			ex : for a table containing 3 classes ("8","90","21"), "8" must be represent in red, "90" in green, "21" in blue
	"""
	filein=open(fileLUT)
        ct=gdal.ColorTable()
	for line in filein:
   	   entry = line
   	   classID = entry.split(" ")
           codeColor= [int(i) for i in (classID[1:4])]
           ct.SetColorEntry(int(classID[0]),tuple(codeColor))
        filein.close()	
        return ct

def CreateIndexedColorImage(pszFilename,fileL):
	indataset = gdal.Open( pszFilename, gdal.GA_ReadOnly)
        if indataset is None:
		print 'Could not open '+pszFilename
		sys.exist(1)
	outpath = pszFilename.split('/')
	if len(outpath)==1:
		outname = os.getcwd()+'/'+outpath[0].split('.')[0]+'_ColorIndexed.tif'
	else:
		outname = '/'.join(outpath[0:-1])+'/'+outpath[-1].split('.')[0]+'_ColorIndexed.tif'
	inband = indataset.GetRasterBand(1)
	gt = indataset.GetGeoTransform()
	driver = gdal.GetDriverByName("GTiff")
	outdataset=driver.Create(outname,indataset.RasterXSize,indataset.RasterYSize,1, gdal.GDT_Byte)
	if gt is not None and gt != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
   		outdataset.SetGeoTransform(gt)
	prj = indataset.GetProjectionRef()
	if prj is not None and len(prj) > 0:
   		outdataset.SetProjection(prj)
	inarray = inband.ReadAsArray(0, 0)
	ct=CreateColorTable(fileL)
	outband=outdataset.GetRasterBand(1)
	outband.SetColorTable(ct)
	outband.WriteArray(inarray)
	print 'The file '+outname+' has been created'

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you to generate an image of classification with color")
	parser.add_argument("-color ",dest = "color",help ="path to the color file (mandatory)",required=True)
	parser.add_argument("-classification",dest = "pathClassification",help ="path out",required=True)
	args = parser.parse_args()

	CreateIndexedColorImage(args.pathClassification,args.color)



