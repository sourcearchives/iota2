#!/usr/bin/python
#-*- coding: utf-8 -*-

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

import os,sys
import glob
import argparse,time

import New_DataProcessing as DP

from Utils import Opath
from CreateDateFile import CreateFichierDatesReg
import ClassificationN as CL
import RandomSelectionInsitu_LV as RSi
import moduleLog_hpc as ML
from Sensors import Spot4
from Sensors import Landsat8
from Sensors import Landsat5
from Sensors import Sentinel_2
from Sensors import Formosat
from config import Config
import fileUtils as fu
import shutil

def PreProcessS2(config,tileFolder,workingDirectory):

	cfg = Config(args.config)
	struct = cfg.Sentinel_2.arbo
	outputPath = Config(file(config)).chain.outputPath
	projOut = Config(file(config)).GlobChain.proj
	projOut = projOut.split(":")[-1]
	arbomask = Config(file(config)).Sentinel_2.arbomask
	cloud = Config(file(config)).Sentinel_2.nuages
	sat = Config(file(config)).Sentinel_2.saturation
	div = Config(file(config)).Sentinel_2.div
	cloud_reproj = Config(file(config)).Sentinel_2.nuages_reproj
	sat_reproj = Config(file(config)).Sentinel_2.saturation_reproj
	div_reproj = Config(file(config)).Sentinel_2.div_reproj
	"""
	B5 = fu.fileSearchRegEx(tileFolder+"/"+struct+"/*FRE_B5.tif")
	B6 = fu.fileSearchRegEx(tileFolder+"/"+struct+"/*FRE_B6.tif")
	B7 = fu.fileSearchRegEx(tileFolder+"/"+struct+"/*FRE_B7.tif")
	B8A = fu.fileSearchRegEx(tileFolder+"/"+struct+"/*FRE_B8A.tif")
	B11 = fu.fileSearchRegEx(tileFolder+"/"+struct+"/*FRE_B11.tif")
	B12 = fu.fileSearchRegEx(tileFolder+"/"+struct+"/*FRE_B12.tif")

	AllBands = B5+B6+B7+B8A+B11+B12#AllBands to resample
	"""
	#Resample
	"""
	for band in AllBands:
		folder = "/".join(band.split("/")[0:len(band.split("/"))-1])
		pathOut = folder
		nameOut = band.split("/")[-1].replace(".tif","_10M.tif")
		if workingDirectory: #HPC 
			pathOut = workingDirectory
		cmd = "otbcli_RigidTransformResample -in "+band+" -out "+pathOut+"/"+nameOut+" int16 -transform.type.id.scalex 2 -transform.type.id.scaley 2 -interpolator bco -interpolator.bco.radius 2"
		if not os.path.exists(folder+"/"+nameOut):
			print cmd
			os.system(cmd)
			if workingDirectory: #HPC
				shutil.copy(pathOut+"/"+nameOut,folder+"/"+nameOut)
	"""
	
	
	#Datas reprojection and buid stack
	dates = os.listdir(tileFolder)
	for date in dates:

		#Masks reprojection
		AllCloud = fu.FileSearch_AND(tileFolder+"/"+date,True,cloud)
		AllSat = fu.FileSearch_AND(tileFolder+"/"+date,True,sat)
		AllDiv = fu.FileSearch_AND(tileFolder+"/"+date,True,div)

		for Ccloud,Csat,Cdiv in zip(AllCloud,AllSat,AllDiv):
			cloudProj = fu.getRasterProjectionEPSG(Ccloud)
			satProj = fu.getRasterProjectionEPSG(Csat)
			divProj = fu.getRasterProjectionEPSG(Cdiv)
			if cloudProj != int(projOut):
				outFolder = os.path.split(Ccloud)[0]
				cloudOut = os.path.split(Ccloud)[1].replace(cloud,cloud_reproj)
				tmpInfo = outFolder+"/ImgInfo.txt"
				spx,spy = fu.getGroundSpacing(Ccloud,tmpInfo)
				cmd = 'gdalwarp -tr '+spx+' '+spx+' -s_srs "EPSG:'+str(cloudProj)+'" -t_srs "EPSG:'+str(projOut)+'" '+Ccloud+' '+workingDirectory+"/"+cloudOut
				if not os.path.exists(outFolder+"/"+cloudOut):
					print cmd
					os.system(cmd)
					print outFolder+"/"+cloudOut
					shutil.copy(workingDirectory+"/"+cloudOut,outFolder+"/"+cloudOut)

			if satProj != int(projOut):
				outFolder = os.path.split(Csat)[0]
				satOut = os.path.split(Csat)[1].replace(sat,sat_reproj)
				tmpInfo = outFolder+"/ImgInfo.txt"
				spx,spy = fu.getGroundSpacing(Csat,tmpInfo)
				cmd = 'gdalwarp -tr '+spx+' '+spx+' -s_srs "EPSG:'+str(cloudProj)+'" -t_srs "EPSG:'+str(projOut)+'" '+Csat+' '+workingDirectory+"/"+satOut
				if not os.path.exists(outFolder+"/"+satOut):
					print cmd
					os.system(cmd)
					shutil.copy(workingDirectory+"/"+satOut,outFolder+"/"+satOut)

			if divProj != int(projOut):
				outFolder = os.path.split(Cdiv)[0]
				tmpInfo = outFolder+"/ImgInfo.txt"
				divOut = os.path.split(Cdiv)[1].replace(div,div_reproj)
				
				reverse = workingDirectory+"/"+divOut.replace(".tif","_reverse.tif")
				spx,spy = fu.getGroundSpacing(Cdiv,tmpInfo)

				if not os.path.exists(outFolder+"/"+divOut):
					cmd = 'otbcli_BandMath -il '+Cdiv+' -out '+reverse+' -exp "im1b1==0?1:0"'
					print cmd 
					os.system(cmd)

					cmd = 'gdalwarp -tr '+spx+' '+spx+' -s_srs "EPSG:'+str(cloudProj)+'" -t_srs "EPSG:'+str(projOut)+'" '+reverse+' '+workingDirectory+"/"+divOut
					print cmd
					os.system(cmd)
					shutil.copy(workingDirectory+"/"+divOut,outFolder+"/"+divOut)

		#B2 = fu.fileSearchRegEx(tileFolder+"/"+date+"/"+date+"/*FRE_B2.tif")[0]

		B3 = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B3.tif")[0]
		B4 = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B4.tif")[0]

		#B5 = fu.fileSearchRegEx(tileFolder+"/"+date+"/"+date+"/*FRE_B5_10M.tif")[0]
		#B6 = fu.fileSearchRegEx(tileFolder+"/"+date+"/"+date+"/*FRE_B6_10M.tif")[0]
		#B7 = fu.fileSearchRegEx(tileFolder+"/"+date+"/"+date+"/*FRE_B7_10M.tif")[0]

		B8 = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B8.tif")[0]

		#B8A = fu.fileSearchRegEx(tileFolder+"/"+date+"/"+date+"/*FRE_B8A_10M.tif")[0]
		#B11 = fu.fileSearchRegEx(tileFolder+"/"+date+"/"+date+"/*FRE_B11_10M.tif")[0]
		#B12 = fu.fileSearchRegEx(tileFolder+"/"+date+"/"+date+"/*FRE_B12_10M.tif")[0]
		#listBands = B2+" "+B3+" "+B4+" "+B5+" "+B6+" "+B7+" "+B8+" "+B8A+" "+B11+" "+B12
		listBands = B3+" "+B4+" "+B8
		currentProj = fu.getRasterProjectionEPSG(B3)
		stackName = "_".join(B3.split("/")[-1].split("_")[0:7])+"_STACK.tif"
		stackNameProjIN = "_".join(B3.split("/")[-1].split("_")[0:7])+"_STACK_EPSG"+str(currentProj)+".tif"
		if os.path.exists(tileFolder+"/"+date+"/"+stackName):
			stackProj = fu.getRasterProjectionEPSG(tileFolder+"/"+date+"/"+stackName)
			if stackProj != int(projOut):
				tmpInfo = tileFolder+"/"+date+"/ImgInfo.txt"
				spx,spy = fu.getGroundSpacing(tileFolder+"/"+date+"/"+stackName,tmpInfo)
				cmd = 'gdalwarp -tr '+spx+' '+spx+' -s_srs "EPSG:'+str(stackProj)+'" -t_srs "EPSG:'+str(projOut)+'" '+tileFolder+"/"+date+"/"+stackName+' '+workingDirectory+"/"+stackName
				print cmd
				os.system(cmd)
				os.remove(tileFolder+"/"+date+"/"+stackName)
				shutil.copy(workingDirectory+"/"+stackName,tileFolder+"/"+date+"/"+stackName)
		else:
			cmd = "otbcli_ConcatenateImages -il "+listBands+" -out "+workingDirectory+"/"+stackNameProjIN
			print cmd
			os.system(cmd)
			tmpInfo = workingDirectory+"/ImgInfo.txt"
			spx,spy = fu.getGroundSpacing(workingDirectory+"/"+stackNameProjIN,tmpInfo)
			cmd = 'gdalwarp -tr '+spx+' '+spx+' -s_srs "EPSG:'+str(currentProj)+'" -t_srs "EPSG:'+str(projOut)+'" '+workingDirectory+"/"+stackNameProjIN+' '+workingDirectory+"/"+stackName
			print cmd
			os.system(cmd)

			shutil.copy(workingDirectory+"/"+stackName,tileFolder+"/"+date+"/"+stackName)

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
                            help="Landsat Image path", default = None)

    parser.add_argument("-iS",dest="ipathS4",action="store",\
                            help="Spot Image path",default = None)

    parser.add_argument("-iL5", dest="ipathL5", action="store", \
                            help="Landsat5 Image path", default = None)

    parser.add_argument("-iS2", dest="ipathS2", action="store", \
                            help="Sentinel2 Image path", default = None)

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

    parser.add_argument("--db_S2", dest="dateB_S2", action="store",\
                            help="Date for begin regular grid", required = False, default = None)
    
    parser.add_argument("--de_S2", dest="dateE_S2", action="store",\
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
listIndices = sorted(listIndices)
nbLook = cfg.GlobChain.nbLook
batchProcessing = cfg.GlobChain.batchProcessing

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

if not ("None" in args.ipathS2):
    PreProcessS2(args.config,args.ipathS2,args.opath)#resample if needed
    Sentinel2 = Sentinel_2(args.ipathS2,opath,fconf,workRes)
    datesVoulues = CreateFichierDatesReg(args.dateB_S2,args.dateE_S2,args.gap,opath.opathT,Sentinel2.name)
    Sentinel2.setDatesVoulues(datesVoulues)
	
    list_Sensor.append(Sentinel2)

imRef = list_Sensor[0].imRef
sensorRef = list_Sensor[0].name


StackName = fu.getFeatStackName(args.config)
Stack = args.wOut+"/Final/"+StackName
print "-----------------------"
print Stack
print "-----------------------"
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
            
	
	if batchProcessing == 'False':
		Step = log.update(Step)

		if os.path.exists(args.wOut+"/tmp"):
			os.system("rm -rf "+args.opath+"/tmp/*")
			os.system("rm -r "+args.opath+"/Final")
			for sensor in list_Sensor:
				os.system("cp "+args.wOut+"/tmp/"+sensor.serieTempGap+" "+args.opath+"/tmp")
				os.system("cp "+args.wOut+"/tmp/DatesInterpReg"+str(sensor.name)+".txt "+args.opath+"/tmp")
			os.system("cp -R "+args.wOut+"/Final "+args.opath)
			os.system("rm -r "+args.wOut+"/tmp")
			os.system("rm -r "+args.wOut+"/Final")
		deb = time.time()
		for sensor in list_Sensor:
	  	  #get possible features
	  	  feat_sensor = []
	  	  for d in listIndices:
	    		if d in sensor.indices:
				feat_sensor.append(d)
	  	  print feat_sensor
	   	  DP.FeatureExtraction(sensor,datesVoulues,opath.opathT,feat_sensor)

		if len(listIndices)>=1:
			seriePrim = DP.ConcatenateFeatures(opath,listIndices)
		serieRefl = DP.OrderGapFSeries(opath,list_Sensor,opath.opathT)

		if len(listIndices)>=1:
			CL.ConcatenateAllData(opath.opathF,args.config,args.opath,args.wOut,serieRefl+" "+seriePrim)
		fin = time.time()
		print "Temps de production des primitives (NO BATCH) : "+str(fin-deb)
	

	
	else: #be careful about bands order in case of multi sensor gapfilling, different from no batchProcessing mode
		'''
		Example with 2 sensors : S1, S2
		
		NO batchProcessing
			Reflectances S1
			Reflectances S2
			Features S1
			Features S2
		batchProcessing
			Reflectances S1
			Features S1
			Reflectances S2
			Features S2
		'''
		for sensor in list_Sensor:
			red = str(sensor.bands["BANDS"]["red"])
			nir = str(sensor.bands["BANDS"]["NIR"])
			swir = str(sensor.bands["BANDS"]["SWIR"])
			comp = str(len(sensor.bands["BANDS"].keys()))
			serieTempGap = sensor.serieTempGap
			outputFeatures = args.opath+"/Features_"+sensor.name+".tif"
			cmd = "otbcli_iota2FeatureExtraction -in "+serieTempGap+" -out "+outputFeatures+" int16 -comp "+comp+" -red "+red+" -nir "+nir+" -swir "+swir
			print cmd
			deb = time.time()
			os.system(cmd)
			fin = time.time()
			print "Temps de production des primitives (BATCH) : "+str(fin-deb)
		
		AllFeatures = fu.FileSearch_AND(args.opath,True,"Features",".tif")
		if len(AllFeatures)==1:
			if not os.path.exists(args.wOut+"/Final/"):
				os.system("mkdir "+args.wOut+"/Final/")
			shutil.copy(AllFeatures[0],Stack)
		elif len(AllFeatures)>1:
			AllFeatures = " ".join(AllFeatures)
			cmd = "otbcli_ConcatenateImages -il "+AllFeatures+" -out "+args.opath+"/Final/"+StackName
			print cmd 
			os.system(cmd)
		else:
			raise Exception("No features detected")
	
	os.system("cp -R "+args.opath+"/Final "+args.wOut)
	os.system("mkdir "+args.wOut+"/tmp")
	
	for sensor in list_Sensor:
		os.system("cp "+args.opath+"/tmp/"+str(sensor.name)+"_ST_REFL_GAP.tif "+args.wOut+"/tmp")
		os.system("cp "+args.opath+"/tmp/DatesInterpReg"+str(sensor.name)+".txt "+args.wOut+"/tmp")
	
	os.system("cp "+args.opath+"/tmp/MaskCommunSL.tif "+args.wOut)
	os.system("cp "+args.opath+"/tmp/MaskCommunSL.shp "+args.wOut)
	os.system("cp "+args.opath+"/tmp/MaskCommunSL.shx "+args.wOut)
	os.system("cp "+args.opath+"/tmp/MaskCommunSL.dbf "+args.wOut)
	os.system("cp "+args.opath+"/tmp/MaskCommunSL.prj "+args.wOut)

	
	Mask = fu.FileSearch_AND(args.opath+"/tmp",True,"_ST_MASK.tif")
	for maskPath in Mask:
		shutil.copy(maskPath,args.wOut)












	
	


