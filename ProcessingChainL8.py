#!/usr/bin/python

import os
import glob
from sys import argv
import SpotData as SD
import SpotProcessing as SP
import LandsatData as LD
import LandsatProcessing as LP
import DataProcessing as DP
import Gapfilling as GP
import Classification as CL
import TemporalResampling as TP
import RapideyeData as RD
import Dico as dico
import RandomSelectionInsitu as RSi
import RandomSelectionInsituForFusion as RSiF
import time

ipathL = argv[1]
opath = argv[2]
vectorFile = argv[3]
opathT = argv[2]+"/tmp"
opathF =argv[2]+"/Final"
opathTR = argv[2]+"/Final/TempRes"
opathSM = argv[2]+"/Final/Smoothing"
opathCL = argv[2]+"/Final/Images"
opathDF = argv[2]+"/Final/DF-Fusion"
opathIS = argv[2]+"/in-situ"
opathDFIS = argv[2]+"/Final/DF-Fusion/in-situ"
Sbands = dico.Sbands
Lbands = dico.Lbands
interp = dico.interp
sr = dico.sr
rr = dico.rr
maxiter = dico.maxiter
delta = dico.delta


#Pre-Processing of the data

DP.CreateDir(opath)

LP.CreateBorderMaskLandsat30m(ipathL, opathT)

vectorMask = DP.CreateCommonZoneL30m(opathT)

LP.CreateMaskSeriesLandsat30m(ipathL, opathT)

LP.createSerieLandsat30m(ipathL, opathT)

DP.Gapfilling(opathT+"/LANDSAT_MultiTempIm_clip.tif", opathT+"/LANDSAT_MultiTempMask_clip.tif", opathF+"/LANDSAT_MultiTemp_GapF_clip.tif", Lbands, interp, opathT+"/LANDSATimagesDateList.txt")

DP.FeatExtLandsat(opathF+"/LANDSAT_MultiTemp_GapF_clip.tif", "LANDSATimagesDateList.txt", opathT, opathF)

DP.ConcatenateFeatures(opathT, opathF)

#Next fonction creates a image series with the common bands to SPOT -> LANDSAT_MultiTemp_GapF_clip_4bpi_SPOTcombands.tif and this is the image series that will be used afterwards. If all the bands are required do not use this function and replace LANDSAT_MultiTemp_GapF_clip_4bpi_SPOTcombands by LANDSAT_MultiTemp_GapF_clip in all the functions.

DP.refl_LandsatGap(opathF+"/LANDSAT_MultiTemp_GapF_clip.tif", opathT,opathF, "SPOT")

CL.ConcatenateAllData(opathF, opathF+"/LANDSAT_MultiTemp_GapF_clip_4bpi_SPOTcombands.tif "+opathF+"/NDVI.tif "+opathF+"/NDWI.tif "+opathF+"/Brightness.tif")

#**************************************PROCESSING OF IN-SITU DATA*********************************************************
'''
samplesFile = CL.GetCropSamples(vectorFile, opathT)
RSi.RandomInSitu(samplesFile, "CODE", 10, opathIS)
'''


#************************************RF and SVM-RF CLASSIFICATION*********************************************************

valsamples = CL.getListValsamples(vectorFile, opathIS)
learnsamples = CL.getListLearnsamples(vectorFile, opathIS)
'''
start_time = time.time()

for samples in learnsamples:
   CL.RFClassif(samples, opathF, opathT, opathF, opathF+"/LANDSAT_MultiTemp_GapF_clip_4bpi_SPOTcombands.tif "+opathF+"/NDVI.tif "+opathF+"/NDWI.tif "+opathF+"/Brightness.tif")
listModel = CL.getListModel(opathF+"/RF")
for model in listModel:
   classification = CL.imageClassification(model, opathF+"/LANDSAT_MultiTemp_GapF_clip_4bpi_SPOTcombands_NDVI_NDWI_Brightness_.tif", opathCL)
   refdata = CL.getValsamples(classification, valsamples)
   CL.ConfMatrix(classification, refdata, opathCL)

confMList = CL.getListConfMat(opathCL, "RF", "bm0")
CL.ComputeMetrics(opathCL, opathCL, confMList)

etimeRF = time.time()-start_time
print etimeRF
'''
start_time = time.time()
"""
for samples in learnsamples:
   CL.SVMClassif(samples, opathF, opathT, opathF, opathF+"/LANDSAT_MultiTemp_GapF_clip_4bpi_SPOTcombands.tif "+opathF+"/NDVI.tif "+opathF+"/NDWI.tif "+opathF+"/Brightness.tif")
listModel = CL.getListModel(opathF+"/SVM_new")
"""
opathCL = argv[2]+"/Final/Images"
"""
for model in listModel:
   classification = CL.imageClassification(model, opathF+"/LANDSAT_MultiTemp_GapF_clip_4bpi_SPOTcombands_NDVI_NDWI_Brightness_.tif", opathCL)
   refdata = CL.getValsamples(classification, valsamples)
   CL.ConfMatrix(classification, refdata, opathCL)
"""
confMList = CL.getListConfMat(opathCL, "SVM", "bm1")
CL.ComputeMetrics(opathCL, opathCL, confMList)

#etimeSVM = time.time()-start_time
#print etimeRF
#print etimeSVM

#------------------------------------------------------------DATA SMOOTHING----------------------------------------------------
'''
start_time = time.time()

DP.MeanShiftSmooth(opathF+"/LANDSAT_MultiTemp_GapF_clip_4bpi_SPOTcombands.tif", sr, rr, maxiter, opathSM)

DP.FeatExtSPOT(opathSM+"/LANDSAT_MultiTemp_GapF_clip_4bpi_SPOTcombands8_120_20_SMTH.tif", opathF+"/LANDSATimagesDateList.txt", opathSM)

DP.ConcatenateFeatures(opathSM, opathSM)

CL.ConcatenateAllData(opathSM, opathSM+"/LANDSAT_MultiTemp_GapF_clip_4bpi_SPOTcombands8_120_20_SMTH.tif "+opathSM+"/NDVI.tif "+opathSM+"/NDWI.tif "+opathSM+"/Brightness.tif")

etimeSmooth = time.time()-start_time
'''
#---------------------------------------DATA SMOOTHING WITH BEST CLASSIFIER----------------------------------------------------
'''
start_time = time.time()

learnsamples = CL.getListLearnsamples(vectorFile, opathIS)
valsamples = CL.getListValsamples(vectorFile, opathIS)

for samples in learnsamples:
   CL.RFClassif(samples, opathSM, opathT, opathSM, opathSM+"/LANDSAT_MultiTemp_GapF_clip_4bpi_SPOTcombands8_120_20_SMTH.tif "+opathSM+"/NDVI.tif "+opathSM+"/NDWI.tif "+opathSM+"/Brightness.tif")
listModel = CL.getListModel(opathSM+"/RF")
for model in listModel:
   classification = CL.imageClassification(model, opathSM+"/LANDSAT_MultiTemp_GapF_clip_4bpi_SPOTcombands8_120_20_SMTH_NDVI_NDWI_Brightness_.tif", opathSM+"/Images")
   refdata = CL.getValsamples(classification, valsamples)
   #print refdata
   CL.ConfMatrix(classification, refdata, opathSM+"/Images")

confMList = CL.getListConfMat(opathSM+"/Images", "RF", "bm0")
CL.ComputeMetrics(opathSM+"/Images", opathSM+"/Images", confMList)

etimeSmoothRF = time.time()-start_time

# Temporal resampling

start_time = time.time()

filedates = TP.RangeDates("LANDSATimagesDateList.txt", 5, opathT)

TP.TempResampling(opathF+"/LANDSAT_MultiTemp_GapF_clip_4bpi_SPOTcombands.tif", opathT+"/LANDSAT_MultiTempMask_clip.tif", opathTR+"/LANDSAT_TemRes_"+str(delta)+"days_clip.tif", Sbands, interp, opathT+"/LANDSATimagesDateList.txt", filedates)

DP.FeatExtSPOT(opathTR+"/LANDSAT_TemRes_"+str(delta)+"days_clip.tif", filedates, opathTR)

DP.ConcatenateFeatures(opathTR, opathTR)

CL.ConcatenateAllData(opathTR, opathTR+"/LANDSAT_TemRes_"+str(delta)+"days_clip.tif "+opathTR+"/NDVI.tif "+opathTR+"/NDWI.tif "+opathTR+"/Brightness.tif")

etimeTemp = time.time()-start_time
'''
#---------------------------------------TEMPORAL RESAMPLING WITH BEST CLASSIFIER--------------------------------------------------
start_time = time.time()
'''
learnsamples = CL.getListLearnsamples(vectorFile, opathIS)
valsamples = CL.getListValsamples(vectorFile, opathIS)

for samples in learnsamples:
   CL.RFClassif(samples, opathTR, opathT, opathTR, opathTR+"/LANDSAT_TemRes_5days_clip.tif "+opathTR+"/NDVI.tif "+opathTR+"/NDWI.tif "+opathTR+"/Brightness.tif")
listModel = CL.getListModel(opathTR+"/RF")
for model in listModel:
   classification = CL.imageClassification(model, opathTR+"/LANDSAT_TemRes_5days_clip_NDVI_NDWI_Brightness_.tif", opathTR+"/Images")
   refdata = CL.getValsamples(classification, valsamples)
   #print refdata
   CL.ConfMatrix(classification, refdata, opathTR+"/Images")

confMList = CL.getListConfMat(opathTR+"/Images", "RF", "bm0")
CL.ComputeMetrics(opathTR+"/Images", opathTR+"/Images", confMList)

etimeTempRF = time.time()-start_time
'''
#*************************************************DEMPSTER-SHAFER FUSION***********************************************************
'''
samplesFileFusion = CL.GetCropSamples(vectorFile, opathT)
RSiF.RandomInSituFusion(samplesFileFusion, "CODE", 10, opathDFIS)


for seed in range(0,10):
   learnFussamples = CL.getListFussamples(vectorFile, opathDFIS, seed, "DSF-learn")
   learnVal1samples = CL.getListFussamples(vectorFile, opathDFIS, seed, "DSF-val1")
   learnVal2samples = CL.getListFussamples(vectorFile, opathDFIS, seed, "DSF-val2")
   CL.RFClassif(learnFussamples[0], opathDF, opathT, opathF, opathF+"/LANDSAT_MultiTemp_GapF_clip_4bpi_SPOTcombands.tif "+opathF+"/NDVI.tif "+opathF+"/NDWI.tif "+opathF+"/Brightness.tif", )
   modelRF = opathDF+"/RF/RF_Classification_seed"+str(seed)+"_bm0.txt"
   classificationRF = CL.imageClassification(modelRF, opathF+"/LANDSAT_MultiTemp_GapF_clip_4bpi_SPOTcombands_NDVI_NDWI_Brightness_.tif ", opathDF+"/RF")
   confMatRF = CL.ConfMatrix(classificationRF, learnVal1samples[0], opathDF+"/Images")
   CL.SVMClassif(learnFussamples[0], opathDF, opathT, opathF, opathF+opathF+"/LANDSAT_MultiTemp_GapF_clip_4bpi_SPOTcombands.tif "+opathF+"/NDVI.tif "+opathF+"/NDWI.tif "+opathF+"/Brightness.tif")
   modelSVM = opathDF+"/SVM/SVM_Classification_seed"+str(seed)+"_bm1.txt"
   classificationSVM = CL.imageClassification(modelSVM, opathF+"/LANDSAT_MultiTemp_GapF_clip_4bpi_SPOTcombands_NDVI_NDWI_Brightness_.tif ", opathDF+"/SVM")
   confMatSVM = CL.ConfMatrix(classificationSVM, learnVal1samples[0], opathDF+"/Images")
   fusion = CL.DFfusion(classificationRF, confMatRF, classificationSVM, confMatSVM, opathDF+"/Images")
   confMatFusion = CL.ConfMatrixFusion(fusion, learnVal2samples[0], opathDF+"/Images")

confMList = CL.getListConfMat(opathDF+"/Images", "RF", "SVM")
CL.ComputeMetrics(opathDF+"/Images", opathDF+"/Images", confMList)
confMList = CL.getListConfMat(opathDF+"/Images", "RF", "bm0")
CL.ComputeMetrics(opathDF+"/Images", opathDF+"/Images", confMList)
confMList = CL.getListConfMat(opathDF+"/Images", "SVM", "bm1")
CL.ComputeMetrics(opathDF+"/Images", opathDF+"/Images", confMList)
'''
