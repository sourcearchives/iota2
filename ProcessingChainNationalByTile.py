#!/usr/bin/python

import os
import glob
from sys import argv
import LandsatDataN as LD
import numpy
import Dico as dico
#import ClassificationN as CL
import RandomSelectionInsituN as RSi
import ClassificationN as CL
import time
import ConfigClassifN as Config
import string
import BufferOgr as bogr
import functions_irregular as fi
import sys

if(len(argv)< 6):
   print "[ ERROR ] you must supply: <IPATH(where original images are)> <OUTPATH> <SHAPEFILE> <PERCENTAGE> <TILE_LIST>"
   sys.exit( 1 )
else:
   ipath = argv[1]
   opath = argv[2]
   percentage = float(argv[4])
   vectorFile = argv[3]
   tileList = [t for t in argv[5:]]
   per = str(percentage)
   newper = string.replace(per,'.','p')

flist = []
llist = []
args = Config.dicRF()
Lbands = dico.Lbands

#python ProcessingChainNationalByTile.py /ptmp//inglada/tuiles/ /ptmp//inglada/tmp/ /ptmp//inglada/tuiles/in-situ/FR_SUD_2013_LC_SM_V2.shp 10 Landsat8_D0004H0002 Landsat8_D0004H0003
print "Tile list: ", tileList


#---------------------------------------------One model per tile----------------------------------------------------


#************Prepare the mask series and the image series****************
for tile in tileList:
   if not os.path.exists(opath+"/"+tile):
      os.mkdir(opath+"/"+tile)
   print tile

   start_time = time.time()
   opathT = opath+"/"+tile+"/tmp"
   opathF =opath+"/"+tile+"/Final"
   opathIS = opath+"/"+tile+"/in-situ_"+str(newper)
   opathCL = opath+"/"+tile+"/Final/Images_"+str(newper)
   folders = [opathT, opathF, opathIS, opathCL, opathIS]

   for f in folders:
      if not os.path.exists(f):
         os.mkdir(f)      

   LD.CreateDir(opath, tile)
   #Pre-processing of images

   LD.getLandsatImages(ipath, opathF, tile)
   LD.CreateBorderMaskLandsat(ipath, tile, opathT)
   imserie = LD.createSerieLandsat(ipath, opathT, tile)
   mserie = LD.CreateMaskSeriesLandsat(ipath, opathT, tile)


#************Prepare the mask series and the image series****************
#WARNING: The next file is created with createFileResampledDates.py using the file of dates of each tile produced before during the preparation of the data.
fileRes = "TemRes_20130419-20131205-16days.txt"
#os.system("python ~/ProcessingChainS5T5-L8/createFileResampledDates.py "+opath+" "+opath+" 16")

#************Cut the in-situ data within tile****************

for tile in tileList:
   # WARNING: Temporal so tests can be done
   opathIM = "/mnt/MD1200/DONNEES/S2_AGRI/GAPFILLING/FranceSudOuest"
   opathIMT = opathIM+"/"+tile+"/tmp/"
   opathT = opath+"/"+tile+"/tmp"
   #bogr.buffer(opathIMT+"/MaskL30m.shp", opathIMT+"/MaskL30m_buffer.shp",-10000)
   cutFile = opathIMT+"/MaskL30m_buffer.shp"
   fi.ClipVectorData(vectorFile, cutFile, opathT)

#************Resample the image time series and compute the classification model****************
for tile in tileList:
   opathT = opath+"/"+tile+"/tmp"
   opathF =opath+"/"+tile+"/Final"
   opathIS = opath+"/"+tile+"/in-situ_"+str(newper)
   opathCL = opath+"/"+tile+"/Final/Images_"+str(newper)
   imserie = opath+"/"+tile+"/tmp/LANDSAT_MultiTempIm_clip.tif"
   mserie = opath+"/"+tile+"/tmp/LANDSAT_MultiTempMask_clip.tif"

   LD.TempRes(imserie, mserie, opathF+"/LANDSAT8_"+tile+"_TempRes.tif", Lbands, 0, opathF+"/LANDSATimagesDateList_"+tile+".txt", fileRes)
   LD.FeatExtLandsat(opathF+"/LANDSAT8_"+tile+"_TempRes.tif", fileRes, opathT, opathF)
   LD.ConcatenateFeatures(opathT, opathF)
   LD.ConcatenateAllData(opathF, opathF+"/LANDSAT8_"+tile+"_TempRes.tif "+opathF+"/NDVI.tif "+opathF+"/NDWI.tif "+opathF+"/Brightness.tif")

   opathIM = "/mnt/MD1200/DONNEES/S2_AGRI/GAPFILLING/FranceSudOuest"
   opathIMT = opathIM+"/"+tile+"/tmp/"
   #image = opathT+"/MaskL30m.tif"
   #CL.BuildCropMask(samplesFile, image, opathT) #S2-Agri
   #mask = opathT+"/CropMask.tif" #S2-Agri
   opathIMT = opathIM+"/"+tile+"/tmp/"
   mask = opathIMT+"/MaskL30m.tif"
   #mask = opathT+"/MaskL30m.tif"

#*****************IN-SITU DATA PROCESSING****************
   #Select crop samples
   #samplesFile = CL.GetCropSamples(vectorFile, opathT) #S2-Agri
   samplesFile = opathT+"/"+vectorFile.split('/')[-1]
   #Select a percentage of the samples

   print samplesFile
   samplesSelFile = RSi.shpPercentageSelection(samplesFile, 'CODE', percentage, opathT,0)

   #Random draws using the percentage samples file
   samplesSelFile = opathT+"/"+vectorFile.split('.')[0].split('/')[-1]+"-"+str(newper)+"perc.shp"
   print samplesSelFile

   RSi.RandomInSitu(samplesSelFile, 'CODE', 5, opathIS, 0)

   learnsamples = CL.getListLearnsamples(samplesSelFile, opathIS)
   valsamples = CL.getListValsamples(samplesSelFile, opathIS)

#*****************CLASSIFICATION PROCESSING****************
   opathIMF = "/mnt/MD1200/DONNEES/S2_AGRI/GAPFILLING/FranceSudOuest/"+tile+"/Final/"

   for samples in learnsamples:
      # WARNING: Temporal so tests can be done
      #CL.RFClassif(newper, samples, opathF, opathT, opathF, opathF+"/LANDSAT8_"+tile+"_TempRes.tif "+opathF+"/NDVI.tif "+opathF+"/NDWI.tif "+opathF+"/Brightness.tif") # Original
      CL.RFClassif(newper, samples, opathF, opathT, opathIMF, opathIMF+"/LANDSAT8_"+tile+"_TempRes.tif "+opathIMF+"/NDVI.tif "+opathIMF+"/NDWI.tif "+opathIMF+"/Brightness.tif") # Tests cand be done

   listModel = CL.getListModel(opathF+"/RF_"+str(newper))
   
   for model in listModel:
      #Original
      #classification = CL.imageClassification(model, opathF+"/LANDSAT8_"+tile+"_TempRes_NDVI_NDWI_Brightness_.tif", opathCL, mask) #
      classification = CL.imageClassification(model, opathIMF+"/LANDSAT8_"+tile+"_TempRes_NDVI_NDWI_Brightness_.tif", opathCL, mask)
      refdata = CL.getValsamples(classification, valsamples)
      CL.ConfMatrix(classification, refdata, opathCL)

   confMList = CL.getListConfMat(opathCL, "RF", "bm0")
   #CL.ComputeMetrics(opathCL, opathCL, confMList)



