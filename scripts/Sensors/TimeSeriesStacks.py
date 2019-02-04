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

import os
import sys
import argparse
import shutil
import ast
import logging
import time
from config import Config
from Sensors import Landsat8
from Sensors import Landsat5
from Sensors import Sentinel_2
from Sensors import Sentinel_2_S2C
from Common.Utils import run
from Common.Utils import Opath
from CreateDateFile import CreateFichierDatesReg
from Common import FileUtils as fu
from gdal import Warp

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


def PreProcessS2_S2C(outproj, ipathS2_S2C, tile_name, s2_s2c_target_dir, workingDirectory, logger=logger):
    """ preprocess sen2cor images in order to be usable by IOTA2

    Parameters
    ----------

    outproj : string
        epsg's projection code
    ipathS2_S2C : string
        absolute path to a directory containing all dates to a given tile
    s2_s2c_target_dir : string
        output target directory
    workingDirectory : string
        absolute path to a workingDirectory
    logger : logging object
        root logger
    
    Note
    ----
    See also `here <https://framagit.org/inglada/iota2/issues/13>`_
    """

    def reproj_raster(raster_stack, outproj, workingDirectory=None):
        """ use to reproject sen2cor S2 STACK

        Parameters
        ----------
        raster_stack : string
            absolute path to a sen2cor S2 STACK (compute by IOTA2)
        outproj : string
            epsg's projection code
        workingDirectory : string
            absolute path to a workingDirectory

        issue : 
            output height and width may not respect raster_stack extent due to 
            interpolation
        """

        current_proj = fu.getRasterProjectionEPSG(raster_stack)
        if int(current_proj) != int(outproj):
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
        """ use to check if all bands contains the same dates, if a date is missing
        raise an Exception "some dates in sen2cor sensor are missing"
        
        Parameters
        ----------

        s2c_bands_dates : dict
            dictionnary which resume all sen2cor date found for a given tile

        Example
        -------
        consider the tile T31UDP containing one date :
        >>> dico = {'B2': {'20180310T105849': '/abslutePath/L2A_T31UDP_20180310T105849_B03_10m.jp2'}, ...,
        >>>         'B12': {'20180310T105849': '/abslutePath/L2A_T31UDP_20180310T105849_B08_10m.jp2'}}
        >>> check_bands_dates(dico)

        """
        nb_bands = 10

        dates = [date for band, date_img in s2c_bands_dates.items() for date in date_img.keys()]
        dates_unique = set(dates)
        
        date_ap = [dates.count(date_u) for date_u in dates_unique]

        if date_ap.count(date_ap[0]) != len(date_ap):
            error_msg = "some dates in sen2cor sensor are missing"
            logger.error(error_msg)
            raise Exception(error_msg)

    def stack_dates(s2c_bands_dates, outproj, s2_s2c_dir, s2_s2c_target_dir, tile_name, workingDirectory):
        """ usage : stack all bands into a raster

            Args :
            s2c_bands_dates [dict of dict]
                print s2c_bands_dates["BandName"]["date"]
                > /path/to/MySentinel-2_Sen2Cor_Band_Date.jp2
            outproj [string] : output projection
            workingDirectory [string] working directory
        """
        import otbApplication as otb
        from Common import OtbAppBank
        
        #get all dates
        s2c_dates = s2c_bands_dates[s2c_bands_dates.keys()[0]].keys()
        
        #for each date concatenates bands
        for s2c_date in s2c_dates:
            concatenate = otb.Registry.CreateApplication("ConcatenateImages")
            concatenate_out_dir, B2_name = os.path.split(s2c_bands_dates["B2"][s2c_date])
            concatenate_out_name = B2_name.replace("B02", "STACK").replace(".jp2", ".tif")
            if s2_s2c_target_dir:
                concatenate_out_dir = os.path.join(s2_s2c_target_dir,concatenate_out_dir.replace(s2_s2c_dir, ""))
            working_dir = concatenate_out_dir
            if workingDirectory:
                working_dir = workingDirectory
            fu.ensure_dir(concatenate_out_dir)
            concatenate_output = os.path.join(concatenate_out_dir, concatenate_out_name)
            concatenate_working_path = os.path.join(working_dir, concatenate_out_name)
            concatenate.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint16)
            B2 = s2c_bands_dates["B2"][s2c_date]
            B3 = s2c_bands_dates["B3"][s2c_date]
            B4 = s2c_bands_dates["B4"][s2c_date]
            B8 = s2c_bands_dates["B8"][s2c_date]
            B5 = OtbAppBank.CreateRigidTransformResampleApplication({"in":s2c_bands_dates["B5"][s2c_date],
                                                                     "pixType" : "int16",
                                                                     "transform.type.id.scalex": "2",
                                                                     "transform.type.id.scaley": "2",
                                                                     "interpolator": "bco",
                                                                     "interpolator.bco.radius":"2"})
            B5.Execute()
            B6 = OtbAppBank.CreateRigidTransformResampleApplication({"in":s2c_bands_dates["B6"][s2c_date],
                                                                     "pixType" : "int16",
                                                                     "transform.type.id.scalex": "2",
                                                                     "transform.type.id.scaley": "2",
                                                                     "interpolator": "bco",
                                                                     "interpolator.bco.radius":"2"})
            B6.Execute()
            B7 = OtbAppBank.CreateRigidTransformResampleApplication({"in":s2c_bands_dates["B7"][s2c_date],
                                                                     "pixType" : "int16",
                                                                     "transform.type.id.scalex": "2",
                                                                     "transform.type.id.scaley": "2",
                                                                     "interpolator": "bco",
                                                                     "interpolator.bco.radius":"2"})
            B7.Execute()
            B8A = OtbAppBank.CreateRigidTransformResampleApplication({"in":s2c_bands_dates["B8A"][s2c_date],
                                                                      "pixType" : "int16",
                                                                      "transform.type.id.scalex": "2",
                                                                      "transform.type.id.scaley": "2",
                                                                      "interpolator": "bco",
                                                                      "interpolator.bco.radius":"2"})
            B8A.Execute()
            B11 = OtbAppBank.CreateRigidTransformResampleApplication({"in":s2c_bands_dates["B11"][s2c_date],
                                                                      "pixType" : "int16",
                                                                      "transform.type.id.scalex": "2",
                                                                      "transform.type.id.scaley": "2",
                                                                      "interpolator": "bco",
                                                                      "interpolator.bco.radius":"2"})
            B11.Execute()
            B12 = OtbAppBank.CreateRigidTransformResampleApplication({"in":s2c_bands_dates["B12"][s2c_date],
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

            concatenate.SetParameterString("out", concatenate_working_path)
            if not os.path.exists(concatenate_output):
                concatenate.ExecuteAndWriteOutput()
                reproj_raster(concatenate_working_path, outproj)
                if workingDirectory:
                    shutil.copy(concatenate_working_path, concatenate_output)
                    os.remove(concatenate_working_path)
            else:
                reproj_raster(concatenate_output,
                              outproj, workingDirectory)

    def extract_SCL_masks(ipathS2_S2C, outproj, s2_s2c_target_dir, tile_name, workingDirectory):
        """usage : build masks from SCL images
                   SCL : image's description
                   http://step.esa.int/thirdparties/sen2cor/2.5.5/docs/S2-PDGS-MPC-L2A-PDD-V2.5.5.pdf 
        """
        from Common import OtbAppBank

        NODATA_flag = 0
        #pixels to interpolate
        invalid_flags = [0, 1, 3, 8, 9, 10]
        #invalid_flags = [0, 1, 3, 9, 10]
        raster_border_name = "nodata_10m.tif"
        raster_invalid_name = "invalid_10m.tif"

        SCL_dates = fu.FileSearch_AND(os.path.join(ipathS2_S2C, tile_name), True, "SCL_20m.jp2")
        for SCL in SCL_dates:
            R20_directory, SCL_name = os.path.split(SCL)
            IMG_DATA_dir = os.path.normpath(R20_directory).split(os.sep)[0:-1:1]
            R10_directory = os.sep.join(IMG_DATA_dir + ["R10m"])
            SCL_10m_app = OtbAppBank.CreateRigidTransformResampleApplication({"in": SCL,
                                                                              "pixType" : "uint8",
                                                                              "transform.type.id.scalex": "2",
                                                                              "transform.type.id.scaley": "2",
                                                                              "interpolator": "nn"})
            SCL_10m_app.Execute()
            masks = []

            #border MASK            
            border_name = SCL_name.replace("SCL_20m.jp2", raster_border_name)
            if s2_s2c_target_dir:
                R10_directory = os.path.join(s2_s2c_target_dir, R10_directory.replace(ipathS2_S2C, ""))
            working_dir = R10_directory
            if workingDirectory:
                working_dir = workingDirectory
            fu.ensure_dir(R10_directory)
            border_output = os.path.join(R10_directory, border_name)
            border_working_path = os.path.join(working_dir, border_name)

            border_app = OtbAppBank.CreateBandMathApplication({"il": SCL_10m_app,
                                                               "exp": "im1b1=={}?0:1".format(NODATA_flag),
                                                               "out": border_working_path,
                                                               "pixType" : "uint8"})
            if not os.path.exists(border_output):
                border_app.ExecuteAndWriteOutput()
                reproj_raster(border_working_path, outproj)
                if workingDirectory:
                    shutil.copy(border_working_path, border_output)
                    os.remove(border_working_path)
                masks.append(border_output)
            else:
                reproj_raster(border_output, outproj, workingDirectory)
            
            #invalid MASK
            invalid_name = SCL_name.replace("SCL_20m.jp2", raster_invalid_name)
            invalid_output = os.path.join(R10_directory, invalid_name)
            invalid_working_output = os.path.join(working_dir, invalid_name)
            invalid_expr = " or ".join(["im1b1=={}".format(flag) for flag in invalid_flags])
            invalid_app = OtbAppBank.CreateBandMathApplication({"il": SCL_10m_app,
                                                                "exp": "{}?1:0".format(invalid_expr),
                                                                "out": invalid_working_output,
                                                                "pixType" : "uint8"})
            if not os.path.exists(invalid_output):
                invalid_app.ExecuteAndWriteOutput()
                reproj_raster(invalid_working_output, outproj)
                if workingDirectory:
                    shutil.copy(invalid_working_output, invalid_output)
                    os.remove(invalid_working_output)
                masks.append(invalid_output)
            else:
                reproj_raster(invalid_output, outproj, workingDirectory)

    from Sensors import Sentinel_2_S2C
    #dummy object
    sen2cor_s2 = Sentinel_2_S2C("_", "_", "_", "_")
    tile_s2c_dir = os.path.join(ipathS2_S2C, tile_name)
    #get 20m images
    B5 = fu.FileSearch_AND(tile_s2c_dir, True, "B05_20m.jp2")
    B6 = fu.FileSearch_AND(tile_s2c_dir, True, "B06_20m.jp2")
    B7 = fu.FileSearch_AND(tile_s2c_dir, True, "B07_20m.jp2")
    B8A = fu.FileSearch_AND(tile_s2c_dir, True, "B8A_20m.jp2")
    B11 = fu.FileSearch_AND(tile_s2c_dir, True, "B11_20m.jp2")
    B12 = fu.FileSearch_AND(tile_s2c_dir, True, "B12_20m.jp2")

    #get 10m  images
    B2 = fu.FileSearch_AND(tile_s2c_dir, True, "B02_10m.jp2")
    B3 = fu.FileSearch_AND(tile_s2c_dir, True, "B03_10m.jp2")
    B4 = fu.FileSearch_AND(tile_s2c_dir, True, "B04_10m.jp2")
    B8 = fu.FileSearch_AND(tile_s2c_dir, True, "B08_10m.jp2")

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
    stack_dates(s2c_bands_dates, outproj, ipathS2_S2C, s2_s2c_target_dir, tile_name, workingDirectory)

    #masks
    extract_SCL_masks(ipathS2_S2C, outproj, s2_s2c_target_dir, tile_name, workingDirectory)


def resample_s2(raster_in, s2_dir, target_dir, tile_name,
                workingDirectory, logger=logger):
    """
    function use to resample a S2 band from 20m to 10m

    Parameters
    ----------
    raster_in : string
        raster to resample
    s2_dir : string
        directory containing all s2 tiles
    target_dir : string
        directory to write resampled data
    tile_name : string
        tile's name
    workingDirectory : string
        path to a working directory
    logger : logging
        root logger

    Return
    ------
    string
        output path
    """
    from Common import OtbAppBank
    from Common.FileUtils import ensure_dir

    folder, file_name = os.path.split(raster_in)
    output_name = file_name.replace(".tif", "_10M.tif")
    output_dir = folder

    if target_dir:
        output_dir = folder.replace(s2_dir, target_dir)

    working_dir = output_dir
    if workingDirectory:
        working_dir = workingDirectory

    ensure_dir(output_dir)
    output_path = os.path.join(output_dir, output_name)
    output_working_path = os.path.join(working_dir, output_name)

    resample_parameters = {"in": raster_in,
                           "out": output_working_path,
                           "transform.type.id.scalex": 2,
                           "transform.type.id.scaley": 2,
                           "interpolator": "bco",
                           "interpolator.bco.radius": 2,
                           "pixType" : "int16"}

    resample_app = OtbAppBank.CreateRigidTransformResampleApplication(resample_parameters)
    if not os.path.exists(output_path):
        logger.info("launch resampling : {}".format(file_name))
        resample_app.ExecuteAndWriteOutput()
        logger.debug("resampling of {} done at {}".format(raster_in,
                                                          output_path))
        if workingDirectory:
            shutil.copy(output_working_path, output_path)
            os.remove(output_working_path)
    return output_path


def reprojection_s2_mask(raster_in, s2_dir, target_dir, tile_name, out_epsg,
                         suffix, init_raster_val, workingDirectory, logger=logger):
    """
    function use to reproject

    Parameters
    ----------
    raster_in : string
        raster to resample
    s2_dir : string
        directory containing all s2 tiles
    target_dir : string
        directory to write resampled data
    tile_name : string
        tile's name
    out_epsg : int
        output epsg code
    suffix : string
        output is define thanks to input raster's name and a suffix
        example : "_cloud.tif"
    workingDirectory : string
        path to a working directory
    logger : logging
        root logger
    """
    from Common import OtbAppBank
    from Common.FileUtils import ensure_dir
    from Common.Utils import run

    folder, file_name = os.path.split(raster_in)
    output_name = file_name.replace(".tif", suffix)
    output_dir = folder

    if target_dir:
        output_dir = folder.replace(s2_dir, target_dir)

    working_dir = output_dir
    if workingDirectory:
        working_dir = workingDirectory

    ensure_dir(output_dir)
    output_path = os.path.join(output_dir, output_name)
    output_working_path = os.path.join(working_dir, output_name)
    target_res_x, target_res_y = fu.getRasterResolution(raster_in)
    in_epsg = fu.getRasterProjectionEPSG(raster_in)
    cmd = "gdalwarp -wo INIT_DEST={} -tr {} {} -s_srs \"EPSG:{}\" -t_srs \"EPSG:{}\" {} {}".format(init_raster_val,
                                                                                                   target_res_x,
                                                                                                   target_res_x,
                                                                                                   in_epsg,
                                                                                                   out_epsg,
                                                                                                   raster_in,
                                                                                                   output_working_path)
    if not os.path.exists(output_path):
        logger.info("reproject : {}".format(raster_in))
        if in_epsg != out_epsg:
            run(cmd)
            if workingDirectory:
                shutil.copy(output_working_path, output_path)
                os.remove(output_working_path)
        else:
            shutil.copy(raster_in, output_path)
        logger.debug("reproject : {} DONE at {}".format(raster_in, output_path))
    return output_path


def stack_s2(s2_bands, s2_dir, target_dir, tile_name, suffix, out_epsg,
             workingDirectory, logger=logger):
    """
    concatenate s2 bands (10m and 20m) and reproject the stack

    s2_bands : dict
        dictionnary containing "b2", "b3", "b4", "b5", "b6", "b7", "b8",
        "b8a","b11", "b12" keys
    s2_dir : string
        directory containing all s2 dates
    target_dir : string
        output target directory
    tile_name : string
        tile's name
    suffix : string
        stack suffix
    out_epsg : int
        output epsg code
    workingDirectory : string
        path to a working directory
    logger : logging object
        root logger
    """
    from gdal import Warp

    from Common import OtbAppBank
    from Common.FileUtils import ensure_dir
    from Common.Utils import run

    folder, file_name = os.path.split(s2_bands["b2"])
    output_name = file_name.replace("B2.tif", suffix)
    output_dir = folder

    if target_dir:
        output_dir = folder.replace(s2_dir, target_dir)

    working_dir = output_dir
    if workingDirectory:
        working_dir = workingDirectory

    ensure_dir(output_dir)
    output_path = os.path.join(output_dir, output_name)
    output_working_path = os.path.join(working_dir, output_name)

    # concatenate bands
    bands = [s2_bands["b2"],
             s2_bands["b3"],
             s2_bands["b4"],
             s2_bands["b5"],
             s2_bands["b6"],
             s2_bands["b7"],
             s2_bands["b8"],
             s2_bands["b8a"],
             s2_bands["b11"],
             s2_bands["b12"]]
    concatenation_param = {"il": bands,
                           "out": output_working_path,
                           "pixType": "int16"}
    epsg_origin = fu.getRasterProjectionEPSG(s2_bands["b2"])
    if os.path.exists(output_path):
        epsg_stack = fu.getRasterProjectionEPSG(output_path)
        if epsg_stack != out_epsg:
            # reproject to target EPSG thanks to gdal.Warp()
            logger.info("reprojecting stack : {}".format(output_path))
            Warp(output_working_path, output_path,
                 multithread=True, format="GTiff", xRes=10, yRes=10,
                 srcSRS="EPSG:{}".format(epsg_origin), dstSRS="EPSG:{}".format(out_epsg),
                 options=["INIT_DEST=-10000"])
            logger.debug("reprojecting stack : {} DONE".format(output_path))
            if workingDirectory:
                shutil.copy(output_working_path, output_path)
                os.remove(output_working_path)
    else:
        # concatenate
        concat_app = OtbAppBank.CreateConcatenateImagesApplication(concatenation_param)
        logger.info("generating stack : {}".format(output_path))
        concat_app.ExecuteAndWriteOutput()
        logger.debug("stack : {} generated".format(output_path))

        # reproject to target EPSG thanks to gdal.Warp()
        logger.info("reprojecting stack : {}".format(output_path))
        Warp(output_working_path, output_working_path,
             multithread=True, format="GTiff", xRes=10, yRes=10,
             srcSRS="EPSG:{}".format(epsg_origin), dstSRS="EPSG:{}".format(out_epsg),
             options=["INIT_DEST=-10000"])
        logger.debug("reprojecting stack : {} DONE".format(output_path))
        if workingDirectory:
            shutil.copy(output_working_path, output_path)
            os.remove(output_working_path)

def PreProcessS2(config, s2_dir, tile, outRes, projOut, workingDirectory,
                 s2_target_dir, logger=logger):
    """
    """

    logger = logging.getLogger(__name__)

    cfg = Config(config)
    struct = cfg.Sentinel_2.arbo
    arbomask = Config(file(config)).Sentinel_2.arbomask
    cloud = Config(file(config)).Sentinel_2.nuages
    sat = Config(file(config)).Sentinel_2.saturation
    div = Config(file(config)).Sentinel_2.div
    cloud_reproj = Config(file(config)).Sentinel_2.nuages_reproj
    sat_reproj = Config(file(config)).Sentinel_2.saturation_reproj
    div_reproj = Config(file(config)).Sentinel_2.div_reproj

    needReproj = False
    tileFolder = os.path.join(s2_dir, tile)

    # resample s2 20m bands
    b5 = fu.fileSearchRegEx(tileFolder+"/"+struct+"/*FRE_B5.tif")
    b6 = fu.fileSearchRegEx(tileFolder+"/"+struct+"/*FRE_B6.tif")
    b7 = fu.fileSearchRegEx(tileFolder+"/"+struct+"/*FRE_B7.tif")
    b8a = fu.fileSearchRegEx(tileFolder+"/"+struct+"/*FRE_B8A.tif")
    b11 = fu.fileSearchRegEx(tileFolder+"/"+struct+"/*FRE_B11.tif")
    b12 = fu.fileSearchRegEx(tileFolder+"/"+struct+"/*FRE_B12.tif")

    bands_20m = b5 + b6 + b7 + b8a + b11 + b12

    for band in bands_20m:
        resample_s2(band, s2_dir, s2_target_dir, tile, workingDirectory)

    # masks reprojection + stack s2 bands
    dates = os.listdir(tileFolder)
    for date in dates:
        # masks reprojection
        Cloud = fu.FileSearch_AND(os.path.join(tileFolder, date), True, cloud)[0]
        Sat = fu.FileSearch_AND(os.path.join(tileFolder, date), True, sat)[0]
        Div = fu.FileSearch_AND(os.path.join(tileFolder, date), True, div)[0]
        reprojection_s2_mask(Cloud, s2_dir, s2_target_dir, tile, projOut,
                             "_reproj.tif", 0, workingDirectory)
        reprojection_s2_mask(Sat, s2_dir, s2_target_dir, tile, projOut,
                             "_reproj.tif", 0, workingDirectory)
        reprojection_s2_mask(Div, s2_dir, s2_target_dir, tile, projOut,
                             "_reproj.tif", 1, workingDirectory)
        # stack s2
        bands_10m_dir = tileFolder
        if s2_target_dir:
            bands_10m_dir = os.path.join(s2_target_dir, tile)
        s2_bands = {}
        s2_bands["b2"] = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B2*.tif")[0]
        s2_bands["b3"] = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B3*.tif")[0]
        s2_bands["b4"] = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B4*.tif")[0]
        s2_bands["b5"] = fu.fileSearchRegEx(bands_10m_dir+"/"+date+"/*FRE_B5*_10M.tif")[0]
        s2_bands["b6"] = fu.fileSearchRegEx(bands_10m_dir+"/"+date+"/*FRE_B6*_10M.tif")[0]
        s2_bands["b7"] = fu.fileSearchRegEx(bands_10m_dir+"/"+date+"/*FRE_B7*_10M.tif")[0]
        s2_bands["b8"] = fu.fileSearchRegEx(tileFolder+"/"+date+"/*FRE_B8.tif")[0]
        s2_bands["b8a"] = fu.fileSearchRegEx(bands_10m_dir+"/"+date+"/*FRE_B8A*_10M.tif")[0]
        s2_bands["b11"] = fu.fileSearchRegEx(bands_10m_dir+"/"+date+"/*FRE_B11*_10M.tif")[0]
        s2_bands["b12"] = fu.fileSearchRegEx(bands_10m_dir+"/"+date+"/*FRE_B12*_10M.tif")[0]

        stack_s2(s2_bands, s2_dir, s2_target_dir, tile, "STACK.tif", projOut,
                 workingDirectory)


def generateStack(tile, cfg, outputDirectory, writeOutput=False,
                  workingDirectory=None,
                  testMode=False, testSensorData=None, enable_Copy=False,
                  logger=logger):

    logger.info("prepare sensor's stack for tile : " + tile)

    import Sensors
    from GenSensors import CreateCommonZone_bindings
    from Common import ServiceConfigFile as SCF
    if writeOutput == "False":
        writeOutput = False
    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)
    if outputDirectory and not os.path.exists(outputDirectory) and not testMode:
        try:
            os.mkdir(outputDirectory)
        except OSError:
            logger.warning(outputDirectory + "allready exists")
    if not os.path.exists(cfg.pathConf):
        raise Exception("'"+cfg.pathConf+"' does not exists")
    logger.info("features generation using '%s' configuration file"%(cfg.pathConf))

    ipathL5 = cfg.getParam('chain', 'L5Path')
    if ipathL5 == "None":
        ipathL5 = None
    ipathL8 = cfg.getParam('chain', 'L8Path')
    if ipathL8 == "None":
        ipathL8 = None
    ipathS2 = cfg.getParam('chain', 'S2Path')
    s2_target_dir = cfg.getParam('chain', 'S2_output_path')
    if ipathS2 == "None":
        ipathS2 = None
    ipathS2_S2C = cfg.getParam('chain', 'S2_S2C_Path')
    if ipathS2_S2C == "None":
        ipathS2_S2C = None
    autoDate = cfg.getParam('GlobChain', 'autoDate')
    tiles = cfg.getParam('chain', 'listTile').split(" ")
    gapL5 = str(cfg.getParam('Landsat5', 'temporalResolution'))
    gapL8 = str(cfg.getParam('Landsat8', 'temporalResolution'))
    gapS2 = str(cfg.getParam('Sentinel_2', 'temporalResolution'))
    gapS2_S2C = str(cfg.getParam('Sentinel_2_S2C', 'temporalResolution'))
    
    sensorConfig = (os.path.join(os.environ.get('IOTA2DIR'), "scripts")).split(os.path.sep)
    sensorConfig = (os.path.sep).join(sensorConfig[0:-1] + ["config", "sensors.cfg"])
    cfg_sensors = SCF.serviceConfigFile(sensorConfig, iota_config=False)
    
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

    if ipathL5:
        ipathL5 = ipathL5+"/Landsat5_"+tile
        L5res = cfg_sensors.getParam('Landsat5', 'nativeRes')
        if "TMPDIR" in os.environ and enable_Copy is True:
            ipathL5 = copy_inputs_sensors_data(folder_to_copy=ipathL5,
                                               workingDirectory=os.environ["TMPDIR"],
                                               data_dir_name="sensors_data", logger=logger)

        landsat5 = Landsat5(ipathL5, wDir, cfg.pathConf, L5res)
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

    if ipathL8:
        ipathL8 = ipathL8+"/Landsat8_"+tile
        L8res = cfg_sensors.getParam('Landsat8', 'nativeRes')
        if "TMPDIR" in os.environ and enable_Copy is True:
            ipathL8 = copy_inputs_sensors_data(folder_to_copy=ipathL8,
                                               workingDirectory=os.environ["TMPDIR"],
                                               data_dir_name="sensors_data", logger=logger)

        landsat8 = Landsat8(ipathL8, wDir, cfg.pathConf, L8res)
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

    if ipathS2:
        output_projection = (cfg.getParam("GlobChain", "proj")).split(":")[-1]
        output_res = cfg.getParam("chain", "spatialResolution")
        PreProcessS2(sensorConfig, ipathS2, tile, output_res, output_projection,
                     workingDirectory, s2_target_dir)

        #if TMPDIR -> copy inputs to TMPDIR and change input path
        if "TMPDIR" in os.environ and enable_Copy is True:
            ipathS2 = copy_inputs_sensors_data(folder_to_copy=ipathS2,
                                               workingDirectory=os.environ["TMPDIR"],
                                               data_dir_name="sensors_data", logger=logger)

        S2res = 10
        Sentinel2 = Sentinel_2(os.path.join(ipathS2, tile), wDir, cfg.pathConf, S2res)
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
    
    if ipathS2_S2C:
        projection = cfg.getParam("GlobChain", "proj").split(":")[-1]
        s2_s2c_target_dir = cfg.getParam('chain', 'S2_S2C_output_path')
        PreProcessS2_S2C(projection, ipathS2_S2C, tile, s2_s2c_target_dir, workingDirectory)
        ipathS2_S2C = os.path.join(ipathS2_S2C, tile)
        if "TMPDIR" in os.environ and enable_Copy is True:
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

    for borderMask, a, b in borderMasks:
        if writeOutput:
            borderMask.ExecuteAndWriteOutput()
        else:
            borderMask.Execute()

    commonRasterMask = CreateCommonZone_bindings(os.path.join(outputDirectory, "tmp"), borderMasks)
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
            fu.cpShapeFile(commonRasterMask.replace(".tif", ""), outputDirectory+"/tmp",
                           [".prj", ".shp", ".dbf", ".shx"], spe=True)

    return temporalSeries, masksSeries, interpDates, realDates, commonRasterMask

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="")

    parser.add_argument("-config", dest="configPath",
                        help="path to the configuration file",
                        default=None, required=True)

    parser.add_argument("-writeOutput", dest="writeOutput",
                        help="write outputs on disk or return otb object",
                        default="False", required=False, choices=["True", "False"])

    parser.add_argument("-outputDirectory", dest="outputDirectory",
                        help="output Directory", default=None, required=True)

    parser.add_argument("-workingDirectory", dest="workingDirectory",
                        help="working directory", default=None, required=False)

    parser.add_argument("-tile", dest="tile",
                        help="current tile to compute", default=None, required=True)


    args = parser.parse_args()
    generateStack(args.tile, args.configPath, args.outputDirectory,
                  args.writeOutput, args.workingDirectory)
