#!/usr/bin/python
#-*- coding: utf-8 -*-
# =========================================================================
#   Program:   S1Processor
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
#
# Authors: Thierry KOLECK (CNES)
#
# =========================================================================


import os
import ogr

class S1FileManager(object):

   def __init__(self,configFile):
      import ConfigParser

      config = ConfigParser.ConfigParser()
      config.read(configFile)

      self.mgrs_shapeFile= config.get('Processing','TilesShapefile')
      if os.path.exists(self.mgrs_shapeFile)==False:
         print "ERROR: "+self.mgrs_shapeFile+" is a wrong path"
         exit(1)

      self.srtm_shapeFile = config.get('Processing','SRTMShapefile')
      if os.path.exists(self.srtm_shapeFile)==False:
         print "ERROR: "+self.srtm_shapeFile+" is a wrong path"
         exit(1)

      self.raw_directory = config.get('Paths','S1Images')

      self.outputPreProcess = config.get('Paths','Output')

      self.VH_pattern = "measurement/*vh*-???.tiff"
      self.VV_pattern = "measurement/*vv*-???.tiff"
      self.HH_pattern = "measurement/*hh*-???.tiff"
      self.HV_pattern = "measurement/*hv*-???.tiff"
      self.manifest_pattern = "manifest.safe" 

      self.tilesList=config.get('Processing','Tiles').split(",")
      self.tileToProductOverlapRatio = float(config.get('Processing','TileToProductOverlapRatio'))
      
      self.stdoutfile=open("/dev/null",'w')
      self.stderrfile=open("S1ProcessorErr.log",'a')
      if "logging" in config.get('Processing','Mode').lower():
         self.stdoutfile=open("S1ProcessorOut.log",'a')
         self.stderrfile=open("S1ProcessorErr.log",'a')
      if "debug" in config.get('Processing','Mode').lower():
         self.stdoutfile=None
         self.stderrfile=None

      self.ProcessedFilenames=self.GetProcessedFilenames()
      self.getS1Img()
      try:
         os.makedirs(self.raw_directory)
      except:
         pass

   def downloadImages(self):
      import numpy as np
      from subprocess import Popen
      import shlex
      import zipfile
      import time
      if self.pepsdownload==True:
         if self.ROIbyTiles is not None:
            if "ALL" in self.ROIbyTiles:
               tilesList=self.tilesList
            else:
               tilesList=self.ROIbyTiles
            latmin=[]
            latmax=[]
            lonmin=[]
            lonmax=[]
            driver = ogr.GetDriverByName("ESRI Shapefile")
            dataSource = driver.Open(self.mgrs_shapeFile, 0)
            layer = dataSource.GetLayer()
            for currentTile in layer:

               if currentTile.GetField('NAME') in tilesList:
                  tileFootPrint = currentTile.GetGeometryRef().GetGeometryRef(0)
                  latmin=np.min([p[1] for p in tileFootPrint.GetPoints()])
                  latmax=np.max([p[1] for p in tileFootPrint.GetPoints()])
                  lonmin=np.min([p[0] for p in tileFootPrint.GetPoints()])
                  lonmax=np.max([p[0] for p in tileFootPrint.GetPoints()])      
                  command="python "+self.pepscommand+" --lonmin "+str(lonmin)+" --lonmax "+str(lonmax)+" --latmin "+str(latmin)+" --latmax "+str(latmax)+" -w "+self.raw_directory
                  print command
                  status=-1
                  while status<>0:
                     pid=Popen(command,stdout=None,stderr=None,shell=True)
                     while pid.poll() is None: 
                        self.unzipImages()
                        time.sleep(20)
                     status=pid.poll()
         else:
            command="python "+self.pepscommand+" --lonmin "+str(self.ROIbyCoordinates[0])+" --lonmax "+str(self.ROIbyCoordinates[2])+" --latmin "+str(self.ROIbyCoordinates[1])+" --latmax "+str(self.ROIbyCoordinates[3])+" -w "+self.raw_directory
            print command
            status=-1
            while status<>0:
               pid=Popen(command,stdout=None,stderr=None,shell=True)
               while pid.poll() is None: 
                  self.unzipImages()
                  time.sleep(20)
               status=pid.poll()
         self.unzipImages()
         self.getS1Img()

   def unzipImages(self):
      import zipfile
      for f in os.walk(self.raw_directory).next()[2]:
         if ".zip" in f:
            print "unzipping "+f
            try:
               zip_ref = zipfile.ZipFile(self.raw_directory+"/"+f, 'r')
               zip_ref.extractall(self.raw_directory)
               zip_ref.close()
            except  zipfile.BadZipfile:
               print "WARNING: "+self.raw_directory+"/"+f+" is corrupted. This file will be removed"
            os.remove(self.raw_directory+"/"+f)


   def getS1Img(self):
      import glob
      self.rawRasterList = []
      self.NbImages=0
      if os.path.exists(self.raw_directory)==False:
         os.makedirs(self.raw_directory)
         return
      content = os.listdir(self.raw_directory)
      for currentContent in content:
         safeDir = os.path.join(self.raw_directory,currentContent)
	 if os.path.isdir(safeDir)==True:
	    manifest = os.path.join(safeDir,self.manifest_pattern)
            acquisition=S1_DateAcquisition(manifest,[])
	    vv = [f for f in glob.glob(os.path.join(safeDir,self.VV_pattern))]
            for vvImage in vv:
               if vvImage not in self.ProcessedFilenames:
                  acquisition.AddImage(vvImage)
                  self.NbImages+=1
	    vh = [f for f in glob.glob(os.path.join(safeDir,self.VH_pattern))]
            for vhImage in vh:
               if vhImage not in self.ProcessedFilenames:
                  acquisition.AddImage(vhImage)
                  self.NbImages+=1
            hh = [f for f in glob.glob(os.path.join(safeDir,self.HH_pattern))]
            for hhImage in hh:
               if hhImage not in self.ProcessedFilenames:
                  acquisition.AddImage(hhImage)
                  self.NbImages+=1
            hv = [f for f in glob.glob(os.path.join(safeDir,self.HV_pattern))]
            for hvImage in hv:
               if hvImage not in self.ProcessedFilenames:
                  acquisition.AddImage(hvImage)
                  self.NbImages+=1
                  
	    self.rawRasterList.append(acquisition)

   def tileExists(self,tileNameField):
      driver = ogr.GetDriverByName("ESRI Shapefile")
      dataSource = driver.Open(self.mgrs_shapeFile, 0)
      layer = dataSource.GetLayer()

      for currentTile in layer:
         if currentTile.GetField('NAME')==tileNameField:
            return True
            break
      return False

   def getTilesCoveredByProducts(self):
      tiles = []
      
      driver = ogr.GetDriverByName("ESRI Shapefile")
      dataSource = driver.Open(self.mgrs_shapeFile, 0)
      layer = dataSource.GetLayer()
      
      #Loop on images
      for image in self.rawRasterList:
         manifest = image.getManifest()
         NW,NE,SE,SW = self.getOrigin(manifest)

         poly = ogr.Geometry(ogr.wkbPolygon)
         ring = ogr.Geometry(ogr.wkbLinearRing)
	 ring.AddPoint(NW[1], NW[0],0)
	 ring.AddPoint(NE[1], NE[0],0)
	 ring.AddPoint(SE[1], SE[0],0)
	 ring.AddPoint(SW[1], SW[0],0)
	 ring.AddPoint(NW[1], NW[0],0)
	 poly.AddGeometry(ring)

         for currentTile in layer:
            tileFootPrint = currentTile.GetGeometryRef()
            intersection = poly.Intersection(tileFootPrint)
            if intersection.GetArea()/tileFootPrint.GetArea()>self.tileToProductOverlapRatio:
               tileName = currentTile.GetField('NAME')
               if tileName not in tiles:
                  tiles.append(tileName)
      return tiles
            
   def getS1IntersectByTile(self,tileNameField):
      intersectRaster=[]
      driver = ogr.GetDriverByName("ESRI Shapefile")
      dataSource = driver.Open(self.mgrs_shapeFile, 0)
      layer = dataSource.GetLayer()
      found = False
      for currentTile in layer:
         if currentTile.GetField('NAME')==tileNameField:
            found = True
            break
      if not found:
         print "Tile "+str(tileNameField)+" does not exist"
         return intersectRaster
               
      poly = ogr.Geometry(ogr.wkbPolygon)
      tileFootPrint = currentTile.GetGeometryRef()

      for image in self.rawRasterList:
         manifest = image.getManifest()
         NW,NE,SE,SW = self.getOrigin(manifest)

         poly = ogr.Geometry(ogr.wkbPolygon)
         ring = ogr.Geometry(ogr.wkbLinearRing)
	 ring.AddPoint(NW[1], NW[0],0)
	 ring.AddPoint(NE[1], NE[0],0)
	 ring.AddPoint(SE[1], SE[0],0)
	 ring.AddPoint(SW[1], SW[0],0)
	 ring.AddPoint(NW[1], NW[0],0)
	 poly.AddGeometry(ring)
   
	 intersection = poly.Intersection(tileFootPrint)
         if intersection.GetArea()!=0:
            area_polygon= tileFootPrint.GetGeometryRef(0)
            points=area_polygon.GetPoints()
            intersectRaster.append((image,[(point[0],point[1]) for point in points[:-1]]))

      return intersectRaster

   def getMGRSTileGeometryByName(self,mgrsTileName):
      driver = ogr.GetDriverByName("ESRI Shapefile")
      mgrs_ds = driver.Open(self.mgrs_shapeFile, 0)
      mgrs_layer = mgrs_ds.GetLayer()
      
      for mgrsTile in mgrs_layer:
            if mgrsTile.GetField('NAME') ==mgrsTileName:
               return mgrsTile.GetGeometryRef().Clone()
      raise "MGRS tile does not exist",mgrsTileName


   
         
   def checkSRTMCoverage(self,tilesToProcess):
      driver = ogr.GetDriverByName("ESRI Shapefile")                
      srtm_ds = driver.Open(self.srtm_shapeFile, 0)
      srtm_layer = srtm_ds.GetLayer()
      
      needed_srtm_tiles = {}
      
      for tile in tilesToProcess:
         srtm_tiles=[]
         mgrs_footprint = self.getMGRSTileGeometryByName(tile)
         area = mgrs_footprint.GetArea()
         srtm_layer.ResetReading()
         for srtm_tile in srtm_layer:
            srtm_footprint = srtm_tile.GetGeometryRef()
            intersection = mgrs_footprint.Intersection(srtm_footprint)
            if intersection.GetArea() > 0:
               coverage = intersection.GetArea()/area
               srtm_tiles.append((srtm_tile.GetField('FILE'),coverage))
         needed_srtm_tiles[tile]=srtm_tiles
      return needed_srtm_tiles


   
   def RecordProcessedFilenames(self):
      with open(os.path.join(self.outputPreProcess,"ProcessedFilenames.txt"), "a") as f:
         for fic in self.ProcessedFilenames:
               f.write(fic+"\n")

   def GetProcessedFilenames(self):
      try:
         with open(os.path.join(self.outputPreProcess,"ProcessedFilenames.txt"), "r") as f:
            #return f.read().splitlines()
            return[] 
      except:
         pass
         return []

   def getRasterList(self):
      return self.rawRasterList

   def getOrigin(self,manifest):
      with open(manifest,"r") as saveFile:
	 for line in saveFile:
	    if "<gml:coordinates>" in line:
	       coor = line.replace("                <gml:coordinates>","").replace("</gml:coordinates>","").split(" ")
	       coord = [(float(val.replace("\n","").split(",")[0]),float(val.replace("\n","").split(",")[1]))for val in coor]
	       return coord[0],coord[1],coord[2],coord[3]
	 raise Exception("Coordinates not found in "+str(manifest))

   def getTileOriginIntersectByS1(GridPath,image):
      import itertools
      manifest = image.getManifest()
      S1FootPrint = getOrigin(manifest)
      poly = ogr.Geometry(ogr.wkbPolygon)
      ring = ogr.Geometry(ogr.wkbLinearRing)
      ring.AddPoint(S1FootPrint[0][1], S1FootPrint[0][0])
      ring.AddPoint(S1FootPrint[1][1], S1FootPrint[1][0])
      ring.AddPoint(S1FootPrint[2][1], S1FootPrint[2][0])
      ring.AddPoint(S1FootPrint[3][1], S1FootPrint[3][0])
      ring.AddPoint(S1FootPrint[0][1], S1FootPrint[0][0])
      poly.AddGeometry(ring)

      driver = ogr.GetDriverByName("ESRI Shapefile")
      dataSource = driver.Open(GridPath, 0)
      layer = dataSource.GetLayer()
       
      intersectTile_tmp = []
      intersectTile = []

      for currentTile in layer:
         tileFootPrint = currentTile.GetGeometryRef()
         intersection = poly.Intersection(tileFootPrint)
         if intersection.GetArea()!=0:
            area_polygon= tileFootPrint.GetGeometryRef(0)
            points=area_polygon.GetPoints()
            intersectTile.append(currentTile.GetField('NAME'))
      return intersectTile

class S1_DateAcquisition(object):
   def __init__(self,manifest,imageFilenamesList):
     self.manifest = manifest
     self.imageFilenamesList = imageFilenamesList
     self.calibrationApplication = None#composed by [[calib,calibDependance],[...]...]

   def getManifest(self):
      return self.manifest

   def AddImage(self,ImageList):
      self.imageFilenamesList.append(ImageList)

   def GetImageList(self):
      return self.imageFilenamesList

   def SetCalibrationApplication(self,calib):
      """
      calib must be compose as the following
      calib = [(calibApplication,dependences),(...)...]
      """
      self.calibrationApplication = calib
   
   def GetCalibrationApplication(self):
       return self.calibrationApplication


