#!/usr/bin/python

import os
import glob
from sys import argv
import SpotData as SD
import SpotProcessing as SP
import LandsatData as LD
import LandsatProcessing as LP
import DataProcessing as DP
#import Gapfilling as GP
import ClassificationN as CL
#import TemporalResampling as TP
import Dico as dico
import RandomSelectionInsitu_LV as RSi
#import RandomSelectionInsituForFusion as RSiF
import time

ipathS = argv[1]
ipathL = argv[2]
opath = argv[3]
vectorFile = argv[4]
opathT = argv[3]+"/tmp"
opathF =argv[3]+"/Final"
opathCL = argv[3]+"/Final/Images"
opathIS = argv[3]+"/in-situ"
Sbands = dico.Sbands
Lbands = dico.Lbands
interp = dico.interp
classField = dico.ClassCol
delta = dico.delta
res = dico.res
tile = "D0001H0001"


#python ~/ProcessingChainS5T5-L8/ProcessingChain.py /mnt/MD1200/DONNEES/SPOT5TAKE5/N2A/AuchFranceD0000B0000/ /mnt/MD1200/DONNEES/S2_AGRI/GAPFILLING/France2015/LANDSAT8/ /mnt/MD1200/DONNEES/S2_AGRI/GAPFILLING/France2015/ /mnt/MD1200/DONNEES/S2_AGRI/GAPFILLING/France2015/FR_MIPY_LC_SM_2015.shp
"""
#Create all the needed directories
DP.CreateDir(opath)

#****************************************DATA PRE-PROCESSING*************************************************
#Create the list of the SPOT images by chronological order
SD.getSpotImages(ipathS, opathT)

#Return the first image of the list of SPOT images, used as reference to resample LANDSAT images
imSref = SD.getSpotImageRef(ipathS, opathT)

#Create the commun zone of the SPOT images (*)
SP.CreateBorderMaskSpot(ipathS, opathT)


#Create the list of the LANDSAT images by chronological order
LD.getLandsatImages(ipathL, opathF, tile)

#Create the commun zone of the LANDSAT images (*)
LP.CreateBorderMaskLandsat(ipathL, tile, opathT, imSref)

#Create the commun zone of the SPOT and LANDSAT images, produce a vector and a raster file
vectorMask = DP.CreateCommonZone(opathT)

#Create the mask image series of SPOT
SP.CreateMaskSeriesSpot(ipathS, opathT)

#Create the image series of SPOT using the commun mask computed before, split the original image, mask it and then concatenate
SP.createSerieSpot(ipathS, opathT)

#Computes the SPOT gapfilled image series
DP.Gapfilling(opathT+"/SPOT_MultiTempIm_clip.tif", opathT+"/SPOT_MultiTempMask_clip.tif", opathF+"/SPOT_MultiTemp_GapF_clip.tif", Sbands, interp, opathT+"/SPOTimagesDateList.txt")

#Corrige values
DP.CorrigeValues(opathF+"/SPOT_MultiTemp_GapF_clip.tif")

#Computes the NDVI, NDWI and Brightness of SPOT
DP.FeatExtSPOT(opathF+"/SPOT_MultiTemp_GapF_clip.tif", opathT+"/SPOTimagesDateList.txt", opathT)

#Resample the LANDSAT images using the SPOT reference image
LP.ResizeLandsatImages(ipathL, opathT, imSref, tile)

#Resample the LANDSAT masks using the SPOT reference image
LP.ResizeLandsatMasks(ipathL, opathT, imSref, tile)

#Create the resampled mask series of LANDSAT
LP.CreateMaskSeriesLandsat(opathT, opathT)

#Create the resampled image series of LANDSAT
LP.createSerieLandsat(opathT, opathT)

#Computes the LANDSAT gapfilled image series
DP.Gapfilling(opathT+"/LANDSAT_r_MultiTempIm_clip.tif", opathT+"/LANDSAT_r_MultiTempMask_clip.tif", opathF+"/LANDSAT_r_MultiTemp_GapF_clip.tif", Lbands, interp, opathT+"/LANDSATimagesDateList_"+tile+".txt")

#Corrige values
#DP.CorrigeValues(opathF+"/LANDSAT_r_MultiTemp_GapF_clip.tif")

#Computes the NDVI, NDWI and Brightness of LANDSAT(*)
DP.FeatExtLandsat(opathF+"/LANDSAT_r_MultiTemp_GapF_clip.tif", "LANDSATimagesDateList_"+tile+".txt", opathT, opathF)

#Create a image series of each feature from SPOT and LANDSAT by chronological order
DP.ConcatenateFeatures(opathT, opathF)

#Order the SPOT and LANDSAT interpolated image series and create one image serie by chronological order (all bands and common bands)
DP.OrderGapFSeries(opathF+"/SPOT_MultiTemp_GapF_clip.tif", opathF+"/LANDSAT_r_MultiTemp_GapF_clip.tif", opathT, opathF, tile)
"""
#Concatenate the reflectances interpolated + NDVI + NDWI + Brightness
CL.ConcatenateAllData(opathF, opathF+"/SL_MultiTempGapF_4bpi.tif "+opathF+"/NDVI.tif "+opathF+"/NDWI.tif "+opathF+"/Brightness.tif")


#**************************************PROCESSING OF IN-SITU DATA*********************************************************
"""
samplesFile = CL.GetCropSamples(vectorFile, opathT)
RSi.RandomInSitu(samplesFile, classField, 10, opathIS)


#************************************RF and SVM-RF CLASSIFICATION*********************************************************

learnsamples = CL.getListLearnsamples(vectorFile, opathIS)
valsamples = CL.getListValsamples(vectorFile, opathIS)

for samples in learnsamples:
   CL.RFClassif(samples, opathF, opathT, opathF, opathF+"/SL_MultiTempGapF_4bpi.tif "+opathF+"/NDVI.tif "+opathF+"/NDWI.tif "+opathF+"/Brightness.tif")

listModel = CL.getListModel(opathF+"/RF")

for model in listModel:
   classification = CL.imageClassification(model, opathF+"/SL_MultiTempGapF_4bpi_NDVI_NDWI_Brightness_.tif", opathCL)
   refdata = CL.getValsamples(classification, valsamples)
   print refdata
   CL.ConfMatrix(classification, refdata, opathCL)

confMList = CL.getListConfMat(opathCL, "RF", "bm0")
CL.ComputeMetrics(opathCL, opathCL, confMList)


for samples in learnsamples:
   CL.SVMClassif(samples, opathF, opathT, opathF, opathF+"/SL_MultiTempGapF_4bpi.tif "+opathF+"/NDVI.tif "+opathF+"/NDWI.tif "+opathF+"/Brightness.tif")

listModel = CL.getListModel(opathF+"/SVM")

for model in listModel:
   classification = CL.imageClassification(model, opathF+"/SL_MultiTempGapF_4bpi_NDVI_NDWI_Brightness_.tif", opathCL)
   refdata = CL.getValsamples(classification, valsamples)
   CL.ConfMatrix(classification, refdata, opathCL)

confMList = CL.getListConfMat(opathCL, "SVM", "bm1")
CL.ComputeMetrics(opathCL, opathCL, confMList)
"""


