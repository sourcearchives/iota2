#!/usr/bin/python

# =========================================================================
#   Program:   iota2
#
#   Copyright (c) CESBIO. All rights reserved.
#
#   See LICENSE for details.
#
#   This software is distributed WITHOUT ANY WARRANTY; without even
#   the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the above copyright notices for more information.
#
# =========================================================================

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
from Sensors import Landsat5
from Sensors import Formosat
from config import Config
interp = dico.interp
res = dico.res

if len(sys.argv) == 1:
    prog = os.path.basename(sys.argv[0])
    print '      '+sys.argv[0]+' [options]'
    print "     Aide : ", prog, " --help"
    print "        ou : ", prog, " -h"

    raise Exception("you need to specify more arguments")

else:

    usage = "Usage: %prog [options] "

    parser = argparse.ArgumentParser(description = "Preprocessing and classification for multispectral,multisensor and multitemporal data")

    parser.add_argument("-cf",dest="config",action="store",\
                        help="Config chaine", required = True)
    parser.add_argument("-iL8", dest="ipathL8", action="store", \
                            help="Landsat8 Image path", default = None)

    parser.add_argument("-iL5", dest="ipathL5", action="store", \
                            help="Landsat5 Image path", default = None)

    parser.add_argument("-iS",dest="ipathS4",action="store",\
                            help="Spot Image path",default = None)

    parser.add_argument("-iF", dest="ipathF", action="store", \
                            help=" Formosat Image path",default = None)

    parser.add_argument("-w", dest="opath", action="store",\
                            help="working path", required = True)

    parser.add_argument("--db_L8", dest="dateB_L8", action="store",\
                            help="Date for begin regular grid", required = False, default = None)
    
    parser.add_argument("--de_L8", dest="dateE_L8", action="store",\
                        help="Date for end regular grid",required = False, default = None)

    parser.add_argument("--db_L5", dest="dateB_L5", action="store",\
                            help="Date for begin regular grid", required = False, default = None)
    
    parser.add_argument("--de_L5", dest="dateE_L5", action="store",\
                        help="Date for end regular grid",required = False, default = None)
    
    parser.add_argument("-g",dest="gap", action="store",\
                        help="Date gap between two images in days", required=True)

    parser.add_argument("-wr",dest="workRes", action="store",\
                        help="Working resolution", required=True)

    parser.add_argument("-fs",dest="forceStep", action="store",\
                        help="Force step", default = None)

    parser.add_argument("-r",dest="Restart",action="store",\
                        help="Restart from previous valid status if parameters are the same",choices =('True','False'),default = 'True')

    parser.add_argument("--wo",dest="wOut", action="store",help="working out",required=False,default=None)
    args = parser.parse_args()
    
#Recuperation de la liste des indices
cfg = Config(args.config)
listIndices = cfg.GlobChain.features
nbLook = cfg.GlobChain.nbLook

arg = args.Restart
if arg == "False":
    restart = False
else:
    restart = True

opath = Opath(args.opath)

#Init du log

log = ML.LogPreprocess(opath.opathT)
#print "opath_log",log.opath
log.initNewLog(args,listIndices)
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

list_Sensor = []
workRes = int(args.workRes)
#Sensors are sorted by resolution
fconf = args.config
if not ("None" in args.ipathL8):
    landsat8 = Landsat8(args.ipathL8,opath,fconf,workRes)
    datesVoulues = CreateFichierDatesReg(args.dateB_L8,args.dateE_L8,args.gap,opath.opathT,landsat8.name)
    landsat8.setDatesVoulues(datesVoulues)

    list_Sensor.append(landsat8)
if not ("None" in args.ipathL5):
    landsat5 = Landsat5(args.ipathL5,opath,fconf,workRes)
    datesVoulues = CreateFichierDatesReg(args.dateB_L5,args.dateE_L5,args.gap,opath.opathT,landsat5.name)
    landsat5.setDatesVoulues(datesVoulues)

    list_Sensor.append(landsat5)

imRef = list_Sensor[0].imRef
sensorRef = list_Sensor[0].name
"""
if len(listIndices)>1:
	listIndices = list(listIndices)
	listIndices = sorted(listIndices)
	listFeat = "_".join(listIndices)
else:
	listFeat = listIndices[0]

Stack = args.opath+"/Final/SL_MultiTempGapF_"+listFeat+"__.tif"
"""
StackName = fu.getFeatStackName(args.config)
Stack = args.wOut+"/Final/"+StackName
if not os.path.exists(Stack):
	#Step 1 Creation des masques de bords
	Step = 1
	if log.dico[Step]:
	    for sensor in list_Sensor:
	        liste = sensor.getImages(opath) #Inutile appelle dans CreateBorderMask et dans le constructeur
	        sensor.CreateBorderMask(opath,imRef,nbLook)
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
		dates = sensor.getDatesVoulues()
	        DP.Gapfilling(sensor.serieTemp,sensor.serieTempMask,sensor.serieTempGap,sensor.nbBands,0,sensor.fdates,dates,args.wOut)
	Step = log.update(Step)

	for sensor in list_Sensor:
	    #get possible features
	    feat_sensor = []
	    for d in listIndices:
	    	if d in sensor.indices:
			feat_sensor.append(d)
	    print feat_sensor
	    DP.FeatureExtraction(sensor,datesVoulues,opath.opathT,feat_sensor)

	#step 9
	seriePrim = DP.ConcatenateFeatures(opath,listIndices)

	#step 10
	serieRefl = DP.OrderGapFSeries(opath,list_Sensor)
	
	#step 11
	print seriePrim
	CL.ConcatenateAllData(opath.opathF, serieRefl+" "+seriePrim)
