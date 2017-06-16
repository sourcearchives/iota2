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

import os,sys,argparse,shutil
from Sensors import Landsat8
from Sensors import Landsat5
from Sensors import Sentinel_2
from config import Config
from Utils import Opath
from CreateDateFile import CreateFichierDatesReg
import New_DataProcessing as DP

def PreProcessS2(config,tileFolder,workingDirectory):

    cfg = Config(args.config)
    struct = cfg.Sentinel_2.arbo
    outputPath = Config(file(config)).chain.outputPath
    outRes = Config(file(config)).chain.spatialResolution
    projOut = Config(file(config)).GlobChain.proj
    projOut = projOut.split(":")[-1]
    arbomask = Config(file(config)).Sentinel_2.arbomask
    cloud = Config(file(config)).Sentinel_2.nuages
    sat = Config(file(config)).Sentinel_2.saturation
    div = Config(file(config)).Sentinel_2.div
    cloud_reproj = Config(file(config)).Sentinel_2.nuages_reproj
    sat_reproj = Config(file(config)).Sentinel_2.saturation_reproj
    div_reproj = Config(file(config)).Sentinel_2.div_reproj

    needReproj = False
    B5 = fu.fileSearchRegEx(tileFolder+"/"+struct+"/*FRE_B5*.tif")
    B6 = fu.fileSearchRegEx(tileFolder+"/"+struct+"/*FRE_B6*.tif")
    B7 = fu.fileSearchRegEx(tileFolder+"/"+struct+"/*FRE_B7*.tif")
    B8A = fu.fileSearchRegEx(tileFolder+"/"+struct+"/*FRE_B8A*.tif")
    B11 = fu.fileSearchRegEx(tileFolder+"/"+struct+"/*FRE_B11*.tif")
    B12 = fu.fileSearchRegEx(tileFolder+"/"+struct+"/*FRE_B12*.tif")

    AllBands = B5+B6+B7+B8A+B11+B12#AllBands to resample
    #Resample
    for band in AllBands:
	x,y = fu.getRasterResolution(band)
        folder = "/".join(band.split("/")[0:len(band.split("/"))-1])
        pathOut = folder
        nameOut = band.split("/")[-1].replace(".tif","_10M.tif")
        if workingDirectory: #HPC
            pathOut = workingDirectory
        cmd = "otbcli_RigidTransformResample -in "+band+" -out "+pathOut+"/"+nameOut+\
              " int16 -transform.type.id.scalex 2 -transform.type.id.scaley 2 -interpolator bco -interpolator.bco.radius 2"
	if str(x)!=str(outRes):needReproj = True
        if str(x)!=str(outRes) and not os.path.exists(folder+"/"+nameOut) and not "10M_10M.tif" in nameOut:
            print cmd
            os.system(cmd)
            if workingDirectory: #HPC
                shutil.copy(pathOut+"/"+nameOut,folder+"/"+nameOut)
		os.remove(pathOut+"/"+nameOut)
    
    #Datas reprojection and buid stack
    dates = os.listdir(tileFolder)
    for date in dates:
	print date
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
                cloudOut = os.path.split(Ccloud)[1].replace(".tif","_reproj.tif")
                tmpInfo = outFolder+"/ImgInfo.txt"
                spx,spy = fu.getRasterResolution(Ccloud)
                cmd = 'gdalwarp -wo INIT_DEST=0 -tr '+str(spx)+' '+str(spx)+' -s_srs "EPSG:'\
                      +str(cloudProj)+'" -t_srs "EPSG:'+str(projOut)+'" '+Ccloud+' '+workingDirectory+"/"+cloudOut
                if not os.path.exists(outFolder+"/"+cloudOut):
                    print cmd
                    os.system(cmd)
                    print outFolder+"/"+cloudOut
                    shutil.copy(workingDirectory+"/"+cloudOut,outFolder+"/"+cloudOut)

            if satProj != int(projOut):
                outFolder = os.path.split(Csat)[0]
                satOut = os.path.split(Csat)[1].replace(".tif","_reproj.tif")
                tmpInfo = outFolder+"/ImgInfo.txt"
                spx,spy = fu.getRasterResolution(Csat)
                cmd = 'gdalwarp -wo INIT_DEST=0 -tr '+str(spx)+' '+str(spx)+' -s_srs "EPSG:'+str(cloudProj)+\
                      '" -t_srs "EPSG:'+str(projOut)+'" '+Csat+' '+workingDirectory+"/"+satOut
                if not os.path.exists(outFolder+"/"+satOut):
                    print cmd
                    os.system(cmd)
                    shutil.copy(workingDirectory+"/"+satOut,outFolder+"/"+satOut)

            if divProj != int(projOut):
                outFolder = os.path.split(Cdiv)[0]
                tmpInfo = outFolder+"/ImgInfo.txt"
                divOut = os.path.split(Cdiv)[1].replace(".tif","_reproj.tif")

                reverse = workingDirectory+"/"+divOut.replace(".tif","_reverse.tif")
                spx,spy = fu.getRasterResolution(Cdiv)

                if not os.path.exists(outFolder+"/"+divOut):
                    #cmd = 'otbcli_BandMath -il '+Cdiv+' -out '+reverse+' -exp "im1b1==0?1:0"'
                    #print cmd
                    #os.system(cmd)

                    cmd = 'gdalwarp -wo INIT_DEST=1 -tr '+str(spx)+' '+str(spx)+' -s_srs "EPSG:'\
                          +str(cloudProj)+'" -t_srs "EPSG:'+str(projOut)+'" '+Cdiv+' '+workingDirectory+"/"+divOut
                    print cmd
                    os.system(cmd)
                    shutil.copy(workingDirectory+"/"+divOut,outFolder+"/"+divOut)
	

	####################################

        B2 = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B2*.tif")[0]
        B3 = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B3*.tif")[0]
        B4 = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B4*.tif")[0]
        B5 = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B5_*.tif")[0]
        B6 = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B6_*.tif")[0]
        B7 = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B7_*.tif")[0]
        B8 = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B8*.tif")[0]
        B8A = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B8A_*.tif")[0]
        B11 = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B11_*.tif")[0]
        B12 = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B12_*.tif")[0]
	
	if needReproj:
		B5 = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B5*_10M.tif")[0]
		B6 = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B6*_10M.tif")[0]
		B7 = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B7*_10M.tif")[0]
		B8 = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B8.tif")[0]
		B8A = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B8A*_10M.tif")[0]
		B11 = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B11*_10M.tif")[0]
		B12 = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B12*_10M.tif")[0]
        listBands = B2+" "+B3+" "+B4+" "+B5+" "+B6+" "+B7+" "+B8+" "+B8A+" "+B11+" "+B12
        #listBands = B3+" "+B4+" "+B8
	print listBands
        currentProj = fu.getRasterProjectionEPSG(B3)
        stackName = "_".join(B3.split("/")[-1].split("_")[0:7])+"_STACK.tif"
        stackNameProjIN = "_".join(B3.split("/")[-1].split("_")[0:7])+"_STACK_EPSG"+str(currentProj)+".tif"
        if os.path.exists(tileFolder+"/"+date+"/"+stackName):
            stackProj = fu.getRasterProjectionEPSG(tileFolder+"/"+date+"/"+stackName)
            if int(stackProj) != int(projOut):
		print "stack proj : "+str(stackProj)+" outproj : "+str(projOut)
                tmpInfo = tileFolder+"/"+date+"/ImgInfo.txt"
                spx,spy = fu.getGroundSpacing(tileFolder+"/"+date+"/"+stackName,tmpInfo)
                cmd = 'gdalwarp -tr '+str(spx)+' '+str(spx)+' -s_srs "EPSG:'+str(stackProj)+'" -t_srs "EPSG:'\
                      +str(projOut)+'" '+tileFolder+"/"+date+"/"+stackName+' '+workingDirectory+"/"+stackName
                print cmd
                os.system(cmd)
                os.remove(tileFolder+"/"+date+"/"+stackName)
                shutil.copy(workingDirectory+"/"+stackName,tileFolder+"/"+date+"/"+stackName)
		os.remove(workingDirectory+"/"+stackName)
        else:

            cmd = "otbcli_ConcatenateImages -il "+listBands+" -out "+workingDirectory+"/"+stackNameProjIN+" int16"
            print cmd
            os.system(cmd)
	    currentProj = fu.getRasterProjectionEPSG(workingDirectory+"/"+stackNameProjIN)
            tmpInfo = workingDirectory+"/ImgInfo.txt"
            spx,spy = fu.getRasterResolution(workingDirectory+"/"+stackNameProjIN)
	    if str(currentProj) == str(projOut):
		shutil.copy(workingDirectory+"/"+stackNameProjIN,tileFolder+"/"+date+"/"+stackName)
		os.remove(workingDirectory+"/"+stackNameProjIN)
	    else :
                cmd = 'gdalwarp -tr '+str(spx)+' '+str(spx)+' -s_srs "EPSG:'+str(currentProj)+'" -t_srs "EPSG:'\
                      +str(projOut)+'" '+workingDirectory+"/"+stackNameProjIN+' '+workingDirectory+"/"+stackName
                print cmd
                os.system(cmd)
            	shutil.copy(workingDirectory+"/"+stackName,tileFolder+"/"+date+"/"+stackName)
	
	#######################

def generateStack(configPath,outputDirectory,ipathL5=None,ipathL8=None,\
                  ipathS2=None,dateB_L5=None,dateE_L5=None,dateB_L8=None,\
                  dateE_L8=None,dateB_S2=None,dateE_S2=None,gapL5=None,\
                  gapL8=None,gapS2=None,writeOutput=False,workingDirectory=None):

    if not os.path.exists (configPath): raise Exception("'"+configPath+"' does not exists")
    print "features generation using '%s' configuration file"%(configPath)

    sensors_ask = []
    outputDirectory = Opath(outputDirectory)
    
    if ipathL5 :
        L5res = Config(file(configPath)).Landsat5.nativeRes
        landsat5 = Landsat5(ipathL5,outputDirectory,configPath,L5res)
        if not (dateB_L5 and dateE_L5 and gapL5):
            raise Exception("missing parameters")
        datesVoulues = CreateFichierDatesReg(dateB_L5,dateE_L5,gapL5,outputDirectory.opathT,landsat5.name)
        landsat5.setDatesVoulues(datesVoulues)
        sensors_ask.append(landsat5)

    if ipathL8 :
        L8res = Config(file(configPath)).Landsat8.nativeRes
        landsat8 = Landsat8(ipathL8,outputDirectory,configPath,L8res)
        if not (dateB_L8 and dateE_L8 and gapL8):
            raise Exception("missing parameters")
        datesVoulues = CreateFichierDatesReg(dateB_L8,dateE_L8,gapL8,outputDirectory.opathT,landsat8.name)
        landsat8.setDatesVoulues(datesVoulues)
        sensors_ask.append(landsat8)    

    if ipathS2 :
        PreProcessS2(configPath,ipathS2,workingDirectory)
        S2res = Config(file(configPath)).Sentinel_2.nativeRes
        Sentinel2 = Sentinel_2(ipathS2,outputDirectory,configPath,S2res)
        if not (dateB_S2 and dateE_S2 and gapS2):
            raise Exception("missing parameters")
        datesVoulues = CreateFichierDatesReg(dateB_S2,dateE_S2,gapS2,outputDirectory.opathT,Sentinel2.name)
        Sentinel2.setDatesVoulues(datesVoulues)
        sensors_ask.append(Sentinel2)

    imRef = sensors_ask[0].imRef
    borderMasks = [sensor.CreateBorderMask_bindings(outputDirectory,imRef,1,wMode=writeOutput) for sensor in sensors_ask]
    for borderMask,a,b in borderMasks :
        if writeOutput : borderMask.ExecuteAndWriteOutput()
        else : borderMask.Execute()
    
    DP.CreateCommonZone_bindings(outputDirectory.opathT,borderMasks,True)

    masksSeries = [sensor.createMaskSeries_bindings(outputDirectory.opathT,wMode=writeOutput) for sensor in sensors_ask]
    temporalSeries = [sensor.createSerie_bindings(outputDirectory.opathT) for sensor in sensors_ask]

    return temporalSeries,masksSeries

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "")
    
    parser.add_argument("-iL5", dest="ipathL5", action="store",\
                        help="Landsat5 Image path", default = None,required=False)
    parser.add_argument("-iL8", dest="ipathL8", action="store",\
                        help="Landsat8 Image path", default = None,required=False)
    parser.add_argument("-iS2", dest="ipathS2", action="store",\
                        help="Sentinel-2 Image path", default = None,required=False)

    parser.add_argument("-db_L8", dest="dateB_L8", action="store",\
                        help="Date for begin regular grid", required = False, default = None)
    parser.add_argument("-de_L8", dest="dateE_L8", action="store",\
                        help="Date for end regular grid", required = False, default = None)
    parser.add_argument("-db_L5", dest="dateB_L5", action="store",\
                        help="Date for begin regular grid", required = False, default = None)
    parser.add_argument("-de_L5", dest="dateE_L5", action="store",\
                        help="Date for end regular grid", required = False, default = None)
    parser.add_argument("-db_S2", dest="dateB_S2", action="store",\
                        help="Date for begin regular grid", required = False, default = None)
    parser.add_argument("-de_S2", dest="dateE_S2", action="store",\
                        help="Date for end regular grid", required = False, default = None)

    parser.add_argument("-gapL5",dest="gapL5", action="store",\
                        help="Date gap between two L5's images in days",default=None,required=False)
    parser.add_argument("-gapL8",dest="gapL8", action="store",\
                        help="Date gap between two L8's images in days",default=None,required=False)
    parser.add_argument("-gapS2",dest="gapS2", action="store",\
                        help="Date gap between two S2's images in days",default=None,required=False)

    parser.add_argument("-config",dest = "configPath",\
                        help ="path to the configuration file",default=None,required=True)
    parser.add_argument("-writeOutput",dest="writeOutput",help ="write outputs on disk or return otb object",\
                        default="False",required=False,choices = ["True","False"])
    parser.add_argument("-outputDirectory",dest = "outputDirectory",\
                        help ="output Directory",default=None,required=True)
    parser.add_argument("-workingDirectory",dest = "workingDirectory",\
                        help ="working directory",default=None,required=False)


    args = parser.parse_args()
    generateStack(args.configPath,args.outputDirectory,args.ipathL5,\
                  args.ipathL8,args.ipathS2,args.dateB_L5,args.dateE_L5,\
                  args.dateB_L8,args.dateE_L8,args.dateB_S2,args.dateE_S2,\
                  args.gapL5,args.gapL8,args.gapS2,args.writeOutput,args.workingDirectory)
	
