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

import sys,os,shutil,glob,math,tarfile
from config import Config

from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from osgeo.gdalconst import *

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
	
	
def erodeOrDilateShapeFile(infile,buffdist):

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

	#Stack_ind = "SL_MultiTempGapF_"+listFeat+"__.tif"
	Stack_ind = "SL_MultiTempGapF_"+listFeat+"__.vrt"
	return Stack_ind

def writeCmds(path,cmds):

	cmdFile = open(path,"w")
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
