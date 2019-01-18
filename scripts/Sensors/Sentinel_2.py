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

class Sentinel_2(Sensor):

    name = 'Sentinel2'

    def __init__(self, config_path, tile_name):
        """
        """
        from Common import ServiceConfigFile as SCF
        Sensor.__init__(self)

        if not os.path.exists(config_path):
            return

        
        self.cfg_IOTA2 = SCF.serviceConfigFile(config_path)
        cfg_sensors = (self.cfg_IOTA2.getParam("chain", "pyAppPath")).split(os.path.sep)
        cfg_sensors = (os.path.sep).join(cfg_sensors[0:-1] + ["config", "sensors.cfg"])
        cfg_sensors = SCF.serviceConfigFile(cfg_sensors, iota_config=False)

        # run attributes
        self.target_proj = int(self.cfg_IOTA2.getParam("GlobChain", "proj").lower().replace(" ","").replace("epsg:",""))
        self.s2_data = self.cfg_IOTA2.getParam("chain", "S2Path")
        self.tile_directory = os.path.join(self.s2_data, tile_name)
        self.struct_path_masks = cfg_sensors.getParam("Sentinel_2", "arbomask")
        self.full_pipeline = self.cfg_IOTA2.getParam("Sentinel_2", "full_pipline")

        # sensors attributes
        self.data_type = "FRE"
        self.output_preprocess_directory = ""
        self.suffix = "STACK"
        self.date_position = 1# if date's name split by "_"
        self.NODATA_VALUE = -10000
        self.masks_rules = {"CLM_R1.tif":1, "SAT_R1.tif":2, "EDG_R1.tif":3}
        # define bands to get and their order
        self.stack_band_position = ["B2", "B3", "B4", "B5", "B6",
                                    "B7", "B8", "B8A", "B11", "B12"]
        # outputs
        ref_image_name = "{}_{}_reference.tif".format(self.__class__.name,
                                                           tile_name)
        self.ref_image = os.path.join(self.cfg_IOTA2.getParam("chain", "outputPath"),
                                      "features",
                                      tile_name,
                                      "tmp",
                                      ref_image_name)

    def sort_dates_directories(self, dates_directories):
        """
        """
        return sorted(dates_directories,
                      key=lambda x : os.path.basename(x).split("_")[self.date_position].split("-")[0])

    def get_available_dates(self):
        """
        return sorted available dates
        """
        from Common.FileUtils import FileSearch_AND

        stacks = sorted(FileSearch_AND(self.output_preprocess_directory, True, "{}.tif".format(self.suffix)),
                        key=lambda x : os.path.basename(x).split("_")[self.date_position].split("-")[0])
        return stacks

    def get_available_dates_masks(self):
        """
        return sorted available masks
        """
        from Common.FileUtils import FileSearch_AND

        masks = sorted(FileSearch_AND(self.output_preprocess_directory, True, "{}.tif".format(self.suffix_mask)),
                       key=lambda x : os.path.basename(x).split("_")[self.date_position].split("-")[0])
        return masks

    def build_stack_date_name(self, date_dir):
        """
        """
        from Common.FileUtils import FileSearch_AND
        _, b2_name = os.path.split(FileSearch_AND(date_dir, True, "FRE_B2.tif")[0])
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
        logger.info("reference image generation {} from {}".format(self.ref_image, base_ref))
        ensure_dir(os.path.dirname(self.ref_image), raise_exe=False)
        base_ref_projection = getRasterProjectionEPSG(base_ref)
        ds = Warp(self.ref_image, base_ref, multithread=True,
                  format="GTiff", xRes=10, yRes=10,
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
        from Common.FileUtils import getRasterProjectionEPSG

        # TODO : throw Exception if no masks are found
        date_mask = []
        for mask_name, rule in self.masks_rules.items():
            #~ date_mask.append(glob.glob(os.path.join(date_dir, "{}{}".format(self.struct_path_masks, mask_name)))[0])
            date_mask = glob.glob(os.path.join(date_dir, "{}{}".format(self.struct_path_masks, mask_name)))[0]
            # manage directories
            mask_dir = os.path.dirname(date_mask)
            logger.debug("preprocessing {} masks".format(mask_dir))
            mask_name = os.path.basename(date_mask).replace(".tif",
                                                            "_{}.tif".format(self.masks_date_suffix))
            out_mask = os.path.join(mask_dir, mask_name)
            if out_prepro:
                _, date_dir_name = os.path.split(mask_dir)
                out_mask_dir = mask_dir.replace(os.path.join(self.s2_l3a_data, self.tile_name), out_prepro)
                ensure_dir(out_mask_dir, raise_exe=False)
                out_mask = os.path.join(out_mask_dir, mask_name)

            out_mask_processing = out_mask
            if working_dir:
                out_mask_processing = os.path.join(working_dir, mask_name)

            # reprojection
            mask_projection = getRasterProjectionEPSG(date_mask)
            if not os.path.exists(out_mask):
                logger.info("Reprojecting {}".format(out_mask))
                ds = Warp(out_mask_processing, date_mask,
                          srcSRS="EPSG:{}".format(mask_projection), dstSRS="EPSG:{}".format(self.target_proj))# multithread=False, format="GTiff", xRes=10, yRes=10, ,options=["INIT_DEST=0"]
                          
                if working_dir:
                    shutil.copy(out_mask_processing, out_mask)
                    os.remove(out_mask_processing)
                logger.info("Reprojection succeed")
            else:
                mask_projection = getRasterProjectionEPSG(out_mask)
                if int(self.target_proj) != int(mask_projection):
                    logger.info("Reprojecting {}".format(out_mask))
                    ds = Warp(out_mask_processing, out_mask,
                              multithread=False, format="GTiff", xRes=10, yRes=10,
                              srcSRS="EPSG:{}".format(mask_projection), dstSRS="EPSG:{}".format(self.target_proj),
                              options=["INIT_DEST=0"])
                    if working_dir:
                        shutil.copy(out_mask_processing, out_mask)
                        os.remove(out_mask_processing)
                    logger.info("Reprojection succeed")
                logger.info("End preprocessing")

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
            #~ current_date = self.get_date_from_name(os.path.basename(data_mask))
            #~ # TODO check if current_date already exists
            #~ preprocessed_dates[current_date] = {"data": data_prepro,
                                                #~ "mask": data_mask}
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