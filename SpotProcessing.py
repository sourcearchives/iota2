#!/usr/bin/python

import os
import glob
from sys import argv
import SpotData as SD
import DataProcessing as DP
import gdal
import numpy
import Dico as dico

maskC = dico.maskC
maskCshp = dico.maskCshp
Sbands = dico.Sbands
Lbands = dico.Lbands
pixelo = dico.pixelotb
pixelg = dico.pixelgdal

def createSerieSpot(ipath, opath):
   """
   Concatenation of all the images SPOT to create one multitemporal multibands image
   ARGs 
       INPUT:
             -ipath: absolute path of the images
             -opath: path were the images will be concatenated
       OUTPUT:
             -Multitemporal, multiband serie   
   """
   imlist = SD.getSpotImages(ipath, opath)
   
   ilist = ""
   bandlist = []
   bandinlist = []
   bandclipped = []

   for image in imlist:
      ilist = ilist + image + " "
      

   for image in imlist:
      impath = image.split('/')
      imname = impath[-1].split('.')
      splitS = "otbcli_SplitImage -in "+image+" -out "+opath+"/"+impath[-1]
      print splitS
      os.system(splitS)
      for band in range(0, int(Sbands)):
         bnamein = imname[0]+"_"+str(band)+".TIF"
         bnameout = imname[0]+"_"+str(band)+"_masked.tif"
         #maskB = "otbcli_BandMath -il "+opath+"/"+maskC+" "+opath+"/"+bnamein+" -exp \"im1b1*im2b1\" -out "+bnameout
         #os.system(maskB)
         maskB = "otbcli_BandMath -il "+opath+"/"+maskC+" "+opath+"/"+bnamein+" -exp \"if(im1b1==0,-10000,im2b1)\" -out "+bnameout
         print maskB
         os.system(maskB)
         bandclipped.append(DP.ClipRasterToShp(bnameout, opath+"/"+maskCshp, opath))
         #print maskB
         bandinlist.append(opath+"/"+bnamein)
         bandlist.append(opath+"/"+bnameout)
         
   bandChain = " "

   for bandclip in bandclipped:
      bandChain = bandChain + bandclip + " "
        
   Concatenate = "otbcli_ConcatenateImages -il "+bandChain+" -out "+opath+"/SPOT_MultiTempIm_clip.tif "
   print Concatenate
   print Concatenate
   os.system(Concatenate)

   #print bandlist
   #print bandinlist
   #print bandclipped

   #for image in bandlist:
      #os.remove(image)
   #for image in bandinlist:
      #os.remove(image)
   #for image in bandclipped:
      #os.remove(i)

  
   return 0

#--------------------------------------------------------------------------

def CreateBorderMaskSpot(ipath, opath):
   
   imlist = SD.getSpotImages(ipath, opath)
   mlist = SD.getList_SpotNoDataMask(imlist)

   listMaskch = ""
   listMask = []
   propBorder = []

   for i in range(len(mlist)):
        name = mlist[i].split("/")
	command = "otbcli_BandMath -il "+mlist[i]\
        +" -out "+opath+"/"+name[-1]+" -exp "\
        +"\"if(im1b1,1,0)\""
        os.system(command)
        print (command)
        listMaskch = listMaskch+opath+"/"+name[-1]+" "
        listMask.append(opath+"/"+name[-1]) 

   expr = "0"
   for i in range(len(listMask)):
      expr += "+im"+str(i+1)+"b1"

   BuildMaskSum = "otbcli_BandMath -il "+listMaskch+" -out "+opath+"/SumMaskS.tif -exp "+expr
   print BuildMaskSum
   os.system(BuildMaskSum)

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
  
   #Builds the mask
   expr = "\"if(im1b1>=8,1,0)\""
   #expr = "\"if(im1b1>="+str(usebands)+",1,0)\""
   BuildMaskBin = "otbcli_BandMath -il "+opath+"/SumMaskS.tif -out "+opath+"/MaskS.tif -exp "+expr
   print BuildMaskBin
   os.system(BuildMaskBin)

   for mask in listMask:
      os.remove(mask)

   return 0

#-----------------------------------------------------------------------------    
def CreateMaskSeriesSpot(ipath, opath):
   """
   Builds one multitemporal binary mask of SPOT images

   ARGs 
       INPUT:
             -ipath: absolute path of the images
             -opath: path were the multitemporal mask will be created
       OUTPUT:
             -Multitemporal binary mask .tif
   """


   imlist = SD.getSpotImages(ipath, opath)
   clist = SD.getList_SpotCloudMask(imlist)
   slist = SD.getList_SpotSatMask(imlist)
   dlist = SD.getList_SpotNoDataMask(imlist)
   maskC = opath+"/MaskCommunSL.tif"
   
  
   chain = ""
   bandChain = ""
   listallNames = []  
   bandclipped = []

   for im in range(0,len(imlist)):
      impath = imlist[im].split('/')
      imname = impath[-1].split('.')
      name = opath+'/'+imname[0]+'_MASK.tif'
      chain = clist[im]+' '+slist[im]+' '+dlist[im]
      #The following expression is for cloud, saturation and border masks
      Binary = "otbcli_BandMath -il "+maskC+" "+chain\
      +" -exp \"(im1b1 * (if(im2b1>0,1,0) or if(im3b1>0,1,0))) or (if(im4b1,0,1)*im1b1)\" -out "+name
      print Binary
      os.system(Binary)
      bandclipped.append(DP.ClipRasterToShp(name, opath+"/"+maskCshp, opath))
      listallNames.append(name)
   
   for bandclip in bandclipped:
      bandChain = bandChain + bandclip + " "
   
   Concatenate = "otbcli_ConcatenateImages -il "+bandChain+" -out "+opath+"/SPOT_MultiTempMask_clip.tif "
   os.system(Concatenate)

   for i in listallNames:
      os.remove(i)
   
   for i in bandclipped:
      os.remove(i)
   
   return 0

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


