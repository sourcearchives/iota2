
import Dico as dico
import os
from osgeo import ogr,osr,gdal
import glob
pathAppGap = dico.pathAppGap
res = str(dico.res)
pixelo = dico.pixelotb
pixelg = dico.pixelgdal
indices = dico.indices
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
   #os.system(mask)
   mask_sensor = ""
   exp = " "
   for i  in range(len(liste_sensor)):
       sensor = liste_sensor[i]
       mask_sensor += sensor.borderMask+" "
       exp = "im%sb1*"%(i+1)
   exp = exp[0:-1]
   print exp
   print mask_sensor
   BuildMask = "otbcli_BandMath -il "+mask_sensor+" -exp "+exp+" -out "+opath+"/MaskCommunSL.tif "+pixelo
   os.system(BuildMask)
  
   shpMask = opath+"/MaskCommunSL.shp"
   
   VectorMask = "gdal_polygonize.py -f \"ESRI Shapefile\" -mask "+opath+"/MaskCommunSL.tif "+opath\
   +"/MaskCommunSL.tif "+opath+"/MaskCommunSL.shp"
   os.system(VectorMask)

   return shpMask


def Gapfilling(imageSeries, maskSeries, outputSeries, compPerDate, interpType, DatelistI, DatelistO):
   
   if (os.path.exists(imageSeries) and os.path.exists(maskSeries)):
      command = pathAppGap+"gapfilling "+imageSeries+" "+maskSeries+" "+outputSeries+" "+str(compPerDate)+" "+str(interpType)+" "+DatelistI+" "+DatelistO
      print command
      os.system(command)

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


def FeatureExtraction(sensor, imListFile, opath):

    imSerie = sensor.serieTempGap
    nbBands = sensor.nbBands
    fdates = open(imListFile)
    dlist = []
    for dates in fdates:
        dlist.append(int(dates))
    bands = sensor.bands['BANDS'].keys()
    dates = getDates(imSerie, 4)
    
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
                   expr =  "\"im1b"+str(nir)+"==-10000?-10000: abs(im1b"+str(nir)+"+im1b"+str(r)+")<0.000001?0:(im1b"+str(nir)+"-im1b"+str(r)+")/(im1b"+str(nir)+"+im1b"+str(r)+")\""
                else:
                   expr = "\"if(im1b"+str(nir)+"==-10000,-10000,(if(abs(im1b"+str(nir)+"+im1b"+str(r)+")<0.000001,0,(im1b"+str(nir)+"-im1b"+str(r)+")/(im1b"+str(nir)+"+im1b"+str(r)+"))))\""
                FeatureExt = "otbcli_BandMath -il "+imSerie+" -out "+opath+"/"+feature+"/"+oname+" "+pixelo+" -exp "+expr
                os.system(FeatureExt)


        if feature == "NDWI":
            for date in dlist:
                i = dlist.index(date)
                nir = sensor.bands["BANDS"]["NIR"] + (i*nbBands)
                swir = sensor.bands["BANDS"]["SWIR"] + (i*nbBands)
                oname = feature+"_"+str(date)+"_"+name[0]+".tif"
                if otbVersion >= 5.0:
                   expr = "\"im1b"+str(nir)+"==-10000?-10000: abs(im1b"+str(swir)+"+im1b"+str(nir)\
                          +")<0.000001?0:(im1b"+str(swir)+"-im1b"+str(nir)+")/(im1b"+str(swir)+"+im1b"+str(nir)+")\""
                else:
                   expr = "\"if(im1b"+str(nir)+"==-10000,-10000,if(abs(im1b"+str(swir)+"+im1b"+str(nir)\
                          +")<0.000001,0,(im1b"+str(swir)+"-im1b"+str(nir)+")/(im1b"+str(swir)+"+im1b"+str(nir)+")))\""
                FeatureExt = "otbcli_BandMath -il "+imSerie+" -out "+opath+"/"+feature+"/"+oname+" "+pixelo+" -exp "+expr
                os.system(FeatureExt)
                ch = ch+opath+"/"+feature+"/"+oname+" "
                print FeatureExt  
            #ConcNDWI = "otbcli_ConcatenateImages -il "+ch+" -out "+opathF+"/NDWI_LANDSAT.tif "+pixelo
            #print (ConcNDWI)
            #os.system(ConcNDWI)

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
                os.system(FeatureExt)

    return 0


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

def ConcatenateFeatures(opath):
   """
   Concatenates all the index found in a directory to create one multiband image
   ARGs:
       INPUT:
            -opath: path were the directories (NDVI, NDWI, Brightness) are.
      OUTPUT:
            -the concatenated bands per feature
   """

   chaine_ret = ""
   features = indices
   for feature in features:
      ch = ""
      indexList = GetFeatList(feature, opath.opathT)
      indexList.sort()
      print indexList
      for image in indexList:
         ch = ch +opath.opathT+"/"+feature+"/"+image + " "
      Concatenate = "otbcli_ConcatenateImages -il "+ch+" -out "+opath.opathF+"/"+feature+".tif "+pixelo
      print Concatenate
      
      os.system(Concatenate)
      chaine_ret += opath.opathF+"/"+feature+".tif "
   return chaine_ret

def OrderGapFSeries(opath,list_sensor):
   print len(list_sensor)
   if len(list_sensor) == 1:
         
      sensor = list_sensor[0]
      command = "cp %s %s"%(sensor.serieTempGap,opath.opathF+"/SL_MultiTempGapF.tif")
      os.system(command)
   else:
      fSL = open(opath.opathF+"/SL_MultiTempGap_DateList.txt", "w")
   
      allDates = []
      dico_dates_sens = {}
      liste_noms_ST = []
      dico_name_ST_sens = {}
      for sensor in list_sensor:
         pathST = sensor.serieTempGap.split("/")
       
         liste_noms_ST.append(sensor.serieTempGap)
         dico_name_ST_sens[sensor.name] = pathST[-1].split('.')
         liste_dates_sensor = []
         fdate = open(sensor.fdates)
         for line in fdate:
            allDates.append(int(line))
            liste_dates_sensor.append(int(line))
            dico_dates_sens[sensor.name]=liste_dates_sensor
          
      allDates.sort()
      print "Avant split",liste_noms_ST
      for serieTemp in liste_noms_ST:
         split = "otbcli_SplitImage -in "+serieTemp+" -out "+serieTemp+" "+pixelo
         os.system(split)                   
      #TODO : fait n'importe quoi
      ch = ""
      for date in allDates:
         for sensor in list_sensor:
            if date in dico_dates_sens[sensor.name]:
               dlist = dico_dates_sens[sensor.name]
               im = dico_name_ST_sens[sensor.name][0]
               nbbands = sensor.nbBands
                 
            i = dlist.index(date)
            for b in range(i*nbbands, (i*nbbands)+nbbands):
               ch = ch+opath.opathF+"/"+im+"_"+str(b)+".tif"+" "
               fSL.write(str(date))
               fSL.write('\n') 

      fSL.close() 
      Concatenate = "otbcli_ConcatenateImages -il "+ch+" -out "+opath.opathF+"/SL_MultiTempGapF.tif "+pixelo
      print Concatenate
      os.system(Concatenate)
   return opath.opathF+"/SL_MultiTempGapF.tif"


   ## #Only SPOT bands
   ## fS = open(opath.opathF+"/SL_MultiTempGapF_4bpi_DateList.txt", "w")

   ## chSbands = ""
   ## for date in allDates:
   ##    if date in dateS:
   ##       dlist = dateS
   ##       j = dlist.index(date)
   ##       im = nameS[0]
   ##       nbbands = Sbands
   ##       imin = j*nbbands
   ##       imax = (j*nbbands)+nbbands
   ##    elif date in dateL:
   ##       dlist = dateL
   ##       j = dlist.index(date)
   ##       #print j
   ##       im = nameL[0]
   ##       nbbands = Lbands
   ##       imin = (j*nbbands)+2
   ##       imax = ((j*nbbands)+nbbands)-1
       
   ##    for b in range(imin, imax):
   ##       chSbands = chSbands+opathF+"/"+im+"_"+str(b)+".tif"+" "
   ##    fS.write(str(date))
   ##    fS.write('\n')
   ## fSL.close()  
   ## print chSbands
   ## ConcatenateSbands = "otbcli_ConcatenateImages -il "+chSbands+" -out "+opathF+"/SL_MultiTempGapF_4bpi.tif "+pixelo
   ## os.system(ConcatenateSbands)
   ## print ConcatenateSbands  

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
