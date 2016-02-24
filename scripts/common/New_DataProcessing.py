
import Dico as dico
import os
from osgeo import ogr,osr,gdal
import glob
pathAppGap = dico.pathAppGap
res = str(dico.res)
pixelo = dico.pixelotb
pixelg = dico.pixelgdal
#indices = dico.indices
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


def Gapfilling(imageSeries, maskSeries, outputSeries, compPerDate, interpType, DatelistI, DatelistO,wOut):
   
   if (os.path.exists(imageSeries) and os.path.exists(maskSeries)):
      if wOut == None:
         command = pathAppGap+"gapfilling "+imageSeries+" "+maskSeries+" "+outputSeries+" "+str(compPerDate)+" "+str(interpType)+" "+DatelistI+" "+DatelistO
      else:
         command = "otbcli_ImageTimeSeriesGapFilling -in "+imageSeries+" -mask "+maskSeries+" -out "+outputSeries+" -comp "+str(compPerDate)+" -it linear -id "+DatelistI+" -od "+DatelistO
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
    indices = sensor.indices
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

	# Modifier les options
	if feature == "Haralick":
            for date in dlist:
                oname = feature+"_"+str(date)+"_"+name[0]+".tif"
                FeatureExt = "otbcli_HaralickTextureExtraction -in "+imSerie+" -out "+opath+"/"+feature+"/"+oname+" "+pixelo
                print FeatureExt
		os.system(FeatureExt)

	# Modifier les options
	if feature == "Statistics":
            for date in dlist:
                oname = feature+"_"+str(date)+"_"+name[0]+".tif"
                FeatureExt = "otbcli_LocalStatisticExtraction -in "+imSerie+" -out "+opath+"/"+feature+"/"+oname+" "+pixelo
		print FeatureExt
                os.system(FeatureExt)

    return 0
########################################################################################################################
def FileSearch_AND(PathToFolder,*names):

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
				out.append(path+"/"+files[i])
	return out
########################################################################################################################
def GetFeatList(feature, opath):
   """
   Gets the list of features in a directory, used for NDVI, NDWI, Brightness 
   ARGs:
       INPUT:
            -feature: the name of the feature            
   """
   imageList = []
   IMG = FileSearch_AND(opath+"/"+feature,feature,".tif")
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
      chaine_concat = " "
      for sensor in list_sensor:
         chaine_concat += sensor.serieTempGap
      command = "otbcli_ConcatenateImages -il "+chaine_concat+" -out "+opath.opathF+"/SL_MultiTempGapF.tif "+pixelo
      print command
      os.system(command)

   return opath.opathF+"/SL_MultiTempGapF.tif"



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