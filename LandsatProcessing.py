#!/usr/bin/python

import os
import glob
from sys import argv
import LandsatData as LD
import DataProcessing as DP
from osgeo import gdal, ogr, osr
from osgeo.gdalconst import GA_ReadOnly
import Dico as dico

maskC = dico.maskC
#maskC = dico.maskR
maskL = dico.maskL
maskCshp = dico.maskCshp
maskLshp = dico.maskLshp
#maskCshp = dico.maskRLshp
Lbands = dico.Lbands
bandsL = dico.bandLandsat()
pixelo = dico.pixelotb
pixelg = dico.pixelgdal
res = str(dico.res)
pathAppGap = "/mnt/data/home/ingladaj/Dev/builds/TemporalGapfilling/applications/"


def CreateBorderMaskLandsat(ipath, tile, opath, imref):
   """
   Creates the mask of borders 
   ARGs 
       INPUT:
             -ipath: absolute path of the LANDSAT images
             -opath: path were the mask will be created
       OUTPUT:
             -Border mask 30 m
   """
   
   imlist = LD.getLandsatImages(ipath, opath, tile)
   mlist = LD.getList_LandsatNoDataMask(imlist)
   print imlist
   print mlist
   #Get the info of the image

   ds = gdal.Open(imref, GA_ReadOnly)
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
   
   chain_proj = srs.GetAuthorityName('PROJCS')+':'+srs.GetAuthorityCode('PROJCS')
   #chain_proj = "EPSG:2154"

   resolX = abs(gt[1]) # resolution en metres de l'image d'arrivee 
   resolY = abs(gt[5]) # resolution en metres de l'image d'arrivee
   chain_extend = str(ulx)+' '+str(lry)+' '+str(lrx)+' '+str(uly)  

   #Builds the individual binary masks
   listMaskch = ""
   listMask = []
   for i in range(len(mlist)):
        name = mlist[i].split("/")
        #os.system("otbcli_BandMath -il "+mlist[i]\
        #+" -out "+opath+"/"+name[-1]+" -exp "\
	#+"\"if(im1b1,1,0)\"")
	#OTB 5.0
        os.system("otbcli_BandMath -il "+mlist[i]\
        +" -out "+opath+"/"+name[-1]+" -exp "\
	+"\"(im1b1?1:0)\"")
        listMaskch = listMaskch+opath+"/"+name[-1]+" "
        listMask.append(opath+"/"+name[-1])
  
   #Builds the complete binary mask
   expr = "0"
   for i in range(len(listMask)):
      expr += "+im"+str(i+1)+"b1"

   BuildMaskSum = "otbcli_BandMath -il "+listMaskch+" -out "+opath+"/SumMaskL30m.tif -exp "+expr
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
   #expr = "\"if(im1b1>=16,1,0)\""
   #expr = "\"if(im1b1>="+str(usebands)+",1,0)\""
   #Builds the mask
   #expr = "\"if(im1b1>=6,1,0)\""
   #expr = "\"if(im1b1>="+str(usebands)+",1,0)\""
   #OTB 5.0
   expr = "\"(im1b1>="+str(usebands)+"?1:0)\""
   BuildMaskBin = "otbcli_BandMath -il "+opath+"/SumMaskL30m.tif -out "+opath+"/MaskL30m.tif -exp "+expr
   print BuildMaskBin
   os.system(BuildMaskBin)

   ResizeMaskBin = 'gdalwarp -of GTiff -r %s -tr %d %d -te %s -t_srs %s %s %s \n'% ('near', resolX,resolY,chain_extend,chain_proj, opath+"/MaskL30m.tif", opath+"/MaskL"+res+"m.tif")
   os.system(ResizeMaskBin)
   #for mask in listMask:
      #os.remove(mask)


#-------------------------------------------------------------

def ResizeLandsatImages(ipath, opath, imref, tile):
   """
   Resizes LANDSAT images using one spot image
   ARGs 
       INPUT:
             -ipath: absolute path of the LANDSAT images
             -opath: path were the mask will be created
             -imref: SPOT Image to use for resizing
       OUTPUT:
             - A text file containing the list of LANDSAT images resized
   """
   imlist = LD.getLandsatImages(ipath, opath, tile)
  
   fileim = open(opath+"/LANDSATimagesListResize.txt", "w")
   imlistout = []
   
   ds = gdal.Open(imref, GA_ReadOnly)
   nb_col=ds.RasterXSize
   nb_lig=ds.RasterYSize
   proj=ds.GetProjection()
   gt=ds.GetGeoTransform()
   ulx = gt[0]
   uly = gt[3]
   lrx = gt[0] + nb_col*gt[1] + nb_lig*gt[2]
   lry = gt[3] + nb_col*gt[4] + nb_lig*gt[5]

   srs=osr.SpatialReference(proj)

   chain_proj = srs.GetAuthorityName('PROJCS')+':'+srs.GetAuthorityCode('PROJCS')
   #chain_proj = "EPSG:2154"
   
   resolX = abs(gt[1]) # resolution en metres de l'image d'arrivee 
   resolY = abs(gt[5]) # resolution en metres de l'image d'arrivee
   chain_extend = str(ulx)+' '+str(lry)+' '+str(lrx)+' '+str(uly)   
 
   for image in imlist:
      line = image.split('/')
      name = line[-1].split('.')
      newname = '_'.join(name[0:-1])
      imout = opath+"/"+newname+"_"+res+"m.TIF"
      #Resize = "otbcli_Superimpose -inr "+imref+" -inm "+image+" -out "+opath+"/"+newname+"_20m.tif"
      Resize = 'gdalwarp -of GTiff -r %s -tr %d %d -te %s -t_srs %s %s %s \n'% ('cubic', resolX,resolY,chain_extend,chain_proj, image, imout)
      print Resize
      os.system(Resize)
      
      fileim.write(imout)
      imlistout.append(imout)
      fileim.write("\n")
   
      
   fileim.close()

        
#--------------------------------------------------------------
def ResizeLandsatMasks(ipath, opath, imref, tile):
   """
   Resizes LANDSAT masks using one spot image
   ARGs 
       INPUT:
             -ipath: absolute path of the LANDSAT images
             -opath: path were the mask will be created
             -imref: SPOT Image to use for resizing
       OUTPUT:
             - A text file containing the list of LANDSAT images resized
   """
   imlist = LD.getLandsatImages(ipath, opath, tile)
   cmask = LD.getList_LandsatCloudMask(imlist)
   smask = LD.getList_LandsatSatMask(imlist)
   dmask = LD.getList_LandsatDivMask(imlist)
   dmask = LD.getList_LandsatNoDataMask(imlist)
   
   allmlists = [cmask, smask, dmask]
   #expMask = {"NUA":"if(im1b1 and 01000000,1,if(im1b1 and 00000010,1,0))", "SAT":"im1b1!=0", "DIV":"if(im1b1 and 00000001,1,0)"}
   #expMask = {"NUA":"if(im1b1 and 00000001,1,if(im1b1 and 00001000,1,0))", "SAT":"im1b1!=0", "DIV":"if(im1b1 and 00000001,1,0)", "NODATA":"if(im1b1,1,0)"}
   #otb 4.3
   #expMask = {"NUA":"if(im1b1 and 00000001,1,if(im1b1 and 00001000,1,0))", "SAT":"im1b1!=0", "NODATA":"if(im1b1,1,0)"}
   #otb 5.0
   expMask = {"NUA":"(im1b1 and 00000001?1:(im1b1 and 00001000?1:0))", "SAT":"im1b1!=0", "NODATA":"(im1b1?1:0)"}
   ds = gdal.Open(imref, GA_ReadOnly)
   nb_col=ds.RasterXSize
   nb_lig=ds.RasterYSize
   proj=ds.GetProjection()
   gt=ds.GetGeoTransform()
   ulx = gt[0]
   uly = gt[3]
   lrx = gt[0] + nb_col*gt[1] + nb_lig*gt[2]
   lry = gt[3] + nb_col*gt[4] + nb_lig*gt[5]

   srs=osr.SpatialReference(proj)
   
   #chain_proj = "EPSG:2154"
   chain_proj = srs.GetAuthorityName('PROJCS')+':'+srs.GetAuthorityCode('PROJCS')

   resolX = abs(gt[1]) # resolution en metres de l'image d'arrivee 
   resolY = abs(gt[5]) # resolution en metres de l'image d'arrivee
   chain_extend = str(ulx)+' '+str(lry)+' '+str(lrx)+' '+str(uly) 

   for mlist in allmlists:
      for mask in mlist:
         line = mask.split('/')
         name = line[-1].split('.')
         typeMask = name[0].split('_')[-1]
         namep = name[-2]+"bordbin"
         namer = name[-2]+res+"m"
         newnameb = namep+'.'+name[-1]
         newnamer = namer+'.'+name[-1]
         imout = opath+"/"+newnameb
         imoutr = opath+"/"+newnamer
         if typeMask == 'NUA':
	    exp = expMask['NUA']
         elif typeMask == 'SAT':
   	    exp = expMask['SAT']
         elif typeMask == 'DIV':
   	    exp = expMask['DIV']
         elif typeMask == 'NODATA':
   	    exp = expMask['NODATA']
         binary = "otbcli_BandMath -il "+mask+" -exp \""+exp+"\" -out "+imout
         print binary
         os.system(binary)
         Resize = 'gdalwarp -of GTiff -r %s -tr %d %d -te %s -t_srs %s %s %s \n'% ('near', resolX,resolY,chain_extend,chain_proj, imout, imoutr)
         print Resize
         os.system(Resize)

#-----------------------------------------------------------------

def CreateMaskSeriesLandsat(ipath, opath):
   """
   Builds one multitemporal binary mask of SPOT images

   ARGs 
       INPUT:
             -ipath: absolute path of the resized masks
             -opath: path were the multitemporal mask will be created
       OUTPUT:
             -Multitemporal binary mask .tif
   """
   imlist = LD.getResizedLandsatImages(ipath, opath)
   imlist.sort()
   clist = LD.getList_LandsatResCloudMask(imlist)
   slist = LD.getList_LandsatResSatMask(imlist)
   #dlist = LD.getList_LandsatResDivMask(imlist)
   dlist = LD.getList_LandsatResNoDataMask(imlist)
   maskC = opath+"/MaskCommunSL.tif"
   chain = ""
   allNames = ""
   listallNames = []
   bandclipped = []
   bandChain = ""

   for im in range(0,len(imlist)):
      impath = imlist[im].split('/')
      imname = impath[-1].split('.')
      name = opath+'/'+imname[0]+'_MASK.TIF'
      chain = clist[im]+' '+slist[im]+' '+dlist[im]
      #IF NODATA MASK
      #otb 4.3
      #Binary = "otbcli_BandMath -il "+maskC+" "+chain+" -exp \"(im1b1 * (if(im2b1>0,1,0) or if(im3b1>0,1,0) or if(im4b1==0,1,0)))\" -out "+name
      #otb 5.0
      Binary = "otbcli_BandMath -il "+maskC+" "+chain+" -exp \"(im1b1 * ((im2b1>0?1:0) or (im3b1>0?1:0) or (im4b1==0?1:0)))\" -out "+name

      #IF DIV MASK
      #otb 4.3
      #Binary = "otbcli_BandMath -il "+maskC+" "+chain+" -exp \"(im1b1 * (if(im2b1>0,1,0) or if(im3b1>0,1,0) or if(im4b1>0,1,0)))\" -out "+name
      #otb 5.0
      #Binary = "otbcli_BandMath -il "+maskC+" "+chain+" -exp \"(im1b1 * ((im2b1>0?1:0) or (im3b1>0?1:0) or (im4b1>0?1:0)))\" -out "+name

      print Binary
      os.system(Binary)
      bandclipped.append(DP.ClipRasterToShp(name, opath+"/"+maskCshp, opath))
      listallNames.append(name)

   for bandclip in bandclipped:
      bandChain = bandChain + bandclip + " "

   Concatenate = "otbcli_ConcatenateImages -il "+bandChain+" -out "+opath+"/LANDSAT_r_MultiTempMask_clip.tif "+pixelo
   print Concatenate
   os.system(Concatenate)


   return 0 

#------------------------------------------------------------------
def createSerieLandsat(ipath, opath):
   """
   Concatenation of all the images Landsat to create one multitemporal multibands image
   ARGs 
       INPUT:
             -ipath: absolute path of the images
             -opath: path were the images will be concatenated
       OUTPUT:
             -Multitemporal, multiband serie   
   """
   imlist = LD.getResizedLandsatImages(ipath, opath)
   imlist.sort()
   ilist = ""
   olist = []
   bandlist = []
   bandclipped = []

   for image in imlist:
      ilist = ilist + image + " "
      olist.append(image)

   for image in imlist:
      impath = image.split('/')
      imname = impath[-1].split('.')
      splitS = "otbcli_SplitImage -in "+image+" -out "+opath+"/"+impath[-1]
      print splitS
      os.system(splitS)
      for band in range(0, int(Lbands)):
         bnamein = imname[0]+"_"+str(band)+".TIF"
         bnameout = imname[0]+"_"+str(band)+"_masked.TIF"
         #maskB = "otbcli_BandMath -il "+opath+"/"+maskC+" "+opath+"/"+bnamein+" -exp \"if(im1b1==0,-10000, if(im2b1!=-10000 and im2b1<0,0,im2b1))\" -out "+opath+"/"+bnameout
         #otb 5.0
         maskB = "otbcli_BandMath -il "+opath+"/"+maskC+" "+opath+"/"+bnamein+" -exp \"(im1b1==0?-10000: (im2b1!=-10000 and im2b1<0?0:im2b1))\" -out "+opath+"/"+bnameout

         print maskB
         os.system(maskB)
         bandclipped.append(DP.ClipRasterToShp(opath+"/"+bnameout, opath+"/"+maskCshp, opath))
         print maskB
         bandlist.append(opath+"/"+bnameout)
 
   bandChain = " "

   for bandclip in bandclipped:
      bandChain = bandChain + bandclip + " "

   Concatenate = "otbcli_ConcatenateImages -il "+bandChain+" -out "+opath+"/LANDSAT_r_MultiTempIm_clip.tif "
   print Concatenate
   os.system(Concatenate)

   outname = "LANDSAT_r_MultiTempIm4bpi_clip.tif"
   chain = ""
   bands = [bandsL["green"], bandsL["red"], bandsL["NIR"], bandsL["SWIR1"]]
   #bands = [bandsL["blue"], bandsL["green"], bandsL["red"], bandsL["NIR"]]
   for image in imlist:
      for band in bands:
         name = image.split('.')
         newname = name[0]+'_'+str(band-1)+'_masked_clipped.TIF'
         chain = chain + newname +" "
   #print chain
   Concatenate = "otbcli_ConcatenateImages -il "+chain+" -out "+opath+"/"+outname
   print Concatenate
   os.system(Concatenate)

   #for image in bandlist:
      #os.remove(image)

   #for image in bandclipped:
      #os.remove(image)
 
   return 0


#-----------------------------------------------------------------     
def refl_LandsatSpot(ipath, opath, typeImage):

   if typeImage == "resized":
      imlist = LD.getResizedLandsatImages(ipath, opath)
      outname = "LANDSAT_r_MultiTempIm4bpi_clip.tif"
   elif typeImage == "normal":
      imlist = LD.getLandsatImages(ipath, opath, "*30m.tif")
      outname = "LANDSAT_MultiTempIm4bpi_clip.tif"
   print outname
   
   bands = [bandsL["green"], bandsL["red"], bandsL["NIR"], bandsL["SWIR1"]]
   chain = ""
   
   for image in imlist:
      for band in bands:
         name = image.split('.')
         newname = name[0]+'_'+str(band-1)+'_masked_clipped.tif'
         chain = chain + newname +" "
   print chain
   Concatenate = "otbcli_ConcatenateImages -il "+chain+" -out "+opath+"/"+outname
   os.system(Concatenate)


#----------------------------------------------------------------
def CreateBorderMaskLandsat30m(ipath, opath):
   """
   Creates the mask of borders and resize it to fit with SPOT
   ARGs 
       INPUT:
             -ipath: absolute path of the LANDSAT images
             -opath: path were the mask will be created
             -imref: SPOT Image to use for resizing
       OUTPUT:
             -Border mask 30 m
             -Border mask 20 m   
   """
   
   imlist = LD.getLandsatImages(ipath, opath, "*_30m.tif")
   mlist = LD.getList_LandsatDivMask(imlist)
   #Get the info of the image

   #Builds the individual binary masks
   listMaskch = ""
   listMask = []
   for i in range(len(mlist)):
        name = mlist[i].split("/")
        #os.system("otbcli_BandMath -il "+mlist[i]\
        #+" -out "+opath+"/"+name[-1]+" -exp "\
        #+"\"if(im1b1 and 00000001,0,1)\"")
        #otb 5.0
        os.system("otbcli_BandMath -il "+mlist[i]\
        +" -out "+opath+"/"+name[-1]+" -exp "\
        +"\"(im1b1 and 00000001?0:1)\"")
        listMaskch = listMaskch+opath+"/"+name[-1]+" "
        listMask.append(opath+"/"+name[-1])

   #Builds the complete binary mask
   expr = "0"
   for i in range(len(listMask)):
      expr += "+im"+str(i+1)+"b1"

   BuildMaskSum = "otbcli_BandMath -il "+listMaskch+" -out "+opath+"/SumMaskL30m.tif -exp "+expr
   os.system(BuildMaskSum)
   #expr = "\"if(im1b1<"+str(len(listMask))+",0,1)\""
   #otb 5.0
   expr = "\"(im1b1<"+str(len(listMask))+"?0:1)\""
   BuildMaskBin = "otbcli_BandMath -il "+opath+"/SumMaskL30m.tif -out "+opath+"/MaskL30m.tif -exp "+expr
   os.system(BuildMaskBin)
 
   #for mask in listMask:
      #os.remove(mask)

#----------------------------------------------------------------
def CreateMaskSeriesLandsat30m(ipath, opath):
   """
   Builds one multitemporal binary mask of SPOT images

   ARGs 
       INPUT:
             -ipath: absolute path of the masks
             -opath: path were the multitemporal mask will be created
       OUTPUT:
             -Multitemporal binary mask .tif
   """
   imlist = LD.getLandsatImages(ipath, opath, "*_30m.tif")
   clist = LD.getList_LandsatCloudMask(imlist)
   slist = LD.getList_LandsatSatMask(imlist)
   dlist = LD.getList_LandsatDivMask(imlist)
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
      #Binary = "otbcli_BandMath -il "+maskC+" "+chain+" -exp \"(im1b1 * (if(im2b1>0,1,0) or if(im3b1>0,1,0))) or ((im4b1 and 00000001)*im1b1)\" -out "+name
      #otb 5.0
      Binary = "otbcli_BandMath -il "+maskC+" "+chain+" -exp \"(im1b1 * ((im2b1>0?1:0) or (im3b1>0?1:0))) or ((im4b1 and 00000001)*im1b1)\" -out "+name
      #print Binary
      os.system(Binary)
      bandclipped.append(DP.ClipRasterToShp(name, opath+"/"+maskLshp, opath))
      listallNames.append(name)

   for bandclip in bandclipped:
      bandChain = bandChain + bandclip + " "

   Concatenate = "otbcli_ConcatenateImages -il "+bandChain+" -out "+opath+"/LANDSAT_MultiTempMask_clip.tif "
   os.system(Concatenate)

   #for image in listallNames:
      #os.remove(image)

   #for image in bandclipped:
      #os.remove(image)


   return 0 

#--------------------------------------------------------------------------------
def createSerieLandsat30m(ipath, opath):
   """
   Concatenation of all the images Landsat to create one multitemporal multibands image
   ARGs 
       INPUT:
             -ipath: absolute path of the images
             -opath: path were the images will be concatenated
       OUTPUT:
             -Multitemporal, multiband serie   
   """
   imlist = LD.getLandsatImages(ipath, opath, "*_30m.tif")
   ilist = ""
   olist = []
   bandlist = []
   bandclipped = []

   for image in imlist:
      ilist = ilist + image + " "
      olist.append(image)

   for image in imlist:
      impath = image.split('/')
      imname = impath[-1].split('.')
      splitS = "otbcli_SplitImage -in "+image+" -out "+opath+"/"+impath[-1]
      #print splitS
      os.system(splitS)
      for band in range(0, int(Lbands)):
         bnamein = imname[0]+"_"+str(band)+".tif"
         bnameout = imname[0]+"_"+str(band)+"_masked.tif"
         #maskB = "otbcli_BandMath -il "+opath+"/"+maskL+" "+opath+"/"+bnamein+" -exp \"if(im1b1==0,-10000, if(im2b1!=-10000 and im2b1<0,0,im2b1))\" -out "+opath+"/"+bnameout
         #otb 5.0
         maskB = "otbcli_BandMath -il "+opath+"/"+maskL+" "+opath+"/"+bnamein+" -exp \"(im1b1==0?-10000: (im2b1!=-10000 and im2b1<0?0:im2b1))\" -out "+opath+"/"+bnameout
         os.system(maskB)
         bandclipped.append(DP.ClipRasterToShp(opath+"/"+bnameout, opath+"/"+maskLshp, opath))
         print maskB
         bandlist.append(opath+"/"+bnameout)
 
   bandChain = " "

   for bandclip in bandclipped:
      bandChain = bandChain + bandclip + " "


   Concatenate = "otbcli_ConcatenateImages -il "+bandChain+" -out "+opath+"/LANDSAT_MultiTempIm_clip.tif "
   os.system(Concatenate)

   #for image in bandlist:
      #os.remove(image)

   #for image in bandclipped:
      #os.remove(image)
 
   return 0

#-----------------------------------------------------------------------------
def CreateSerieLandsat4band(ipath, opath):
   imlist = LD.getResizedLandsatImages(ipath, opath)
   outname = "LANDSAT_r_MultiTempIm4bpi_clip.tif"
   chain = ""
   bands = [bandsL["green"], bandsL["red"], bandsL["NIR"], bandsL["SWIR1"]]
   for image in imlist:
      for band in bands:
         name = image.split('.')
         newname = name[0]+'_'+str(band-1)+'_masked_clipped.tif'
         chain = chain + newname +" "
   #print chain
   Concatenate = "otbcli_ConcatenateImages -il "+chain+" -out "+opath+"/"+outname
   #print Concatenate
   os.system(Concatenate)

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

