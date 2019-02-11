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

class Sentinel_2_S2C(Sensor):

    name = 'Sentinel2S2C'

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
        self.s2_s2c_data = self.cfg_IOTA2.getParam("chain", "S2_S2C_Path")
        self.tile_directory = os.path.join(self.s2_s2c_data, tile_name)
        self.struct_path_masks = cfg_sensors.getParam("Sentinel_2_S2C", "arbomask")
        self.full_pipeline = self.cfg_IOTA2.getParam("Sentinel_2_S2C", "full_pipline")
        self.features_dir = os.path.join(self.cfg_IOTA2.getParam("chain", "outputPath"),
                                         "features", tile_name)
        extract_bands = self.cfg_IOTA2.getParam("Sentinel_2_S2C", "keepBands")
        extract_bands_flag = self.cfg_IOTA2.getParam("iota2FeatureExtraction", "extractBands")
        output_target_dir = self.cfg_IOTA2.getParam("chain", "S2_S2C_output_path")

        if output_target_dir:
            self.output_preprocess_directory = os.path.join(output_target_dir, tile_name)
            if not os.path.exists(self.output_preprocess_directory):
                try:
                    os.mkdir(self.output_preprocess_directory)
                except:
                    pass
        else :
            #~ self.output_preprocess_directory = self.tile_directory
            self.output_preprocess_directory = None

        # sensors attributes
        self.suffix = "STACK"
        self.masks_date_suffix = "BINARY_MASK"
        self.date_position = 2# if date's name split by "_"
        self.NODATA_VALUE = -10000
        #~ self.masks_rules = OrderedDict({"CLM_R1.tif":0, "SAT_R1.tif":0, "EDG_R1.tif":0})# 0 mean data, else noData
        #~ self.border_pos = 2
        self.features_names_list = ["NDVI", "NDWI", "Brightness"]

        # define bands to get and their order
        self.stack_band_position = ["B2", "B3", "B4", "B5", "B6",
                                    "B7", "B8", "B8A", "B11", "B12"]
        self.extracted_bands = None
        if extract_bands_flag:
            # TODO check every mandatory bands still selected -> def check_mandatory bands() return True/False
            self.extracted_bands = [(band_name, band_position + 1) for band_position, band_name in enumerate(self.stack_band_position) if band_name in self.cfg_IOTA2.getParam("Sentinel_2_S2C", "keepBands")]

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
        self.temporal_res = self.cfg_IOTA2.getParam("Sentinel_2_S2C", "temporalResolution")
        self.input_dates = "{}_{}_input_dates.txt".format(self.__class__.name,
                                                           tile_name)
        self.interpolated_dates = "{}_{}_interpolation_dates.txt".format(self.__class__.name,
                                                                         tile_name)
        
    def get_available_dates(self):
        """
        return sorted available dates
        """
        pass

    def get_available_dates_masks(self):
        """
        return sorted available masks
        """
        pass

    def sort_dates_directories(self, dates_directories):
        """
        """
        return sorted(dates_directories,
                      key=lambda x : int(os.path.basename(x).split("_")[self.date_position].split("T")[0]))

    def get_date_dir(self, date_dir, size):
        """
        """
        from Common.FileUtils import FileSearch_AND
        if size == 10:
            target_dir, _ = os.path.split(FileSearch_AND(date_dir, True, "10m.jp2")[0])
        elif size == 20:
            target_dir, _ = os.path.split(FileSearch_AND(date_dir, True, "20m.jp2")[0])
        else:
            raise Exception ("size not in [10, 20]")
        return target_dir

    def build_stack_date_name(self, date_dir):
        """
        """
        from Common.FileUtils import FileSearch_AND
        _, b2_name = os.path.split(FileSearch_AND(date_dir, True, "B02_10m.jp2")[0])
        return b2_name.replace("B02_10m.jp2", "{}.tif".format(self.suffix))

    def preprocess_date(self, date_dir, out_prepro, working_dir=None, ram=128,
                        logger=logger):
        """
        """
        from Common.FileUtils import ensure_dir
        # manage directories
        date_stack_name = self.build_stack_date_name(date_dir)
        logger.debug("preprocessing {}".format(date_dir))
        r10_dir = self.get_date_dir(date_dir, 10)

        out_stack = os.path.join(r10_dir, date_stack_name)
        if out_prepro:
            _, date_dir_name = os.path.split(date_dir)
            out_dir = r10_dir.replace(date_dir, out_prepro)
            ensure_dir(out_dir, raise_exe=False)
            out_stack = os.path.join(out_dir, date_stack_name)
        out_stack_processing = out_stack
        if working_dir:
            out_stack_processing = os.path.join(working_dir, date_stack_name)

    def preprocess(self, working_dir=None, ram=128, logger=logger):
        """
        """       
        input_dates = [os.path.join(self.tile_directory, cdir) for cdir in os.listdir(self.tile_directory)]
        input_dates = self.sort_dates_directories(input_dates)

        preprocessed_dates = OrderedDict() 
        for date in input_dates:
            data_prepro = self.preprocess_date(date, self.output_preprocess_directory,
                                               working_dir, ram)
            #~ data_mask = self.preprocess_date_masks(date, self.output_preprocess_directory,
                                                   #~ working_dir, ram)
            #~ current_date = self.get_date_from_name(os.path.basename(date))
            # TODO check if current_date already exists
            #~ preprocessed_dates[current_date] = {"data": data_prepro,
                                                #~ "mask": data_mask}
        #~ return preprocessed_dates

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