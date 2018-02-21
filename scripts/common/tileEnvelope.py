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

import argparse
import sys,os,shutil,subprocess
from config import Config
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from osgeo.gdalconst import *
import fileUtils as fu
import shutil
import serviceConfigFile as SCF
from Utils import run


"""
It's in this script that tile's priority are manage. This priority use tile origin. If you want to change priority, you have to modify
these functions :
erodeDiag and priorityKey
"""

class Tile(object):

    def __init__(self,path,name,testMode=False):
        gtif = gdal.Open(path)
        self.path = path
        if not testMode : self.x = float(gtif.GetGeoTransform()[0])
        else : self.x = 0
        if not testMode : self.y = float(gtif.GetGeoTransform()[3])
        else : self.y = 0
        self.name = name
        self.envelope = "None"
        self.priorityEnv = "None"
    def getX(self):
        return self.x
    def getY(self):
        return self.y
    def getPath(self):
        return self.path
    def getName(self):
        return self.name
    def setEnvelope(self,env):
        self.envelope = env
    def getEnvelope(self):
        return self.envelope
    def getOrigin(self):
        return self.x,self.y
    def getPriorityEnv(self):
        return self.priorityEnv
    def setPriorityEnv(self,priority):
        self.priorityEnv = priority
    def setX(self,xVal):
        self.x = xVal
    def setY(self,yVal):
        self.y = yVal

def createShape(minX,minY,maxX,maxY,out,name,proj=2154):
    """
    create a shape with only one geometry (a rectangle) 
    described by minX,minY,maxX,maxY and save in 'out' as name
    """
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(minX, minY)
    ring.AddPoint(maxX, minY)
    ring.AddPoint(maxX, maxY)
    ring.AddPoint(minX, maxY)
    ring.AddPoint(minX, minY)
        
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)

    #-----------------
    #-- Create output file

    folder = ""

    driver = ogr.GetDriverByName("ESRI Shapefile")
    try:
        output = driver.CreateDataSource(out)
    except ValueError:
        raise Exception("Could not create output datasource "+out)

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(proj)
    newLayer = output.CreateLayer(name,geom_type=ogr.wkbPolygon,srs=srs)
    if newLayer is None:
        raise Exception("Could not create output layer")

    newLayer.CreateField(ogr.FieldDefn("FID", ogr.OFTInteger))
    newLayerDef = newLayer.GetLayerDefn()
    feature = ogr.Feature(newLayerDef)
    feature.SetGeometry(poly)
    ring.Destroy()
    poly.Destroy()
    newLayer.CreateFeature(feature)
        
    output.Destroy()

def subtractShape(shape1,shape2,shapeout,nameShp,proj):

    """
        shape 1 - shape 2 in shapeout/nameshp.shp
    """
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource1 = driver.Open(shape1, 0)
    dataSource2 = driver.Open(shape2, 0)

    layer1 = dataSource1.GetLayer()
    for feature1 in layer1:
        geom_1 = feature1.GetGeometryRef()

    layer2 = dataSource2.GetLayer()
    for feature2 in layer2:
        geom_2 = feature2.GetGeometryRef()

    newgeom = geom_1.Difference(geom_2)
    poly = ogr.Geometry(ogr.wkbPolygon)

    #-----------------
    #-- Create output file
    try:
        output = driver.CreateDataSource(shapeout)
    except ValueError:
        raise Exception('Could not create output datasource '+str(shapeout))
    
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(proj)

    newLayer = output.CreateLayer(nameShp,geom_type=ogr.wkbPolygon,srs=srs)
    if newLayer is None:
        raise Exception("Could not create output layer")

    newLayer.CreateField(ogr.FieldDefn("FID", ogr.OFTInteger))
    newLayerDef = newLayer.GetLayerDefn()
    feature = ogr.Feature(newLayerDef)
    feature.SetGeometry(newgeom)
    newgeom.Destroy()
    poly.Destroy()
    newLayer.CreateFeature(feature)
        
    output.Destroy()

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

def createRasterFootprint(tilePath, commonVecMask, proj=2154):

    #outpolygonize = pathOut.replace(".shp","_TMP.shp")
    #cmd = 'gdal_polygonize.py -mask '+tilePath+' '+tilePath+' -f "ESRI Shapefile" '+outpolygonize
    #run(cmd)

    fu.keepBiggestArea(tilePath.replace(".tif",".shp"), commonVecMask)
    #fu.removeShape(outpolygonize.replace(".shp",""),[".prj",".shp",".dbf",".shx"])
    return commonVecMask

def IsIntersect(shp1,shp2):
    """
        IN :
            shp1,shp2 : 2 tile's envelope (only one polygon by shapes)
        OUT :
            intersect : true or false
    """
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource1 = driver.Open(shp1, 0)
    dataSource2 = driver.Open(shp2, 0)

    layer1 = dataSource1.GetLayer()
    for feature1 in layer1:
        geom1 = feature1.GetGeometryRef()
    layer2 = dataSource2.GetLayer()
    for feature2 in layer2:
        geom2 = feature2.GetGeometryRef()

    intersection = geom1.Intersection(geom2)
    if intersection.GetArea()!=0:
        return True
    return False

def getShapeExtent(shape):

    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(shape, 0)
    layer = dataSource.GetLayer()
    for feature in layer:
        geom = feature.GetGeometryRef()
    return geom.GetEnvelope()#[minX, maxX, minY, maxY]

def erodeInter(currentTile,NextTile,intersection,buff,proj):

    xo,yo = currentTile.getOrigin()
    xn,yn = NextTile.getOrigin()
    Extent = getShapeExtent(intersection)

    if yo == yn and xo!=xn: #left priority
        minX=Extent[0]
        maxX=Extent[1]-buff
        minY=Extent[2]
        maxY=Extent[3]
        
    elif yo != yn and xo==xn: #upper priority
        minX=Extent[0]
        maxX=Extent[1]
        minY=Extent[2]+buff
        maxY=Extent[3]
    
    else:
        return False

    fu.removeShape(intersection.replace(".shp",""),[".prj",".shp",".dbf",".shx"])
    pathFolder = "/".join(intersection.split("/")[0:len(intersection.split("/"))-1])
    createShape(minX,minY,maxX,maxY,pathFolder,intersection.split("/")[-1].replace(".shp",""),proj)
    return True

def diag(currentTile,NextTile):
    xo,yo = currentTile.getOrigin()
    xn,yn = NextTile.getOrigin()
    if not (yo == yn and xo!=xn) and not (yo != yn and xo==xn):
        return True

def priorityKey(item):
    """
        IN :
            item [list of Tile object]
        OUT :
            return tile origin (upper left corner) in order to manage tile's priority
    """
    #return(-item.getX(),item.getY())#other priority
    #return(item.getX(),item.getY())#other priority
    #return(item.getY(),item.getX())#other priority
    #...
    return(-item.getY(),item.getX())#upper left priority 

def erodeDiag(currentTile,NextTile,intersection,buff,TMP,proj):
    
    xo,yo = currentTile.getOrigin()#tuile la plus prio
    xn,yn = NextTile.getOrigin()
    Extent = getShapeExtent(intersection)#[minX, maxX, minY, maxY]
    
    if yo>yn and xo>xn:
        minX=Extent[1]-buff
        maxX=Extent[1]
        minY=Extent[2]
        maxY=Extent[3]

        fu.removeShape(intersection.replace(".shp",""),[".prj",".shp",".dbf",".shx"])
        pathFolder = "/".join(intersection.split("/")[0:len(intersection.split("/"))-1])
        createShape(minX,minY,maxX,maxY,pathFolder,intersection.split("/")[-1].replace(".shp",""),proj)

        tmpName = NextTile.getName()+"_TMP"
        subtractShape(NextTile.getPriorityEnv(),intersection,TMP,tmpName,proj)

        fu.removeShape(NextTile.getPriorityEnv().replace(".shp",""),[".prj",".shp",".dbf",".shx"])
        fu.cpShapeFile(TMP+"/"+tmpName.replace(".shp",""),NextTile.getPriorityEnv().replace(".shp",""),\
                               [".prj",".shp",".dbf",".shx"])
        fu.removeShape(TMP+"/"+tmpName.replace(".shp",""),[".prj",".shp",".dbf",".shx"])
        
        tmpName = currentTile.getName()+"_TMP"
        subtractShape(currentTile.getPriorityEnv(),NextTile.getPriorityEnv(),TMP,tmpName,proj)

        fu.removeShape(currentTile.getPriorityEnv().replace(".shp",""),[".prj",".shp",".dbf",".shx"])
        fu.cpShapeFile(TMP+"/"+tmpName.replace(".shp",""),currentTile.getPriorityEnv().replace(".shp",""),\
                               [".prj",".shp",".dbf",".shx"])
        fu.removeShape(TMP+"/"+tmpName.replace(".shp",""),[".prj",".shp",".dbf",".shx"])

    if yo>yn and xo<xn:

        tmpName = NextTile.getName()+"_TMP"
        subtractShape(NextTile.getPriorityEnv(),currentTile.getPriorityEnv(),TMP,tmpName,proj)

        fu.removeShape(NextTile.getPriorityEnv().replace(".shp",""),[".prj",".shp",".dbf",".shx"])
        fu.cpShapeFile(TMP+"/"+tmpName.replace(".shp",""),NextTile.getPriorityEnv().replace(".shp",""),\
                               [".prj",".shp",".dbf",".shx"])
        fu.removeShape(TMP+"/"+tmpName.replace(".shp",""),[".prj",".shp",".dbf",".shx"])

def genTileEnvPrio(ObjListTile,out,tmpFile,proj):

    buff = 600 #offset in order to manage nodata in image's border

    ObjListTile.reverse()
    listSHP = [createRasterFootprint(c_ObjListTile.getPath(),tmpFile+"/"+c_ObjListTile.getName()+".shp") for c_ObjListTile in ObjListTile]
    
    for env,currentTile in zip(listSHP,ObjListTile):
        currentTile.setEnvelope(env)
        currentTile.setPriorityEnv(env.replace(".shp","_PRIO.shp"))
        fu.cpShapeFile(env.replace(".shp",""),env.replace(".shp","")+"_PRIO",[".prj",".shp",".dbf",".shx"])
    
    for i in range(len(ObjListTile)):
        currentTileEnv = ObjListTile[i].getEnvelope()
        for j in range(1+i,len(ObjListTile)):
            NextTileEnv = ObjListTile[j].getEnvelope()
            if IsIntersect(currentTileEnv,NextTileEnv):

                InterName = ObjListTile[i].getName()+"_inter_"+ObjListTile[j].getName()
                intersection = fu.ClipVectorData(ObjListTile[i].getEnvelope(),ObjListTile[j].getEnvelope(),\
                                                                 tmpFile,InterName)
                notDiag = erodeInter(ObjListTile[i],ObjListTile[j],intersection,buff,proj)
                if notDiag:
                    tmpName = ObjListTile[i].getName()+"_TMP"
                    subtractShape(ObjListTile[i].getPriorityEnv(),intersection,tmpFile,tmpName,proj)

                    fu.removeShape(ObjListTile[i].getPriorityEnv().replace(".shp",""),\
                                                       [".prj",".shp",".dbf",".shx"])
                    fu.cpShapeFile(tmpFile+"/"+tmpName.replace(".shp",""),\
                                                       ObjListTile[i].getPriorityEnv().replace(".shp",""),\
                                                       [".prj",".shp",".dbf",".shx"])
                    fu.removeShape(tmpFile+"/"+tmpName.replace(".shp",""),[".prj",".shp",".dbf",".shx"])

    ObjListTile.reverse()
    for i in range(len(ObjListTile)):
        currentTileEnv = ObjListTile[i].getEnvelope()
        for j in range(1+i,len(ObjListTile)):
            NextTileEnv = ObjListTile[j].getEnvelope()
            if IsIntersect(currentTileEnv,NextTileEnv) :
                if diag(ObjListTile[i],ObjListTile[j]):
                    InterName = ObjListTile[i].getName()+"_inter_"+ObjListTile[j].getName()
                    intersection = fu.ClipVectorData(ObjListTile[i].getEnvelope(),ObjListTile[j].getEnvelope(),\
                                                                         tmpFile,InterName)
                    erodeDiag(ObjListTile[i],ObjListTile[j],intersection,buff,tmpFile,proj)
                else  :
                    tmpName = ObjListTile[i].getName()+"_TMP"
                    subtractShape(ObjListTile[i].getPriorityEnv(),ObjListTile[j].getPriorityEnv(),\
                                                      tmpFile,tmpName,proj)

                    fu.removeShape(ObjListTile[i].getPriorityEnv().replace(".shp",""),\
                                                       [".prj",".shp",".dbf",".shx"])
                    fu.cpShapeFile(tmpFile+"/"+tmpName.replace(".shp",""),\
                                                       ObjListTile[i].getPriorityEnv().replace(".shp",""),\
                                                       [".prj",".shp",".dbf",".shx"])
                    fu.removeShape(tmpFile+"/"+tmpName.replace(".shp",""),[".prj",".shp",".dbf",".shx"])


def GenerateShapeTile(tiles, pathTiles, pathOut, pathWd, cfg):

    if not isinstance(cfg,SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)
    pathConf = cfg.pathConf
    import ConfigParser
    fu.cleanFiles(cfg)
    featuresPath = cfg.getParam('chain', 'featuresPath')
    cMaskName = fu.getCommonMaskName(cfg)
    for tile in tiles :
        if not os.path.exists(featuresPath + "/" + tile):
            os.mkdir(featuresPath + "/" + tile)
            os.mkdir(featuresPath+"/"+tile+"/tmp")
    commonDirectory = pathOut + "/commonMasks/"
    if not os.path.exists(commonDirectory):
        os.mkdir(commonDirectory)

    common = [featuresPath+"/"+Ctile+"/tmp/"+cMaskName+".tif" for Ctile in tiles]

    tmp_proj = cfg.getParam('GlobChain', 'proj')
    proj = int(tmp_proj.split(":")[-1])

    ObjListTile = [Tile(currentTile,name) for currentTile,name in zip(common,tiles)]
    ObjListTile_sort = sorted(ObjListTile, key=priorityKey)

    tmpFile = pathOut + "/TMP"

    if pathWd:
        tmpFile = pathWd + "/TMP"
    if not os.path.exists(tmpFile):
        os.mkdir(tmpFile)
    genTileEnvPrio(ObjListTile_sort, pathOut, tmpFile, proj)
    AllPRIO = fu.FileSearch_AND(tmpFile, True, "_PRIO.shp")
    for prioTile in AllPRIO:
        tileName = prioTile.split("/")[-1].split("_")[0]
        fu.cpShapeFile(prioTile.replace(".shp",""), pathOut + "/" + tileName, [".prj",".shp",".dbf",".shx"])
        
    shutil.rmtree(tmpFile)
    shutil.rmtree(commonDirectory)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "This function allow you to generate tile's envelope considering tile's priority")
    parser.add_argument("-t",dest = "tiles",help ="All the tiles", nargs='+',required=True)
    parser.add_argument("-t.path",dest = "pathTiles",help ="where are stored features",required=True)
    parser.add_argument("-out",dest = "pathOut",help ="path out",required=True)
    parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
    parser.add_argument("-conf",help ="path to the configuration file which describe the learning method (mandatory)",dest = "pathConf",required=True)
    args = parser.parse_args()
    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)
    # launch GenerateShapeTile
    GenerateShapeTile(args.tiles, args.pathTiles, args.pathOut, args.pathWd, cfg)

