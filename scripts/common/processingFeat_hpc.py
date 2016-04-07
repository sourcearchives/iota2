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

    sys.exit(-1)

else:

    usage = "Usage: %prog [options] "

    parser = argparse.ArgumentParser(description = "Preprocessing and classification for multispectral,multisensor and multitemporal data")

    parser.add_argument("-cf",dest="config",action="store",\
                        help="Config chaine", required = True)
    parser.add_argument("-iL8", dest="ipathL8", action="store", \
                            help="Landsat Image path", default = None)

    parser.add_argument("-iS",dest="ipathS4",action="store",\
                            help="Spot Image path",default = None)

    parser.add_argument("-iL5", dest="ipathL5", action="store", \
                            help="Landsat5 Image path", default = None)

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
listIndices = cfg.GlobChain.indices
nbLook = cfg.GlobChain.nbLook

arg = args.Restart
if arg == "False":
    restart = False
else:
    restart = True

opath = Opath(args.opath)

#Init du log

log = ML.LogPreprocess(args.wOut)

log.initNewLog(args)
if restart:
    nom_fich = args.wOut+"/log"
    #print "nomfich",nom_fich
    if  os.path.exists(nom_fich):
        log_old = ML.load_log(nom_fich)
        log.compareLogInstanceArgs(log_old)        
    else:
        print "Not log file found at %s, all step will be processed"%args.wOut

log.checkStep()

## #Fin Init du log
## #Le log precedent est detruit ici

list_Sensor = []
workRes = int(args.workRes)
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

if len(listIndices)>1:
	listIndices = list(listIndices)
	listIndices = sorted(listIndices)
	listFeat = "_".join(listIndices)
else:
	listFeat = listIndices[0]

Stack = args.wOut+"/Final/SL_MultiTempGapF_"+listFeat+"__.tif"

if not os.path.exists(Stack):
	#Step 1 Creation des masques de bords
	Step = 1
	if log.dico[Step]:
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

	Step = log.update(Step)

	if os.path.exists(args.wOut+"/tmp"):
		"""
		os.system("rm -r "+args.opath+"/tmp")
		os.system("rm -r "+args.opath+"/Final")
		os.system("tar -cjf "+args.wOut+"/Archive.tar -C "+args.wOut+" .")
		os.system("mv "+args.wOut+"/Archive.tar "+args.opath)
		os.system("tar -xvf "+args.opath+"/Archive.tar")
		os.system("mv "+args.opath+"/Archive/Final ../")
		os.system("mv "+args.opath+"/Archive/tmp ../")

		os.system("rm -r "+args.wOut+"/tmp")
		os.system("rm -r "+args.wOut+"/Final")
		"""
		os.system("rm -rf "+args.opath+"/tmp/*")
		os.system("rm -r "+args.opath+"/Final")
		for sensor in list_Sensor:
			os.system("cp "+args.wOut+"/tmp/"+str(sensor.name)+"_ST_REFL_GAP.tif "+args.opath+"/tmp")
			os.system("cp "+args.wOut+"/tmp/DatesInterpReg"+str(sensor.name)+".txt "+args.opath+"/tmp")
		#os.system("cp -R "+args.wOut+"/tmp "+args.opath)
		os.system("cp -R "+args.wOut+"/Final "+args.opath)
		os.system("rm -r "+args.wOut+"/tmp")
		os.system("rm -r "+args.wOut+"/Final")
	for sensor in list_Sensor:
	    #get possible features
	    feat_sensor = []
	    for d in listIndices:
	    	if d in sensor.indices:
			feat_sensor.append(d)
	    print feat_sensor
	    DP.FeatureExtraction(sensor,datesVoulues,opath.opathT,feat_sensor)

	seriePrim = DP.ConcatenateFeatures(opath,listIndices)
	serieRefl = DP.OrderGapFSeries(opath,list_Sensor)
	print seriePrim
	CL.ConcatenateAllData(opath.opathF, serieRefl+" "+seriePrim)
	"""
	os.system("tar -cjf "+args.opath+"/Archive.tar -C "+args.opath+" .")
	os.system("mv "+args.opath+"/Archive.tar "+args.wOut)
	os.system("tar -xvf "+args.wOut+"/Archive.tar")
	os.system("mv "+args.wOut+"/Archive/Final "+args.wOut)
	os.system("mv "+args.wOut+"/Archive/tmp "+args.wOut)
	os.system("cp "+args.opath+"/tmp/Landsat8_Sum_Mask.tif "+args.wOut)
	os.system("cp "+args.opath+"/tmp/MaskCommunSL.tif "+args.wOut)

	os.system("cp "+args.opath+"/tmp/MaskCommunSL.shp "+args.wOut)
	os.system("cp "+args.opath+"/tmp/MaskCommunSL.shx "+args.wOut)
	os.system("cp "+args.opath+"/tmp/MaskCommunSL.dbf "+args.wOut)
	os.system("cp "+args.opath+"/tmp/MaskCommunSL.prj "+args.wOut)
	"""
	os.system("cp -R "+args.opath+"/Final "+args.wOut)
	os.system("mkdir "+args.wOut+"/tmp")
	for sensor in list_Sensor:
		os.system("cp "+args.opath+"/tmp/"+str(sensor.name)+"_ST_REFL_GAP.tif "+args.wOut+"/tmp")
		os.system("cp "+args.opath+"/tmp/DatesInterpReg"+str(sensor.name)+".txt "+args.wOut+"/tmp")
	#os.system("cp -R "+args.opath+"/tmp "+args.wOut)
	os.system("cp "+args.opath+"/tmp/Landsat8_Sum_Mask.tif "+args.wOut)
	os.system("cp "+args.opath+"/tmp/MaskCommunSL.tif "+args.wOut)

	os.system("cp "+args.opath+"/tmp/MaskCommunSL.shp "+args.wOut)
	os.system("cp "+args.opath+"/tmp/MaskCommunSL.shx "+args.wOut)
	os.system("cp "+args.opath+"/tmp/MaskCommunSL.dbf "+args.wOut)
	os.system("cp "+args.opath+"/tmp/MaskCommunSL.prj "+args.wOut)
	
	
	"""
	if log.dico[Step]:
	    for sensor in list_Sensor:
	         #Step 2 : Extract Feature
	        DP.FeatureExtraction(sensor,datesVoulues,opath.opathT)

	Step = log.update(Step)

	#Step 3 Concatene toutes les primitives de tous les capteurs

	if log.dico[Step]:
	    seriePrim = DP.ConcatenateFeatures(opath,listIndices)
	    log.update_SeriePrim(seriePrim)			

	Step = log.update(Step)
	seriePrim = log.seriePrim
	#Step 4 Concatene toutes les reflectances de tous les capteurs

	if log.dico[Step]:
	    serieRefl = DP.OrderGapFSeries(opath,list_Sensor) 
	    log.update_SerieRefl(serieRefl)

	Step = log.update(Step)
	serieRefl = log.serieRefl
	#Step 5 Concatene toutes les series temporelles et cp dans le dossier final
	
	if log.dico[Step]:
	    CL.ConcatenateAllData(opath.opathF, serieRefl+" "+seriePrim)
	    if args.wOut != None:
	        os.system("cp -R "+args.opath+"/Final "+args.wOut)
		os.system("cp -R "+args.opath+"/tmp "+args.wOut)
		os.system("cp "+args.opath+"/tmp/Landsat8_Sum_Mask.tif "+args.wOut)
		os.system("cp "+args.opath+"/tmp/MaskCommunSL.tif "+args.wOut)

		os.system("cp "+args.opath+"/tmp/MaskCommunSL.shp "+args.wOut)
		os.system("cp "+args.opath+"/tmp/MaskCommunSL.shx "+args.wOut)
		os.system("cp "+args.opath+"/tmp/MaskCommunSL.dbf "+args.wOut)
		os.system("cp "+args.opath+"/tmp/MaskCommunSL.prj "+args.wOut)
	Step = log.update(Step)
	"""
