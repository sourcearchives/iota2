
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

import os
from osgeo import ogr,osr,gdal
import glob,shutil,otbAppli
import fileUtils as fu
from Utils import run

pixelo = "int16"
otbVersion = 5.0
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

def CreateCommonZone_bindings(opath, borderMasks,wMode):
   """
   Creates the common zone using the border mask of SPOT  and LANDSAT

   ARGs:
       INPUT:
            -opath: the output path
            
       OUTPUT:
            - A binary mask and a shapefile
   """
   shpMask = opath+"/MaskCommunSL.shp"
   exp = "*".join(["im"+str(i+1)+"b1" for i in range(len(borderMasks))])
   outputRaster = opath+"/MaskCommunSL.tif"
   commonMask = otbAppli.CreateBandMathApplication({"il": borderMasks,
                                                    "exp": exp,
                                                    "pixType": 'uint8',
                                                    "out": outputRaster})

   if not os.path.exists(opath+"/MaskCommunSL.tif") : commonMask.ExecuteAndWriteOutput()
   
   VectorMask = "gdal_polygonize.py -f \"ESRI Shapefile\" -mask "+\
                opath+"/MaskCommunSL.tif "+opath+"/MaskCommunSL.tif "+\
                opath+"/MaskCommunSL.shp"
   print VectorMask
   run(VectorMask)
   return outputRaster

def CreateCommonZone(opath, liste_sensor):
   """
   Creates the common zone using the border mask of SPOT  and LANDSAT

   ARGs:
       INPUT:
            -opath: the output path
            
       OUTPUT:
            - A binary mask and a shapefile
   """
   
   #mask = "otbcli_BandMath -il "+opath+"/MaskS.tif "+opath+"/MaskL20m.tif -exp \"im1b1  and im2b1\""+" -out "+opath+"/MaskCommunSL.tif"
   #run(mask)
   mask_sensor = ""
   exp = " "
   for i  in range(len(liste_sensor)):
       sensor = liste_sensor[i]
       mask_sensor += sensor.borderMask+" "
       exp = "im%sb1*"%(i+1)#to get intersection between sensors
       #exp = "im%sb1+"%(i+1)#to get sensors union
   exp = exp[0:-1]
   print exp
   print mask_sensor
   BuildMask = "otbcli_BandMath -il "+mask_sensor+" -exp "+exp+" -out "+opath+"/MaskCommunSL.tif "+pixelo
   print "BuildMask"
   print BuildMask
   run(BuildMask)
  
   shpMask = opath+"/MaskCommunSL.shp"
   
   VectorMask = "gdal_polygonize.py -f \"ESRI Shapefile\" -mask "+opath+"/MaskCommunSL.tif "+opath\
   +"/MaskCommunSL.tif "+opath+"/MaskCommunSL.shp"
   print VectorMask
   run(VectorMask)
   return shpMask


def Gapfilling(imageSeries, maskSeries, outputSeries, compPerDate, interpType, DatelistI, DatelistO,wOut):
   
   if (os.path.exists(imageSeries) and os.path.exists(maskSeries)):
      command = "otbcli_ImageTimeSeriesGapFilling -in "+imageSeries+" -mask "+maskSeries+" -out "+outputSeries+" "+pixelo+" -comp "+str(compPerDate)+" -it linear -id "+DatelistI+" -od "+DatelistO
      print command
      run(command)

def getDates(image, bandperdate):
   """
   Returns the number of dates of a multiband image
   ARGs:
       INPUT:
            -image: the multiband image
   """
   hDataset = gdal.Open( image, gdal.GA_ReadOnly )
   if hDataset is None:
      print("gdalinfo failed - unable to open '%s'." % image )
   
   bands = 0
   for iBand in range(hDataset.RasterCount):
      bands = bands+1
   
   dates = bands/bandperdate
      
   return dates


def FeatureExtraction(sensor, imListFile, opath,feat_sensor):

    imSerie = sensor.serieTempGap
    nbBands = sensor.nbBands
    fdates = open(imListFile)
    dlist = []
    for dates in fdates:
        dlist.append(int(dates))

    print sensor
    print imListFile
    print opath
    print feat_sensor
    print dlist
    
    bands = sensor.bands['BANDS'].keys()
    dates = getDates(imSerie, 4)
    indices = feat_sensor
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
                r = sensor.bands["BANDS"]["red"] + i*nbBands
                nir = sensor.bands["BANDS"]["NIR"] + i*nbBands
                oname = feature+"_"+str(date)+"_"+name[0]+".tif"
                if otbVersion >= 5.0:
                   expr =  "\"im1b"+str(nir)+"==-10000?-10000: abs(im1b"+str(nir)+"+im1b"+str(r)+")<0.000001?0:1000*(im1b"+str(nir)+"-im1b"+str(r)+")/(im1b"+str(nir)+"+im1b"+str(r)+")\""
                else:
                   expr = "\"if(im1b"+str(nir)+"==-10000,-10000,(if(abs(im1b"+str(nir)+"+im1b"+str(r)+")<0.000001,0,(im1b"+str(nir)+"-im1b"+str(r)+")/(im1b"+str(nir)+"+im1b"+str(r)+"))))\""
                FeatureExt = "otbcli_BandMath -il "+imSerie+" -out "+opath+"/"+feature+"/"+oname+" "+pixelo+" -exp "+expr
		if not os.path.exists(opath+"/"+feature+"/"+oname):
                        print FeatureExt
               		run(FeatureExt)

        if feature == "NDWI":
            for date in dlist:
                i = dlist.index(date)
                nir = sensor.bands["BANDS"]["NIR"] + (i*nbBands)
                swir = sensor.bands["BANDS"]["SWIR"] + (i*nbBands)
                oname = feature+"_"+str(date)+"_"+name[0]+".tif"
                if otbVersion >= 5.0:
                   expr = "\"im1b"+str(nir)+"==-10000?-10000: abs(im1b"+str(swir)+"+im1b"+str(nir)\
                          +")<0.000001?0:1000*(im1b"+str(swir)+"-im1b"+str(nir)+")/(im1b"+str(swir)+"+im1b"+str(nir)+")\""
                else:
                   expr = "\"if(im1b"+str(nir)+"==-10000,-10000,if(abs(im1b"+str(swir)+"+im1b"+str(nir)\
                          +")<0.000001,0,(im1b"+str(swir)+"-im1b"+str(nir)+")/(im1b"+str(swir)+"+im1b"+str(nir)+")))\""
                FeatureExt = "otbcli_BandMath -il "+imSerie+" -out "+opath+"/"+feature+"/"+oname+" "+pixelo+" -exp "+expr
                if not os.path.exists(opath+"/"+feature+"/"+oname):
               		run(FeatureExt)

        if feature == "Brightness":
            for date in dlist:
                i = dlist.index(date)
                if otbVersion >= 5.0:
                   expr = "\"im1b1 == -10000?-10000:(sqrt("
                else:
                   expr = " \"if(im1b1 ==-10000,-10000,sqrt("
                for band in bands:
                    ind = sensor.bands['BANDS'][band] + (i*nbBands)
                    expr += "(im1b%s * im1b%s)+"%(ind,ind)
                expr = expr[0:-1]
                expr += "))\""
                oname = feature+"_"+str(date)+"_"+name[0]+".tif"
                #expr = "\"if(im1b"+str(g)+"==-10000,-10000,sqrt((im1b"+str(g)+" * im1b"+str(g)+") + (im1b"+str(r)+" * im1b"+str(r)+") + (im1b"+str(nir)+" * im1b"+str(nir)+") + (im1b"+str(swir)+" * im1b"+str(swir)+")))\""
                print expr
                FeatureExt = "otbcli_BandMath -il "+imSerie+" -out "+opath+"/"+feature+"/"+oname+" "+pixelo+" -exp "+expr
                if not os.path.exists(opath+"/"+feature+"/"+oname):
               		run(FeatureExt)

	# Modifier les options
	if feature == "Haralick":
            for date in dlist:
                oname = feature+"_"+str(date)+"_"+name[0]+".tif"
                FeatureExt = "otbcli_HaralickTextureExtraction -in "+imSerie+" -out "+opath+"/"+feature+"/"+oname+" "+pixelo
                print FeatureExt
		run(FeatureExt)

	# Modifier les options
	if feature == "Statistics":
            for date in dlist:
                oname = feature+"_"+str(date)+"_"+name[0]+".tif"
                FeatureExt = "otbcli_LocalStatisticExtraction -in "+imSerie+" -out "+opath+"/"+feature+"/"+oname+" "+pixelo
		print FeatureExt
                run(FeatureExt)

    return 0

def ReflExtraction(sensor,tmpPath):
	nameOut = sensor.serieTempGap.split("/")[-1]
	cmd = "otbcli_SplitImage -in "+sensor.serieTempGap+" -out "+tmpPath+"/REFL/"+nameOut+" "+pixelo
	print cmd
	run(cmd)
	
def GetFeatList(feature, opath):
   """
   Gets the list of features in a directory, used for NDVI, NDWI, Brightness 
   ARGs:
       INPUT:
            -feature: the name of the feature            
   """
   imageList = []
   IMG = fu.FileSearch_AND(opath+"/"+feature,True,feature,".tif")
   IMG = sorted(IMG)
   print opath+"/"+feature
   print "les images :"
   print IMG
   #for image in glob.glob(opath+"/"+feature+"/"+feature+"*.tif"): 
   for image in IMG:  
      imagePath = image.split('/')
      imageList.append(imagePath[-1])
   return imageList

def ConcatenateFeatures(opath,Indices):
   """
   Concatenates all the index found in a directory to create one multiband image
   ARGs:
       INPUT:
            -opath: path were the directories (NDVI, NDWI, Brightness) are.
      OUTPUT:
            -the concatenated bands per feature
   """

   chaine_ret = ""
   features = Indices
   for feature in features:
      ch = ""
      indexList = GetFeatList(feature, opath.opathT)
      indexList.sort()
     
      for image in indexList:
         ch = ch +opath.opathT+"/"+feature+"/"+image+" "
    
      Concatenate = "otbcli_ConcatenateImages -il "+ch+" -out "+opath.opathF+"/"+feature+".tif "+pixelo
      
      if not os.path.exists(opath.opathF+"/"+feature+".tif"):
        print Concatenate
      	run(Concatenate)
      chaine_ret += opath.opathF+"/"+feature+".tif "
      
   return chaine_ret

def Reflkey(item):
	return int(item.split("_")[-1].replace(".tif",""))

def OrderGapFSeries(opath,list_sensor,opathT):
   
   print len(list_sensor)
   if len(list_sensor) == 1:
          
      sensor = list_sensor[0]
      command = "cp %s %s"%(sensor.serieTempGap,opath.opathF+"/SL_MultiTempGapF.tif")
      run(command)
   else:
      chaine_concat = " "
      for sensor in list_sensor:
         chaine_concat += sensor.serieTempGap+" "
      command = "otbcli_ConcatenateImages -il "+chaine_concat+" -out "+opath.opathF+"/SL_MultiTempGapF.tif "+pixelo
      print command
      if not os.path.exists(opath.opathF+"/SL_MultiTempGapF.tif"):
      	run(command)

   return opath.opathF+"/SL_MultiTempGapF.tif"
   
   """
   #AllRefl = fu.fileSearchRegEx(opathT+"/REFL/*.tif")
   AllRefl = fu.FileSearch_AND(opathT+"/REFL",True,".tif")
   AllRefl = sorted(AllRefl,key=Reflkey)
   print "ALL REFL sort"
   print AllRefl
   return " ".join(AllRefl)
   """

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
   xmin, xmax, ymin, ymax  = GetCommZoneExtent(shp)
   imageclipped = opath+"/"+imname[0]+"_clipped."+imname[-1]
   if os.path.exists(imageclipped):
      os.remove(imageclipped)
   Clip = 'gdalwarp -te '+str(xmin)+' '+str(ymin)+' '+str(xmax)+' '+str(ymax)+' '+image+' '+imageclipped
   run(Clip)  
   
   return imageclipped
