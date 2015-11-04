#!/usr/bin/python

import os
import glob
from sys import argv
from osgeo import ogr, gdal, osr
import random
import ConfigClassifN as Config
import numpy
from osgeo.gdalconst import  GDT_Int16, GDT_Float64, GDT_Float32
import RandomSelectionInsitu_LV as rsi
rows = 3667
cols = 3667

#--------------------------------------------------------------------
def random_shp_points(shapefile, nbpoints, opath):
   """
   Takes an initial shapefile of points and randomly select an input nb of wanted points .
   Returns the name of the ouput file 
   """
   driver = ogr.GetDriverByName("ESRI Shapefile")
   dataSource = driver.Open(shapefile, 1)
   layer = dataSource.GetLayer()
   FID = []
   for f in layer:
      FID.append(f.GetFID())
   pointsToSelect = random.sample(FID, nbpoints)
   expr = ""
   for p in range(0,len(pointsToSelect)-1):
      expr = "FID = "+str(pointsToSelect[p])+" OR "+expr
   expr = expr+" FID = "+str(pointsToSelect[-1])
   layer.SetAttributeFilter(expr)
   outname = opath+"/"+str(nbpoints)+"points.shp"
   CreateNewLayerPoint(layer, outname)
   return outname

#--------------------------------------------------------------------
def CreateNewLayerPoint(layer, outShapefile):
   """"
   Creates a new file of points using a layer as parameter.
   This layer is normally a previous selection of polygons
   """

   inLayerDefn = layer.GetLayerDefn()
   field_name_target = []
   for i in range(inLayerDefn.GetFieldCount()):
      field =  inLayerDefn.GetFieldDefn(i).GetName()
      field_name_target.append(field)
   outDriver = ogr.GetDriverByName("ESRI Shapefile")
   if os.path.exists(outShapefile):
      outDriver.DeleteDataSource(outShapefile)
   outDataSource = outDriver.CreateDataSource(outShapefile)
   out_lyr_name = os.path.splitext( os.path.split( outShapefile )[1] )[0]
   srsObj = layer.GetSpatialRef()
   outLayer = outDataSource.CreateLayer( out_lyr_name, srsObj, geom_type=ogr.wkbPoint )
   # Add input Layer Fields to the output Layer if it is the one we want
   inLayerDefn = layer.GetLayerDefn()
   for i in range(0, inLayerDefn.GetFieldCount()):
      fieldDefn = inLayerDefn.GetFieldDefn(i)
      fieldName = fieldDefn.GetName()
      if fieldName not in field_name_target:
         continue
      outLayer.CreateField(fieldDefn)
   # Get the output Layer's Feature Definition
   outLayerDefn = outLayer.GetLayerDefn()

   # Add features to the ouput Layer
   for inFeature in layer:
   # Create output Feature
      outFeature = ogr.Feature(outLayerDefn)

   # Add field values from input Layer
      for i in range(0, outLayerDefn.GetFieldCount()):
         fieldDefn = outLayerDefn.GetFieldDefn(i)
         fieldName = fieldDefn.GetName()
         if fieldName not in field_name_target:
             continue

         outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(),
             inFeature.GetField(i))
      # Set geometry as centroid
      geom = inFeature.GetGeometryRef()
      outFeature.SetGeometry(geom.Clone())
      # Add new feature to output Layer
      outLayer.CreateFeature(outFeature)
   return 0
#--------------------------------------------------------------------
def intersect(f1,fid1,f2,fid2):
   """
   This function checks two features in a file to see if they intersect.
   It takes 4 arguments, f1 for the first file, fid1 for the index of the
   first file's feature, f2 for the second file, fid2 for the index of the
   second file's feature. Returns whether the intersection is True or False.
   """
   test = False
   driver = ogr.GetDriverByName("ESRI Shapefile")
   file1 = driver.Open(f1,0)
   layer1 = file1.GetLayer()
   feat1 = layer1.GetFeature(fid1)
   geom1 = feat1.GetGeometryRef()
   file2 = driver.Open(f2,0)
   layer2 = file2.GetLayer()
   feat2 = layer2.GetFeature(fid2)
   geom2 = feat2.GetGeometryRef()
   if geom1.Intersect(geom2) == 1:
      print "INTERSECTION IS TRUE"
      test = True
   else:
      print "INTERSECTION IS FALSE"
      test = False
   return test

#--------------------------------------------------------------------

def getNewXY(x, y, ratio):
   """
   Adds a ratio value to a XY coordinate
   """
   minX = float(x) - float(ratio)
   minY = float(y) - float(ratio)
   maxX = float(x) + float(ratio)
   maxY = float(y) + float(ratio)
   return minX, maxX, minY, maxY

#--------------------------------------------------------------------

def selfeatinXY(shapefile, x, y, outname):
   """
   Does a spatial selection of features. Selects the features that are into a radius of
   40km from the X Y values, and creates a shapefile with this selection
   """
   driver = ogr.GetDriverByName("ESRI Shapefile")
   shppath = shapefile.split('/')
   shpname = shppath[-1].split('.')
   dataSource = driver.Open(shapefile, 0)
   layer = dataSource.GetLayer()
   minX, maxX, minY, maxY = getNewXY(x,y,40000)
   print getNewXY(x,y,40000)
   layer.SetSpatialFilterRect(float(minX), float(minY), float(maxX), float(maxY))
   CreateNewLayer(layer, outname)

#--------------------------------------------------------------------

def getNbFeat(shapefile):
   """
   Return the number of features of a shapefile
   """
   driver = ogr.GetDriverByName("ESRI Shapefile")
   dataSource = driver.Open(shapefile, 0)
   layer = dataSource.GetLayer()
   featureCount = layer.GetFeatureCount()
   return int(featureCount)

#--------------------------------------------------------------------
def readXY(pointfile, fid):
   """
   Read a feature from a file of points and returns the X and Y coordinates
   """
   shpDriver = ogr.GetDriverByName("ESRI Shapefile")
   dataSource = shpDriver.Open(pointfile, 0)
   layer = dataSource.GetLayer()
   feat = layer.GetFeature(fid)
   geom = feat.GetGeometryRef()
   centroid = geom.Centroid()
   x = centroid.GetX()
   y = centroid.GetY()
   return x, y

#--------------------------------------------------------------------
def mergeVectors(outname, opath, *files):
   """
   Merge a list of vector files in one 
   """
   file1 = files[0]
   nbfiles = len(files)
   filename = file1.split('.')
   filefusion = opath+"/"+outname+".shp"
   filefusioname = filefusion.split('.')
   fusion = "ogr2ogr "+filefusion+" "+file1
   print fusion
   os.system(fusion)
   for f in range(1, nbfiles):
      fusion2 = "ogr2ogr -update -append "+filefusion+" "+files[f]+" -nln "+outname
      print fusion2
      os.system(fusion2)
   return filefusion

#--------------------------------------------------------------------
def sameID(shapefile):
   """
   Delete features with the same ID
   """
   driver = ogr.GetDriverByName("ESRI Shapefile")
   dataSource = driver.Open(shapefile, 1)
   layer = dataSource.GetLayer()
   featureCount = layer.GetFeatureCount()
   name = shapefile.split('.')
   listID = []
   for feat in layer:
      ID = feat.GetFieldAsInteger("ID")
      listID.append(ID)
   print len(listID )
   print len(set(listID))
   for i in set(listID):
      layer.SetAttributeFilter("ID = "+str(i))
      count =  layer.GetFeatureCount()
      if count != 1:
         listFID = []
         for f in layer:
            FID = f.GetFID()
            listFID.append(FID)
         print listFID
         for f in range(1,len(listFID)):
            #a = layer.GetFeature(listFID[f])
            layer.DeleteFeature(listFID[f])
      layer.SetAttributeFilter(None)
   dataSource.ExecuteSQL('REPACK '+name[0])

#--------------------------------------------------------------------
def CreateNewLayer(layer, outShapefile):
      """
      This function creates a new shapefile
          ARGs:
            -layer: the input shapefile
            -outShapefile: the name of the output shapefile
    
      """
      inLayerDefn = layer.GetLayerDefn()
      field_name_target = []
      for i in range(inLayerDefn.GetFieldCount()):
          field =  inLayerDefn.GetFieldDefn(i).GetName()
          field_name_target.append(field)

      outDriver = ogr.GetDriverByName("ESRI Shapefile")
      #if file already exists, delete it
      if os.path.exists(outShapefile):
        outDriver.DeleteDataSource(outShapefile)
      outDataSource = outDriver.CreateDataSource(outShapefile)
      out_lyr_name = os.path.splitext( os.path.split( outShapefile )[1] )[0]
      #Get the spatial reference of the input layer
      srsObj = layer.GetSpatialRef()
      #Creates the spatial reference of the output layer
      outLayer = outDataSource.CreateLayer( out_lyr_name, srsObj, geom_type=ogr.wkbMultiPolygon )
      # Add input Layer Fields to the output Layer if it is the one we want

      for i in range(0, inLayerDefn.GetFieldCount()):
         fieldDefn = inLayerDefn.GetFieldDefn(i)
         fieldName = fieldDefn.GetName()
         if fieldName not in field_name_target:
             continue
         outLayer.CreateField(fieldDefn)
     # Get the output Layer's Feature Definition
      outLayerDefn = outLayer.GetLayerDefn()

     # Add features to the ouput Layer
      for inFeature in layer:
      # Create output Feature
         outFeature = ogr.Feature(outLayerDefn)

        # Add field values from input Layer
         for i in range(0, outLayerDefn.GetFieldCount()):
            fieldDefn = outLayerDefn.GetFieldDefn(i)
            fieldName = fieldDefn.GetName()
            if fieldName not in field_name_target:
                continue

            outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(),
                inFeature.GetField(i))
        # Set geometry as centroid
         geom = inFeature.GetGeometryRef()
         outFeature.SetGeometry(geom.Clone())
        # Add new feature to output Layer
         outLayer.CreateFeature(outFeature)
      return outShapefile

#--------------------------------------------------------------------
def getListFile(expr, opath):
   os.chdir(opath)
   listFile = []
   for f in glob.glob(expr):
      listFile.append(opath+"/"+f)
   return listFile

#--------------------------------------------------------------
def RFClassif(vectorFile, opathFcl, opathFim, tile, *SerieList):
   """
   Computes the Random Forest classification, uses the ConfigClassif file
   which containts the classification parameters
    ARGs:
       INPUT:
            - samplesFile : the vector file containing the samples
            - SerieList: list of image series
       OUTPUT:
            - Text file with the model
            - Text file with the confusion matrix
   """
   args = Config.dicRF()
   ch = ""
   i=0
   bm = 0

   newpath = opathFcl
   if not os.path.exists(newpath):
      os.mkdir(newpath)
  
   for key in args:
      ch = ch+"-"+key+" "+str(args[key])+" "

   name = BuildName(opathFim, *SerieList) 
   statFile = opathFim+"/"+name+".xml"
   dataSeries = opathFim+"/"+name+".tif"
   
   Classif = "otbcli_TrainImagesClassifier -io.il "+dataSeries+" -io.vd "+vectorFile\
   +" -io.imstat "+statFile+" -sample.bm "+str(bm)+" -io.confmatout "+newpath+"/RF_ConfMat_"+tile\
   +"_bm"+str(bm)+".csv -io.out "+newpath+"/RF_Classification_"+tile+"_bm"+str(bm)+".txt "+ch
   print Classif
   os.system(Classif)
   return newpath+"/RF_ConfMat_"+tile+"_bm"+str(bm)+".csv"


#--------------------------------------------------------------
def BuildName(opath, *SerieList):
   """
   Returns a name for an output using as input several images series.
   ARGs:
       INPUT:
            -SerieList:  the list of different series
            -opath : output path
   """  
   
   chname = ""
   for serie in SerieList:
      feat = serie.split(' ') 
      for f in feat:
         name = f.split('.')
         feature = name[0].split('/')
         chname = chname+feature[-1]+"_"
   return chname

#--------------------------------------------------------------
def ConcatenateAllData(opath, *SerieList):
   """
   Concatenates all data: Reflectances, NDVI, NDWI, Brightness
   ARGs:
       INPUT:
            -SerieList: the list of different series
            -opath : output path
       OUTPUT:
            - The concatenated data
   """
   ch = GetSerieList(*SerieList)
   name = BuildName(opath, *SerieList)
   ConcFile = opath+"/"+name+".tif"
   Concatenation = "otbcli_ConcatenateImages -il "+ch+" -out "+ConcFile+" "+pixelo
   print Concatenation
   os.system(Concatenation)
#--------------------------------------------------------------
def ClipVectorData(vectorFile, cutFile, opath):
   """
   Cuts a shapefile with another shapefile
   ARGs:
       INPUT:
            -vectorFile: the shapefile to be cut
            -shpMask: the other shapefile 
       OUTPUT:
            -the vector file clipped
   """
   
   nameV = vectorFile.split('.')
   nameF = nameV[0].split('/') 
   outname = opath+"/"+nameF[-1]+".shp"
   if os.path.exists(outname):
      os.remove(outname)
   Clip = "ogr2ogr -clipsrc "+cutFile+" "+outname+" "+vectorFile+" -progress"
   print Clip
   os.system(Clip)
   return outname
#--------------------------------------------------------------
def ClipVectorData2(vectorFile, cutFile, tile, opath):
   """
   Cuts a shapefile with another shapefile
   ARGs:
       INPUT:
            -vectorFile: the shapefile to be cut
            -shpMask: the other shapefile 
       OUTPUT:
            -the vector file clipped
   """
   
   nameV = vectorFile.split('.')
   nameF = nameV[0].split('/') 
   outname = opath+"/"+nameF[-1]+"-"+tile+".shp"
   if os.path.exists(outname):
      os.remove(outname)
   Clip = "ogr2ogr -clipsrc "+cutFile+" "+outname+" "+vectorFile+" -progress"
   print Clip
   os.system(Clip)
   return outname

#--------------------------------------------------------------
def imageClassification(model, name, image, stats, opath, mask):
   """
   Performs a classification of the input image according to a model file.
   ARGs:
      INPUT:
          - model: model file
          - image: input image 
          - opath: output path
      OUTPUT:
          - Classification in TIFF format
   """
   if not os.path.exists(opath):
      os.mkdir(opath) 
   imPath = image.split('.')
   modelPath = model.split('.')
   modelName = modelPath[0].split('/')   
   classifName = opath+"/"+name+".tif"

   Classif = "otbcli_ImageClassifier -in "+image+" -imstat "+stats+" -model "+model\
   +" -out "+classifName+" int16 -ram 256 -mask "+mask
   print Classif
   os.system(Classif)
   return classifName


#--------------------------------------------------------------
def getListModel(ipath):
   """
   Returns the list of models of classifications in a path
   """
   modelList = []
   for model in glob.glob(ipath+"/*Classification*.txt"):
      modelList.append(model)
   modelList.sort()
   return modelList

#--------------------------------------------------------------
def getNbFeat(shapefile):
   driver = ogr.GetDriverByName("ESRI Shapefile")
   dataSource = driver.Open(shapefile, 0)
   layer = dataSource.GetLayer()
   featureCount = layer.GetFeatureCount()
   return featureCount

#--------------------------------------------------------------
def readImage(image):
   """
   Returns image values
   """
   hDataset = gdal.Open(image, gdal.GA_ReadOnly )
   if hDataset is None:
      print("gdalinfo failed - unable to open '%s'." % pszFilename )
      return 1
   else:    
   # Get raster georeference info
      transform = hDataset.GetGeoTransform()
      xOrigin = transform[0]
      yOrigin = transform[3]
      pixelWidth = transform[1]
      pixelHeight = transform[5]
      banddataraster = hDataset.GetRasterBand(1)
   return xOrigin, yOrigin, pixelWidth, pixelHeight

#--------------------------------------------------------------
def getXYsize(image):
   """
   Returns image height and width
   """
   hDataset = gdal.Open(image, gdal.GA_ReadOnly )
   if hDataset is None:
      print("gdalinfo failed - unable to open '%s'." % pszFilename )
      return 1
   else:    
   # Get raster georeference info
      xSize = hDataset.RasterXSize
      ySize = hDataset.RasterYSize
   return xSize, ySize
#--------------------------------------------------------------

def readAsArray(image, band):
   """
   Return image as array
   """
   src_ds = gdal.Open(image)
   inband = src_ds.GetRasterBand(int(band))
   scanline = inband.ReadAsArray(0, 0)
   return scanline

#--------------------------------------------------------------
def pixel2geo(image, col, row):
    """
    Uses a gdal geomatrix (gdal.GetGeoTransform()) to calculate
    the pixel location of a geospatial coordinate 
    """
    raster = gdal.Open(image)
    geomatrix = raster.GetGeoTransform()
    ulX = geoMatrix[0]
    ulY = geoMatrix[3]
    xDist = geoMatrix[1]
    yDist = geoMatrix[5]
    rtnX = geoMatrix[2]
    rtnY = geoMatrix[4]
    x = int ((col * xDist) + ulX)
    y = int((row * yDist) + ulY)
    return (x, y) 
#--------------------------------------------------------------
def GetPixelValue(X, Y, image, band):
   values = os.popen('gdallocationinfo '+image+' -valonly -geoloc -b '+str(band)+' '+str(X)+' '+str(Y)).read()
   return values
#--------------------------------------------------------------
def writeArray(refband, array, outname):
   """ 
   Write an array as raster taking as reference an input image
   """
   src_ds = gdal.Open(refband)
   xsize = src_ds.RasterXSize
   ysize = src_ds.RasterYSize
   gt = src_ds.GetGeoTransform()
   out_driver = gdal.GetDriverByName("GTiff")
   nombands = 1
   outdataset = out_driver.Create(outname, xsize, ysize, nombreDeBande, GDT_Float32)
   if gt is not None and gt != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
      outdataset.SetGeoTransform(gt)
   prj = src_ds.GetProjectionRef()
   if prj is not None and len(prj) > 0:
      outdataset.SetProjection(prj)
   inband = src_ds.GetRasterBand(1)
   outband = outdataset.GetRasterBand(1)
   scanline = array
   outband.WriteArray(scanline)
   return outname
#--------------------------------------------------------------
def verifyDico(in_dico, cl, weight):
  if cl not in in_dico:
     in_dico[cl] = weight
  else:
     in_dico[cl] = in_dico[cl] + weight
#--------------------------------------------------------------

def geoMatrix(image):
    raster = gdal.Open(image)
    geomatrix = raster.GetGeoTransform()
    #print geomatrix
    return geomatrix

#--------------------------------------------------------------

def createClassif(imref, name, xsize, ysize, outarray):
    src_ds = gdal.Open(imref)
    prj = src_ds.GetProjectionRef()
    gt = src_ds.GetGeoTransform()
    out_driver = gdal.GetDriverByName("GTiff")
    nombreDeBande=1
    #GDT_Float32 , GDT_Float64
    outdataset = out_driver.Create(name, xsize, ysize, nombreDeBande, GDT_Float32)
    
    if gt is not None and gt != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
        outdataset.SetGeoTransform(gt)
    prj = src_ds.GetProjectionRef()
    if prj is not None and len(prj) > 0:
        outdataset.SetProjection(prj)
    outband = outdataset.GetRasterBand(1)
    inband = src_ds.GetRasterBand(1)
    scanlineout = outarray
    outband.WriteArray(scanlineout)

#--------------------------------------------------------------

def within(f1,fid1,f2,fid2):
   """
   This function checks two features in a file to see if one is within another.
   It takes 4 arguments, f1 for the first file, fid1 for the index of the
   first file's feature, f2 for the second file, fid2 for the index of the
   second file's feature. Returns whether the within is True or False.
   """

   driver = ogr.GetDriverByName("ESRI Shapefile")
   file1 = driver.Open(f1,0)
   layer1 = file1.GetLayer()
   feat1 = layer1.GetFeature(fid1)
   geom1 = feat1.GetGeometryRef()
   file2 = driver.Open(f2,0)
   layer2 = file2.GetLayer()
   feat2 = layer2.GetFeature(fid2)
   geom2 = feat2.GetGeometryRef()
   if geom1.Within(geom2) == 1:
      print f1, "IS WITHIN", f2
      return True
   else:
      print f1, "IS NOT WITHIN", f2
      return False
#--------------------------------------------------------------
def getExtent(f1):
   """
   Return the extent of a layer
   """
   driver = ogr.GetDriverByName("ESRI Shapefile")
   shpfile = driver.Open(f1,0)
   layer = shpfile.GetLayer()
   return layer.GetExtent()
#--------------------------------------------------------------

def featinXY(shapefile, minX, minY, maxX, maxY):
   """
   Does a spatial selection of features. Selects the features that are into the X Y values,
   and creates a shapefile with this selection
   """
   driver = ogr.GetDriverByName("ESRI Shapefile")
   shppath = shapefile.split('/')
   shpname = shppath[-1].split('.')
   dataSource = driver.Open(shapefile, 0)
   layer = dataSource.GetLayer()
   layer.SetSpatialFilterRect(float(minX), float(minY), float(maxX), float(maxY))
   if layer.GetFeatureCount() > 0:
	return True
   else: return False
#--------------------------------------------------------------

def lyrFeatinXY(shapefile, minX, maxX, minY, maxY, outname):
   """
   Does a spatial selection of features. Selects the features that are into the X Y values,
   and creates a shapefile with this selection
   """
   print "Selecting polygons"
   driver = ogr.GetDriverByName("ESRI Shapefile")
   shppath = shapefile.split('/')
   shpname = shppath[-1].split('.')
   dataSource = driver.Open(shapefile, 0)
   layer = dataSource.GetLayer()
   layer.SetSpatialFilterRect(float(minX), float(minY), float(maxX), float(maxY))
   rsi.CreateNewLayer(layer, outname)

#--------------------------------------------------------------
def getColRows(image):
   hDataset = gdal.Open(image, gdal.GA_ReadOnly )
   hDriver = hDataset.GetDriver()
   cols = hDataset.RasterXSize
   rows = hDataset.RasterYSize
   return cols, rows


#--------------------------------------------------------------
def getCorners(image):
   print readImage(image)
   xmin = readImage(image)[0]
   ymax = readImage(image)[1]
   xmax = readImage(image)[0] + (readImage(image)[2] * getColRows(image)[0])
   ymin = readImage(image)[1] - (readImage(image)[2] * getColRows(image)[1])
   ch = str(xmin)+" "+str(ymin)+" "+str(xmax)+" "+str(ymax)
   return ch

#--------------------------------------------------------------
def listNeighbors():
   listN = {}	
   listN['Landsat8_D0003H0002'] = ['Landsat8_D0003H0003']
   listN['Landsat8_D0003H0003'] = ['Landsat8_D0003H0004']
   listN['Landsat8_D0003H0004'] = ['Landsat8_D0003H0005']
   listN['Landsat8_D0003H0005'] = []
   listN['Landsat8_D0004H0002'] = ['Landsat8_D0003H0002', 'Landsat8_D0003H0003','Landsat8_D0004H0003']
   listN['Landsat8_D0004H0003'] = ['Landsat8_D0003H0003', 'Landsat8_D0003H0004','Landsat8_D0004H0004']
   listN['Landsat8_D0004H0004'] = ['Landsat8_D0003H0004', 'Landsat8_D0003H0005','Landsat8_D0004H0005']
   listN['Landsat8_D0004H0005'] = ['Landsat8_D0003H0005']
   listN['Landsat8_D0005H0002'] = ['Landsat8_D0004H0002', 'Landsat8_D0004H0003','Landsat8_D0005H0003']
   listN['Landsat8_D0005H0003'] = ['Landsat8_D0004H0003', 'Landsat8_D0004H0004','Landsat8_D0005H0004']
   listN['Landsat8_D0005H0004'] = ['Landsat8_D0004H0004', 'Landsat8_D0004H0005','Landsat8_D0005H0005']
   listN['Landsat8_D0005H0005'] = ['Landsat8_D0004H0005']
   listN['Landsat8_D0006H0002'] = ['Landsat8_D0005H0002', 'Landsat8_D0005H0003','Landsat8_D0006H0003']
   listN['Landsat8_D0006H0003'] = ['Landsat8_D0005H0003', 'Landsat8_D0005H0004','Landsat8_D0006H0004']
   listN['Landsat8_D0006H0004'] = ['Landsat8_D0005H0004', 'Landsat8_D0005H0005','Landsat8_D0006H0005']
   listN['Landsat8_D0006H0005'] = ['Landsat8_D0005H0005']
   listN['Landsat8_D0007H0002'] = ['Landsat8_D0006H0002', 'Landsat8_D0006H0003','Landsat8_D0007H0003']
   listN['Landsat8_D0007H0003'] = ['Landsat8_D0006H0003', 'Landsat8_D0006H0004','Landsat8_D0007H0004']
   listN['Landsat8_D0007H0004'] = ['Landsat8_D0006H0004', 'Landsat8_D0006H0005','Landsat8_D0007H0005']
   listN['Landsat8_D0007H0005'] = ['Landsat8_D0006H0005']
   listN['Landsat8_D0008H0002'] = ['Landsat8_D0007H0002', 'Landsat8_D0007H0003','Landsat8_D0008H0003']
   listN['Landsat8_D0008H0003'] = ['Landsat8_D0007H0003', 'Landsat8_D0007H0004','Landsat8_D0008H0004']
   listN['Landsat8_D0008H0004'] = ['Landsat8_D0007H0004', 'Landsat8_D0007H0005']
   return listN

#--------------------------------------------------------------
def listIntersection(tile):
   dicoN = listNeighbors()
   #print dicoN[tile]
   return dicoN[tile]

#--------------------------------------------------------------
def listsimiZones():
   zone = {}
   zone['1'] = [1, 0.6, 0.4, 0.4, 0.2, 0.2, 0.4, 0.2]
   zone['2'] = [0.6, 1, 0.4, 0.6, 0.4, 0.2, 0.4, 0.2]
   zone['3'] = [0.4, 0.4, 1, 0.6, 0.4, 0.4, 0.6, 0.2]
   zone['4'] = [0.4, 0.6, 0.6, 1, 0.6, 0.4, 0.6, 0.4]
   zone['5'] = [0.2, 0.4, 0.4, 0.6, 1, 0.2, 0.2, 0.8]
   zone['6'] = [0.2, 0.2, 0.4, 0.4, 0.2, 1, 0.4, 0.8]
   zone['7'] = [0.4, 0.4, 0.6, 0.6, 0.2, 0.4, 1, 0.4]
   zone['8'] = [0.2, 0.2, 0.2, 0.4, 0.8, 0.8, 0.4, 1]
   return zone


#--------------------------------------------------------------
def simZone(zone1,zone2):
   dicoSim = listsimiZones()
   z1 = str(zone1)
   z2 = int(zone2)-1
   return str(dicoSim[z1][z2]) 


