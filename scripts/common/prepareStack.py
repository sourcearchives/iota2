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

import os,sys,argparse,shutil,ast
from Sensors import Landsat8
from Sensors import Landsat5
from Sensors import Sentinel_2
from config import Config
from Utils import Opath, run
from CreateDateFile import CreateFichierDatesReg
import New_DataProcessing as DP
import fileUtils as fu


def copy_inputs_sensors_data(folder_to_copy, workingDirectory,
                             data_dir_name="sensors_data"):
    """
    IN
    folder_to_copy [strubg] : path to the directory containing input data ex:
                              /XXX/X/XXX/TTT
                              where TTT must be the tile's name ex "T31TCJ" or "Landsat8_D0005H0002"
    """

    from shutil import copytree, ignore_patterns
    import time
    tile = os.path.split(folder_to_copy)[-1]
    data_sens_path = os.path.join(workingDirectory, data_dir_name)

    try:
        os.mkdir(data_sens_path)
    except:
        print(data_sens_path + "allready exists")

    output_dir = os.path.join(data_sens_path, tile)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    copy_start = time.time()
    shutil.copytree(folder_to_copy,
                    output_dir,
                    ignore=ignore_patterns('*FRE_B*.tif', '*R1.tif'))
    copy_end = time.time()
    print ("copy time : " + str(copy_end - copy_start) + " seconds")
    return output_dir


def PreProcessS2(config,tileFolder,workingDirectory):

    cfg = Config(config)
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
            run(cmd)
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
                if not workingDirectory:
                    wDir = outFolder
                else:
                    wDir = workingDirectory
                cmd = 'gdalwarp -wo INIT_DEST=0 -tr '+str(spx)+' '+str(spx)+' -s_srs "EPSG:'\
                      +str(cloudProj)+'" -t_srs "EPSG:'+str(projOut)+'" '+Ccloud+' '+wDir+"/"+cloudOut
                if not os.path.exists(outFolder+"/"+cloudOut):
                    run(cmd)
                    print outFolder+"/"+cloudOut
                    if workingDirectory:
                        shutil.copy(workingDirectory+"/"+cloudOut,outFolder+"/"+cloudOut)

            if satProj != int(projOut):
                outFolder = os.path.split(Csat)[0]
                satOut = os.path.split(Csat)[1].replace(".tif","_reproj.tif")
                tmpInfo = outFolder+"/ImgInfo.txt"
                spx,spy = fu.getRasterResolution(Csat)
                if not workingDirectory:
                    wDir = outFolder
                else:
                    wDir = workingDirectory
                cmd = 'gdalwarp -wo INIT_DEST=0 -tr '+str(spx)+' '+str(spx)+' -s_srs "EPSG:'+str(cloudProj)+\
                      '" -t_srs "EPSG:'+str(projOut)+'" '+Csat+' '+wDir+"/"+satOut
                if not os.path.exists(outFolder+"/"+satOut):

                    run(cmd)
                    if workingDirectory:
                        shutil.copy(workingDirectory+"/"+satOut,outFolder+"/"+satOut)

            if divProj != int(projOut):
                outFolder = os.path.split(Cdiv)[0]
                tmpInfo = outFolder+"/ImgInfo.txt"
                divOut = os.path.split(Cdiv)[1].replace(".tif","_reproj.tif")
                spx,spy = fu.getRasterResolution(Cdiv)
                if not workingDirectory:
                    wDir = outFolder
                else:
                    wDir = workingDirectory
                reverse = wDir+"/"+divOut.replace(".tif","_reverse.tif")
                if not os.path.exists(outFolder+"/"+divOut):

                    #cmd = 'otbcli_BandMath -il '+Cdiv+' -out '+reverse+' -exp "im1b1==0?1:0"'
                    #run(cmd)

                    cmd = 'gdalwarp -wo INIT_DEST=1 -tr '+str(spx)+' '+str(spx)+' -s_srs "EPSG:'\
                          +str(cloudProj)+'" -t_srs "EPSG:'+str(projOut)+'" '+Cdiv+' '+wDir+"/"+divOut
                    run(cmd)
                    if workingDirectory:
                        shutil.copy(workingDirectory+"/"+divOut,outFolder+"/"+divOut)

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
        print listBands
        currentProj = fu.getRasterProjectionEPSG(B3)
        stackName = "_".join(B3.split("/")[-1].split("_")[0:7])+"_STACK.tif"
        stackNameProjIN = "_".join(B3.split("/")[-1].split("_")[0:7])+"_STACK_EPSG"+str(currentProj)+".tif"
        
        if not workingDirectory:
            outputFolder = tileFolder+"/"+date+"/"
        else:
            outputFolder = workingDirectory

        if os.path.exists(tileFolder+"/"+date+"/"+stackName):
            stackProj = fu.getRasterProjectionEPSG(tileFolder+"/"+date+"/"+stackName)
            if int(stackProj) != int(projOut):
                print "stack proj : "+str(stackProj)+" outproj : "+str(projOut)
                tmpInfo = tileFolder+"/"+date+"/ImgInfo.txt"
                spx,spy = fu.getGroundSpacing(tileFolder+"/"+date+"/"+stackName,tmpInfo)
                cmd = 'gdalwarp -tr '+str(spx)+' '+str(spx)+' -s_srs "EPSG:'+str(stackProj)+'" -t_srs "EPSG:'\
                    +str(projOut)+'" '+tileFolder+"/"+date+"/"+stackName+' '+outputFolder+"/"+stackName
                run(cmd)

                os.remove(tileFolder+"/"+date+"/"+stackName)
                if workingDirectory:
                    shutil.copy(outputFolder+"/"+stackName,tileFolder+"/"+date+"/"+stackName)
                    os.remove(outputFolder+"/"+stackName)
        else:
            cmd = "otbcli_ConcatenateImages -il "+listBands+" -out "+outputFolder+"/"+stackNameProjIN+" int16"
            run(cmd)
            currentProj = fu.getRasterProjectionEPSG(outputFolder+"/"+stackNameProjIN)
            tmpInfo = outputFolder+"/ImgInfo.txt"
            spx,spy = fu.getRasterResolution(outputFolder+"/"+stackNameProjIN)

            if str(currentProj) == str(projOut):
                shutil.copy(outputFolder+"/"+stackNameProjIN,tileFolder+"/"+date+"/"+stackName)
                os.remove(outputFolder+"/"+stackNameProjIN)
            else :
                cmd = 'gdalwarp -tr '+str(spx)+' '+str(spx)+' -s_srs "EPSG:'+str(currentProj)+'" -t_srs "EPSG:'\
                        +str(projOut)+'" '+outputFolder+"/"+stackNameProjIN+' '+outputFolder+"/"+stackName
                run(cmd)
                os.remove(outputFolder+"/"+stackNameProjIN)
                if workingDirectory:
                    shutil.copy(outputFolder+"/"+stackName,tileFolder+"/"+date+"/"+stackName)

def generateStack(tile,cfg,outputDirectory,writeOutput=False,
                  workingDirectory=None,
                  testMode=False,testSensorData=None, enable_Copy=False,):
    import Sensors
    import serviceConfigFile as SCF
    if writeOutput == "False":
        writeOutput = False
    if not isinstance(cfg,SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)
    if outputDirectory and not os.path.exists(outputDirectory) and not testMode:
        os.mkdir(outputDirectory)
    if not os.path.exists (cfg.pathConf):
        raise Exception("'"+cfg.pathConf+"' does not exists")
    print "features generation using '%s' configuration file"%(cfg.pathConf)

    ipathL5 = cfg.getParam('chain', 'L5Path')
    if ipathL5 == "None":
        ipathL5 = None
    ipathL8 = cfg.getParam('chain', 'L8Path')
    if ipathL8 == "None":
        ipathL8 = None
    ipathS2 = cfg.getParam('chain', 'S2Path')
    if ipathS2 == "None":
        ipathS2 = None
    autoDate = ast.literal_eval(cfg.getParam('GlobChain', 'autoDate'))
    gapL5 = cfg.getParam('Landsat5', 'temporalResolution')
    gapL8 = cfg.getParam('Landsat8', 'temporalResolution')
    gapS2 = cfg.getParam('Sentinel_2', 'temporalResolution')
    tiles = cfg.getParam('chain', 'listTile').split(" ")
    if testMode:
        ipathL8 = testSensorData
    dateB_L5 = dateE_L5 = dateB_L8 = dateE_L8 = dateB_S2 = dateE_S2 = None
    if ipathL5:
        dateB_L5, dateE_L5 = fu.getDateL5(ipathL5, tiles)
    if not autoDate:
        dateB_L5 = cfg.getParam('Landsat5', 'startDate')
        dateE_L5 = cfg.getParam('Landsat5', 'endDate')
    if ipathL8:
        dateB_L8, dateE_L8 = fu.getDateL8(ipathL8, tiles)
        if not autoDate:
            dateB_L8 = cfg.getParam('Landsat8', 'startDate')
            dateE_L8 = cfg.getParam('Landsat8', 'endDate')
    if ipathS2:
        dateB_S2, dateE_S2 = fu.getDateS2(ipathS2, tiles)
        if not autoDate:
            dateB_S2 = cfg.getParam('Sentinel_2', 'startDate')
            dateE_S2 = cfg.getParam('Sentinel_2', 'endDate')

    sensors_ask = []
    realDates = []
    interpDates = []
    if workingDirectory : wDir = workingDirectory
    else : wDir = outputDirectory
    wDir = Opath(wDir)
    
    S2 = Sensors.Sentinel_2("", Opath("", create=False), cfg.pathConf, "", createFolder=None)
    L8 = Sensors.Landsat8("", Opath("", create=False), cfg.pathConf, "", createFolder=None)
    L5 = Sensors.Landsat5("", Opath("", create=False), cfg.pathConf, "", createFolder=None)
    SensorsList = [S2, L8, L5]
    
    if ipathL5 :
        ipathL5=ipathL5+"/Landsat5_"+tile
        L5res = cfg.getParam('Landsat5', 'nativeRes')
        if "TMPDIR" in os.environ and enable_Copy==True:
            ipathL5 = copy_inputs_sensors_data(folder_to_copy=ipathL5,
                                               workingDirectory=os.environ["TMPDIR"],
                                               data_dir_name="sensors_data")

        landsat5 = Landsat5(ipathL5,wDir, cfg.pathConf,L5res)
        if not (dateB_L5 and dateE_L5 and gapL5):
            raise Exception("missing parameters")
        datesVoulues = CreateFichierDatesReg(dateB_L5,dateE_L5,gapL5,wDir.opathT,landsat5.name)
        landsat5.setDatesVoulues(datesVoulues)
        interpDates.append(datesVoulues)
        realDates.append(landsat5.fdates)
        sensors_ask.append(landsat5)

    if ipathL8 :
        ipathL8=ipathL8+"/Landsat8_"+tile
        L8res = cfg.getParam('Landsat8', 'nativeRes')
        if "TMPDIR" in os.environ and enable_Copy==True:
            ipathL8 = copy_inputs_sensors_data(folder_to_copy=ipathL8,
                                               workingDirectory=os.environ["TMPDIR"],
                                               data_dir_name="sensors_data")
        landsat8 = Landsat8(ipathL8,wDir, cfg.pathConf,L8res)
        if not (dateB_L8 and dateE_L8 and gapL8):
            raise Exception("missing parameters")
        datesVoulues = CreateFichierDatesReg(dateB_L8,dateE_L8,gapL8,wDir.opathT,landsat8.name)
        landsat8.setDatesVoulues(datesVoulues)
        interpDates.append(datesVoulues)
        realDates.append(landsat8.fdates)
        sensors_ask.append(landsat8)    

    if ipathS2 :
        ipathS2=ipathS2+"/"+tile
        PreProcessS2(cfg.pathConf,ipathS2,workingDirectory)
        if "TMPDIR" in os.environ and enable_Copy==True:
            ipathS2 = copy_inputs_sensors_data(folder_to_copy=ipathS2,
                                               workingDirectory=os.environ["TMPDIR"],
                                               data_dir_name="sensors_data")

        S2res = cfg.getParam('Sentinel_2', 'nativeRes')
        Sentinel2 = Sentinel_2(ipathS2,wDir, cfg.pathConf,S2res)
        if not (dateB_S2 and dateE_S2 and gapS2):
            raise Exception("missing parameters")
        datesVoulues = CreateFichierDatesReg(dateB_S2,dateE_S2,gapS2,wDir.opathT,Sentinel2.name)
        Sentinel2.setDatesVoulues(datesVoulues)
        interpDates.append(datesVoulues)
        realDates.append(Sentinel2.fdates)
        sensors_ask.append(Sentinel2)
    imRef = sensors_ask[0].imRef
    borderMasks = [sensor.CreateBorderMask_bindings(wDir,imRef,1,wMode=writeOutput) for sensor in sensors_ask]
    for borderMask,a,b in borderMasks :
        if writeOutput : borderMask.ExecuteAndWriteOutput()
        else : borderMask.Execute()
    
    commonRasterMask = DP.CreateCommonZone_bindings(wDir.opathT,borderMasks,True)
    masksSeries = [sensor.createMaskSeries_bindings(wDir.opathT,wMode=writeOutput) for sensor in sensors_ask]
    temporalSeries = [sensor.createSerie_bindings(wDir.opathT) for sensor in sensors_ask]
    if workingDirectory:
        if outputDirectory and not os.path.exists(outputDirectory+"/tmp"):

            try:
                os.mkdir(outputDirectory+"/tmp")
            except:
                print outputDirectory+"/tmp"+" allready exists"

        if outputDirectory and not os.path.exists(outputDirectory+"/tmp/"+os.path.split(commonRasterMask)[-1]):
            shutil.copy(commonRasterMask,outputDirectory+"/tmp")
            fu.cpShapeFile(commonRasterMask.replace(".tif",""),outputDirectory+"/tmp",
                           [".prj",".shp",".dbf",".shx"],spe=True)
    return temporalSeries,masksSeries,interpDates,realDates,commonRasterMask

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "")

    parser.add_argument("-config", dest="configPath",
                        help="path to the configuration file",
                        default=None, required=True)
                        
    parser.add_argument("-writeOutput", dest="writeOutput",
                        help="write outputs on disk or return otb object",
                        default="False", required=False, choices = ["True", "False"])

    parser.add_argument("-outputDirectory", dest="outputDirectory",
                        help ="output Directory", default=None, required=True)

    parser.add_argument("-workingDirectory", dest="workingDirectory",
                        help ="working directory", default=None, required=False)

    parser.add_argument("-tile", dest="tile",
                        help ="current tile to compute", default=None, required=True)


    args = parser.parse_args()
    generateStack(args.tile, args.configPath, args.outputDirectory,
                  args.writeOutput, args.workingDirectory)
	
