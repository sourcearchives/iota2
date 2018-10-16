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
import argparse
import ast
import os
import sys
import shutil
import logging
import glob
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

def coregister(insrc, inref, band, bandref, resample, step, minstep, minsiftpoints, iterate, prec, mode, datadir, pattern, pathWd, writeFeatures):
    """
    usage : Function use to compute features according to a configuration file.

    IN
    insrc [string] : source raster
    inref [string] : reference raster
    band [int] : band number for the source raster
    bandref [int] : band number for the raster reference raster
    resample [boolean] : resample to referance raster resolution
    step [int]
    prec [int]
    pathWd [string]
    cfg [string]
    writeFeatures [boolean]
    OUT

     [OTB Application object] : otb object ready to Execute()
    """
    if pathWd == None :
        pathWd = os.path.dirname(insrc)

    # #SensorModel generation
    logger.info("Source Raster Registration")
    outSensorModel=str(pathWd+os.sep+'SensorModel.geom')
    PMCMApp = OtbAppBank.CreatePointMatchCoregistrationModel({"in":insrc,
                                                    "band1":band,
                                                    "inref":inref,
                                                    "bandref":bandref,
                                                    "resample": resample,
                                                    "precision": str(prec),
                                                    "mfilter": "1",
                                                    "backmatching": "1",
                                                    "outgeom":outSensorModel,
                                                    "initgeobinstep": str(step),
                                                    "mingeobinstep": str(minstep),
                                                    "minsiftpoints": str(minsiftpoints),
                                                    "iterate": iterate
                                                    })
    PMCMApp.ExecuteAndWriteOutput()

    # mode 1 : application on the source image
    if mode == 1 :
        outSrc=str(pathWd+os.sep+'temp_file.tif')
        io_Src=str(insrc+'?&skipcarto=true&geom='+outSensorModel)
        ds = gdal.Open(insrc)
        prj = ds.GetProjection()
        gt = ds.GetGeoTransform()
        srs = osr.SpatialReference()
        srs.ImportFromWkt(prj)
        code = srs.GetAuthorityCode(None)
        gsp = str(int(2 * round(max(abs(gt[1]), abs(gt[5])))))
        ds = None
        orthoRecApp = OtbAppBank.CreateOrthoRectification({"in":io_Src,
                                                           "io.out":outSrc,
                                                           "map":"epsg",
                                                           "map.epsg.code":code,
                                                           "opt.gridspacing":gsp,
                                                           "pixType": "uint16"
                                                           })
        
        if writeFeatures:
            orthoRecApp[0].ExecuteAndWriteOutput()
        else :
            orthoRecApp[0].Execute()

        ext = os.path.splitext(insrc)[1]
        finalOutput = insrc.replace(ext, ext.replace('.', '_COREG.'))
        superImposeApp= OtbAppBank.CreateSuperimposeApplication({"inr":insrc,
                                                                "inm":orthoRecApp[0],
                                                                "out":finalOutput,
                                                                "pixType": "uint16"})
        superImposeApp[0].ExecuteAndWriteOutput()

		# Mask registration if exists
        masks = glob.glob(os.path.dirname(insrc)+os.sep+'*MASK*'+ext)
        if len(masks) != 0 :
            for mask in masks :
                outSrc=str(os.path.dirname(insrc)+os.sep+'temp_file.tif')
                io_Src=str(mask+'?&skipcarto=true&geom='+outSensorModel)
                orthoRecApp = OtbAppBank.CreateOrthoRectification({"in":io_Src,
                                                                   "io.out":outSrc,
                                                                   "map":"epsg",
                                                                   "map.epsg.code":code,
                                                                   "opt.gridspacing":gsp,
                                                                   "pixType": "uint16"
                                                                   })
                if writeFeatures:
                    orthoRecApp[0].ExecuteAndWriteOutput()
                else :
                    orthoRecApp[0].Execute()

                ext = os.path.splitext(insrc)[1]
                finalmask = mask.replace(ext, ext.replace('.', '_COREG.'))
                superImposeApp= OtbAppBank.CreateSuperimposeApplication({"inr":mask,
                                                                        "inm":orthoRecApp[0],
                                                                        "out":finalmask,
                                                                        "pixType": "uint16"})
                superImposeApp[0].ExecuteAndWriteOutput()

        if not writeFeatures and os.path.exists(outSensorModel):
            os.remove(outSensorModel)

	# mode 2 : application on the time series
    elif mode == 2 :
        ext = os.path.splitext(insrc)[1]
        file_list = glob.glob(datadir+os.sep+'*'+os.sep+pattern+ext)
        for insrc in file_list :
            outSrc=str(os.path.dirname(insrc)+os.sep+'temp_file.tif')
            io_Src=str(insrc+'?&skipcarto=true&geom='+outSensorModel)
            ds = gdal.Open(insrc)
            prj = ds.GetProjection()
            gt = ds.GetGeoTransform()
            srs = osr.SpatialReference()
            srs.ImportFromWkt(prj)
            code = srs.GetAuthorityCode(None)
            gsp = str(int(2 * round(max(abs(gt[1]), abs(gt[5])))))
            ds = None
            orthoRecApp = OtbAppBank.CreateOrthoRectification({"in":io_Src,
                                                               "io.out":outSrc,
                                                               "map":"epsg",
                                                               "map.epsg.code":code,
                                                               "opt.gridspacing":gsp,
                                                               "pixType": "uint16"
                                                               })
            
            if writeFeatures:
                orthoRecApp[0].ExecuteAndWriteOutput()
            else :
                orthoRecApp[0].Execute()

            ext = os.path.splitext(insrc)[1]
            finalOutput = insrc.replace(ext, ext.replace('.', '_COREG.'))
            superImposeApp= OtbAppBank.CreateSuperimposeApplication({"inr":insrc,
                                                                    "inm":orthoRecApp[0],
                                                                    "out":finalOutput,
                                                                    "pixType": "uint16"})
            superImposeApp[0].ExecuteAndWriteOutput()
            
			# Mask registration if exists
            masks = glob.glob(os.path.dirname(insrc)+os.sep+'*MASK*'+ext)
            if len(masks) != 0 :
                for mask in masks :
                    outSrc=str(os.path.dirname(insrc)+os.sep+'temp_file.tif')
                    io_Src=str(mask+'?&skipcarto=true&geom='+outSensorModel)
                    orthoRecApp = OtbAppBank.CreateOrthoRectification({"in":io_Src,
                                                                       "io.out":outSrc,
                                                                       "map":"epsg",
                                                                       "map.epsg.code":code,
                                                                       "opt.gridspacing":gsp,
                                                                       "pixType": "uint16"
                                                                       })
                    if writeFeatures:
                        orthoRecApp[0].ExecuteAndWriteOutput()
                    else :
                        orthoRecApp[0].Execute()

                    ext = os.path.splitext(insrc)[1]
                    finalmask = mask.replace(ext, ext.replace('.', '_COREG.'))
                    superImposeApp= OtbAppBank.CreateSuperimposeApplication({"inr":mask,
                                                                            "inm":orthoRecApp[0],
                                                                            "out":finalmask,
                                                                            "pixType": "uint16"})
                    superImposeApp[0].ExecuteAndWriteOutput()
                
        if not writeFeatures and os.path.exists(outSensorModel):
            os.remove(outSensorModel)

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
    parser.add_argument("-pattern", dest="pattern", help="pattern of the file to registrate", default='*STACK', required=False)
    parser.add_argument("-wd", dest="pathWd", help="path to the working directory", default=None, required=False)
    parser.add_argument("-writeFeatures", type=str2bool, dest="writeFeatures",
                        help="path to the working directory", default=False, required=False)
    args = parser.parse_args()

    args.mode = int(args.mode)
    if args.mode not in [1,2,3] :
        sys.exit("Wrong mode argument, please use the following options : 1 : simple registration ; 2 : time series registration ; 3 : time series cascade registration")
    elif args.mode in [2,3] :
        if (args.datadir is None or not os.path.exists(args.datadir)):
            sys.exit("Valid data direction needed for time series registration (mode 2 and 3)")
        if args.pattern is None :
            sys.exit("A pattern is needed for time series registration (mode 2 and 3)")

    coregister(args.insrc, args.inref, args.band, args.bandref, args.resample, args.step, args.minstep, args.minsiftpoints, args.iterate, args.prec, args.mode, args.datadir, args.pattern, args.pathWd, args.writeFeatures)
