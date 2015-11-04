#!/usr/bin/python

import os
import glob
from sys import argv
import gdal, osr, ogr
import csv 
import Dico as dico
from datetime import date, datetime, timedelta


pathAppGap = dico.pathAppGap
Sbands = dico.Sbands
Lbands = dico.Lbands
bandsL = dico.bandLandsat()
maskCshp = dico.maskCshp
pixelo = dico.pixelotb
pixelg = dico.pixelgdal
res = str(dico.res)
field = dico.ClassCol

def CreateDir(opath):
   """
   Creates the folders
   """
   path = ['tmp', 'Final', 'in-situ']
   for p in path:
      if not os.path.exists(opath+"/"+p):
         os.mkdir(opath+"/"+p)
   subpath = ['Images']
   for sp in subpath:
      if not os.path.exists(opath+"/Final/"+sp):
         os.mkdir(opath+"/Final/"+sp)
   

def CreateCommonZone(opath):
   """
   Creates the common zone using the border mask of SPOT  and LANDSAT

   ARGs:
       INPUT:
            -opath: the output path
            
       OUTPUT:
            - A binary mask and a shapefile
   """
   
   #mask = "otbcli_BandMath -il "+opath+"/MaskS.tif "+opath+"/MaskL20m.tif -exp \"im1b1  and im2b1\""+" -out "+opath+"/MaskCommunSL.tif"
   #os.system(mask)

   BuildMask = "otbcli_BandMath -il "+opath+"/MaskS.tif "+opath+"/MaskL"+res+"m.tif -exp \"im1b1*im2b1\""\
   +" -out "+opath+"/MaskCommunSL.tif "+pixelo
   os.system(BuildMask)
  
   shpMask = opath+"/MaskCommunSL.shp"
   
   VectorMask = "gdal_polygonize.py -f \"ESRI Shapefile\" -mask "+opath+"/MaskCommunSL.tif "+opath\
   +"/MaskCommunSL.tif "+opath+"/MaskCommunSL.shp"
   os.system(VectorMask)

   return shpMask


def ExtractConcBands(image, nbmin, nbmax):
   """
   Extract the range of bands from a multiband image and concatenate them.
   ARGs:
       INPUT:
            -image: the multiband image
            -nbmin: the min position of the band 
            -nbmax: the max position of the band 
       OUTPUT:
            - A multiband image containg the bands of the defined range
   """

   listBands = []
   name = image.split('/')
   imname = name[0].split('.')
   path = '/'.join(name[0:-1])
   #print name
   #print path
   for i in range(int(nbmin), int(nbmax)+1):
      extract = "otbcli_ExtractROI -in "+image+" -cl Channel"+str(i)+" -out "+path+"/"+"Band"+str(i)+"_"+name[-1]+" "+pixelo
      print extract
      os.system(extract)
      listBands.append(path+"/"+"Band"+str(i)+"_"+name[-1])
  
   #print listBands
   chlistBands = ""
   for band in listBands:
      chlistBands = chlistBands+band+" "
   #print name[0] 
   concatenate = "otbcli_ConcatenateImages -il "+chlistBands+" -out "+path+"/ExtROI_"+"band"+nbmin+"To"+"band"+nbmax+"_"+name[-1]+" "+pixelo
   #print concatenate
   os.system(concatenate)


   for band in listBands:
      os.remove(band)

#-----------------------------------------------------------------
def getDates(image, bandperdate):
   """
   Returns the number of dates of a multiband image
   ARGs:
       INPUT:
            -image: the multiband image
   """
   hDataset = gdal.Open( image, gdal.GA_ReadOnly )
   if hDataset is None:
      print("gdalinfo failed - unable to open '%s'." % pszFilename )
   
   bands = 0
   for iBand in range(hDataset.RasterCount):
      bands = bands+1
   
   dates = bands/bandperdate
      
   return dates

#----------------------------------------------------------------
def OrderGapFSeries(serieGapS, serieGapL, opathT, opathF,tile):
   """
   Uses SPOT and LANDSAT interpolated series and creates one serie
   in chronological order using the dates text files
   ARGs:
       INPUT:
            -serieGapS: the SPOT gapfilling serie
            -serieGapL: the LANDSAT gapfilling serie
            -opath
       OUTPUT:
            - One file containing Spot + Landsat interpolated bands

   """
   fspot = open(opathT+"/SPOTimagesDateList.txt")
   flandsat = open(opathT+"/LANDSATimagesDateList_"+tile+".txt")
   fSL = open(opathF+"/SL_MultiTempGap_DateList.txt", "w")
   
   dateS = []
   dateL = []
   allDates = []
   
   pathS = serieGapS.split('/')
   nameS = pathS[-1].split('.')
   pathL = serieGapL.split('/')
   nameL = pathL[-1].split('.')
   
   for line in fspot:
      allDates.append(int(line))
      dateS.append(int(line))
   for line in flandsat:
      allDates.append(int(line))
      dateL.append(int(line))
   allDates.sort()
   #print allDates

   splitS = "otbcli_SplitImage -in "+serieGapS+" -out "+serieGapS+" "+pixelo
   print splitS
   os.system(splitS)
   splitL = "otbcli_SplitImage -in "+serieGapL+" -out "+serieGapL+" "+pixelo
   print splitL
   os.system(splitL)

   datesS = getDates(serieGapS, Sbands) * Sbands 
   datesL = getDates(serieGapL, Lbands) * Lbands
   
   ch = ""
   for date in allDates:
      if date in dateS:
         dlist = dateS
         im = nameS[0]
         nbbands = Sbands
         #im = "S" 
      elif date in dateL:
         dlist = dateL
         im = nameL[0]
         nbbands = Lbands
      i = dlist.index(date)
      for b in range(i*nbbands, (i*nbbands)+nbbands):
         ch = ch+opathF+"/"+im+"_"+str(b)+".tif"+" "
      fSL.write(str(date))
      fSL.write('\n') 
   #print ch
   fSL.close() 
   Concatenate = "otbcli_ConcatenateImages -il "+ch+" -out "+opathF+"/SL_MultiTempGapF.tif "+pixelo
   print Concatenate
   os.system(Concatenate)

   #Only SPOT bands
   fS = open(opathF+"/SL_MultiTempGapF_4bpi_DateList.txt", "w")

   chSbands = ""
   for date in allDates:
      if date in dateS:
         dlist = dateS
         j = dlist.index(date)
         im = nameS[0]
         nbbands = Sbands
         imin = j*nbbands
         imax = (j*nbbands)+nbbands
      elif date in dateL:
         dlist = dateL
         j = dlist.index(date)
         #print j
         im = nameL[0]
         nbbands = Lbands
         imin = (j*nbbands)+2
         imax = ((j*nbbands)+nbbands)-1
       
      for b in range(imin, imax):
         chSbands = chSbands+opathF+"/"+im+"_"+str(b)+".tif"+" "
      fS.write(str(date))
      fS.write('\n')
   fSL.close()  
   print chSbands
   ConcatenateSbands = "otbcli_ConcatenateImages -il "+chSbands+" -out "+opathF+"/SL_MultiTempGapF_4bpi.tif "+pixelo
   os.system(ConcatenateSbands)
   print ConcatenateSbands  
            
   """
   for mask in glob.glob(opathT+"/"+"*masked.tif"):
      os.remove(mask)     
   for bandS in glob.glob(opathF+"/"+nameS[0]+"_*.tif"):
      os.remove(bandS)
   for bandL in glob.glob(opathF+"/"+nameL[0]+"_*.tif"):
      os.remove(bandL)
   """
#-------------------------------------------------------------------------------

def refl_LandsatGap(serieGapL, opathT, opathF, capteur):

   pathL = serieGapL.split('/')
   nameL = pathL[-1].split('.')
   print nameL

   if capteur == "SPOT":
      bands = [bandsL["green"], bandsL["red"], bandsL["NIR"], bandsL["SWIR1"]]
   elif capteur == "rapideye":
      bands = [bandsL["blue"], bandsL["green"], bandsL["red"], bandsL["NIR"]]
   elif capteur != "SPOT" and capteur!= "rapideye":
      print "Capteur not recognized"

   chSbands = ""
      
   chain = ""
   splitL = "otbcli_SplitImage -in "+serieGapL+" -out "+serieGapL
   print splitL
   #os.system(splitL)
   dates = getDates(serieGapL, Lbands)
   #print dates

   for j in range(0,dates):
      im = nameL[0]
      nbbands = Lbands
      #print nbbands
      imin = (j*nbbands)+bands[0]-1
      print imin
      imax = ((j*nbbands)+bands[-1])
      print imax
       
      for b in range(imin, imax):
         chSbands = chSbands+opathF+"/"+im+"_"+str(b)+".tif"+" "
   print chSbands

   Concatenate = "otbcli_ConcatenateImages -il "+chSbands+" -out "+opathF+"/"+nameL[0]+"_4bpi_"+capteur+"combands.tif "
   print Concatenate
   os.system(Concatenate)

#-------------------------------------------------------------------------------

def FeatExtSPOT(imSerie, imListFile, opath):
   """
   Calculates NDVI, NDWI and Brightness from SPOT interplated serie
   ARGs:
       INPUT:
            -imSerie: the SPOT gapfilling serie
            -imListFile: text file containing the dates of imSerie
            -opath
       OUTPUT:
            - A directory per feature containing the feature calculated per date

   """
   #Use serie with 4 bands for SPOT and L8
   fdates = open(imListFile)
   dlist = []
   for dates in fdates:
      dlist.append(int(dates))
   bandsS = dico.bandSpot()   
   dates = getDates(imSerie, 4)
   indices = ['NDVI', 'NDWI', 'Brightness']
   for feature in indices:
      if not os.path.exists(opath+"/"+feature):
         os.mkdir(opath+"/"+feature)   

   name = imSerie.split('/')
   name = name[-1]
   name = name.split('.')
   for feature in indices:

      if feature == "NDVI":
         for date in dlist:
            i = dlist.index(date)
            r = bandsS["red"] + (i*4)
            nir = bandsS["NIR"] + (i*4)
            oname = feature+"_"+str(date)+"_"+name[0]+".tif"
            #expr = "\"if(im1b"+str(nir)+"==-10000,-10000,if(abs(im1b"+str(nir)+"+im1b"+str(r)+")<0.000001,0,(im1b"+str(nir)+"-im1b"+str(r)+")/(im1b"+str(nir)+"+im1b"+str(r)+")))\""
	    #OTB 4.3
            #expr = "\"if(im1b"+str(nir)+"==-10000,-10000,(if(abs(im1b"+str(nir)+"+im1b"+str(r)+")<0.000001,0,(im1b"+str(nir)+"-im1b"+str(r)+")/(im1b"+str(nir)+"+im1b"+str(r)+"))))\""
	    #OTB 5.0
            expr = "\"(im1b"+str(nir)+"==-10000?-10000:((abs(im1b"+str(nir)+"+im1b"+str(r)+")<0.000001?0:(im1b"+str(nir)+"-im1b"+str(r)+")/(im1b"+str(nir)+"+im1b"+str(r)+"))))\""
            FeatureExt = "otbcli_BandMath -il "+imSerie+" -out "+opath+"/"+feature+"/"+oname+" "+pixelo+" -exp "+expr
	    print FeatureExt
            os.system(FeatureExt)
            
      
      if feature == "NDWI":
         for date in dlist:
            i = dlist.index(date)
            nir = bandsS["NIR"] + (i*4)
            swir = bandsS["SWIR"] + (i*4)
            oname = feature+"_"+str(date)+"_"+name[0]+".tif"
            #expr = "\"if(im1b"+str(nir)+"==-10000,-10000,if(abs(im1b"+str(swir)+"+im1b"+str(nir)+")<0.000001,0,(im1b"+str(swir)+"-im1b"+str(nir)+")/(im1b"+str(swir)+"+im1b"+str(nir)+")))\""
	    #OTB 4.3
            #expr = "\"if(im1b"+str(nir)+"==-10000,-10000,(if(abs(im1b"+str(swir)+"+im1b"+str(nir)+")<0.000001,0,(im1b"+str(swir)+"-im1b"+str(nir)+")/(im1b"+str(swir)+"+im1b"+str(nir)+"))))\""
	    #OTB 5.0
            expr = "\"(im1b"+str(nir)+"==-10000?-10000:((abs(im1b"+str(swir)+"+im1b"+str(nir)+")<0.000001?0:(im1b"+str(swir)+"-im1b"+str(nir)+")/(im1b"+str(swir)+"+im1b"+str(nir)+"))))\""
            FeatureExt = "otbcli_BandMath -il "+imSerie+" -out "+opath+"/"+feature+"/"+oname+" "+pixelo+" -exp "+expr
	    print FeatureExt
            os.system(FeatureExt)
            

      if feature == "Brightness":
         for date in dlist:
            i = dlist.index(date)
            g = bandsS["green"] + (i*4)
            r = bandsS["red"] + (i*4)
            nir = bandsS["NIR"] + (i*4)
            swir = bandsS["SWIR"] + (i*4)
            oname = feature+"_"+str(date)+"_"+name[0]+".tif"
	    #OTB 4.3
            #expr = "\"if(im1b"+str(g)+"==-10000,-10000,sqrt((im1b"+str(g)+" * im1b"+str(g)+") + (im1b"+str(r)+" * im1b"+str(r)+") + (im1b"+str(nir)+" * im1b"+str(nir)+") + (im1b"+str(swir)+" * im1b"+str(swir)+")))\""
	    #OTB 5.0
            expr = "\"(im1b"+str(g)+"==-10000?-10000:sqrt((im1b"+str(g)+" * im1b"+str(g)+") + (im1b"+str(r)+" * im1b"+str(r)+") + (im1b"+str(nir)+" * im1b"+str(nir)+") + (im1b"+str(swir)+" * im1b"+str(swir)+")))\""
            FeatureExt = "otbcli_BandMath -il "+imSerie+" -out "+opath+"/"+feature+"/"+oname+" "+pixelo+" -exp "+expr
	    print FeatureExt
            os.system(FeatureExt)
            

   return
    
#--------------------------------------------------------------------------------------------------------------   
def FeatExtLandsat(imSerie, imListFile, opath, opathF):
   """
   Calculates NDVI, NDWI and Brightness from LANDSAT interpolated serie
   ARGs:
       INPUT:
            -imSerie: the LANDSAT gapfilling serie
            -imListFile: text file containing the dates of imSerie
            -opath
       OUTPUT:
            - A directory per feature containing the feature calculated per date

   """
   fdates = open(opath+"/"+imListFile)
   #dates = getDates(imSerie, 7)
   dlist = []
   bandsL = dico.bandLandsat()
   ch = ""

   for dates in fdates:
      dlist.append(int(dates))
   indices = ['NDVI', 'NDWI', 'Brightness', 'Greenness']
   for feature in indices:
      if not os.path.exists(opath+"/"+feature):
         os.mkdir(opath+"/"+feature)   
 
   name = imSerie.split('/')
   name = name[-1]
   name = name.split('.')
   for feature in indices:

      if feature == "NDVI":
         for date in dlist:
            i = dlist.index(date)
            r = bandsL["red"] + (i*7)
            nir = bandsL["NIR"] + (i*7)
            oname = feature+"_"+str(date)+"_"+name[0]+".tif"
	    #OTB 4.3
            #expr = "\"if(im1b"+str(nir)+"==-10000,-10000,if(abs(im1b"+str(nir)+"+im1b"+str(r)\
            #+")<0.000001,0,(im1b"+str(nir)+"-im1b"+str(r)+")/(im1b"+str(nir)+"+im1b"+str(r)+")))\""
	    #OTB 5.0
            expr = "\"(im1b"+str(nir)+"==-10000?-10000:if(abs(im1b"+str(nir)+"+im1b"+str(r)\
            +")<0.000001?0:(im1b"+str(nir)+"-im1b"+str(r)+")/(im1b"+str(nir)+"+im1b"+str(r)+")))\""
            FeatureExt = "otbcli_BandMath -il "+imSerie+" -out "+opath+"/"+feature+"/"+oname+" "+pixelo+" -exp "+expr
            print FeatureExt           
            os.system(FeatureExt)


      if feature == "NDWI":
         for date in dlist:
            i = dlist.index(date)
            nir = bandsL["NIR"] + (i*7)
            swir = bandsL["SWIR1"] + (i*7)
            oname = feature+"_"+str(date)+"_"+name[0]+".tif"
	    #OTB 4.3
            #expr = "\"if(im1b"+str(nir)+"==-10000,-10000,if(abs(im1b"+str(swir)+"+im1b"+str(nir)\
            #+")<0.000001,0,(im1b"+str(swir)+"-im1b"+str(nir)+")/(im1b"+str(swir)+"+im1b"+str(nir)+")))\""
	    #OTB 5.0
            expr = "\"(im1b"+str(nir)+"==-10000?-10000:if(abs(im1b"+str(swir)+"+im1b"+str(nir)\
            +")<0.000001?0:(im1b"+str(swir)+"-im1b"+str(nir)+")/(im1b"+str(swir)+"+im1b"+str(nir)+")))\""
            FeatureExt = "otbcli_BandMath -il "+imSerie+" -out "+opath+"/"+feature+"/"+oname+" "+pixelo+" -exp "+expr
            print FeatureExt  
            os.system(FeatureExt)
            ch = ch+opath+"/"+feature+"/"+oname+" "

         ConcNDWI = "otbcli_ConcatenateImages -il "+ch+" -out "+opathF+"/NDWI_LANDSAT.tif "+pixelo
         print (ConcNDWI)
         os.system(ConcNDWI)


      if feature == "Brightness":
         for date in dlist:
            i = dlist.index(date)
            a = bandsL["aero"] + (i*7)
            b = bandsL["blue"] + (i*7)
            g = bandsL["green"] + (i*7)
            r = bandsL["red"] + (i*7)
            nir = bandsL["NIR"] + (i*7)
            swir = bandsL["SWIR1"] + (i*7)
            swir2 = bandsL["SWIR2"] + (i*7)
            oname = feature+"_"+str(date)+"_"+name[0]+".tif"
	    #OTB 4.3
            #expr = "\"if(im1b"+str(g)+"==-10000,-10000,sqrt((im1b"+str(g)+" * im1b"+str(g)\
            #+") + (im1b"+str(r)+" * im1b"+str(r)+") + (im1b"+str(nir)+" * im1b"+str(nir)\
            #+") + (im1b"+str(swir)+" * im1b"+str(swir)+")))\""
	    #OTB 5.0
            expr = "\"(im1b"+str(g)+"==-10000?-10000:sqrt((im1b"+str(g)+" * im1b"+str(g)\
            +") + (im1b"+str(r)+" * im1b"+str(r)+") + (im1b"+str(nir)+" * im1b"+str(nir)\
            +") + (im1b"+str(swir)+" * im1b"+str(swir)+")))\""
            FeatureExt = "otbcli_BandMath -il "+imSerie+" -out "+opath+"/"+feature+"/"+oname+" "+pixelo+" -exp "+expr
            print FeatureExt
            os.system(FeatureExt)


      if feature == "Greenness":
         ch = ""
         for date in dlist:
            i = dlist.index(date)
            b = bandsL["blue"] + (i*7)
            g = bandsL["green"] + (i*7)
            r = bandsL["red"] + (i*7)
            oname = feature+"_"+str(date)+"_"+name[0]+".tif"
	    #OTB 4.3
            #expr = "\"if(im1b"+str(b)+"==-10000,-10000,if(abs(im1b"+str(r)+" + im1b"+str(b)\
            #+" + im1b"+str(g)+")<0.000001,0,(im1b"+str(g)+"/(im1b"+str(r)+" + im1b"+str(b)+" + im1b"+str(g)+"))))\""
	    #OTB 5.0
            expr = "\"(im1b"+str(b)+"==-10000?-10000:if(abs(im1b"+str(r)+" + im1b"+str(b)\
            +" + im1b"+str(g)+")<0.000001?0:(im1b"+str(g)+"/(im1b"+str(r)+" + im1b"+str(b)+" + im1b"+str(g)+"))))\""
            FeatureExt = "otbcli_BandMath -il "+imSerie+" -out "+opath+"/"+feature+"/"+oname+" "+pixelo+" -exp "+expr
            print FeatureExt
            os.system(FeatureExt)
            ch = ch+opath+"/"+feature+"/"+oname+" "
         ConcGr = "otbcli_ConcatenateImages -il "+ch+" -out "+opathF+"/Greenness_LANDSAT.tif "+pixelo
         print ConcGr
         os.system(ConcGr)     

   return 
      

#----------------------------------------------------------------------------
def Gapfilling(imageSeries, maskSeries, outputSeries, compPerDate, interpType, Datelist):
   
   if (os.path.exists(imageSeries) and os.path.exists(maskSeries)):
      command = pathAppGap+"gapfilling "+imageSeries+" "+maskSeries+" "+outputSeries+" "+str(compPerDate)+" "+str(interpType)+" "+Datelist
      print command
      os.system(command)
   
#------------------------------------------------------------------------------
def GetCommZoneExtent(shp):
   """
   Gets the extent of a shapefile:xmin, ymin, xmax,ymax
   ARGs:
       INPUT:
            -shp: the shapefile
   """

   inDriver = ogr.GetDriverByName("ESRI Shapefile")
   inDataSource = inDriver.Open(shp, 0)
   inLayer = inDataSource.GetLayer()
   extent = inLayer.GetExtent()

   return extent
   
#-----------------------------------------------------------------------------
def ClipRasterToShp(image, shp, opath):
   """
   Cuts a raster image using a shapefile
   ARGs:
       INPUT:
            -image: the image to be cut
            -shp: the shapefile
            -opath
       OUTPUT:
            -the initial raster image cut by the shapefile
   """
 
   impath = image.split('/')
   imname = impath[-1].split('.')
   extent = GetCommZoneExtent(shp)
   xmin, xmax, ymin, ymax  = GetCommZoneExtent(shp)
   imageclipped = opath+"/"+imname[0]+"_clipped."+imname[-1]
   if os.path.exists(imageclipped):
      os.remove(imageclipped)
   Clip = "gdalwarp -te "+str(xmin)+" "+str(ymin)+" "+str(xmax)+" "+str(ymax)+" "+image+" "+imageclipped
   os.system(Clip)  
   
   return imageclipped

#------------------------------------------------------------------------------

def MeanShiftSmooth(imageSerie, sr, rr, mi, opath):
   """
   Applies the Mean Shift Smoothing
   ARGs:
       INPUT:
            -imageSerie
            -sr: spatial radius (integer)
            -rr: range radius (integer)
            -maxiter: maximum of iterations (integer)
       OUTPUT:
            -the image serie smoothed
   """    
   name = imageSerie.split('.')
   name2 = name[0].split('/')
   Smooth = "otbcli_MeanShiftSmoothing -in "+imageSerie+" -spatialr "+str(sr)+" -ranger "+str(rr)+" -maxiter "+str(mi)+" -fout "+opath+"/"+name2[-1]+str(sr)+"_"+str(rr)+"_"+str(mi)+"_SMTH.tif"+" -foutpos "+opath+"/"+name2[-1]+str(sr)+"_"+str(rr)+"_"+str(mi)+"_SMTH_foutpos.tif -ram 128" 
   print Smooth
   os.system(Smooth)  

#-------------------------------------------------------------------------------- 
def ClipVectorData(vectorFile, shpMask):
   """
   Cuts a shapefile with another shapefile
   ARGs:
       INPUT:
            -vectorFile: the shapefile to be cut
            -shpMask: the other shapefile 
       OUTPUT:
            -the vector file cut
   """
   nameV = vectorFile.split('.') 
   Clip = "ogr2ogr -clipsrc "+shpMask+" "+nameV[0]+"clipped."+nameV[1]+" "+vectorFile
   print Clip
   os.system(Clip)

#---------------------------------------------------------------------------------
def GetFeatList(feature, opath):
   """
   Gets the list of features in a directory, used for NDVI, NDWI, Brightness 
   ARGs:
       INPUT:
            -feature: the name of the feature            
   """
   imageList = []
   for image in glob.glob(opath+"/"+feature+"/"+feature+"*.tif"):  
      imagePath = image.split('/')
      imageList.append(imagePath[-1])
   return imageList
#---------------------------------------------------------------------------------
def ConcatenateFeatures(opathT, opathF):
   """
   Concatenates all the index found in a directory to create one multiband image
   ARGs:
       INPUT:
            -opath: path were the directories (NDVI, NDWI, Brightness) are.
      OUTPUT:
            -the concatenated bands per feature
   """

   features = ['NDVI', 'NDWI', 'Brightness']

   for feature in features:
      ch = ""
      indexList = GetFeatList(feature, opathT)
      indexList.sort()
      print indexList
      for image in indexList:
         ch = ch +opathT+"/"+feature+"/"+image + " "
      Concatenate = "otbcli_ConcatenateImages -il "+ch+" -out "+opathF+"/"+feature+".tif "+pixelo
      print Concatenate 
      os.system(Concatenate)
#------------------------------------------------------------------------------ 
def ComputeImageStats(imSerie):
   name = imSerie.split('.')
   Stat = "otbcli_ComputeImageStatistics -il "+imSerie+" -out "+name[0]+".xml"
   os.system(Stat)
#-------------------------------------------------------------------------------
def CreateCommonZoneL30m(opath):
   """
   Creates the common zone using the border mask LANDSAT
   ARGs:
       INPUT:
            -opath: the output path
          
       OUTPUT:
            - A binary mask and a shapefile
   """
  
   shpMask = opath+"/MaskL30m.shp"
   
   VectorMask = "gdal_polygonize.py -f \"ESRI Shapefile\" -mask "+opath+"/MaskL30m.tif "+opath\
   +"/MaskL30m.tif "+opath+"/MaskL30m.shp"
   os.system(VectorMask)

   return shpMask
#-------------------------------------------------------------------------------
def getNbBands(pszFilename):
   hDataset = gdal.Open( pszFilename, gdal.GA_ReadOnly)
   return hDataset.RasterCount

#-------------------------------------------------------------------------------

def confusionMap(refrasterdata, classification, opath):
   nameout = classification.split('/')
   if len(nameout) > 0:
	name = nameout[-1].split('.')[0]
   elif len(nameout)== 0:
	name = classification.split('.')[0]
   #OTB 4.3
   #command = "otbcli_BandMath -il "+refrasterdata+" "+classification+" -exp \"if(im1b1==0,255,if(im1b1==im2b1, 0, 1))\" -out "+opath+"/confusionMap_"+name+".tif uint8"
   #OTB 5.0
   command = "otbcli_BandMath -il "+refrasterdata+" "+classification+" -exp \"(im1b1==0?255:(im1b1==im2b1? 0: 1))\" -out "+opath+"/confusionMap_"+name+".tif uint8"
   print command
   os.system(command)

#-------------------------------------------------------------------------------
def rasterize(refvectordata, refimage, field, opath):
   name = refvectordata.split('/')[-1].split('.')[0]
   command = "otbcli_Rasterization -in "+refvectordata+" -im "+refimage+" -out "+opath+"/"+name\
   +".tif -mode attribute -mode.attribute.field "+field
   print command
   exit =  os.system(command)
   if exit == 0:
      return opath+"/"+name+".tif"
   else:
      print "Not possible to rasterize"
      return -1
	





	

#---------------------------------------------------------------------------------

def GetBorderProp(mask):
   """
   Calculates the proportion of valid pixels in a mask. Is used to calculate
   the number of images to be used to build the mask

   ARGs 
       INPUT:
             -mask: the binary mask 
       OUTPUT:
             -Returns the proportion of valid pixels
   """

   hDataset = gdal.Open(mask, gdal.GA_ReadOnly )
   x = hDataset.RasterXSize
   y = hDataset.RasterYSize
   hBand = hDataset.GetRasterBand(1)
   stats = hBand.GetStatistics(True, True)
   mean = stats[2]
   nbPixel=x*y
   nbPixelCorrect=nbPixel*mean
   p=nbPixelCorrect*100/nbPixel
   
   return p
