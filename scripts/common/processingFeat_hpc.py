#!/usr/bin/python

import os,sys
import glob
import argparse

import New_DataProcessing as DP

from Utils import Opath
import Dico as dico
from CreateDateFile import CreateFichierDatesReg
import ClassificationN as CL
import RandomSelectionInsitu_LV as RSi
import moduleLog_hpc as ML
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

    parser.add_argument("-w", dest="opath", action="store",\
                            help="working path", required = True)

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

    parser.add_argument("--wo",dest="wOut", action="store",help="working out",required=False,default=None)
    args = parser.parse_args()
    


arg = args.Restart
if arg == "False":
    restart = False
else:
    restart = True

opath = Opath(args.opath)

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

#Recuperation de la liste des indices
cfg = Config(args.config)
listIndices = cfg.GlobChain.indices
listIndices.sort()
nbLook = cfg.GlobChain.nbLook

#recherche de la stack d'images
Stack = wOut+"/Final/SL_MultiTempGapF"
#Step 1 Creation des masques de bords

for sensor in list_Sensor:
	liste = sensor.getImages(opath) #Inutile appelle dans CreateBorderMask et dans le constructeur
	sensor.CreateBorderMask(opath,imRef,nbLook)

DP.CreateCommonZone(opath.opathT,list_Sensor)

for sensor in list_Sensor:
    if not sensor.work_res == sensor.native_res:
        #reech les donnees
        if not os.path.exists(sensor.pathRes):
          os.mkdir(sensor.pathRes)
        sensor.ResizeImages(opath.opathT,imRef)

for sensor in list_Sensor:
    if not sensor.work_res == sensor.native_res:
        if not os.path.exists(sensor.pathRes):
            os.mkdir(sensor.pathRes)
        sensor.ResizeMasks(opath.opathT,imRef)

for sensor in list_Sensor:
    sensor.createMaskSeries(opath.opathT)

for sensor in list_Sensor: 
    sensor.createSerie(opath.opathT)

for sensor in list_Sensor:
    DP.Gapfilling(sensor.serieTemp,sensor.serieTempMask,sensor.serieTempGap,sensor.nbBands,0,sensor.fdates,datesVoulues,args.wOut)

for sensor in list_Sensor:
    DP.FeatureExtraction(sensor,datesVoulues,opath.opathT)

#Step 3 Concatene toutes les primitives de tous les capteurs


seriePrim = DP.ConcatenateFeatures(opath,listIndices)			

#Step 4 Concatene toutes les reflectances de tous les capteurs

serieRefl = DP.OrderGapFSeries(opath,list_Sensor) 

#Step 5 Concatene toutes les series temporelles et cp dans le dossier final

CL.ConcatenateAllData(opath.opathF, serieRefl+" "+seriePrim)
if args.wOut != None:
	os.system("cp -R "+args.opath+"/Final "+args.wOut)
	os.system("cp "+args.opath+"/tmp/*_Sum_Mask.tif "+args.wOut)
	os.system("cp "+args.opath+"/tmp/MaskCommunSL.tif "+args.wOut)

	os.system("cp "+args.opath+"/tmp/MaskCommunSL.shp "+args.wOut)
	os.system("cp "+args.opath+"/tmp/MaskCommunSL.shx "+args.wOut)
	os.system("cp "+args.opath+"/tmp/MaskCommunSL.dbf "+args.wOut)
	os.system("cp "+args.opath+"/tmp/MaskCommunSL.prj "+args.wOut)


