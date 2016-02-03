#!/usr/bin/python
"""
python New_ProcessingChain.py -cf /mnt/data/home/vincenta/THEIA_OSO/conf/ConfigChaineSat.cfg -iL /mnt/MD1200/DONNEES/LANDSAT8/N2_THEIA/ -w /mnt/data/home/vincenta/tmp/TestPrim/ -vd /mnt/data/home/tardyb/These/DT/Donnees_Traitee/dt_so07.shp -db 20130414 -de 20131210 -g 16 -wr 30 

python New_ProcessingChain.py -cf /mnt/data/home/vincenta/THEIA_OSO/conf/ConfigChaineSat.cfg -iL /mnt/MD1200/DONNEES/LANDSAT8/N2_THEIA/ -w /mnt/data/home/vincenta/tmp/TestPrim/ -vd /mnt/data/home/tardyb/These/DT/Donnees_Traitee/dt_so07.shp -db 20130414 -de 20131210 -g 16 -wr 30
python New_ProcessingChain.py -cf /mnt/data/home/vincenta/THEIA_OSO/conf/ConfigChaineSat_1Tile.cfg -iL /mnt/data/home/vincenta/tmp/TUILES/Landsat8_D0003H0004 -w /mnt/data/home/vincenta/tmp/TestPrim/ -vd /mnt/data/home/tardyb/These/DT/Donnees_Traitee/dt_so07.shp -db 20130414 -de 20130428 -g 10 -wr 30
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
from Sensors import Spot4
from Sensors import Landsat8
from Sensors import Formosat
from config import Config
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

    """
    parser.add_argument("-vd", dest="shapeF", action="store", \
                            help="vector data for labelling", required = True)
    """

    parser.add_argument("-w", dest="opath", action="store",\
                            help="Output path", required = True)

    parser.add_argument("-db", dest="dateB", action="store",\
                            help="Date for begin regular grid", required = True)
    
    parser.add_argument("-de", dest="dateE", action="store",\
                        help="Date for end regular grid",required = True)
    
    parser.add_argument("-g",dest="gap", action="store",\
                        help="Date gap between two images in days", required=True)

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

log = ML.LogPreprocess(opath.opathT)
#print "opath_log",log.opath
log.initNewLog(args)
if restart:
    nom_fich = opath.opathT+"/log"
    #print "nomfich",nom_fich
    if  os.path.exists(nom_fich):
        log_old = ML.load_log(nom_fich)
        log.compareLogInstanceArgs(log_old)        
    else:
        print "Not log file found at %s, all step will be processed"%opath.opathT

log.checkStep()

## #Fin Init du log
## #Le log precedent est detruit ici
datesVoulues = CreateFichierDatesReg(args.dateB,args.dateE,args.gap,opath.opathT)
list_Sensor = []
workRes = int(args.workRes)
#Sensors are sorted by resolution
fconf = args.config
if not (args.ipathF is None):
    formosat = Formosat(args.ipathF,opath,fconf,workRes)
    list_Sensor.append(formosat)
if not (args.ipathS4 is None):
    spot = Spot4(args.ipathS4,opath,fconf,workRes)
    list_Sensor.append(spot)
if not (args.ipathL8 is None):
    landsat = Landsat8(args.ipathL8,opath,fconf,workRes)
    list_Sensor.append(landsat)

imRef = list_Sensor[0].imRef
sensorRef = list_Sensor[0].name
print imRef
#Step 1 Creation des masques de bords
Step = 1
if log.dico[Step]:
    for sensor in list_Sensor:
        liste = sensor.getImages(opath) #Inutile appelle dans CreateBorderMask et dans le constructeur
        sensor.CreateBorderMask(opath,imRef)
Step = log.update(Step)

#Step 2 :Creation de l'emprise commune
#print "Avant masque commum",Step,log.dico[Step]
if log.dico[Step]:
    DP.CreateCommonZone(opath.opathT,list_Sensor)
Step = log.update(Step)
#print 'Masque empr',Step
#PreProcess

for sensor in list_Sensor:
    if not sensor.work_res == sensor.native_res:
        #reech les donnees
        #Step 3 reech Refl
        if log.dico[Step]:
            if not os.path.exists(sensor.pathRes):
                os.mkdir(sensor.pathRes)

            sensor.ResizeImages(opath.opathT,imRef)
Step = log.update(Step)

if log.dico[Step]:
    for sensor in list_Sensor:
        if not sensor.work_res == sensor.native_res:
            #Step 4 reech Mask
            if not os.path.exists(sensor.pathRes):
                os.mkdir(sensor.pathRes)
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

#Recuperation de la liste des indices
cfg = Config(args.config)
listIndices = cfg.GlobChain.indices

if log.dico[Step]:
    seriePrim = DP.ConcatenateFeatures(opath,listIndices)
    log.update_SeriePrim(seriePrim)			
Step = log.update(Step)
seriePrim = log.seriePrim
#Step 10 Concatene toutes les reflectances de tous les capteurs
if log.dico[Step]:
    serieRefl = DP.OrderGapFSeries(opath,list_Sensor) 
    log.update_SerieRefl(serieRefl)
Step = log.update(Step)
serieRefl = log.serieRefl
#Step 11 Concatene toutes les series temporelles
if log.dico[Step]:
    #CL.ConcatenateAllData(opath.opathF, serieRefl+" "+seriePrim)
    CL.ConcatenateAllData(opath.opathF, serieRefl+" "+seriePrim)
    #CL.ConcatenateAllData(opath.opathF, serieRefl+seriePrim)
Step = log.update(Step)


