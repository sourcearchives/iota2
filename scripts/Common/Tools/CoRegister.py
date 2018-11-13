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
            with open(file) as f:
                for line in f:
                    if 'CLOUD_COVER ' in line :
                        cloud = float(line.split(' = ')[1])
                        percent = 1-cloud /100
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
            with open(file) as f:
                for line in f:
                    if 'name="CloudPercent"' in line :
                        cloud = float(line.split("</")[0].split('>')[1])
                        percent = 1-cloud/100
            fitScore = delta*percent
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

    pattern = cfg.getParam('coregistration','pattern')

    ipathL5 = cfg.getParam('chain', 'L5Path')
    if ipathL5 != "None" and os.path.exists(os.path.join(ipathL5,tile)):
        datadir = os.path.join(ipathL5,tile)
        datatype='L5'
    ipathL8 = cfg.getParam('chain', 'L8Path')
    if ipathL8 != "None" and os.path.exists(os.path.join(ipathL8,tile)):
        datadir = os.path.join(ipathL8,tile)
        datatype='L8'
    ipathS2 = cfg.getParam('chain', 'S2Path')
    if ipathS2 != "None" and os.path.exists(os.path.join(ipathS2,tile)):
        datadir = os.path.join(ipathS2,tile)
        datatype='S2'
    ipathS2_S2C = cfg.getParam('chain', 'S2_S2C_Path')
    if ipathS2_S2C != "None" and os.path.exists(os.path.join(ipathS2_S2C,tile)):
        datadir = os.path.join(ipathS2_S2C,tile)
        datatype='S2_S2C'

    inref = os.path.join(cfg.getParam('coregistration','VHRPath'))
    datesSrc = cfg.getParam('coregistration', 'dateSrc')
    if datesSrc != "None":
        tiles = cfg.getParam('chain', 'listTile').split(" ")
        tile_ind = tiles.index(tile)
        dateSrc = datesSrc.split(" ")[tile_ind]
        if dateSrc == "None" :
            dateVHR = cfg.getParam('coregistration', 'dateVHR')
            if dateVHR=='None':
                logger.warning("No dateVHR in configuration file, please fill dateVHR value")
            else :
                dateSrc = fitnessDateScore(dateVHR,datadir,datatype)
    else:
        dateVHR = cfg.getParam('coregistration', 'dateVHR')
        if dateVHR=='None':
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
    mode = cfg.getParam('coregistration','mode')

    coregister(insrc, inref, bandsrc, bandref, resample, step, minstep, minsiftpoints, iterate, prec, mode, datadir, pattern, False)

def coregister(insrc, inref, band, bandref, resample=1, step=256, minstep=16, minsiftpoints=40, iterate=1, prec=3, mode=2, datadir=None, pattern='*STACK*', writeFeatures=False):
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
    pathWd = os.path.dirname(insrc)

    # #SensorModel generation
    outSensorModel = str(pathWd + os.sep + 'SensorModel.geom')
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

    # mode 1 : application on the source image
    if mode == 1:
        outSrc = str(pathWd + os.sep + 'temp_file.tif')
        io_Src = str(insrc + '?&skipcarto=true&geom=' + outSensorModel)
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
        finalOutput = insrc.replace(ext, ext.replace('.', '_COREG.'))
        superImposeApp = OtbAppBank.CreateSuperimposeApplication({"inr": insrc,
                                                                "inm": orthoRecApp[0],
                                                                "out": finalOutput,
                                                                "pixType": "uint16"})
        superImposeApp[0].ExecuteAndWriteOutput()
        os.remove(insrc)
        shutil.move(finalOutput,insrc)

        # Mask registration if exists
        masks = glob.glob(os.path.dirname(insrc) + os.sep + 'MASKS' + os.sep + '*reproj' + ext)
        if len(masks) != 0:
            for mask in masks:
                outSrc = str(os.path.dirname(insrc) + os.sep + 'temp_file.tif')
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
                finalmask = mask.replace(ext, ext.replace('.', '_COREG.'))
                superImposeApp= OtbAppBank.CreateSuperimposeApplication({"inr": mask,
                                                                        "inm": orthoRecApp[0],
                                                                        "out": finalmask,
                                                                        "pixType": "uint16"})
                superImposeApp[0].ExecuteAndWriteOutput()
                os.remove(mask)
                shutil.move(finalmask,mask)

        if not writeFeatures and os.path.exists(outSensorModel):
            os.remove(outSensorModel)

    # mode 2 : application on the time series
    elif mode == 2:
        ext = os.path.splitext(insrc)[1]
        file_list = glob.glob(datadir + os.sep + '*' + os.sep + pattern + ext)
        for insrc in file_list:
            outSrc = str(os.path.dirname(insrc) + os.sep + 'temp_file.tif')
            io_Src = str(insrc + '?&skipcarto=true&geom=' + outSensorModel)
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
            finalOutput = insrc.replace(ext, ext.replace('.', '_COREG.'))
            superImposeApp = OtbAppBank.CreateSuperimposeApplication({"inr": insrc,
                                                                    "inm": orthoRecApp[0],
                                                                    "out": finalOutput,
                                                                    "pixType": "uint16"})
            superImposeApp[0].ExecuteAndWriteOutput()
            os.remove(insrc)
            shutil.move(finalOutput,insrc)

            # Mask registration if exists
            masks = glob.glob(os.path.dirname(insrc) + os.sep + 'MASKS' + os.sep + '*reproj*' + ext)
            if len(masks) != 0:
                for mask in masks:
                    outSrc = str(os.path.dirname(insrc) + os.sep + 'temp_file.tif')
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
                    finalmask = mask.replace(ext, ext.replace('.', '_COREG.'))
                    superImposeApp= OtbAppBank.CreateSuperimposeApplication({"inr": mask,
                                                                            "inm": orthoRecApp[0],
                                                                            "out": finalmask,
                                                                            "pixType": "uint16"})
                    superImposeApp[0].ExecuteAndWriteOutput()
                    os.remove(mask)
                    shutil.move(finalmask,mask)

        if not writeFeatures and os.path.exists(outSensorModel):
            os.remove(outSensorModel)
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
