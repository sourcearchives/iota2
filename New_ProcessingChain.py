#!/usr/bin/python
"""
python New_ProcessingChain.py -cf /mnt/data/home/tardyb/These/processingchain-l8-spot/ConfigFormosatM.cfg -iF /mnt/data/home/tardyb/These/Data/Formosat/2007/ -w /mnt/data/home/tardyb/These/Test_Chaine_Refactor_Form/ -vd /mnt/data/home/tardyb/These/DT/Donnees_Traitee/dt_so07.shp -db 20061001 -de 20070930 -g 4 -wr 8 

"""
import os,sys
import glob
import argparse

import New_DataProcessing as DP

from Utils import Opath
import Dico as dico
from CreateDateFile import CreateFichierDatesReg
import ClassificationN as CL
import RandomSelectionInsitu_LV as RSi
import moduleLog as ML
from Sensor_Spot import Spot4
from Sensor_Landsat8 import Landsat8
from Sensor_Formosat import Formosat
interp = dico.interp
res = dico.res

if len(sys.argv) == 1:
    prog = os.path.basename(sys.argv[0])
    print '      '+sys.argv[0]+' [options]'
    print "     Aide : ", prog, " --help"
    print "        ou : ", prog, " -h"

    sys.exit(-1)

else:

    usage = "Usage: %prog [options] "

    parser = argparse.ArgumentParser(description = "Preprocessing and classification for multispectral,multisensor and multitemporal data")

    parser.add_argument("-cf",dest="config",action="store",\
                        help="Config chaine", required = True)
    parser.add_argument("-iL", dest="ipathL8", action="store", \
                            help="Landsat Image path", default = None)

    parser.add_argument("-iS",dest="ipathS4",action="store",\
                            help="Spot Image path",default = None)

    parser.add_argument("-iF", dest="ipathF", action="store", \
                            help=" Formosat Image path",default = None)

    parser.add_argument("-vd", dest="shapeF", action="store", \
                            help="vector data for labelling", required = True)

    parser.add_argument("-w", dest="opath", action="store",\
                            help="Output path", required = True)

    parser.add_argument("-db", dest="dateB", action="store",\
                            help="Date for begin regular grid", required = True)
    
    parser.add_argument("-de", dest="dateE", action="store",\
                        help="Date for end regular grid",required = True)
    
    parser.add_argument("-g",dest="gap", action="store",\
                        help="Date gap between two images in week", required=True)

    parser.add_argument("-wr",dest="workRes", action="store",\
                        help="Working resolution", required=True)

    parser.add_argument("-fs",dest="forceStep", action="store",\
                        help="Force step", default = None)

    parser.add_argument("-r",dest="Restart",action="store",\
                        help="Restart from previous valid status if parameters are the same",choices =('True','False'),default = 'True')

    args = parser.parse_args()
    


arg = args.Restart
if arg == "False":
    restart = False
else:
    restart = True

opath = Opath(args.opath)

#Init du log

log = ML.Log(opath.opathT)
#print "opath_log",log.opath
log.initNewLog(args)
if restart:
    nom_fich = opath.opathT+"/log"
    #print "nomfich",nom_fich
    if  os.path.exists(nom_fich):
        log_old = ML.load_log(nom_fich)
        ML.compareLogInstanceArgs(log_old,log)        
    else:
        print "Not log file found at %s, all step will be processed"%opath.opathT

log.checkStep()

## #Fin Init du log
## #Le log precedent est detruit ici
datesVoulues = CreateFichierDatesReg(args.dateB,args.dateE,args.gap,opath.opathT)
list_Sensor = []
workRes = int(args.workRes)
#Sensors are sorted by resolution
#The first sensors of the list define the working resolution
fconf = args.config
if not (args.ipathF is None):
    formosat = Formosat(args.ipathF,opath,fconf,workRes)
    list_Sensor.append(formosat)
if not (args.ipathS4 is None):
    spot = Spot4(args.ipathS4,opath,workRes)
    list_Sensor.append(spot)
if not (args.ipathL8 is None):
    landsat = Landsat8(args.ipathL8,opath,workRes)
    list_Sensor.append(landsat)

imRef = list_Sensor[0].imRef
sensorRef = list_Sensor[0].name

#Step 1 Creation des masques de bords
Step = 1
if log.dico[Step]:
    for sensor in list_Sensor:
        liste = sensor.getImages(opath) #Inutile appelle dans CreateBorderMask et dans le constructeur
        sensor.CreateBorderMask(opath,imRef)
Step = log.update(Step)

#Step 2 :Creation de l'emprise commune
print "Avant masque commum",Step,log.dico[Step]
if log.dico[Step]:
    DP.CreateCommonZone(opath.opathT,list_Sensor)
Step = log.update(Step)
print 'Masque empr',Step
#PreProcess
for sensor in list_Sensor:
    if not sensor.work_res == sensor.native_res:
        #reech les donnees
        #Step 3 reech Refl
        if log.dico[Step]:
            sensor.ResizeImages(opath.opathT,imRef)
Step = log.update(Step)

if log.dico[Step]:
    for sensor in list_Sensor:
        if not sensor.work_res == sensor.native_res:
            #Step 4 reech Mask
            sensor.ResizeMasks(opath.opathT,imRef)
Step = log.update(Step)

if log.dico[Step]:
    for sensor in list_Sensor:
        #Step 5 Creer Serie de masques
        sensor.createMaskSeries(opath.opathT)
Step = log.update(Step)

if log.dico[Step]:
    for sensor in list_Sensor:
        #Step 6 : Creer Serie Tempo 
        sensor.createSerie(opath.opathT)
Step = log.update(Step)

if log.dico[Step]:
    for sensor in list_Sensor:
        #Step 7 : GapFilling
        DP.Gapfilling(sensor.serieTemp,sensor.serieTempMask,sensor.serieTempGap,sensor.nbBands,0,sensor.fdates,datesVoulues)
Step = log.update(Step)
if log.dico[Step]:
    for sensor in list_Sensor:
         #Step 8 : Extract Feature
        DP.FeatureExtraction(sensor,datesVoulues,opath.opathT)
Step = log.update(Step)

#Step 9 Concatene toutes les primitives de tous les capteurs

if log.dico[Step]:
    seriePrim = DP.ConcatenateFeatures(opath)
Step = log.update(Step)

#Step 10 Concatene toutes les reflectances de tous les capteurs
if log.dico[Step]:
    serieRefl = DP.OrderGapFSeries(opath,list_Sensor)
Step = log.update(Step)
#Step 11 Concatene toutes les series temporelles
if log.dico[Step]:
    CL.ConcatenateAllData(opath.opathF, serieRefl+" "+seriePrim)
Step = log.update(Step)
#### SUITE IN situ et Classif
if log.dico[Step]:
    vectorFile = args.shapeF
    #samplesFile = CL.GetCropSamples(vectorFile, opath.opathT)#Dedier S2
    RSi.RandomInSitu(vectorFile, "ID_CLASS", 10, opath.opathIS)
Step = log.update(Step)
## #************************************RF and SVM-RF CLASSIFICATION*********************************************************

## opathT = opath.opathT
## opathF = opath.opathF
## opathIS = opath.opathIS
## opathCL = opath.opathCL
## learnsamples = CL.getListLearnsamples(vectorFile, opathIS)
## valsamples = CL.getListValsamples(vectorFile, opathIS)

## for samples in learnsamples:
##    CL.RFClassif(samples, opathF, opathT, opathF, opathF+"/SL_MultiTempGapF_4bpi.tif "+opathF+"/NDVI.tif "+opathF+"/NDWI.tif "+opathF+"/Brightness.tif")

## listModel = CL.getListModel(opathF+"/RF")

## for model in listModel:
##    classification = CL.imageClassification(model, opathF+"/SL_MultiTempGapF_4bpi_NDVI_NDWI_Brightness_.tif", opathCL)
##    refdata = CL.getValsamples(classification, valsamples)
##    print refdata
##    CL.ConfMatrix(classification, refdata, opathCL)

## confMList = CL.getListConfMat(opathCL, "RF", "bm0")
## CL.ComputeMetrics(opathCL, opathCL, confMList)


## for samples in learnsamples:
##    CL.SVMClassif(samples, opathF, opathT, opathF, opathF+"/SL_MultiTempGapF_4bpi.tif "+opathF+"/NDVI.tif "+opathF+"/NDWI.tif "+opathF+"/Brightness.tif")

## listModel = CL.getListModel(opathF+"/SVM")

## for model in listModel:
##    classification = CL.imageClassification(model, opathF+"/SL_MultiTempGapF_4bpi_NDVI_NDWI_Brightness_.tif", opathCL)
##    refdata = CL.getValsamples(classification, valsamples)
##    CL.ConfMatrix(classification, refdata, opathCL)

## confMList = CL.getListConfMat(opathCL, "SVM", "bm1")
## CL.ComputeMetrics(opathCL, opathCL, confMList)


#

