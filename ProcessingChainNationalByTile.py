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


ipath = argv[1]
opath = argv[2]
percentage = float(argv[3])
vectorFile = argv[4]
per = str(percentage)
newper = string.replace(per,'.','p')
flist = []
llist = []
args = Config.dicRF()
Lbands = dico.Lbands

#python ~/croptype_bench/ProcessingChainNationalByTile.py /mnt/MD1200/DONNEES/LANDSAT8/N2_THEIA/ /mnt/MD1200/DONNEES/S2_AGRI/GAPFILLING/FranceSudOuest/FranceAllClasses/TestCl/ 20 /mnt/MD1200/DONNEES/S2_AGRI/GAPFILLING/FranceSudOuest/FranceAllClasses/filesToTest/in-situ/FR_SUD_2013_LC_SM_V2.shp


#tileList =['Landsat8_D0003H0001','Landsat8_D0003H0002', 'Landsat8_D0003H0003', 'Landsat8_D0003H0004', 'Landsat8_D0003H0005','Landsat8_D0004H0001','Landsat8_D0004H0002','Landsat8_D0004H0003', 'Landsat8_D0004H0004', 'Landsat8_D0004H0005', 'Landsat8_D0005H0001', 'Landsat8_D0005H0002', 'Landsat8_D0005H0003', 'Landsat8_D0005H0004', 'Landsat8_D0005H0005', 'Landsat8_D0006H0001', 'Landsat8_D0006H0002', 'Landsat8_D0006H0003', 'Landsat8_D0006H0004', 'Landsat8_D0006H0005', 'Landsat8_D0007H0002', 'Landsat8_D0007H0003', 'Landsat8_D0007H0004', 'Landsat8_D0007H0005', 'Landsat8_D0008H0002', 'Landsat8_D0008H0003', 'Landsat8_D0008H0004']

tileList =['Landsat8_D0004H0002','Landsat8_D0004H0003']



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

#************Cut the in-situ data within tile****************

for tile in tileList:
   opathT = opath+"/"+tile+"/tmp/"
   bogr.buffer(opathT+"/MaskL30m.shp", opathT+"/MaskL30m_buffer.shp",-10000)
   cutFile = opathT+"/MaskL30m_buffer.shp"
   fi.ClipVectorData(vectorFile, cutFile, opathT)

#************Prepare the mask series and the image series****************
#WARNING: The next file is created with createFileResampledDates.py using the file of dates of each tile produced before during the preparation of the data.
fileRes = "~/croptype_bench/TemRes_20130419-20131205-16days.txt"
#os.system("python ~/croptypeNational/createFileResampledDates.py "+opath+" "+opath+" 16")


#************Resample the image time series****************
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
   #image = opathT+"/MaskL30m.tif"
   #CL.BuildCropMask(samplesFile, image, opathT) #S2-Agri
   #mask = opathT+"/CropMask.tif" #S2-Agri
   mask = opathT+"/MaskL30m.tif"

#*****************IN-SITU DATA PROCESSING****************
   #Select crop samples
   #samplesFile = CL.GetCropSamples(vectorFile, opathT) #S2-Agri
   samplesFile = opathT+"/"+vectorFile.split('/')[-1]
   #Select a percentage of the samples
   samplesSelFile = RSi.shpPercentageSelection(samplesFile, 'CODE', percentage, opathT,0)
   #Random draws using the percentage samples file
   RSi.RandomInSitu(samplesSelFile, 'CODE', 1, opathIS, 0)
   samplesSelFile = opathT+"/"+vectorFile.split('.')[0].split('/')[-1]+"-"+str(newper)+"perc.shp"
   learnsamples = CL.getListLearnsamples(samplesSelFile, opathIS)
   valsamples = CL.getListValsamples(samplesSelFile, opathIS)

#*****************CLASSIFICATION PROCESSING****************

   for samples in learnsamples:
      CL.RFClassif(newper, samples, opathF, opathT, opathF, opathF+"/LANDSAT8_"+tile+"_TempRes.tif "+opathF+"/NDVI.tif "+opathF+"/NDWI.tif "+opathF+"/Brightness.tif")

   listModel = CL.getListModel(opathF+"/RF_"+str(newper))
   
   for model in listModel:
      classification = CL.imageClassification(model, opathF+"/LANDSAT8_"+tile+"_TempRes_NDVI_NDWI_Brightness_.tif", opathCL, mask)
      refdata = CL.getValsamples(classification, valsamples)
      CL.ConfMatrix(classification, refdata, opathCL)

   confMList = CL.getListConfMat(opathCL, "RF", "bm0")
   #CL.ComputeMetrics(opathCL, opathCL, confMList)



