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
from Sensors import Sentinel_2_S2C
from config import Config
from Utils import Opath, run
from CreateDateFile import CreateFichierDatesReg
import New_DataProcessing as DP
import fileUtils as fu
import logging
import time
logger = logging.getLogger(__name__)


def copy_inputs_sensors_data(folder_to_copy, workingDirectory,
                             data_dir_name="sensors_data", logger=logger):
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
        logger.debug(data_sens_path + "allready exists")


    output_dir = os.path.join(data_sens_path, tile)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    copy_start = time.time()
    shutil.copytree(folder_to_copy,
                    output_dir,
                    ignore=ignore_patterns('*FRE_B*.tif', '*R1.tif'))
    copy_end = time.time()
    logger.debug("copy time : " + str(copy_end - copy_start) + " seconds")
    return output_dir


def PreProcessS2_S2C(cfg, ipathS2_S2C, workingDirectory, logger=logger):
    """ usage : preprocess sen2cor images to be usable by IOTA2
                extract masks...
    """
    
    def reproj_raster(raster_stack, outproj, workingDirectory=None):
        """ use to reproject sen2cor S2 STACK
        
        issue : 
            output height and width may not respect raster_stack extent due to 
            interpolation
        """
        from gdal import Warp
        import shutil
        current_proj = fu.getRasterProjectionEPSG(raster_stack)
        if not current_proj == outproj:
            reproj_out_dir, raster_stack_name = os.path.split(raster_stack)
            reproj_out_name = raster_stack_name.replace(".tif", "_reproj.tif")
            reproj_output = os.path.join(reproj_out_dir, reproj_out_name)
            if workingDirectory:
                reproj_output = os.path.join(workingDirectory, reproj_out_name)
            #reproj is done thanks to gdal.Warp()
            ds = Warp(reproj_output, raster_stack,
                      multithread=True, format="GTiff", xRes=10, yRes=10,
                      srcSRS="EPSG:{}".format(current_proj), dstSRS="EPSG:{}".format(outproj),
                      options=["INIT_DEST=0"])
            os.remove(raster_stack)
            shutil.move(reproj_output, raster_stack)

    def check_bands_dates(s2c_bands_dates, logger=logger):
        """ use to check if all bands contains the same dates
        
        Args :
            s2c_bands_dates [dict of dict]
                print s2c_bands_dates["BandName"]["date"]
                > /path/to/MySentinel-2_Sen2Cor_Band_Date.jp2
        
        OUTPUT :
            True if all bands contains the same dates, else False
        """
        nb_bands = 10

        dates = [date for band, date_img in s2c_bands_dates.items() for date in date_img.keys()]
        dates_unique = set(dates)
        
        date_ap = [dates.count(date_u) for date_u in dates_unique]

        if not date_ap.count(date_ap[0]) == len(date_ap):
            error_msg = "some dates in sen2cor sensor are missing"
            logger.error(error_msg)
            raise Exception(error_msg)

    def stack_dates(s2c_bands_dates, outproj, workingDirectory):
        """ usage : stack all bands into a raster
            
            Args :
            s2c_bands_dates [dict of dict]
                print s2c_bands_dates["BandName"]["date"]
                > /path/to/MySentinel-2_Sen2Cor_Band_Date.jp2
            outproj [string] : output projection
            workingDirectory [string] working directory
        """
        import otbApplication as otb
        import otbAppli as otbApp
        
        #get all dates
        s2c_dates = s2c_bands_dates[s2c_bands_dates.keys()[0]].keys()
        
        #for each date concatenates bands
        for s2c_date in s2c_dates:
            concatenate = otb.Registry.CreateApplication("ConcatenateImages")
            concatenate_out_dir, B2_name = os.path.split(s2c_bands_dates["B2"][s2c_date])
            concatenate_out_name = B2_name.replace("B02", "STACK").replace(".jp2", ".tif")
            concatenate_output = os.path.join(concatenate_out_dir, concatenate_out_name)
            if workingDirectory:
                concatenate_output = os.path.join(workingDirectory, concatenate_out_name)

            concatenate.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint16)
            B2 = s2c_bands_dates["B2"][s2c_date]
            B3 = s2c_bands_dates["B3"][s2c_date]
            B4 = s2c_bands_dates["B4"][s2c_date]
            B8 = s2c_bands_dates["B8"][s2c_date]
            B5 = otbApp.CreateRigidTransformResampleApplication({"in":s2c_bands_dates["B5"][s2c_date],
                                                                 "pixType" : "int16",
                                                                 "transform.type.id.scalex": "2",
                                                                 "transform.type.id.scaley": "2",
                                                                 "interpolator": "bco",
                                                                 "interpolator.bco.radius":"2"})
            B5.Execute()
            B6 = otbApp.CreateRigidTransformResampleApplication({"in":s2c_bands_dates["B6"][s2c_date],
                                                                 "pixType" : "int16",
                                                                 "transform.type.id.scalex": "2",
                                                                 "transform.type.id.scaley": "2",
                                                                 "interpolator": "bco",
                                                                 "interpolator.bco.radius":"2"})
            B6.Execute()
            B7 = otbApp.CreateRigidTransformResampleApplication({"in":s2c_bands_dates["B7"][s2c_date],
                                                                 "pixType" : "int16",
                                                                 "transform.type.id.scalex": "2",
                                                                 "transform.type.id.scaley": "2",
                                                                 "interpolator": "bco",
                                                                 "interpolator.bco.radius":"2"})
            B7.Execute()
            B8A = otbApp.CreateRigidTransformResampleApplication({"in":s2c_bands_dates["B8A"][s2c_date],
                                                                 "pixType" : "int16",
                                                                 "transform.type.id.scalex": "2",
                                                                 "transform.type.id.scaley": "2",
                                                                 "interpolator": "bco",
                                                                 "interpolator.bco.radius":"2"})
            B8A.Execute()
            B11 = otbApp.CreateRigidTransformResampleApplication({"in":s2c_bands_dates["B11"][s2c_date],
                                                                 "pixType" : "int16",
                                                                 "transform.type.id.scalex": "2",
                                                                 "transform.type.id.scaley": "2",
                                                                 "interpolator": "bco",
                                                                 "interpolator.bco.radius":"2"})
            B11.Execute()
            B12 = otbApp.CreateRigidTransformResampleApplication({"in":s2c_bands_dates["B12"][s2c_date],
                                                                 "pixType" : "int16",
                                                                 "transform.type.id.scalex": "2",
                                                                 "transform.type.id.scaley": "2",
                                                                 "interpolator": "bco",
                                                                 "interpolator.bco.radius":"2"})
            B12.Execute()

            concatenate.AddParameterStringList("il", B2)
            concatenate.AddParameterStringList("il", B3)
            concatenate.AddParameterStringList("il", B4)
            concatenate.AddImageToParameterInputImageList("il",
                                                          B5.GetParameterOutputImage("out"))
            concatenate.AddImageToParameterInputImageList("il",
                                                          B6.GetParameterOutputImage("out"))
            concatenate.AddImageToParameterInputImageList("il",
                                                          B7.GetParameterOutputImage("out"))
            concatenate.AddParameterStringList("il", B8)
            concatenate.AddImageToParameterInputImageList("il",
                                                          B8A.GetParameterOutputImage("out"))
            concatenate.AddImageToParameterInputImageList("il",
                                                          B11.GetParameterOutputImage("out"))
            concatenate.AddImageToParameterInputImageList("il",
                                                          B12.GetParameterOutputImage("out"))

            concatenate.SetParameterString("out", concatenate_output)
            if not os.path.exists(os.path.join(concatenate_out_dir, concatenate_out_name)):
                concatenate.ExecuteAndWriteOutput()
                reproj_raster(concatenate_output, outproj)
                if workingDirectory:
                    shutil.copy(concatenate_output, concatenate_out_dir)
            else:
                reproj_raster(os.path.join(concatenate_out_dir, concatenate_out_name),
                              outproj, workingDirectory)

    def extract_SCL_masks(ipathS2_S2C, outproj, workingDirectory):
        """usage : build masks from SCL images
                   SCL : image's description
                   http://step.esa.int/thirdparties/sen2cor/2.5.5/docs/S2-PDGS-MPC-L2A-PDD-V2.5.5.pdf 
        """
        import otbAppli as otbApp
        NODATA_flag = 0
        #pixels to interpolate
        invalid_flags = [0, 1, 3, 8, 9, 10]
        raster_border_name = "nodata_10m.tif"
        raster_invalid_name = "invalid_10m.tif"

        SCL_dates = fu.FileSearch_AND(ipathS2_S2C, True, "SCL_20m.jp2")
        for SCL in SCL_dates:
            R20_directory, SCL_name = os.path.split(SCL)
            IMG_DATA_dir = os.path.normpath(R20_directory).split(os.sep)[0:-1:1]
            R10_directory = os.sep.join(IMG_DATA_dir + ["R10m"])
            SCL_10m_app = otbApp.CreateRigidTransformResampleApplication({"in": SCL,
                                                                          "pixType" : "uint8",
                                                                          "transform.type.id.scalex": "2",
                                                                          "transform.type.id.scaley": "2",
                                                                          "interpolator": "nn"})
            SCL_10m_app.Execute()
            masks = []

            #border MASK            
            border_name = SCL_name.replace("SCL_20m.jp2", raster_border_name)
            border_output = os.path.join(R10_directory, border_name)
            if workingDirectory:
                border_output = os.path.join(workingDirectory, border_name)
            border_app = otbApp.CreateBandMathApplication({"il": SCL_10m_app,
                                                           "exp": "im1b1=={}?0:1".format(NODATA_flag),
                                                           "out": border_output,
                                                           "pixType" : "uint8"})
            if not os.path.exists(os.path.join(R10_directory, border_name)):
                border_app.ExecuteAndWriteOutput()
                reproj_raster(border_output, outproj, workingDirectory)
                masks.append(border_output)
            else:
                reproj_raster(os.path.join(R10_directory, border_name), outproj, workingDirectory)
            
            #invalid MASK
            invalid_name = SCL_name.replace("SCL_20m.jp2", raster_invalid_name)
            invalid_output = os.path.join(R10_directory, invalid_name)
            if workingDirectory:
                invalid_output = os.path.join(workingDirectory, invalid_name)
            invalid_expr = " or ".join(["im1b1=={}".format(flag) for flag in invalid_flags])
            invalid_app = otbApp.CreateBandMathApplication({"il": SCL_10m_app,
                                                           "exp": "{}?0:1".format(invalid_expr),
                                                           "out": invalid_output,
                                                           "pixType" : "uint8"})
            if not os.path.exists(os.path.join(R10_directory, invalid_name)):
                invalid_app.ExecuteAndWriteOutput()
                reproj_raster(invalid_output, outproj, workingDirectory)
                masks.append(invalid_output)
            else:
                reproj_raster(os.path.join(R10_directory, invalid_name), outproj, workingDirectory)

            #cp data
            if workingDirectory:
                for mask in masks:
                    shutil.copy(mask, R10_directory)
                    os.remove(mask)



    outproj = cfg.getParam("GlobChain", "proj")
    outproj = outproj.split(":")[-1]
    
    from Sensors import Sentinel_2_S2C
    #dummy object
    sen2cor_s2 = Sentinel_2_S2C("_", "_", "_", "_")

    #get 20m images
    B5 = fu.FileSearch_AND(ipathS2_S2C, True, "B05_20m.jp2")
    B6 = fu.FileSearch_AND(ipathS2_S2C, True, "B06_20m.jp2")
    B7 = fu.FileSearch_AND(ipathS2_S2C, True, "B07_20m.jp2")
    B8A = fu.FileSearch_AND(ipathS2_S2C, True, "B8A_20m.jp2")
    B11 = fu.FileSearch_AND(ipathS2_S2C, True, "B11_20m.jp2")
    B12 = fu.FileSearch_AND(ipathS2_S2C, True, "B12_20m.jp2")

    #get 10m  images
    B2 = fu.FileSearch_AND(ipathS2_S2C, True, "B02_10m.jp2")
    B3 = fu.FileSearch_AND(ipathS2_S2C, True, "B03_10m.jp2")
    B4 = fu.FileSearch_AND(ipathS2_S2C, True, "B04_10m.jp2")
    B8 = fu.FileSearch_AND(ipathS2_S2C, True, "B08_10m.jp2")

    #s2c_bands_dates[band][date] : image
    s2c_bands_dates = {}

    #init python dictionary
    s2c_bands_dates["B5"] = {}
    s2c_bands_dates["B6"] = {}
    s2c_bands_dates["B7"] = {}
    s2c_bands_dates["B8"] = {}
    s2c_bands_dates["B8A"] = {}
    s2c_bands_dates["B11"] = {}
    s2c_bands_dates["B12"] = {}
    s2c_bands_dates["B2"] = {}
    s2c_bands_dates["B3"] = {}
    s2c_bands_dates["B4"] = {}
    s2c_bands_dates["B8"] = {}

    #fill-up python dictionary
    for img in B5:
        s2c_bands_dates["B5"][sen2cor_s2.getDateFromName(img, complete_date=True)] = img
    for img in B6:
        s2c_bands_dates["B6"][sen2cor_s2.getDateFromName(img, complete_date=True)] = img
    for img in B7:
        s2c_bands_dates["B7"][sen2cor_s2.getDateFromName(img, complete_date=True)] = img
    for img in B8A:
        s2c_bands_dates["B8A"][sen2cor_s2.getDateFromName(img, complete_date=True)] = img
    for img in B11:
        s2c_bands_dates["B11"][sen2cor_s2.getDateFromName(img, complete_date=True)] = img
    for img in B12:
        s2c_bands_dates["B12"][sen2cor_s2.getDateFromName(img, complete_date=True)] = img
    for img in B2:
        s2c_bands_dates["B2"][sen2cor_s2.getDateFromName(img, complete_date=True)] = img
    for img in B3:
        s2c_bands_dates["B3"][sen2cor_s2.getDateFromName(img, complete_date=True)] = img
    for img in B4:
        s2c_bands_dates["B4"][sen2cor_s2.getDateFromName(img, complete_date=True)] = img
    for img in B8:
        s2c_bands_dates["B8"][sen2cor_s2.getDateFromName(img, complete_date=True)] = img

    #check if all bands are found for each date
    check_bands_dates(s2c_bands_dates)

    #Write stack by dates
    stack_dates(s2c_bands_dates, outproj, workingDirectory)

    #masks
    extract_SCL_masks(ipathS2_S2C, outproj, workingDirectory)

    


def PreProcessS2(config, tileFolder, workingDirectory, logger=logger):

    logger = logging.getLogger(__name__)

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

    TMPDIR = workingDirectory
    AllBands = B5+B6+B7+B8A+B11+B12#AllBands to resample
    
    TMPDIR = workingDirectory
    #Resample
    for band in AllBands:
        x,y = fu.getRasterResolution(band)
        folder = "/".join(band.split("/")[0:len(band.split("/"))-1])
        pathOut = folder
        nameOut = band.split("/")[-1].replace(".tif","_10M.tif")
        if TMPDIR: #HPC
            pathOut = workingDirectory
        cmd = "otbcli_RigidTransformResample -in "+band+" -out "+pathOut+"/"+nameOut+\
              " int16 -transform.type.id.scalex 2 -transform.type.id.scaley 2 -interpolator bco -interpolator.bco.radius 2"
        if str(x)!=str(outRes):needReproj = True
        if str(x)!=str(outRes) and not os.path.exists(folder+"/"+nameOut) and not "10M_10M.tif" in nameOut:
            run(cmd,'[Preprocessing S2] Upsampling band {} to highest resolution'.format(band))
            if workingDirectory: #HPC
                shutil.copy(pathOut+"/"+nameOut,folder+"/"+nameOut)
                os.remove(pathOut+"/"+nameOut)
    
    #Datas reprojection and buid stack
    dates = os.listdir(tileFolder)
    for date in dates:
        logging.debug('PreProcessS2(): processing date {}'.format(date))
        
        #Masks reprojection
        AllCloud = fu.FileSearch_AND(tileFolder+"/"+date,True,cloud)
        AllSat = fu.FileSearch_AND(tileFolder+"/"+date,True,sat)
        AllDiv = fu.FileSearch_AND(tileFolder+"/"+date,True,div)

        for Ccloud,Csat,Cdiv in zip(AllCloud,AllSat,AllDiv):
            cloudProj = fu.getRasterProjectionEPSG(Ccloud)
            satProj = fu.getRasterProjectionEPSG(Csat)
            divProj = fu.getRasterProjectionEPSG(Cdiv)
            
            cloudOut = os.path.split(Ccloud)[1].replace(".tif","_reproj.tif")
            if cloudProj != int(projOut):
                outFolder = os.path.split(Ccloud)[0]
                if not TMPDIR:
                    workingDirectory = outFolder
                tmpInfo = outFolder+"/ImgInfo.txt"
                spx,spy = fu.getRasterResolution(Ccloud)
                if not TMPDIR:
                    wDir = outFolder
                else:
                    wDir = workingDirectory
                cmd = 'gdalwarp -wo INIT_DEST=0 -tr '+str(spx)+' '+str(spx)+' -s_srs "EPSG:'\
                      +str(cloudProj)+'" -t_srs "EPSG:'+str(projOut)+'" '+Ccloud+' '+wDir+"/"+cloudOut
                if not os.path.exists(outFolder+"/"+cloudOut):
                    run(cmd,desc='[Preprocessing S2] Reprojecting cloud mask of date {} to output projection ({})'.format(date,projOut))
                    if TMPDIR:
                        shutil.copy(workingDirectory+"/"+cloudOut,outFolder+"/"+cloudOut)
            else:
                shutil.copy(Ccloud, cloudOut)

            satOut = os.path.split(Csat)[1].replace(".tif","_reproj.tif")
            if satProj != int(projOut):
                outFolder = os.path.split(Csat)[0]
                if not TMPDIR:
                    workingDirectory = outFolder
                
                tmpInfo = outFolder+"/ImgInfo.txt"
                spx,spy = fu.getRasterResolution(Csat)
                if not TMPDIR:
                    wDir = outFolder
                else:
                    wDir = workingDirectory
                cmd = 'gdalwarp -wo INIT_DEST=0 -tr '+str(spx)+' '+str(spx)+' -s_srs "EPSG:'+str(cloudProj)+\
                      '" -t_srs "EPSG:'+str(projOut)+'" '+Csat+' '+wDir+"/"+satOut
                if not os.path.exists(outFolder+"/"+satOut):
                    run(cmd,desc='[Preprocessing S2] Reprojecting image of date {} to output projection ({})'.format(date,projOut))
                    if TMPDIR:
                        shutil.copy(workingDirectory+"/"+satOut,outFolder+"/"+satOut)
            else:
                shutil.copy(Csat, satOut)

            divOut = os.path.split(Cdiv)[1].replace(".tif","_reproj.tif")
            if divProj != int(projOut):
                outFolder = os.path.split(Cdiv)[0]
                if not TMPDIR:
                    workingDirectory = outFolder
                tmpInfo = outFolder+"/ImgInfo.txt"
                
                spx,spy = fu.getRasterResolution(Cdiv)
                if not TMPDIR:
                    wDir = outFolder
                else:
                    wDir = workingDirectory
                reverse = wDir+"/"+divOut.replace(".tif","_reverse.tif")
                if not os.path.exists(outFolder+"/"+divOut):
                    cmd = 'gdalwarp -wo INIT_DEST=1 -tr '+str(spx)+' '+str(spx)+' -s_srs "EPSG:'\
                          +str(cloudProj)+'" -t_srs "EPSG:'+str(projOut)+'" '+Cdiv+' '+wDir+"/"+divOut
                    run(cmd,desc='[Preprocessing S2] Reprojecting div of date {} to output projection ({})'.format(date,projOut))
                    if TMPDIR:
                        shutil.copy(workingDirectory+"/"+divOut,outFolder+"/"+divOut)
            else:
                shutil.copy(Cdiv, divOut)

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
        #print listBands
        currentProj = fu.getRasterProjectionEPSG(B3)
        stackName = "_".join(B3.split("/")[-1].split("_")[0:7])+"_STACK.tif"
        stackNameProjIN = "_".join(B3.split("/")[-1].split("_")[0:7])+"_STACK_EPSG"+str(currentProj)+".tif"

        logger.debug("Bands used to create : %s are %s"%(tileFolder+"/"+date+"/"+stackName, listBands))
        if not TMPDIR:
            outputFolder = tileFolder+"/"+date+"/"
        else:
            outputFolder = workingDirectory

        if os.path.exists(tileFolder+"/"+date+"/"+stackName):
            stackProj = fu.getRasterProjectionEPSG(tileFolder+"/"+date+"/"+stackName)
            if int(stackProj) != int(projOut):
                #print "stack proj : "+str(stackProj)+" outproj : "+str(projOut)
                tmpInfo = tileFolder+"/"+date+"/ImgInfo.txt"
                spx,spy = fu.getGroundSpacing(tileFolder+"/"+date+"/"+stackName,tmpInfo)
                cmd = 'gdalwarp -tr '+str(spx)+' '+str(spx)+' -s_srs "EPSG:'+str(stackProj)+'" -t_srs "EPSG:'\
                    +str(projOut)+'" '+tileFolder+"/"+date+"/"+stackName+' '+outputFolder+"/"+stackName
                run(cmd,desc='[Preprocessing S2] Reprojecting stack of date {} to output projection ({})'.format(date,projOut))

                os.remove(tileFolder+"/"+date+"/"+stackName)
                if TMPDIR:
                    shutil.copy(outputFolder+"/"+stackName,tileFolder+"/"+date+"/"+stackName)
                    os.remove(outputFolder+"/"+stackName)
        else:
            cmd = "otbcli_ConcatenateImages -il "+listBands+" -out "+outputFolder+"/"+stackNameProjIN+" int16"
            run(cmd,'[Preprocessing S2] Concatenating all bands for date {}'.format(date))
            currentProj = fu.getRasterProjectionEPSG(outputFolder+"/"+stackNameProjIN)
            tmpInfo = outputFolder+"/ImgInfo.txt"
            spx,spy = fu.getRasterResolution(outputFolder+"/"+stackNameProjIN)

            if str(currentProj) == str(projOut):
                shutil.copy(outputFolder+"/"+stackNameProjIN,tileFolder+"/"+date+"/"+stackName)
                os.remove(outputFolder+"/"+stackNameProjIN)
            else :
                cmd = 'gdalwarp -tr '+str(spx)+' '+str(spx)+' -s_srs "EPSG:'+str(currentProj)+'" -t_srs "EPSG:'\
                        +str(projOut)+'" '+outputFolder+"/"+stackNameProjIN+' '+outputFolder+"/"+stackName
                run(cmd,desc='[Preprocessing S2] Reprojecting stack of date {} to output projection ({})'.format(date,projOut))
                os.remove(outputFolder+"/"+stackNameProjIN)
                if TMPDIR:
                    shutil.copy(outputFolder+"/"+stackName,tileFolder+"/"+date+"/"+stackName)


def generateStack(tile, cfg, outputDirectory, writeOutput=False,
                  workingDirectory=None,
                  testMode=False, testSensorData=None, enable_Copy=False,
                  logger=logger):

    logger.info("prepare sensor's stack for tile : " + tile)

    import Sensors
    import serviceConfigFile as SCF
    if writeOutput == "False":
        writeOutput = False
    if not isinstance(cfg,SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)
    if outputDirectory and not os.path.exists(outputDirectory) and not testMode:
        try:
            os.mkdir(outputDirectory)
        except OSError:
            logger.warning(outputDirectory + "allready exists")
    if not os.path.exists (cfg.pathConf):
        raise Exception("'"+cfg.pathConf+"' does not exists")
    logger.info("features generation using '%s' configuration file"%(cfg.pathConf))

    ipathL5 = cfg.getParam('chain', 'L5Path')
    if ipathL5 == "None":
        ipathL5 = None
    ipathL8 = cfg.getParam('chain', 'L8Path')
    if ipathL8 == "None":
        ipathL8 = None
    ipathS2 = cfg.getParam('chain', 'S2Path')
    if ipathS2 == "None":
        ipathS2 = None
    ipathS2_S2C = cfg.getParam('chain', 'S2_S2C_Path')
    if ipathS2_S2C == "None":
        ipathS2_S2C = None
    autoDate = cfg.getParam('GlobChain', 'autoDate')
    gapL5 = str(cfg.getParam('Landsat5', 'temporalResolution'))
    gapL8 = str(cfg.getParam('Landsat8', 'temporalResolution'))
    gapS2 = str(cfg.getParam('Sentinel_2', 'temporalResolution'))
    gapS2_S2C = str(cfg.getParam('Sentinel_2_S2C', 'temporalResolution'))
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
    if ipathS2_S2C:
        dateB_S2_S2C, dateE_S2_S2C = fu.getDateS2_S2C(ipathS2_S2C, tiles)
        if not autoDate:
            dateB_S2_S2C = cfg.getParam('Sentinel_2_S2C', 'startDate')
            dateE_S2_S2C = cfg.getParam('Sentinel_2_S2C', 'endDate')

    sensors_ask = []
    realDates = []
    interpDates = []
    if workingDirectory:
        wDir = workingDirectory
    else:
        wDir = outputDirectory
    wDir = Opath(wDir)

    enable_Copy = False

    if ipathL5 :
        ipathL5=ipathL5+"/Landsat5_"+tile
        L5res = cfg.getParam('Landsat5', 'nativeRes')
        if "TMPDIR" in os.environ and enable_Copy==True:
            ipathL5 = copy_inputs_sensors_data(folder_to_copy=ipathL5,
                                               workingDirectory=os.environ["TMPDIR"],
                                               data_dir_name="sensors_data", logger=logger)

        landsat5 = Landsat5(ipathL5,wDir, cfg.pathConf,L5res)
        if not os.path.exists(os.path.join(outputDirectory, "tmp")):
            try:
                os.mkdir(os.path.join(outputDirectory, "tmp"))
            except OSError:
                logger.warning(os.path.join(outputDirectory, "tmp"))
        inputDatesL5 = landsat5.setInputDatesFile(os.path.join(outputDirectory, "tmp"))
        if not (dateB_L5 and dateE_L5 and gapL5):
            raise Exception("missing parameters")
        datesVoulues = CreateFichierDatesReg(dateB_L5, dateE_L5, gapL5,
                                             os.path.join(outputDirectory, "tmp"),
                                             landsat5.name)
        landsat5.setDatesVoulues(datesVoulues)
        interpDates.append(datesVoulues)
        realDates.append(inputDatesL5)
        sensors_ask.append(landsat5)

    if ipathL8 :
        ipathL8=ipathL8+"/Landsat8_"+tile
        L8res = cfg.getParam('Landsat8', 'nativeRes')
        if "TMPDIR" in os.environ and enable_Copy==True:
            ipathL8 = copy_inputs_sensors_data(folder_to_copy=ipathL8,
                                               workingDirectory=os.environ["TMPDIR"],
                                               data_dir_name="sensors_data", logger=logger)

        landsat8 = Landsat8(ipathL8,wDir, cfg.pathConf,L8res)
        if not os.path.exists(os.path.join(outputDirectory, "tmp")):
            try:
                os.mkdir(os.path.join(outputDirectory, "tmp"))
            except OSError:
                logger.warning(os.path.join(outputDirectory, "tmp"))
        inputDatesL8 = landsat8.setInputDatesFile(os.path.join(outputDirectory, "tmp"))
        if not (dateB_L8 and dateE_L8 and gapL8):
            raise Exception("missing parameters")
        datesVoulues = CreateFichierDatesReg(dateB_L8, dateE_L8, gapL8,
                                             os.path.join(outputDirectory, "tmp"),
                                             landsat8.name)
        landsat8.setDatesVoulues(datesVoulues)
        interpDates.append(datesVoulues)
        realDates.append(inputDatesL8)
        sensors_ask.append(landsat8)    

    if ipathS2 :
        ipathS2=ipathS2+"/"+tile
        PreProcessS2(cfg.pathConf,ipathS2,workingDirectory)
        
        #if TMPDIR -> copy inputs to TMPDIR and change input path
        if "TMPDIR" in os.environ and enable_Copy==True:
            ipathS2 = copy_inputs_sensors_data(folder_to_copy=ipathS2,
                                               workingDirectory=os.environ["TMPDIR"],
                                               data_dir_name="sensors_data", logger=logger)

        S2res = 10
        Sentinel2 = Sentinel_2(ipathS2,wDir, cfg.pathConf, S2res)
        if not os.path.exists(os.path.join(outputDirectory, "tmp")):
            try:
                os.mkdir(os.path.join(outputDirectory, "tmp"))
            except OSError:
                logger.warning(os.path.join(outputDirectory, "tmp"))
        inputDatesS2 = Sentinel2.setInputDatesFile(os.path.join(outputDirectory, "tmp"))
        if not (dateB_S2 and dateE_S2 and gapS2):
            raise Exception("missing parameters")
        datesVoulues = CreateFichierDatesReg(dateB_S2, dateE_S2, gapS2,
                                             os.path.join(outputDirectory, "tmp"),
                                             Sentinel2.name)
        Sentinel2.setDatesVoulues(datesVoulues)
        interpDates.append(datesVoulues)
        realDates.append(inputDatesS2)
        sensors_ask.append(Sentinel2)
    
    if ipathS2_S2C :
        ipathS2_S2C = os.path.join(ipathS2_S2C, tile)
        PreProcessS2_S2C(cfg, ipathS2_S2C, workingDirectory)
        if "TMPDIR" in os.environ and enable_Copy==True:
            ipathS2_S2C = copy_inputs_sensors_data(folder_to_copy=ipathS2_S2C,
                                                   workingDirectory=os.environ["TMPDIR"],
                                                   data_dir_name="sensors_data", logger=logger)

        S2res = 10
        Sentinel2_S2C = Sentinel_2_S2C(ipathS2_S2C, wDir, cfg.pathConf, S2res)
        if not os.path.exists(os.path.join(outputDirectory, "tmp")):
            try:
                os.mkdir(os.path.join(outputDirectory, "tmp"))
            except OSError:
                logger.warning(os.path.join(outputDirectory, "tmp"))
        inputDatesS2_S2C = Sentinel2_S2C.setInputDatesFile(os.path.join(outputDirectory, "tmp"))
        if not (dateB_S2_S2C and dateE_S2_S2C and gapS2_S2C):
            raise Exception("missing parameters")
        datesVoulues = CreateFichierDatesReg(dateB_S2_S2C, dateE_S2_S2C, gapS2_S2C,
                                             os.path.join(outputDirectory, "tmp"),
                                             Sentinel2_S2C.name)
        
        Sentinel2_S2C.setDatesVoulues(datesVoulues)
        interpDates.append(datesVoulues)
        realDates.append(inputDatesS2_S2C)
        sensors_ask.append(Sentinel2_S2C)

    borderMasks = [sensor.CreateBorderMask_bindings(wDir, wMode=writeOutput) for sensor in sensors_ask]

    for borderMask,a,b in borderMasks :
        if writeOutput:
            borderMask.ExecuteAndWriteOutput()
        else:
            borderMask.Execute()

    commonRasterMask = DP.CreateCommonZone_bindings(os.path.join(outputDirectory, "tmp"), borderMasks)
    masksSeries = [sensor.createMaskSeries_bindings(wDir.opathT, commonRasterMask, wMode=writeOutput) for sensor in sensors_ask]
    temporalSeries = [sensor.createSerie_bindings(wDir.opathT) for sensor in sensors_ask]

    if workingDirectory:
        if outputDirectory and not os.path.exists(outputDirectory+"/tmp"):
            try:
                os.mkdir(outputDirectory+"/tmp")
            except:
                print outputDirectory+"/tmp"+" allready exists"

        if outputDirectory and not os.path.exists(outputDirectory+"/tmp/"+os.path.split(commonRasterMask)[-1]):            
            shutil.copy(commonRasterMask, outputDirectory+"/tmp")
            fu.cpShapeFile(commonRasterMask.replace(".tif",""),outputDirectory+"/tmp",
                           [".prj",".shp",".dbf",".shx"],spe=True)
                           
    
    return temporalSeries, masksSeries, interpDates, realDates, commonRasterMask

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
	
