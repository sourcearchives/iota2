
#!/usr/bin/python

import os
import glob
import sys
import gdal, osr, ogr

def CreateColorTable(fileLUT):
	filein=open(fileLUT)
        ct=gdal.ColorTable()
	for line in filein:
   	   entry = line
   	   classID = entry.split(" ")
           codeColor= [int(i) for i in (classID[1:4])]
           ct.SetColorEntry(int(classID[0]),tuple(codeColor))
        filein.close()	
        return ct

def CreateIndexedColorImage(pszFilename):
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
   if(len(sys.argv)!= 3):
      print "[ ERROR ] you must supply: <LUT file> <Classification file>"
      sys.exit( 1 )
   else:
      fileL = sys.argv[1]
      CreateIndexedColorImage(sys.argv[2])


