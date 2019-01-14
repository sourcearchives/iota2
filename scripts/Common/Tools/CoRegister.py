#!/usr/bin/python
# -*- coding: utf-8 -*-

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
import argparse
import ast
import os
import sys
import shutil
import logging
import glob
from datetime import date
from osgeo import gdal
from osgeo import osr
from config import Config
from Common import OtbAppBank
from Common import FileUtils as fu
from Common import ServiceConfigFile as SCF

logger = logging.getLogger("CoRegister.py")
streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)

logger.addHandler(streamHandler)


def str2bool(v):
    """
    usage : use in argParse as function to parse options

    IN:
    v [string]
    out [bool]
    """
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def get_S2_Tile_Coverage(file):
    str=''
    with open(file) as f:
        for line in f:
            str+=line
            
    band_str=str.split('<Band_Viewing_Incidence_Angles_Grids_List band_id="B2">')[-1].split('</Band_Viewing_Incidence_Angles_Grids_List>')[0]
    detector_list=[]
    for detector in band_str.split('<Values_List>')[1:]:
        detector = detector.split('</Values_List>')[0]
        tab = []
        for line in detector.split('<VALUES>')[1:]:
            line = line.split('</VALUES>')[0]
            tab.append(line.split(' '))
        detector_list.append(tab)

    res_tab=[]
    H=len(detector_list[0])
    W=len(detector_list[0][0])
    for i in range(0,H):
        for j in range (0,W):
            res=0
            for array in detector_list:
                if res == 0 and array[i][j] != 'NaN':
                    res = 1
            res_tab.append(res)
    coverage_percent = float(sum(res_tab))/float(len(res_tab))
    return coverage_percent

def get_S2_Tile_Cloud_Cover(file):
    with open(file) as f:
        for line in f:
            if 'name="CloudPercent"' in line :
                cloud = float(line.split("</")[0].split('>')[1])
                percent = 1-cloud/100
    return percent

def get_L8_Tile_Cloud_Cover(file):
    with open(file) as f:
        for line in f:
            if 'CLOUD_COVER ' in line :
                cloud = float(line.split(' = ')[1])
                percent = 1-cloud /100
    return percent

def fitnessDateScore(dateVHR, datadir, datatype):
    """ get the date of the best image for the coregistration step

    Parameters
    ----------
    dateVHR : string
        date format YYYYMMDD
    datadir : string
        path to the data directory
    """
    dateVHR=date(int(str(dateVHR)[:4]),int(str(dateVHR)[4:6]),int(str(dateVHR)[6:]))
    fitDate = None
    resultlist = []
    max_pixel = None
    if datatype in ['L5', 'L8'] :
        maxFitScore = None
        for file in glob.glob(datadir+os.sep+'*'+os.sep+'*_MTL.txt'):
            inDate = os.path.basename(file).split("_")[3]
            year = int(inDate[:4])
            month = int(inDate[4:6])
            day = int(inDate[6:8])
            delta = 1 - min(abs((date(year,month,day) - dateVHR).days)/500,1)
            percent = get_L8_Tile_Cloud_Cover(file)
            fitScore = delta*percent
            if maxFitScore < fitScore or maxFitScore is None:
                maxFitScore = fitScore
                fitDate = inDate

    elif datatype in ['S2','S2_S2C']:
        maxFitScore = None
        for file in glob.glob(datadir+os.sep+'*'+os.sep+'*_MTD_ALL.xml'):
            inDate = os.path.basename(file).split("_")[1].split("-")[0]
            year = int(inDate[:4])
            month = int(inDate[4:6])
            day = int(inDate[6:8])
            delta = 1 - min(abs((date(year,month,day) - dateVHR).days)/500,1)
            percent = get_S2_Tile_Cloud_Cover(file)
            cover = get_S2_Tile_Coverage(file)
            fitScore = delta*percent*cover
            if maxFitScore < fitScore or maxFitScore is None:
                maxFitScore = fitScore
                fitDate = inDate
    return fitDate

def launch_coregister(tile, cfg, workingDirectory):
    """ register an image / a time series on a reference image

    Parameters
    ----------
    tile : string
        tile id
    cfg : serviceConfig obj
        configuration object for parameters
    workingDirectory : string
        path to the working directory

    Note
    ------
    This function use the OTB's application **PointMatchCoregistrationModel**,**OrthoRectification** and **SuperImpose**
    more documentation for
    `OrthoRectification <https://www.orfeo-toolbox.org/Applications/OrthoRectification.html>`_
    and
    `SuperImpose <https://www.orfeo-toolbox.org/Applications/Superimpose.html>`_
    """

    from Common import ServiceConfigFile as SCF

    logger.info("Source Raster Registration")
    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    ipathL5 = cfg.getParam('chain', 'L5Path')
    if ipathL5 != "None" and os.path.exists(os.path.join(ipathL5,tile)):
        datadir = os.path.join(ipathL5,tile)
        datatype = 'L5'
        pattern = "ORTHO_SURF_CORR_PENTE*.TIF"
    ipathL8 = cfg.getParam('chain', 'L8Path')
    if ipathL8 != "None" and os.path.exists(os.path.join(ipathL8,tile)):
        datadir = os.path.join(ipathL8,tile)
        datatype = 'L8'
        pattern = "ORTHO_SURF_CORR_PENTE*.TIF"
    ipathS2 = cfg.getParam('chain', 'S2Path')
    if ipathS2 != "None" and os.path.exists(os.path.join(ipathS2,tile)):
        datadir = os.path.join(ipathS2,tile)
        datatype = 'S2'
        pattern = "*STACK.tif"
    ipathS2_S2C = cfg.getParam('chain', 'S2_S2C_Path')
    if ipathS2_S2C != "None" and os.path.exists(os.path.join(ipathS2_S2C,tile)):
        datadir = os.path.join(ipathS2_S2C,tile)
        datatype = 'S2_S2C'
        pattern = "*STACK_10m.tif"

    if cfg.getParam('coregistration', 'pattern') != "None" :
        pattern = cfg.getParam('coregistration', 'pattern')

    inref = os.path.join(cfg.getParam('coregistration', 'VHRPath'))
    datesSrc = cfg.getParam('coregistration', 'dateSrc')
    if datesSrc != "None":
        tiles = cfg.getParam('chain', 'listTile').split(" ")
        tile_ind = tiles.index(tile)
        dateSrc = datesSrc.split(" ")[tile_ind]
        if dateSrc == "None" :
            dateVHR = cfg.getParam('coregistration', 'dateVHR')
            if dateVHR =='None':
                logger.warning("No dateVHR in configuration file, please fill dateVHR value")
            else :
                dateSrc = fitnessDateScore(dateVHR,datadir,datatype)
    else:
        dateVHR = cfg.getParam('coregistration', 'dateVHR')
        if dateVHR =='None':
            logger.warning("No dateVHR in configuration file, please fill dateVHR value")
        else :
            dateSrc = fitnessDateScore(dateVHR,datadir,datatype)
    insrc = glob.glob(os.path.join(datadir,'*'+str(dateSrc)+'*',pattern))[0]
    bandsrc = cfg.getParam('coregistration','bandSrc')
    bandref = cfg.getParam('coregistration','bandRef')
    resample = cfg.getParam('coregistration','resample')
    step = cfg.getParam('coregistration','step')
    minstep = cfg.getParam('coregistration','minstep')
    minsiftpoints = cfg.getParam('coregistration','minsiftpoints')
    iterate = cfg.getParam('coregistration','iterate')
    prec = cfg.getParam('coregistration','prec')
    mode = int(cfg.getParam('coregistration','mode'))
    if workingDirectory != None :
        workingDirectory = os.path.join(workingDirectory, tile)
    
    coregister(insrc, inref, bandsrc, bandref, resample, step, minstep, minsiftpoints, iterate, prec, mode, datadir, pattern, datatype,False,workingDirectory)
    fu.getCommonMasks(tile,cfg)

def coregister(insrc, inref, band, bandref, resample=1, step=256, minstep=16, minsiftpoints=40, iterate=1, prec=3, mode=2, datadir=None, pattern='*STACK.tif', datatype='S2', writeFeatures=False, workingDirectory=None):
    """ register an image / a time series on a reference image

    Parameters
    ----------
    insrc : string
        source raster
    inref : string
        reference raster
    band : int
        band number for the source raster
    bandref : int
        band number for the raster reference raster
    resample : boolean
        resample to reference raster resolution
    step : int
        initial step between the geobins
    minstep : int
        minimal step between the geobins when iterates
    minsiftpoints : int
        minimal number of sift points to perform the registration
    iterate : boolean
        argument to iterate with smaller geobin step to find more sift points
    prec : int
        precision between the source and reference image (in source pixel unit)
    mode : int
        registration mode,
        1 : simple registration ;
        2 : time series registration ;
        3 : time series cascade registration (to do)
    datadir : string
        path to the data directory
    pattern : string
        pattern of the STACK files to register
    writeFeatures : boolean
        argument to keep temporary files

    Note
    ------
    This function use the OTB's application **OrthoRectification** and **SuperImpose**
    more documentation for
    `OrthoRectification <https://www.orfeo-toolbox.org/Applications/OrthoRectification.html>`_
    and
    `SuperImpose <https://www.orfeo-toolbox.org/Applications/Superimpose.html>`_
    """
    pathWd = os.path.dirname(insrc) if not workingDirectory else workingDirectory
    if os.path.exists(pathWd) == False :
        os.path.mkdir(pathWd)

    # #SensorModel generation
    SensorModel = os.path.join(pathWd,'SensorModel.geom')
    PMCMApp = OtbAppBank.CreatePointMatchCoregistrationModel({"in": insrc,
                                                            "band1": band,
                                                            "inref": inref,
                                                            "bandref": bandref,
                                                            "resample": resample,
                                                            "precision": str(prec),
                                                            "mfilter": "1",
                                                            "backmatching": "1",
                                                            "outgeom": SensorModel,
                                                            "initgeobinstep": str(step),
                                                            "mingeobinstep": str(minstep),
                                                            "minsiftpoints": str(minsiftpoints),
                                                            "iterate": iterate
                                                            })
    PMCMApp.ExecuteAndWriteOutput()

    # mode 1 : application on the source image
    if mode == 1 or mode == 3:
        outSrc = os.path.join(pathWd, 'temp_file.tif')
        io_Src = str(insrc + '?&skipcarto=true&geom=' + SensorModel)
        ds = gdal.Open(insrc)
        prj = ds.GetProjection()
        gt = ds.GetGeoTransform()
        srs = osr.SpatialReference()
        srs.ImportFromWkt(prj)
        code = srs.GetAuthorityCode(None)
        gsp = str(int(2 * round(max(abs(gt[1]), abs(gt[5])))))
        ds = None
        orthoRecApp = OtbAppBank.CreateOrthoRectification({"in": io_Src,
                                                           "io.out": outSrc,
                                                           "map": "epsg",
                                                           "map.epsg.code": code,
                                                           "opt.gridspacing": gsp,
                                                           "pixType": "uint16"
                                                           })

        if writeFeatures:
            orthoRecApp[0].ExecuteAndWriteOutput()
        else:
            orthoRecApp[0].Execute()

        ext = os.path.splitext(insrc)[1]
        finalOutput = os.path.join(pathWd,os.path.basename(insrc.replace(ext, ext.replace('.', '_COREG.'))))
        superImposeApp = OtbAppBank.CreateSuperimposeApplication({"inr": insrc,
                                                                "inm": orthoRecApp[0],
                                                                "out": finalOutput,
                                                                "pixType": "uint16"})
        if writeFeatures:
            superImposeApp[0].ExecuteAndWriteOutput()
        else:
            superImposeApp[0].Execute()

        extractROIApp = OtbAppBank.CreateExtractROIApplication({"in": superImposeApp[0],
                                                                "mode": "fit",
                                                                "mode.fit.im": inref,
                                                                "out": finalOutput,
                                                                "pixType": "uint16"})
        extractROIApp.ExecuteAndWriteOutput()
        shutil.move(finalOutput,insrc.replace(ext, ext.replace('.', '_COREG.')))
        shutil.move(finalOutput.replace(ext, '.geom'),insrc.replace(ext, '_COREG.geom'))

        # Mask registration if exists
        masks = glob.glob(os.path.dirname(insrc) + os.sep + 'MASKS' + os.sep + '*reproj' + ext)
        if len(masks) != 0:
            for mask in masks:
                outSrc = os.path.join(pathWd, 'temp_file.tif')
                io_Src = str(mask + '?&skipcarto=true&geom=' + SensorModel)
                orthoRecApp = OtbAppBank.CreateOrthoRectification({"in": io_Src,
                                                                   "io.out": outSrc,
                                                                   "map": "epsg",
                                                                   "map.epsg.code": code,
                                                                   "opt.gridspacing": gsp,
                                                                   "pixType": "uint16"
                                                                   })
                if writeFeatures:
                    orthoRecApp[0].ExecuteAndWriteOutput()
                else:
                    orthoRecApp[0].Execute()

                ext = os.path.splitext(insrc)[1]
                finalMask = os.path.join(pathWd,os.path.basename(mask.replace(ext, ext.replace('.', '_COREG.'))))
                superImposeApp= OtbAppBank.CreateSuperimposeApplication({"inr": mask,
                                                                        "inm": orthoRecApp[0],
                                                                        "out": finalMask,
                                                                        "pixType": "uint16"})
                if writeFeatures:
                    superImposeApp[0].ExecuteAndWriteOutput()
                else:
                    superImposeApp[0].Execute()

                extractROIApp = OtbAppBank.CreateExtractROIApplication({"in": superImposeApp[0],
                                                                        "mode": "fit",
                                                                        "mode.fit.im": inref,
                                                                        "out": finalMask,
                                                                        "pixType": "uint16"})
                extractROIApp.ExecuteAndWriteOutput()
                if finalMask != mask.replace(ext, ext.replace('.', '_COREG.')) :
                    shutil.move(finalMask,mask.replace(ext, ext.replace('.', '_COREG.')))
                    shutil.move(finalMask.replace(ext, '.geom'),mask.replace(ext, '_COREG.geom'))

        if mode == 3:
            folders = glob.glob(os.path.join(datadir,'*'))
            vhr_ref = inref
            if datatype in ['S2','S2_S2C']:
                dates = [os.path.basename(fld).split('_')[1].split("-")[0] for fld in folders]
                ref_date = os.path.basename(insrc).split('_')[1].split("-")[0]
            elif datatype in ['L5','L8']:
                dates = [os.path.basename(fld).split('_')[3] for fld in folders]
                ref_date = os.path.basename(insrc).split('_')[3]
            dates.sort()
            ref_date_ind = dates.index(ref_date)
            bandref = band
            clean_dates = [ref_date]
            for date in reversed(dates[:ref_date_ind]):
                PMCMApp = None
                inref = glob.glob(os.path.join(datadir,'*'+clean_dates[-1]+'*',pattern))[0]
                insrc = glob.glob(os.path.join(datadir,'*'+date+'*',pattern))[0]
                outSensorModel = os.path.join(pathWd,'SensorModel_%s.geom'%date)
                try :
                    PMCMApp = OtbAppBank.CreatePointMatchCoregistrationModel({"in": insrc,
                                                                            "band1": band,
                                                                            "inref": inref,
                                                                            "bandref": bandref,
                                                                            "resample": resample,
                                                                            "precision": str(prec),
                                                                            "mfilter": "1",
                                                                            "backmatching": "1",
                                                                            "outgeom": outSensorModel,
                                                                            "initgeobinstep": str(step),
                                                                            "mingeobinstep": str(minstep),
                                                                            "minsiftpoints": str(minsiftpoints),
                                                                            "iterate": iterate
                                                                            })
                    PMCMApp.ExecuteAndWriteOutput()
                except RuntimeError :
                    shutil.copy(SensorModel,outSensorModel)
                    logger.warning('Coregistration failed, %s will be process with %s' %(insrc, outSensorModel))
                    continue

                outSrc = os.path.join(pathWd, 'temp_file.tif')
                io_Src = str(insrc + '?&skipcarto=true&geom=' + outSensorModel)
                ds = gdal.Open(insrc)
                prj = ds.GetProjection()
                gt = ds.GetGeoTransform()
                srs = osr.SpatialReference()
                srs.ImportFromWkt(prj)
                code = srs.GetAuthorityCode(None)
                gsp = str(int(2 * round(max(abs(gt[1]), abs(gt[5])))))
                ds = None
                try :
                    orthoRecApp = OtbAppBank.CreateOrthoRectification({"in": io_Src,
                                                                       "io.out": outSrc,
                                                                       "map": "epsg",
                                                                       "map.epsg.code": code,
                                                                       "opt.gridspacing": gsp,
                                                                       "pixType": "uint16"
                                                                       })

                    if writeFeatures:
                        orthoRecApp[0].ExecuteAndWriteOutput()
                    else:
                        orthoRecApp[0].Execute()
                except RuntimeError :
                    os.remove(outSensorModel)
                    shutil.copy(SensorModel,outSensorModel)
                    logger.warning('Coregistration failed, %s will be process with %s' %(insrc, outSensorModel))
                    orthoRecApp = OtbAppBank.CreateOrthoRectification({"in": io_Src,
                                                                       "io.out": outSrc,
                                                                       "map": "epsg",
                                                                       "map.epsg.code": code,
                                                                       "opt.gridspacing": gsp,
                                                                       "pixType": "uint16"
                                                                       })
                    continue

                    if writeFeatures:
                        orthoRecApp[0].ExecuteAndWriteOutput()
                    else:
                        orthoRecApp[0].Execute()

                ext = os.path.splitext(insrc)[1]
                finalOutput = os.path.join(pathWd, os.path.basename(insrc.replace(ext, ext.replace('.', '_COREG.'))))
                superImposeApp = OtbAppBank.CreateSuperimposeApplication({"inr": insrc,
                                                                        "inm": orthoRecApp[0],
                                                                        "out": finalOutput,
                                                                        "pixType": "uint16"})
                if writeFeatures:
                    superImposeApp[0].ExecuteAndWriteOutput()
                else:
                    superImposeApp[0].Execute()

                extractROIApp = OtbAppBank.CreateExtractROIApplication({"in": superImposeApp[0],
                                                                        "mode": "fit",
                                                                        "mode.fit.im": vhr_ref,
                                                                        "out": finalOutput,
                                                                        "pixType": "uint16"})
                extractROIApp.ExecuteAndWriteOutput()
                shutil.move(finalOutput,insrc.replace(ext, ext.replace('.', '_COREG.')))
                shutil.move(finalOutput.replace(ext, '.geom'),insrc.replace(ext, '_COREG.geom'))

                # Mask registration if exists
                masks = glob.glob(os.path.dirname(insrc) + os.sep + 'MASKS' + os.sep + '*reproj' + ext)
                if len(masks) != 0:
                    for mask in masks:
                        outSrc = os.path.join(pathWd, 'temp_file.tif')
                        io_Src = str(mask + '?&skipcarto=true&geom=' + outSensorModel)
                        orthoRecApp = OtbAppBank.CreateOrthoRectification({"in": io_Src,
                                                                           "io.out": outSrc,
                                                                           "map": "epsg",
                                                                           "map.epsg.code": code,
                                                                           "opt.gridspacing": gsp,
                                                                           "pixType": "uint16"
                                                                           })
                        if writeFeatures:
                            orthoRecApp[0].ExecuteAndWriteOutput()
                        else:
                            orthoRecApp[0].Execute()

                        ext = os.path.splitext(insrc)[1]
                        finalMask = os.path.join(pathWd, os.path.basename(mask.replace(ext, ext.replace('.', '_COREG.'))))
                        superImposeApp= OtbAppBank.CreateSuperimposeApplication({"inr": mask,
                                                                                "inm": orthoRecApp[0],
                                                                                "out": finalMask,
                                                                                "pixType": "uint16"})
                        if writeFeatures:
                            superImposeApp[0].ExecuteAndWriteOutput()
                        else:
                            superImposeApp[0].Execute()

                        extractROIApp = OtbAppBank.CreateExtractROIApplication({"in": superImposeApp[0],
                                                                                "mode": "fit",
                                                                                "mode.fit.im": vhr_ref,
                                                                                "out": finalMask,
                                                                                "pixType": "uint16"})
                        extractROIApp.ExecuteAndWriteOutput()
                        shutil.move(finalMask,mask.replace(ext, ext.replace('.', '_COREG.')))
                        shutil.move(finalMask.replace(ext, '.geom'),mask.replace(ext, '_COREG.geom'))
                
                if not writeFeatures and os.path.exists(outSensorModel):
                    os.remove(outSensorModel)

                if datatype in ['S2','S2_S2C']:
                    mtd_file = glob.glob(os.path.join(os.path.dirname(insrc),'*_MTD_ALL*'))[0]
                    cloud_clear = get_S2_Tile_Cloud_Cover(mtd_file)
                    cover = get_S2_Tile_Coverage(mtd_file)
                    if cloud_clear > 0.6 and cover > 0.8 :
                        clean_dates.append(date)
                elif datatype in ['L5','L8']:
                    mlt_file = glob.glob(os.path.join(os.path.dirname(insrc),'*_MTL*'))[0]
                    cloud_clear = get_L8_Tile_Cloud_Cover(mlt_file)
                    if cloud_clear > 0.6 :
                        clean_dates.append(date)

            clean_dates = [ref_date]
            for date in dates[ref_date_ind+1:]:
                inref = glob.glob(os.path.join(datadir,'*'+clean_dates[-1]+'*',pattern))[0]
                insrc = glob.glob(os.path.join(datadir,'*'+date+'*',pattern))[0]
                outSensorModel = os.path.join(pathWd,'SensorModel_%s.geom'%date)
                try :
                    PMCMApp = OtbAppBank.CreatePointMatchCoregistrationModel({"in": insrc,
                                                                            "band1": band,
                                                                            "inref": inref,
                                                                            "bandref": bandref,
                                                                            "resample": resample,
                                                                            "precision": str(prec),
                                                                            "mfilter": "1",
                                                                            "backmatching": "1",
                                                                            "outgeom": outSensorModel,
                                                                            "initgeobinstep": str(step),
                                                                            "mingeobinstep": str(minstep),
                                                                            "minsiftpoints": str(minsiftpoints),
                                                                            "iterate": iterate
                                                                            })
                    PMCMApp.ExecuteAndWriteOutput()
                except RuntimeError :
                    shutil.copy(SensorModel,outSensorModel)
                    logger.warning('Coregistration failed, %s will be process with %s' %(insrc, outSensorModel))
                    continue

                outSrc = os.path.join(pathWd,'temp_file.tif')
                io_Src = str(insrc + '?&skipcarto=true&geom=' + outSensorModel)
                ds = gdal.Open(insrc)
                prj = ds.GetProjection()
                gt = ds.GetGeoTransform()
                srs = osr.SpatialReference()
                srs.ImportFromWkt(prj)
                code = srs.GetAuthorityCode(None)
                gsp = str(int(2 * round(max(abs(gt[1]), abs(gt[5])))))
                ds = None
                try :
                    orthoRecApp = OtbAppBank.CreateOrthoRectification({"in": io_Src,
                                                                       "io.out": outSrc,
                                                                       "map": "epsg",
                                                                       "map.epsg.code": code,
                                                                       "opt.gridspacing": gsp,
                                                                       "pixType": "uint16"
                                                                       })

                    if writeFeatures:
                        orthoRecApp[0].ExecuteAndWriteOutput()
                    else:
                        orthoRecApp[0].Execute()
                except RuntimeError :
                    os.remove(outSensorModel)
                    shutil.copy(SensorModel,outSensorModel)
                    orthoRecApp = OtbAppBank.CreateOrthoRectification({"in": io_Src,
                                                                       "io.out": outSrc,
                                                                       "map": "epsg",
                                                                       "map.epsg.code": code,
                                                                       "opt.gridspacing": gsp,
                                                                       "pixType": "uint16"
                                                                       })
                    continue

                    if writeFeatures:
                        orthoRecApp[0].ExecuteAndWriteOutput()
                    else:
                        orthoRecApp[0].Execute()

                ext = os.path.splitext(insrc)[1]
                finalOutput = os.path.join(pathWd, os.path.basename(insrc.replace(ext, ext.replace('.', '_COREG.'))))
                superImposeApp = OtbAppBank.CreateSuperimposeApplication({"inr": insrc,
                                                                        "inm": orthoRecApp[0],
                                                                        "out": finalOutput,
                                                                        "pixType": "uint16"})
                if writeFeatures:
                    superImposeApp[0].ExecuteAndWriteOutput()
                else:
                    superImposeApp[0].Execute()

                extractROIApp = OtbAppBank.CreateExtractROIApplication({"in": superImposeApp[0],
                                                                        "mode": "fit",
                                                                        "mode.fit.im": vhr_ref,
                                                                        "out": finalOutput,
                                                                        "pixType": "uint16"})
                extractROIApp.ExecuteAndWriteOutput()
                shutil.move(finalOutput,insrc.replace(ext, ext.replace('.', '_COREG.')))
                shutil.move(finalOutput.replace(ext, '.geom'),insrc.replace(ext, '_COREG.geom'))

                # Mask registration if exists
                masks = glob.glob(os.path.dirname(insrc) + os.sep + 'MASKS' + os.sep + '*reproj' + ext)
                if len(masks) != 0:
                    for mask in masks:
                        outSrc = os.path.join(pathWd, 'temp_file.tif')
                        io_Src = str(mask + '?&skipcarto=true&geom=' + outSensorModel)
                        orthoRecApp = OtbAppBank.CreateOrthoRectification({"in": io_Src,
                                                                           "io.out": outSrc,
                                                                           "map": "epsg",
                                                                           "map.epsg.code": code,
                                                                           "opt.gridspacing": gsp,
                                                                           "pixType": "uint16"
                                                                           })
                        if writeFeatures:
                            orthoRecApp[0].ExecuteAndWriteOutput()
                        else:
                            orthoRecApp[0].Execute()

                        ext = os.path.splitext(insrc)[1]
                        finalMask = os.path.join(pathWd, os.basename(mask.replace(ext, ext.replace('.', '_COREG.'))))
                        superImposeApp= OtbAppBank.CreateSuperimposeApplication({"inr": mask,
                                                                                "inm": orthoRecApp[0],
                                                                                "out": finalMask,
                                                                                "pixType": "uint16"})
                        if writeFeatures:
                            superImposeApp[0].ExecuteAndWriteOutput()
                        else:
                            superImposeApp[0].Execute()

                        extractROIApp = OtbAppBank.CreateExtractROIApplication({"in": superImposeApp[0],
                                                                                "mode": "fit",
                                                                                "mode.fit.im": vhr_ref,
                                                                                "out": finalMask,
                                                                                "pixType": "uint16"})
                        extractROIApp.ExecuteAndWriteOutput()
                        shutil.move(finalMask,mask.replace(ext, ext.replace('.', '_COREG.')))
                        shutil.move(finalMask.replace(ext, '.geom'),mask.replace(ext, '_COREG.geom'))
                
                if writeFeatures == False and os.path.exists(outSensorModel):
                    os.remove(outSensorModel)

                if datatype in ['S2','S2_S2C']:
                    mtd_file = glob.glob(os.path.join(os.path.dirname(insrc),'*_MTD_ALL*'))[0]
                    cloud_clear = get_S2_Tile_Cloud_Cover(mtd_file)
                    cover = get_S2_Tile_Coverage(mtd_file)
                    if cloud_clear > 0.6 and cover > 0.8 :
                        clean_dates.append(date)
                elif datatype in ['L5','L8']:
                    mlt_file = glob.glob(os.path.join(os.path.dirname(insrc),'*_MTL*'))[0]
                    cloud_clear = get_L8_Tile_Cloud_Cover(mlt_file)
                    if cloud_clear > 0.6 :
                        clean_dates.append(date)

        if not writeFeatures and os.path.exists(SensorModel):
            os.remove(SensorModel)
    # mode 2 : application on the time series
    elif mode == 2:
        ext = os.path.splitext(insrc)[1]
        file_list = glob.glob(datadir + os.sep + '*' + os.sep + pattern)
        for insrc in file_list:
            outSrc = os.path.join(pathWd,'temp_file.tif')
            io_Src = str(insrc + '?&skipcarto=true&geom=' + SensorModel)
            ds = gdal.Open(insrc)
            prj = ds.GetProjection()
            gt = ds.GetGeoTransform()
            srs = osr.SpatialReference()
            srs.ImportFromWkt(prj)
            code = srs.GetAuthorityCode(None)
            gsp = str(int(2 * round(max(abs(gt[1]), abs(gt[5])))))
            ds = None
            orthoRecApp = OtbAppBank.CreateOrthoRectification({"in": io_Src,
                                                               "io.out": outSrc,
                                                               "map": "epsg",
                                                               "map.epsg.code": code,
                                                               "opt.gridspacing": gsp,
                                                               "pixType": "uint16"
                                                               })

            if writeFeatures:
                orthoRecApp[0].ExecuteAndWriteOutput()
            else:
                orthoRecApp[0].Execute()

            ext = os.path.splitext(insrc)[1]
            finalOutput = os.path.join(pathWd, os.path.basename(insrc.replace(ext, ext.replace('.', '_COREG.'))))
            superImposeApp = OtbAppBank.CreateSuperimposeApplication({"inr": insrc,
                                                                    "inm": orthoRecApp[0],
                                                                    "out": finalOutput,
                                                                    "pixType": "uint16"})
            if writeFeatures:
                superImposeApp[0].ExecuteAndWriteOutput()
            else:
                superImposeApp[0].Execute()

            extractROIApp = OtbAppBank.CreateExtractROIApplication({"in": superImposeApp[0],
                                                                    "mode": "fit",
                                                                    "mode.fit.im": inref,
                                                                    "out": finalOutput,
                                                                    "pixType": "uint16"})
            extractROIApp.ExecuteAndWriteOutput()
            shutil.move(finalOutput,insrc.replace(ext, ext.replace('.', '_COREG.')))
            shutil.move(finalOutput.replace(ext, '.geom'),insrc.replace(ext, '_COREG.geom'))

            # Mask registration if exists
            masks = glob.glob(os.path.dirname(insrc) + os.sep + 'MASKS' + os.sep + '*reproj*' + ext)
            if len(masks) != 0:
                for mask in masks:
                    outSrc = os.path.join(pathWd,'temp_file.tif')
                    io_Src = str(mask + '?&skipcarto=true&geom=' + SensorModel)
                    orthoRecApp = OtbAppBank.CreateOrthoRectification({"in": io_Src,
                                                                       "io.out": outSrc,
                                                                       "map": "epsg",
                                                                       "map.epsg.code": code,
                                                                       "opt.gridspacing": gsp,
                                                                       "pixType": "uint16"
                                                                       })
                    if writeFeatures:
                        orthoRecApp[0].ExecuteAndWriteOutput()
                    else:
                        orthoRecApp[0].Execute()

                    ext = os.path.splitext(insrc)[1]
                    finalMask = os.path.join(pathWd,os.path.basename(mask.replace(ext, ext.replace('.', '_COREG.'))))
                    superImposeApp= OtbAppBank.CreateSuperimposeApplication({"inr": mask,
                                                                            "inm": orthoRecApp[0],
                                                                            "out": finalMask,
                                                                            "pixType": "uint16"})
                    if writeFeatures:
                        superImposeApp[0].ExecuteAndWriteOutput()
                    else:
                        superImposeApp[0].Execute()

                    extractROIApp = OtbAppBank.CreateExtractROIApplication({"in": superImposeApp[0],
                                                                            "mode": "fit",
                                                                            "mode.fit.im": inref,
                                                                            "out": finalMask,
                                                                            "pixType": "uint16"})
                    extractROIApp.ExecuteAndWriteOutput()
                    shutil.move(finalMask,mask.replace(ext, ext.replace('.', '_COREG.')))
                    shutil.move(finalMask.replace(ext, '.geom') ,mask.replace(ext, '_COREG.geom'))


        if not writeFeatures and os.path.exists(SensorModel):
            os.remove(SensorModel)

    return None

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Computes a time series of features")
    parser.add_argument("-insrc", dest="insrc", help="Source raster", required=True)
    parser.add_argument("-inref", dest="inref", help="Reference raster", required=True)
    parser.add_argument("-band", dest="band", help="Band from the source raster", default=3, required=False)
    parser.add_argument("-bandref", dest="bandref", help="Band from the reference raster", default=3, required=False)
    parser.add_argument("-resample", type=str2bool, dest="resample",
                        help="path to the working directory", default=False, required=False)
    parser.add_argument("-step", dest="step", help="", default=256, required=False)
    parser.add_argument("-minstep", dest="minstep", help="", default=16, required=False)
    parser.add_argument("-minsiftpoints", dest="minsiftpoints", help="", default=40, required=False)
    parser.add_argument("-iterate", type=str2bool, dest="iterate",
                        help="path to the working directory", default=True, required=False)
    parser.add_argument("-prec", dest="prec", help="", default=3, required=False)
    parser.add_argument("-mode", dest="mode", help="1 : simple registration ; 2 : time series registration ; 3 : time series cascade registration", default=1, required=False)
    parser.add_argument("-dd", dest="datadir", help="path to the root data directory", default=None, required=False)
    parser.add_argument("-pattern", dest="pattern", help="pattern of the file to register", default='*STACK', required=False)
    parser.add_argument("-writeFeatures", type=str2bool, dest="writeFeatures",
                        help="path to the working directory", default=False, required=False)
    args = parser.parse_args()

    args.mode = int(args.mode)
    if args.mode not in [1, 2, 3]:
        sys.exit("Wrong mode argument, please use the following options : 1 : simple registration ; 2 : time series registration ; 3 : time series cascade registration")
    elif args.mode in [2, 3]:
        if (args.datadir is None or not os.path.exists(args.datadir)):
            sys.exit("Valid data direction needed for time series registration (mode 2 and 3)")
        if args.pattern is None:
            sys.exit("A pattern is needed for time series registration (mode 2 and 3)")

    coregister(args.insrc, args.inref, args.band, args.bandref, args.resample, args.step, args.minstep, args.minsiftpoints, args.iterate, args.prec, args.mode, args.datadir, args.pattern, args.writeFeatures)
