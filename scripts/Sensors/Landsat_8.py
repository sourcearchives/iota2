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

from config import Config
import logging
import glob
import os

from GenSensors import Sensor
from collections import OrderedDict

logger = logging.getLogger(__name__)

#in order to avoid issue 'No handlers could be found for logger...'
logger.addHandler(logging.NullHandler())

class Landsat_8(Sensor):

    name = 'Landsat8'

    def __init__(self, config_path, tile_name):
        """
        """
        from Common import ServiceConfigFile as SCF
        Sensor.__init__(self)

        if not os.path.exists(config_path):
            return

        self.tile_name = tile_name
        self.cfg_IOTA2 = SCF.serviceConfigFile(config_path)
        cfg_sensors = (self.cfg_IOTA2.getParam("chain", "pyAppPath")).split(os.path.sep)
        cfg_sensors = (os.path.sep).join(cfg_sensors[0:-1] + ["config", "sensors.cfg"])
        cfg_sensors = SCF.serviceConfigFile(cfg_sensors, iota_config=False)

        # running attributes
        self.target_proj = int(self.cfg_IOTA2.getParam("GlobChain", "proj").lower().replace(" ","").replace("epsg:",""))
        self.all_tiles = self.cfg_IOTA2.getParam("chain", "listTile")
        self.l8_data = self.cfg_IOTA2.getParam("chain", "L8Path")
        self.tile_directory = os.path.join(self.l8_data, tile_name)
        self.struct_path_masks = cfg_sensors.getParam("Landsat8", "arbomask")
        self.full_pipeline = self.cfg_IOTA2.getParam("Landsat8", "full_pipline")
        self.features_dir = os.path.join(self.cfg_IOTA2.getParam("chain", "outputPath"),
                                         "features", tile_name)
        extract_bands = self.cfg_IOTA2.getParam("Landsat8", "keepBands")
        extract_bands_flag = self.cfg_IOTA2.getParam("iota2FeatureExtraction", "extractBands")
        output_target_dir = self.cfg_IOTA2.getParam("chain", "L8_output_path")
        if output_target_dir:
            self.output_preprocess_directory = os.path.join(output_target_dir, tile_name)
            if not os.path.exists(self.output_preprocess_directory):
                try:
                    os.mkdir(self.output_preprocess_directory)
                except:
                    pass
        else :
            self.output_preprocess_directory = self.tile_directory

        # sensors attributes
        self.native_res = 30
        self.data_type = "FRE"
        self.suffix = "STACK"
        self.masks_date_suffix = "BINARY_MASK"
        self.date_position = 1# if date's name split by "_"
        self.NODATA_VALUE = -10000
        self.masks_rules = OrderedDict({"CLM_XS.tif":0, "SAT_XS.tif":0, "EDG_ALL.tif":0})# 0 mean data, else noData
        self.border_pos = 2
        self.features_names_list = ["NDVI", "NDWI", "Brightness"]

        # define bands to get and their order
        self.stack_band_position = ["B1", "B2", "B3", "B4", "B5", "B6", "B7"]
        self.extracted_bands = None
        if extract_bands_flag:
            # TODO check every mandatory bands still selected -> def check_mandatory bands() return True/False
            self.extracted_bands = [(band_name, band_position + 1) for band_position, band_name in enumerate(self.stack_band_position) if band_name in self.cfg_IOTA2.getParam("Sentinel_2", "keepBands")]

        # output's names
        self.footprint_name = "{}_{}_footprint.tif".format(self.__class__.name,
                                                           tile_name)
        ref_image_name = "{}_{}_reference.tif".format(self.__class__.name,
                                                           tile_name)
        self.ref_image = os.path.join(self.cfg_IOTA2.getParam("chain", "outputPath"),
                                      "features",
                                      tile_name,
                                      "tmp",
                                      ref_image_name)
        self.time_series_name = "{}_{}_TS.tif".format(self.__class__.name,
                                                      tile_name)
        self.time_series_masks_name = "{}_{}_MASKS.tif".format(self.__class__.name,
                                                               tile_name)
        self.time_series_gapfilling_name = "{}_{}_TSG.tif".format(self.__class__.name,
                                                                  tile_name)
        self.features_names = "{}_{}_Features.tif".format(self.__class__.name,
                                                          tile_name)
        # about gapFilling interpolations
        self.temporal_res = self.cfg_IOTA2.getParam("Sentinel_2", "temporalResolution")
        self.input_dates = "{}_{}_input_dates.txt".format(self.__class__.name,
                                                           tile_name)
        self.interpolated_dates = "{}_{}_interpolation_dates.txt".format(self.__class__.name,
                                                                         tile_name)

    def get_date_from_name(self, product_name):
        """
        """
        return product_name.split("_")[self.date_position].split("-")[0]

    def sort_dates_directories(self, dates_directories):
        """
        """
        return sorted(dates_directories,
                      key=lambda x : int(os.path.basename(x).split("_")[self.date_position].split("-")[0]))

    def get_available_dates(self):
        """
        return sorted available dates
        """
        from Common.FileUtils import FileSearch_AND

        stacks = sorted(FileSearch_AND(self.output_preprocess_directory, True, "{}.tif".format(self.suffix)),
                        key=lambda x : int(os.path.basename(x).split("_")[self.date_position].split("-")[0]))
        return stacks

    def get_available_dates_masks(self):
        """
        return sorted available masks
        """
        from Common.FileUtils import FileSearch_AND
        masks = sorted(FileSearch_AND(self.output_preprocess_directory, True, "{}.tif".format(self.masks_date_suffix)),
                       key=lambda x : int(os.path.basename(x).split("_")[self.date_position].split("-")[0]))
        return masks

    def build_stack_date_name(self, date_dir):
        """
        """
        from Common.FileUtils import FileSearch_AND
        _, b2_name = os.path.split(FileSearch_AND(date_dir, True, "{}_B2.tif".format(self.data_type))[0])
        return b2_name.replace("{}_B2.tif".format(self.data_type), "{}_{}.tif".format(self.data_type, self.suffix))

    def preprocess_date(self, date_dir, out_prepro, working_dir=None, ram=128,
                        logger=logger):
        """
        """
        import os
        import shutil
        from gdal import Warp
        from osgeo.gdalconst import  GDT_Byte

        from Common.FileUtils import ensure_dir
        from Common.FileUtils import getRasterProjectionEPSG
        from Common.FileUtils import FileSearch_AND
        from Common.OtbAppBank import CreateConcatenateImagesApplication
        from Common.OtbAppBank import CreateSuperimposeApplication

        # manage directories
        date_stack_name = self.build_stack_date_name(date_dir)
        logger.debug("preprocessing {}".format(date_dir))
        out_stack = os.path.join(date_dir, date_stack_name)
        if out_prepro:
            _, date_dir_name = os.path.split(date_dir)
            out_dir = os.path.join(out_prepro, date_dir_name)
            if not os.path.exists(out_dir):
                try:
                    os.mkdir(out_dir)
                except:
                    logger.warning("{} already exists".format(out_dir))
            out_stack = os.path.join(out_dir, date_stack_name)

        out_stack_processing = out_stack
        if working_dir:
            out_stack_processing = os.path.join(working_dir, date_stack_name)

        # get bands
        date_bands = [FileSearch_AND(date_dir, True, "{}_{}.tif".format(self.data_type, bands_name))[0] for bands_name in self.stack_band_position]

        # tile reference image generation
        base_ref = date_bands[0]
        ensure_dir(os.path.dirname(self.ref_image), raise_exe=False)
        base_ref_projection = getRasterProjectionEPSG(base_ref)

        if not os.path.exists(self.ref_image):
            logger.info("reference image generation {} from {}".format(self.ref_image, base_ref))
            ds = Warp(self.ref_image, base_ref, multithread=True,
                      format="GTiff", xRes=self.native_res, yRes=self.native_res,
                      outputType=GDT_Byte, srcSRS="EPSG:{}".format(base_ref_projection),
                      dstSRS="EPSG:{}".format(self.target_proj))

        # reproject / resample
        bands_proj = OrderedDict()
        all_reproj = []
        for band, band_name in zip(date_bands, self.stack_band_position):
            superimp, _ = CreateSuperimposeApplication({"inr": self.ref_image,
                                                        "inm": band,
                                                        "ram": str(ram)})
            bands_proj[band_name] = superimp
            all_reproj.append(superimp)

        if not self.full_pipeline:
            for reproj in all_reproj:
                reproj.Execute()
            date_stack = CreateConcatenateImagesApplication({"il": all_reproj,
                                                             "ram": str(ram),
                                                             "pixType" : "int16",
                                                             "out": out_stack_processing})
            if not os.path.exists(out_stack):
                date_stack.ExecuteAndWriteOutput()
                if working_dir:
                    shutil.copy(out_stack_processing, out_stack)
                    os.remove(out_stack_processing)
        return bands_proj if self.full_pipeline else out_stack

    def preprocess_date_masks(self, date_dir, out_prepro,
                              working_dir=None, ram=128,
                              logger=logger):
        """
        """
        from gdal import Warp
        import shutil
        from Common.FileUtils import ensure_dir
        from Common.OtbAppBank import CreateBandMathApplication
        from Common.OtbAppBank import CreateSuperimposeApplication
        from Common.FileUtils import getRasterProjectionEPSG

        # TODO : throw Exception if no masks are found
        date_mask = []
        for mask_name, rule in self.masks_rules.items():
            date_mask.append(glob.glob(os.path.join(date_dir, "{}{}".format(self.struct_path_masks, mask_name)))[0])
        
        # manage directories
        mask_dir = os.path.dirname(date_mask[0])
        logger.debug("preprocessing {} masks".format(mask_dir))
        mask_name = os.path.basename(date_mask[0]).replace(self.masks_rules.items()[0][0],
                                                           "{}.tif".format(self.masks_date_suffix))
        out_mask = os.path.join(mask_dir, mask_name)
        if out_prepro:
            _, date_dir_name = os.path.split(mask_dir)
            out_mask_dir = mask_dir.replace(os.path.join(self.l8_data, self.tile_name), out_prepro)
            ensure_dir(out_mask_dir, raise_exe=False)
            out_mask = os.path.join(out_mask_dir, mask_name)

        out_mask_processing = out_mask
        if working_dir:
            out_mask_processing = os.path.join(working_dir, mask_name)

        # build binary mask
        expr = "+".join(["im{}b1".format(cpt + 1) for cpt in range(len(date_mask))])
        expr = "({})==0?0:1".format(expr)
        binary_mask_rule = CreateBandMathApplication({"il": date_mask,
                                                      "exp":expr})
        binary_mask_rule.Execute()
        # reproject using reference image
        superimp, _ = CreateSuperimposeApplication({"inr": self.ref_image,
                                                    "inm": binary_mask_rule,
                                                    "out": out_mask_processing,
                                                    "pixType":"uint8",
                                                    "ram": str(ram)})
        
        # needed to travel throught iota2's library
        app_dep = [binary_mask_rule]
        
        if not self.full_pipeline:
            if not os.path.exists(out_mask):
                superimp.ExecuteAndWriteOutput()
                if working_dir:
                    shutil.copy(out_mask_processing, out_mask)
                    os.remove(out_mask_processing)

        return superimp, app_dep

    def preprocess(self, working_dir=None, ram=128, logger=logger):
        """
        """
        input_dates = [os.path.join(self.tile_directory, cdir) for cdir in os.listdir(self.tile_directory)]
        input_dates = self.sort_dates_directories(input_dates)

        preprocessed_dates = OrderedDict() 
        for date in input_dates:
            data_prepro = self.preprocess_date(date, self.output_preprocess_directory,
                                               working_dir, ram)
            data_mask = self.preprocess_date_masks(date, self.output_preprocess_directory,
                                                   working_dir, ram)
            current_date = self.get_date_from_name(os.path.basename(date))
            # TODO check if current_date already exists
            preprocessed_dates[current_date] = {"data": data_prepro,
                                                "mask": data_mask}
        return preprocessed_dates

    def footprint(self, ram=128):
        """
        """
        pass

    def get_time_series(self, ram=128):
        """
        """
        pass

    def get_time_series_masks(self, ram=128, logger=logger):
        """
        """
        pass

    def get_time_series_gapFilling(self, ram=128):
        """
        """
        pass

    def get_features(self, ram=128, logger=logger):
        """
        """
        pass