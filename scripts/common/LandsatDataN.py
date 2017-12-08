#!/usr/bin/python

import os
import glob
from sys import argv
from osgeo import gdal, ogr, osr
from osgeo.gdalconst import GA_ReadOnly
from datetime import date, datetime, timedelta
import Dico as dico
from Utils import run

"""This is the module to get LANDSAT data \n
including images and masks and according \n
to the LANDSAT8/N2A_THEIA folders organization"""

Lbands = 7
pathAppGap = dico.pathAppGap
bandsL = dico.bandLandsat()
maskC = dico.maskL
pixelo = dico.pixelotb

def CreateDir(opath, tile):
   """
   Creates the folders
   """
   sp = ['Final', 'tmp', 'in-situ']
   #for p in tileList:
   if not os.path.exists(opath+"/"+tile):
      os.mkdir(opath+"/"+tile)
   for s in sp:      
      if not os.path.exists(opath+"/"+tile+"/"+s):
         os.mkdir(opath+"/"+tile+"/"+s)
   #if os.path.exists(opath+"/"+tile+"/Final/Images"):
      #os.remove(opath+"/"+tile+"/Final/Images")
   if not os.path.exists(opath+"/"+tile+"/Final/Images"):
      os.mkdir(opath+"/"+tile+"/Final/Images")


def getLandsatImages(ipath, opath, tile):
   """
   Returns the list of the LANDSAT Images in choronological order
       INPUT:
            -ipath: LANDSAT images path
            -opath: output path
           
       OUTPUT:
            - A texte file named LandsatImagesList.txt, containing the names and path of the LANDSAT images 
            - A texte file named LandsatImagesDateList.txt, containing the list of the dates in chronological order
    
   """

   file = open(opath+"/LANDSATimagesList_"+tile+".txt", "w")
   filedate = open(opath+"/LANDSATimagesDateList_"+tile+".txt", "w")
   count = 0
   imageList = []
   fList = []
   dateList = []
  
   #Find all matches and put them in a list 
   for image in glob.glob(ipath+"/"+tile+"/*/*ORTHO_SURF_CORR_PENTE*.TIF"):
      imagePath = image.split('/')
      imageName = imagePath[-1].split('.')
      imageNameParts = imageName[0].split('_')
      if int(imageNameParts[3]) <= 20131231:
         file.write(image)
         file.write('\n')
         imageList.append(imageNameParts)
         fList.append(image) 

  #Re-organize the names by date according to LANDSAT naming
   imageList.sort(key=lambda x: x[3])
   #Write all the images in chronological order in a text file
   for imSorted  in imageList:
      filedate.write(imSorted[3])
      filedate.write('\n')
      count = count + 1
    
   filedate.close() 
   file.close()    
   return fList

def getLandsatCloudMask(imagePath):
   """
   Get the name of the cloud mask using the name of the image
   ARGs:
       INPUT:
            -imagePath: the absolute path of one image
       OUTPUT:
            -The name of the corresponding cloud mask

   """
   folder = imagePath.split('/')
   imageName = folder[-1].split('.')
   imageNameP = imageName[0].split('_')
   maskName = '_'.join(imageNameP[0:-5])+'_'+imageNameP[-1]+'_NUA.TIF'
   mask = '/'.join(folder[0:-1])+'/MASK/'+maskName
           
   return mask

def getLandsatSatMask(imagePath):
   """
   Get the name of the saturation mask using the name of the image
   ARGs:
       INPUT:
            -imagePath: the absolute path of one image
       OUTPUT:
            -The name of the corresponding cloud mask

   """
   folder = imagePath.split('/')
   imageName = folder[-1].split('.')
   imageNameP = imageName[0].split('_')
   maskName = '_'.join(imageNameP[0:-5])+'_'+imageNameP[-1]+'_SAT.TIF'
   mask = '/'.join(folder[0:-1])+'/MASK/'+maskName
           
   return mask

def getLandsatDivMask(imagePath):
   """
   Get the name of the divers mask using the name of the image
   ARGs:
       INPUT:
            -imagePath: the absolute path of one image
       OUTPUT:
            -The name of the corresponding cloud mask

   """
   folder = imagePath.split('/')
   imageName = folder[-1].split('.')
   imageNameP = imageName[0].split('_')
   maskName = '_'.join(imageNameP[0:-5])+'_'+imageNameP[-1]+'_DIV.TIF'
   mask = '/'.join(folder[0:-1])+'/MASK/'+maskName
           
   return mask

def getLandsatNoDataMask(imagePath):
   """
   Get the name of the divers mask using the name of the image
   ARGs:
       INPUT:
            -imagePath: the absolute path of one image
       OUTPUT:
            -The name of the corresponding cloud mask

   """
   folder = imagePath.split('/')
   imageName = folder[-1].split('.')
   imageNameP = imageName[0].split('_')
   maskName = '_'.join(imageNameP[0:-5])+'_'+imageNameP[-1]+'_NODATA.TIF'
   mask = '/'.join(folder[0:-1])+'/MASK/'+maskName
           
   return mask
 
def getList_LandsatCloudMask(listimagePath):
   """
   Get the list of the cloud masks for each image on the images list
   ARGs:
       INPUT:
            -listimagePath: the list with the absolute path of the images
       OUTPUT:
            -The list with the name of the corresponding masks
   """
   listMask = []
   for image in listimagePath:
      listMask.append(getLandsatCloudMask(image))
   
   return listMask

def getList_LandsatSatMask(listimagePath):
   """
   Get the list of the cloud masks for each image on the images list
   ARGs:
       INPUT:
            -listimagePath: the list with the absolute path of the images
       OUTPUT:
            -The list with the name of the corresponding masks
   """
   listMask = []
   for image in listimagePath:
      listMask.append(getLandsatSatMask(image))
  
   return listMask

def getList_LandsatDivMask(listimagePath):
   """
   Get the list of the cloud masks for each image on the images list
   ARGs:
       INPUT:
            -listimagePath: the list with the absolute path of the images
       OUTPUT:
            -The list with the name of the corresponding masks
   """
   listMask = []
   for image in listimagePath:
      listMask.append(getLandsatDivMask(image))
  
   return listMask

def getList_LandsatNoDataMask(listimagePath):
   """
   Get the list of the cloud masks for each image on the images list
   ARGs:
       INPUT:
            -listimagePath: the list with the absolute path of the images
       OUTPUT:
            -The list with the name of the corresponding masks
   """
   listMask = []
   for image in listimagePath:
      listMask.append(getLandsatNoDataMask(image))
  
   return listMask

def CreateBorderMaskLandsat(ipath, tile, opath):
   """
   Creates the mask of borders 
   ARGs 
       INPUT:
             -ipath: absolute path of the LANDSAT images
             -opath: path were the mask will be created
       OUTPUT:
             -Border mask 30 m
   """
   
   imlist = getLandsatImages(ipath, opath, tile)
   mlist = getList_LandsatDivMask(imlist)
   #Get the info of the image
   ds = gdal.Open(imlist[0], GA_ReadOnly)
   nb_col=ds.RasterXSize
   nb_lig=ds.RasterYSize
   proj=ds.GetProjection()
   gt=ds.GetGeoTransform()
   ulx = gt[0]
   uly = gt[3]
   lrx = gt[0] + nb_col*gt[1] + nb_lig*gt[2]
   lry = gt[3] + nb_col*gt[4] + nb_lig*gt[5]
   propBorder = []

   srs=osr.SpatialReference(proj)
   
   #chain_proj = srs.GetAuthorityName('PROJCS')+':'+srs.GetAuthorityCode('PROJCS')
   chain_proj = "EPSG:2154"

   resolX = abs(gt[1]) # resolution en metres de l'image d'arrivee 
   resolY = abs(gt[5]) # resolution en metres de l'image d'arrivee
   chain_extend = str(ulx)+' '+str(lry)+' '+str(lrx)+' '+str(uly)  

   #Builds the individual binary masks
   listMaskch = ""
   listMask = []
   for i in range(len(mlist)):
        name = mlist[i].split("/")
	#OTB 4.3
        #run("otbcli_BandMath -il "+mlist[i]\
        #+" -out "+opath+"/"+name[-1]+" -exp "\
        #+"\"if(im1b1 and 00000001,0,1)\"")
	#OTB 5.0
        run("otbcli_BandMath -il "+mlist[i]\
        +" -out "+opath+"/"+name[-1]+" -exp "\
        +"\"(im1b1 and 00000001?0:1)\"")
        listMaskch = listMaskch+opath+"/"+name[-1]+" "
        listMask.append(opath+"/"+name[-1])
  
   #Builds the complete binary mask
   expr = "0"
   for i in range(len(listMask)):
      expr += "+im"+str(i+1)+"b1"

   BuildMaskSum = "otbcli_BandMath -il "+listMaskch+" -out "+opath+"/SumMaskL30m.tif -exp "+expr
   run(BuildMaskSum)

   #Calculate how many bands will be used for building the common mask

   for mask in listMask:
      p = GetBorderProp(mask)
      propBorder.append(p)
   sumMean = 0
   for value in propBorder:
      sumMean = sumMean+value
   meanMean = sumMean/len(propBorder)
   usebands = 0
   for value in propBorder:
      if value>=meanMean:
         usebands = usebands +1
   usebands = 6
   #Builds the mask
   #OTB 4.3
   #expr = "\"if(im1b1>="+str(usebands)+",1,0)\""
   #OTB 5.0
   expr = "\"(im1b1>="+str(usebands)+"?1:0)\""
   BuildMaskBin = "otbcli_BandMath -il "+opath+"/SumMaskL30m.tif -out "+opath+"/MaskL30m.tif -exp "+expr
   print BuildMaskBin
   run(BuildMaskBin)

   VectorMask = "gdal_polygonize.py -f \"ESRI Shapefile\" -mask "+opath+"/MaskL30m.tif "+opath\
   +"/MaskL30m.tif "+opath+"/MaskL30m.shp"
   run(VectorMask)

   #for mask in listMask:
      #os.remove(mask)

   return 0

def CreateMaskSeriesLandsat(ipath, opath, tile):
   """
   Builds one multitemporal binary mask of L8 images

   ARGs 
       INPUT:
             -ipath: absolute path of the resized masks
             -opath: path were the multitemporal mask will be created
       OUTPUT:
             -Multitemporal binary mask .tif
   """
   imlist = getLandsatImages(ipath, opath, tile)
   clist = getList_LandsatResCloudMask(imlist)
   slist = getList_LandsatResSatMask(imlist)
   dlist = getList_LandsatResDivMask(imlist)
   maskL = opath+"/MaskL30m.tif"
   
   #print imlist
   chain = ""
   allNames = ""
   listallNames = []
   bandclipped = []
   bandChain = ""

   for im in range(0,len(imlist)):
      impath = imlist[im].split('/')
      imname = impath[-1].split('.')
      name = opath+'/'+imname[0]+'_MASK.tif'
      chain = clist[im]+' '+slist[im]+' '+dlist[im]
      #OTB 4.3
      #Binary = "otbcli_BandMath -il "+maskC+" "+chain+" -exp \"(im1b1 * (if(im2b1>0,1,0) or if(im3b1>0,1,0))) or ((im4b1 and 00000001)*im1b1)\" -out "+name
      #OTB 5.0
      Binary = "otbcli_BandMath -il "+maskC+" "+chain+" -exp \"(im1b1 * ((im2b1>0?1:0) or (im3b1>0?1:0))) or ((im4b1 and 00000001)*im1b1)\" -out "+name
      run(Binary)
      #bandclipped.append(DP.ClipRasterToShp(name, opath+"/"+maskCshp, opath))
      listallNames.append(name)

   for bandclip in bandclipped:
      bandChain = bandChain + bandclip + " "

   Concatenate = "otbcli_ConcatenateImages -il "+bandChain+" -out "+opath+"/LANDSAT_MultiTempMask_clip.tif"
   run(Concatenate)

def createSerieLandsat(ipath, opath, tile):
   """
   Concatenation of all the images Landsat to create one multitemporal multibands image
   ARGs 
       INPUT:
             -ipath: absolute path of the images
             -opath: path were the images will be concatenated
       OUTPUT:
             -Multitemporal, multiband serie   
   """
   imlist = getLandsatImages(ipath, opath, tile)
   ilist = ""
   olist = []
   bandlist = []
   bandclipped = []
   maskL = "MaskL30m.tif"
   for image in imlist:
      ilist = ilist + image + " "
      olist.append(image)

   for image in imlist:
      impath = image.split('/')
      imname = impath[-1].split('.')
      splitS = "otbcli_SplitImage -in "+image+" -out "+opath+"/"+impath[-1]
      #print splitS
      run(splitS)
      for band in range(0, int(Lbands)):
         bnamein = imname[0]+"_"+str(band)+".TIF"
         bnameout = imname[0]+"_"+str(band)+"_masked.tif"
         #OTB 4.3
         #maskB = "otbcli_BandMath -il "+opath+"/"+maskL+" "+opath+"/"+bnamein+" -exp \"if(im1b1==0,-10000, if(im2b1!=-10000 and im2b1<0,0,im2b1))\" -out "+opath+"/"+bnameout
         #OTB 5.0
         maskB = "otbcli_BandMath -il "+opath+"/"+maskL+" "+opath+"/"+bnamein+" -exp \"(im1b1==0?-10000: (im2b1!=-10000 and im2b1<0?0:im2b1))\" -out "+opath+"/"+bnameout

         run(maskB)
         #bandclipped.append(DP.ClipRasterToShp(opath+"/"+bnameout, opath+"/"+maskCshp, opath))
         print maskB
         bandlist.append(opath+"/"+bnameout)
 
   bandChain = " "

   for band in bandlist:
      bandChain = bandChain + band + " "


   Concatenate = "otbcli_ConcatenateImages -il "+bandChain+" -out "+opath+"/LANDSAT_MultiTempIm_clip.tif"
   run(Concatenate)
   
   return opath+"/LANDSAT_MultiTempIm_clip.tif"

def CreateMaskSeriesLandsat(ipath, opath, tile):
   """
   Builds one multitemporal binary mask of SPOT images

   ARGs 
       INPUT:
             -ipath: absolute path of the resized masks
             -opath: path were the multitemporal mask will be created
       OUTPUT:
             -Multitemporal binary mask .tif
   """
   imlist = getLandsatImages(ipath, opath, tile)
   clist = getList_LandsatCloudMask(imlist)
   slist = getList_LandsatSatMask(imlist)
   dlist = getList_LandsatDivMask(imlist)
   maskC = opath+"/MaskL30m.tif"
   
   #print imlist
   chain = ""
   allNames = ""
   listallNames = []
   bandclipped = []
   bandChain = ""

   for im in range(0,len(imlist)):
      impath = imlist[im].split('/')
      #print impath
      imname = impath[-1].split('.')
      name = opath+'/'+imname[0]+'_MASK.tif'
      chain = clist[im]+' '+slist[im]+' '+dlist[im]
      #OTB 4.3
      #Binary = "otbcli_BandMath -il "+maskC+" "+chain+" -exp \"(im1b1 * (if(im2b1>0,1,0) or if(im3b1>0,1,0))) or ((im4b1 and 00000001)*im1b1)\" -out "+name
      #OTB 5.0
      Binary = "otbcli_BandMath -il "+maskC+" "+chain+" -exp \"(im1b1 * ((im2b1>0?1:0) or (im3b1>0?1:0))) or ((im4b1 and 00000001)*im1b1)\" -out "+name
      #print Binary
      run(Binary)
      #bandclipped.append(DP.ClipRasterToShp(name, opath+"/"+maskCshp, opath))
      #allNames = allNames +name+" "
      listallNames.append(name)

   for band in listallNames:
      bandChain = bandChain + band + " "

   Concatenate = "otbcli_ConcatenateImages -il "+bandChain+" -out "+opath+"/LANDSAT_MultiTempMask_clip.tif "
   run(Concatenate)

   return opath+"/LANDSAT_MultiTempMask_clip.tif"

def TempRes(imageSeries, maskSeries, outputSeries, compPerDate, interpType, inDatelist, outDatelist):
   
   if (os.path.exists(imageSeries) and os.path.exists(maskSeries)):
      command = "otbcli_ImageTimeSeriesGapFilling -in "+imageSeries+" -mask "+maskSeries+" -out "+outputSeries+" -comp "+str(compPerDate)+" -it linear -id "+inDatelist+" -od "+outDatelist
      print command
      run(command)
   else:
      print "Files dont exist"

def getfirstdate(opath, tile):
   """Get the first date of a range of dates"""
   f = open(opath+'/'+tile+'/Final/LANDSATimagesDateList_'+tile+'.txt', 'r')
   dateList = f.readlines()
   f.close()
   fdate = int(dateList[0])
   print fdate
   return fdate

def getlastdate(opath, tile):
   """Get the last date of a range of dates"""
   f = open(opath+'/'+tile+'/Final/LANDSATimagesDateList_'+tile+'.txt', 'r')
   dateList = f.readlines()
   f.close()
   ldate = int(dateList[len(dateList)-1])
   print ldate
   return ldate

"""
def getlastfirstdate(opath, *tiles):
   firstDates = []
   for i in tiles:
      print i
      date = getfirstdate(opath, i)
      firstDates.append(date)
   firstDates.sort()
   print firstDates
   #print firstDates
"""
#------------------------------------------------------------------------------
def readDatesFile(filedates):
   """
   Reads a txt file containing a list of dates, returns the first and the last one
   ARGs:
       INPUT:
            - File containing the list of dates
   """
   count = 0
   dList = []
   with open(filedates) as f:
      data = f.readlines()
   reader = csv.reader(data)
   dates = list(reader)
   st_date = dates[0][0]
   end_date = dates[len(dates)-1][0]
   return st_date, end_date

#-------------------------------------------------------------------------------
def RangeDates(startD, endD, delta, opath):
   """
   Creates a file of resampled dates.
   ARGs:
       INPUT:
            - File containing the list of dates
            - Number of dates between them
            - opath
      OUTPUT:
            - Text file containgin the list of dates
   """
   
   start = datetime.strptime(startD, '%Y%m%d' )
   end = datetime.strptime(endD, '%Y%m%d')
   
   if start > end:
      raise ValueError('You provided a start_date that comes after the end_date.')
   #Here days = 3 to resample LANDSAT images, if not days = 0
   start2 = start + timedelta(days=3)
   start = start2
   fileD = opath+"/"+"TemRes_"+startD+"-"+endD+"-"+str(delta)+"days.txt"
   if os.path.exists(fileD):
      os.remove(fileD)
   f = open(fileD, 'w')
   step = timedelta(days=int(delta))
   while start <= end:
      date = str(start.date())
      ymd = date.split('-')
      dateinF = ''.join(ymd)
      f.write(dateinF+'\n')
      #print dateinF
      start += step
   f.close
   print "The file "+fileD+" has been created"
   return fileD

#------------------------------------------------------------------------------------------
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
   fdates = open(imListFile)
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
            #expr = "\"if(im1b"+str(nir)+"==-10000,-10000,if(abs(im1b"+str(nir)+"+im1b"+str(r)\
            #+")<0.000001,0,(im1b"+str(nir)+"-im1b"+str(r)+")/(im1b"+str(nir)+"+im1b"+str(r)+")))*1000\""
            #OTB 5.0
            expr = "\"(im1b"+str(nir)+"==-10000?-10000:(abs(im1b"+str(nir)+"+im1b"+str(r)\
            +")<0.000001?0:(im1b"+str(nir)+"-im1b"+str(r)+")/(im1b"+str(nir)+"+im1b"+str(r)+")))\""
            FeatureExt = "otbcli_BandMath -il "+imSerie+" -out "+opath+"/"+feature+"/"+oname+" "+pixelo+" -exp "+expr
            run(FeatureExt)

            print FeatureExt           

      if feature == "NDWI":
         for date in dlist:
            i = dlist.index(date)
            nir = bandsL["NIR"] + (i*7)
            swir = bandsL["SWIR1"] + (i*7)
            oname = feature+"_"+str(date)+"_"+name[0]+".tif"
            #expr = "\"if(im1b"+str(nir)+"==-10000,-10000,if(abs(im1b"+str(swir)+"+im1b"+str(nir)\
            #+")<0.000001,0,(im1b"+str(swir)+"-im1b"+str(nir)+")/(im1b"+str(swir)+"+im1b"+str(nir)+")))*1000\""
	    #OTB 5.0
            expr = "\"(im1b"+str(nir)+"==-10000?-10000:(abs(im1b"+str(swir)+"+im1b"+str(nir)\
            +")<0.000001?0:(im1b"+str(swir)+"-im1b"+str(nir)+")/(im1b"+str(swir)+"+im1b"+str(nir)+")))\""
            FeatureExt = "otbcli_BandMath -il "+imSerie+" -out "+opath+"/"+feature+"/"+oname+" "+pixelo+" -exp "+expr
            run(FeatureExt)
            ch = ch+opath+"/"+feature+"/"+oname+" "
            print FeatureExt  
         ConcNDWI = "otbcli_ConcatenateImages -il "+ch+" -out "+opathF+"/NDWI_LANDSAT.tif "+pixelo
         print (ConcNDWI)
         run(ConcNDWI)


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
            #expr = "\"if(im1b"+str(g)+"==-10000,-10000,sqrt((im1b"+str(a)+" * im1b"+str(a)+" )+(im1b"+str(b)+" * im1b"+str(b)\
	    #+")+(im1b"+str(g)+" * im1b"+str(g)+") + (im1b"+str(r)+" * im1b"+str(r)+") + (im1b"+str(nir)+" * im1b"+str(nir)\
            #+") + (im1b"+str(swir)+" * im1b"+str(swir)+")+(im1b"+str(swir2)+" * im1b"+str(swir2)+")))\""
            #OTB 5.0
            expr = "\"(im1b"+str(g)+"==-10000?-10000:sqrt((im1b"+str(a)+" * im1b"+str(a)+" )+(im1b"+str(b)+" * im1b"+str(b)\
	    +")+(im1b"+str(g)+" * im1b"+str(g)+") + (im1b"+str(r)+" * im1b"+str(r)+") + (im1b"+str(nir)+" * im1b"+str(nir)\
            +") + (im1b"+str(swir)+" * im1b"+str(swir)+")+(im1b"+str(swir2)+" * im1b"+str(swir2)+")))\""
            print expr
            FeatureExt = "otbcli_BandMath -il "+imSerie+" -out "+opath+"/"+feature+"/"+oname+" "+pixelo+" -exp "+expr
            print FeatureExt
            run(FeatureExt)


   return 
#--------------------------------------------------------------------------------------------------------
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

#----------------------------------------------------------------------------------------------------------
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
      for image in indexList:
         ch = ch +opathT+"/"+feature+"/"+image + " "
      Concatenate = "otbcli_ConcatenateImages -il "+ch+" -out "+opathF+"/"+feature+".tif "+pixelo
      print Concatenate 
      run(Concatenate)
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

#---------------------------------------------------------------------------
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
   run(Concatenation)

#-----------------------------------------------------------------------------
def GetSerieList(*SerieList):
   """
   Returns a list of images likes a character chain.
   ARGs:
       INPUT:
            -SerieList: the list of different series
       OUTPUT:
   """  
   ch = ""
   for serie in SerieList:
     name = serie.split('.')
     ch = ch+serie+" "
   return ch

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
#-------------------------------------------------------------------------------
def getNbBands(pszFilename):
   hDataset = gdal.Open( pszFilename, gdal.GA_ReadOnly)
   return hDataset.RasterCount
#-------------------------------------------------------------------------------

   
