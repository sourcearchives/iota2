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

class Sentinel_2_L3A(Sensor):

    name = 'Sentinel2L3A'

    def __init__(self, config_path, tile_name):
        from Common import ServiceConfigFile as SCF
        Sensor.__init__(self)

        if not os.path.exists(config_path):
            return

        self.cfg_IOTA2 = SCF.serviceConfigFile(config_path)
        cfg_sensors = (self.cfg_IOTA2.getParam("chain", "pyAppPath")).split(os.path.sep)
        cfg_sensors = (os.path.sep).join(cfg_sensors[0:-1] + ["config", "sensors.cfg"])
        cfg_sensors = SCF.serviceConfigFile(cfg_sensors, iota_config=False)
        
        # attributes
        self.s2_l3a_data = self.cfg_IOTA2.getParam("chain", "S2_L3A_Path")
        self.all_tiles = self.cfg_IOTA2.getParam("chain", "listTile")

        output_target_dir = self.cfg_IOTA2.getParam("chain", "S2_L3A_output_path")
        self.tile_name = tile_name
        self.tile_directory = os.path.join(self.s2_l3a_data, tile_name)
        self.target_proj = int(self.cfg_IOTA2.getParam("GlobChain", "proj").lower().replace(" ","").replace("epsg:",""))
        self.struct_path_data = cfg_sensors.getParam("Sentinel_2_L3A", "arbo")
        self.struct_path_masks = cfg_sensors.getParam("Sentinel_2_L3A", "arbomask")
        self.suffix = "STACK"
        self.suffix_mask = "BINARY_MASK"
        self.masks_pattern = "FLG_R1.tif"
        self.masks_values = [0, 1] # NODATA, CLOUD
        self.date_position = 1 # if date's name split by "_"
        self.features_dir = os.path.join(self.cfg_IOTA2.getParam("chain", "outputPath"),
                                         "features", tile_name)
        extract_bands = self.cfg_IOTA2.getParam("Sentinel_2_L3A", "keepBands")
        extract_bands_flag = self.cfg_IOTA2.getParam("iota2FeatureExtraction", "extractBands")

        # outputs
        self.footprint_name = "{}_{}_footprint.tif".format(self.__class__.name,
                                                           tile_name)
        self.time_series_name = "{}_{}_TS.tif".format(self.__class__.name,
                                                      tile_name)
        self.time_series_gapfilling_name = "{}_{}_TSG.tif".format(self.__class__.name,
                                                                  tile_name)
        self.time_series_masks_name = "{}_{}_MASKS.tif".format(self.__class__.name,
                                                               tile_name)
        self.features_names = "{}_{}_Features.tif".format(self.__class__.name,
                                                          tile_name)
        # bands order
        self.stack_band_position = ["B2", "B3", "B4", "B5", "B6",
                                    "B7", "B8", "B8A", "B11", "B12"]
        # TODO move into the base-class
        self.extracted_bands = None
        if extract_bands_flag:
            # TODO check every mandatory bands still selected -> def check_mandatory bands() return True/False
            self.extracted_bands = [(band_name, band_position + 1) for band_position, band_name in enumerate(self.stack_band_position) if band_name in self.cfg_IOTA2.getParam("Sentinel_2_L3A", "keepBands")]

        # about gapFilling interpolations
        self.temporal_res = self.cfg_IOTA2.getParam("Sentinel_2_L3A", "temporalResolution")
        self.input_dates = "{}_{}_input_dates.txt".format(self.__class__.name,
                                                           tile_name)
        self.interpolated_dates = "{}_{}_interpolation_dates.txt".format(self.__class__.name,
                                                                         tile_name)
        if output_target_dir:
            self.output_preprocess_directory = os.path.join(output_target_dir, tile_name)
            if not os.path.exists(self.output_preprocess_directory):
                try:
                    os.mkdir(self.output_preprocess_directory)
                except:
                    pass
        else :
            self.output_preprocess_directory = self.tile_directory
        
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
        _, b2_name = os.path.split(FileSearch_AND(date_dir, True, "FRC_B2.tif")[0])
        return b2_name.replace("FRC_B2.tif", "FRC_{}.tif".format(self.suffix))

    def preprocess_date(self, date_dir, out_prepro, working_dir=None, ram=128,
                        logger=logger):
        """
        """
        import os
        import shutil
        from gdal import Warp
        from Common.FileUtils import getRasterProjectionEPSG
        from Common.FileUtils import FileSearch_AND
        from Common.OtbAppBank import CreateConcatenateImagesApplication

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
        b2 = FileSearch_AND(date_dir, True, "FRC_B2.tif")[0]
        b3 = FileSearch_AND(date_dir, True, "FRC_B3.tif")[0]
        b4 = FileSearch_AND(date_dir, True, "FRC_B4.tif")[0]
        b5 = FileSearch_AND(date_dir, True, "FRC_B5.tif")[0]
        b6 = FileSearch_AND(date_dir, True, "FRC_B6.tif")[0]
        b7 = FileSearch_AND(date_dir, True, "FRC_B7.tif")[0]
        b8 = FileSearch_AND(date_dir, True, "FRC_B8.tif")[0]
        b8a = FileSearch_AND(date_dir, True, "FRC_B8A.tif")[0]
        b11 = FileSearch_AND(date_dir, True, "FRC_B11.tif")[0]
        b12 = FileSearch_AND(date_dir, True, "FRC_B12.tif")[0]

        # resample bands
        (b5_10m, b6_10m,
         b7_10m, b8a_10m,
         b11_10m, b12_10m) = [self.resample(band, 10, out_prepro, working_dir, ram) for band in [b5, b6, b7, b8a, b11, b12]]

        # stack bands
        logger.info("Creating : {}".format(out_stack))
        stack_bands = CreateConcatenateImagesApplication({"il": [b2, b3, b4, b5_10m,
                                                                 b6_10m, b7_10m, b8,
                                                                 b8a_10m, b11_10m, b12_10m],
                                                          "out": out_stack_processing,
                                                          "ram": str(ram)})
        if not os.path.exists(out_stack):
            stack_bands.ExecuteAndWriteOutput()
            if working_dir:
                shutil.copy(out_stack_processing, out_stack)
                os.remove(out_stack_processing)

        # reproject if needed
        stack_projection = getRasterProjectionEPSG(out_stack)
        if int(self.target_proj) != int(stack_projection):
            logger.info("Reprojecting {}".format(out_stack))
            ds = Warp(out_stack, out_stack,
                      multithread=True, format="GTiff", xRes=10, yRes=10,
                      srcSRS="EPSG:{}".format(stack_projection), dstSRS="EPSG:{}".format(self.target_proj),
                      options=["INIT_DEST=-10000"])
            logger.info("Reprojection succeed")
        logger.info("End preprocessing")

    def resample(self, band, out_size, out_prepro, working_dir, ram, logger=logger):
        """
        """
        import os
        import shutil
        from Common.OtbAppBank import CreateRigidTransformResampleApplication
        from Common.FileUtils import readRaster

        # manage directories
        out_band_name = os.path.split(band)[1].replace(".tif", "_10M.tif")
        _, date_dir_name = os.path.split(os.path.dirname(band))
        out_band = os.path.join(date_dir_name, out_band_name)
        if out_prepro:
            out_dir = os.path.join(out_prepro, date_dir_name)
            out_band = os.path.join(out_dir, out_band_name)
        out_band_processing = out_band
        if working_dir:
            out_band_processing = os.path.join(working_dir, out_band_name)

        # resampling
        if not os.path.exists(out_band):
            logger.info("Creating {}".format(out_band_processing))
            _, _, _, (_, x_res, _, _, _, y_res) = readRaster(band)
            rigid_app = CreateRigidTransformResampleApplication({"in":band, 
                                                                 "transform.type.id.scalex": float(x_res) / float(out_size),
                                                                 "transform.type.id.scaley": float(x_res) / float(out_size),
                                                                 "ram":ram,
                                                                 "out":out_band_processing})
            rigid_app.ExecuteAndWriteOutput()

            if working_dir:
                shutil.copy(out_band_processing, out_band)
                os.remove(out_band_processing)

        return out_band

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
        date_mask = glob.glob(os.path.join(date_dir, "{}{}".format(self.struct_path_masks, self.masks_pattern)))[0]

        # manage directories
        mask_dir = os.path.dirname(date_mask)
        logger.debug("preprocessing {} masks".format(mask_dir))
        mask_name = os.path.basename(date_mask).replace(self.masks_pattern,
                                                        "{}.tif".format(self.suffix_mask))
        out_mask = os.path.join(mask_dir, mask_name)
        if out_prepro:
            _, date_dir_name = os.path.split(mask_dir)
            out_mask_dir = mask_dir.replace(os.path.join(self.s2_l3a_data, self.tile_name), out_prepro)
            ensure_dir(out_mask_dir, raise_exe=False)
            out_mask = os.path.join(out_mask_dir, mask_name)

        out_mask_processing = out_mask
        if working_dir:
            out_mask_processing = os.path.join(working_dir, mask_name)

        # compute mask
        if not os.path.exists(out_mask):
            mask_exp = "?1:".join(["im1b1=={}".format(value) for value in self.masks_values])
            mask_exp = "{}?1:0".format(mask_exp)
            mask_gen = CreateBandMathApplication({"il": date_mask,
                                                  "ram": str(ram),
                                                  "exp": mask_exp, 
                                                  "pixType": "uint8",
                                                  "out":out_mask_processing})
            mask_gen.ExecuteAndWriteOutput()
            if working_dir:
                shutil.copy(out_mask_processing, out_mask)
                os.remove(out_mask_processing)

        # reproject if needed
        mask_projection = getRasterProjectionEPSG(out_mask)
        if int(self.target_proj) != int(mask_projection):
            logger.info("Reprojecting {}".format(out_mask))
            ds = Warp(out_mask_processing, out_mask,
                      multithread=True, format="GTiff", xRes=10, yRes=10,
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
        for date in input_dates:
            self.preprocess_date(date, self.output_preprocess_directory,
                                 working_dir, ram)
            self.preprocess_date_masks(date, self.output_preprocess_directory,
                                       working_dir, ram)

    def footprint(self, ram=128):
        """
        in this case (L3A), we consider the whole tile
        """
        from Common.OtbAppBank import CreateBandMathApplication
        from Common.FileUtils import ensure_dir
        
        date = self.get_available_dates()[0]
        footprint_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(footprint_dir,raise_exe=False)
        footprint_out = os.path.join(footprint_dir, self.footprint_name)
        
        s2_l3a_border = CreateBandMathApplication({"il": date,
                                                   "out": footprint_out,
                                                   "exp":"1",
                                                   "ram": str(ram)})
        # needed to travel throught iota2's library
        app_dep = []

        return s2_l3a_border, app_dep

    def write_interpolation_dates_file(self):
        """
        TODO : mv to base-class
        """
        from Common.FileUtils import getDateS2
        from Common.FileUtils import ensure_dir
        from Common.FileUtils import dateInterval
        
        interp_date_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(interp_date_dir, raise_exe=False)
        interp_date_file = os.path.join(interp_date_dir, self.interpolated_dates)
        # get dates in the whole S2 data-set
        date_interp_min, date_interp_max = getDateS2(self.s2_l3a_data, self.all_tiles.split(" "))
        # force dates
        if not self.cfg_IOTA2.getParam("GlobChain", "autoDate"):
            date_interp_min = self.cfg_IOTA2.getParam("Sentinel_2_L3A", "startDate")
            date_interp_max = self.cfg_IOTA2.getParam("Sentinel_2_L3A", "endDate")

        dates = [str(date).replace("-","") for date in dateInterval(date_interp_min, date_interp_max, self.temporal_res)]
        if not os.path.exists(interp_date_file):
            with open(interp_date_file, "w") as interpolation_date_file:
                interpolation_date_file.write("\n".join(dates))
        return interp_date_file, dates

    def write_dates_file(self):
        """
        """
        from Common.FileUtils import ensure_dir
        date_file = os.path.join(self.features_dir, "tmp", self.input_dates)
        all_available_dates = [os.path.basename(date).split("_")[self.date_position].split("-")[0] for date in self.get_available_dates()]

        if not os.path.exists(date_file):
            with open(date_file, "w") as input_date_file:
                input_date_file.write("\n".join(all_available_dates))
        return date_file, all_available_dates

    def get_time_series(self, ram=128):
        """
        TODO : be able of using a date interval
        Return
        ------
            list
                [(otb_Application, some otb's objects), time_series_labels]
                Functions dealing with otb's application instance has to 
                returns every objects in the pipeline
        """
        from Common.OtbAppBank import CreateConcatenateImagesApplication
        from Common.FileUtils import ensure_dir

        dates_concatenation = self.get_available_dates()
        
        time_series_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(time_series_dir, raise_exe=False)
        times_series_raster = os.path.join(time_series_dir, self.time_series_name)
        dates_time_series = CreateConcatenateImagesApplication({"il": dates_concatenation,
                                                                "out": times_series_raster,
                                                                "pixType": "int16",
                                                                "ram": str(ram)})
        dates_in_file, dates_in = self.write_dates_file()
        # build labels
        features_labels = ["{}_{}_{}".format(self.__class__.name, band_name, date) for date in dates_in for band_name in self.stack_band_position]

        # needed to travel throught iota2's library
        app_dep = []

        # if not all bands must be used
        if self.extracted_bands:
            app_dep.append(dates_time_series)
            (dates_time_series,
             features_labels) = self.extract_bands_time_series(dates_time_series,
                                                               dates_in,
                                                               len(self.stack_band_position),
                                                               self.extracted_bands,
                                                               ram)

        return (dates_time_series, app_dep), features_labels

    def extract_bands_time_series(self, dates_time_series,
                                  dates_in,
                                  comp,
                                  extract_bands,
                                  ram):
        """
        TODO : mv to base class ?
        extract_bands : list
             [('bandName', band_position), ...]
        comp : number of bands in original stack
        """
        from Common.OtbAppBank import CreateExtractROIApplication

        nb_dates = len(dates_in)
        channels_interest = []
        for date_number in range(nb_dates):
            for band_name, band_position in extract_bands:
                channels_interest.append(band_position + int(date_number * comp))

        features_labels = ["{}_{}_{}".format(self.__class__.name, band_name, date) for date in dates_in for band_name, band_pos in extract_bands]
        channels_list = ["Channel{}".format(channel) for channel in channels_interest]
        time_series_out = dates_time_series.GetParameterString("out")
        dates_time_series.Execute()
        extract = CreateExtractROIApplication({"in":dates_time_series,
                                               "cl":channels_list,
                                               "ram":str(ram),
                                               "out":dates_time_series.GetParameterString("out")})
        return extract, features_labels

    def get_time_series_masks(self, ram=128, logger=logger):
        """
        """
        from Common.FileUtils import ensure_dir
        from Common.OtbAppBank import CreateConcatenateImagesApplication

        available_dates = self.get_available_dates()
        available_masks = self.get_available_dates_masks()
        if len(available_dates) != len(available_masks):
            error = "Available dates ({}) and avaibles masks ({}) are different".format(available_dates,
                                                                                             available_masks)
            logger.error(error)
            raise Exception (error)

        time_series_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(time_series_dir, raise_exe=False)
        times_series_masks_raster = os.path.join(time_series_dir, self.time_series_masks_name)
        dates_time_series = CreateConcatenateImagesApplication({"il": available_masks,
                                                                "out": times_series_masks_raster,
                                                                "pixType": "int16",
                                                                "ram": str(ram)})
        dep = []
        return dates_time_series, dep

    def get_time_series_gapFilling(self, ram=128):
        """
        """
        from Common.OtbAppBank import CreateImageTimeSeriesGapFillingApplication
        from Common.FileUtils import ensure_dir

        gap_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(gap_dir, raise_exe=False)
        gap_out = os.path.join(gap_dir, self.time_series_gapfilling_name)
        
        dates_interp_file, dates_interp = self.write_interpolation_dates_file()
        dates_in_file, _ = self.write_dates_file()
        masks, masks_dep = self.get_time_series_masks()
        (time_series, time_series_dep), _ = self.get_time_series()

        time_series.Execute()
        masks.Execute()
        
        comp = len(self.stack_band_position) if not self.extracted_bands else len(self.extracted_bands)

        # no temporal interpolation (only cloud)
        gap = CreateImageTimeSeriesGapFillingApplication({"in": time_series,
                                                          "mask": masks,
                                                          "comp": str(comp),
                                                          "it": "linear",
                                                          "out": gap_out,
                                                          "ram": str(ram),
                                                          "pixType": "int16"})
        app_dep = [time_series, masks, masks_dep, time_series_dep]

        bands = self.stack_band_position
        if self.extracted_bands:
            bands = [band_name for band_name, band_pos in self.extracted_bands]

        features_labels = ["{}_{}_{}".format(self.__class__.name, band_name, date) for date in dates_interp for band_name in bands]
        return (gap, app_dep), features_labels

    def get_features(self, ram=128, logger=logger):
        """
        """
        from Common.OtbAppBank import CreateIota2FeatureExtractionApplication
        from Common.FileUtils import ensure_dir

        features_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(features_dir, raise_exe=False)
        features_out = os.path.join(features_dir, self.features_names)
        
        features = self.cfg_IOTA2.getParam("GlobChain", "features")
        enable_gapFilling = self.cfg_IOTA2.getParam("GlobChain", "useGapFilling")
        
        (in_stack, in_stack_dep), in_stack_features_labels = self.get_time_series_gapFilling()
        if not enable_gapFilling:
            (in_stack, in_stack_dep), in_stack_features_labels = self.get_sensors_time_series()

        in_stack.Execute()
        
        if features:
            bands_avail = self.stack_band_position
            if self.extracted_bands:
                bands_avail = [band_name for band_name, _ in self.extracted_bands]
                # check mandatory bands
                if not "B4" in bands_avail:
                    raise Exception("red band (B4) is needed to compute features")
                if not "B8" in bands_avail:
                    raise Exception("nir band (B8) is needed to compute features")
                if not "B11" in bands_avail:
                    raise Exception("swir band (11) is needed to compute features")
            feat_parameters = {"in": in_stack,
                               "out": features_out,
                               "comp": len(bands_avail),
                               "red": bands_avail.index("B4") + 1,
                               "nir": bands_avail.index("B8") + 1,
                               "swir": bands_avail.index("B11") + 1,
                               "copyinput": self.cfg_IOTA2.getParam('iota2FeatureExtraction', 'copyinput'),
                               "pixType": "int16",
                               "ram": str(ram)}
            copyinput = self.cfg_IOTA2.getParam('iota2FeatureExtraction', 'copyinput')
            relRefl = self.cfg_IOTA2.getParam('iota2FeatureExtraction', 'relrefl')
            keepduplicates = self.cfg_IOTA2.getParam('iota2FeatureExtraction', 'keepduplicates')
            acorfeat = self.cfg_IOTA2.getParam('iota2FeatureExtraction', 'acorfeat')

            if relRefl:
                featExtr.SetParameterEmpty("relrefl", True)
                feat_parameters["relrefl"] = True
            if keepduplicates:
                feat_parameters["keepduplicates"] = True
            if acorfeat:
                feat_parameters["acorfeat"] = True
            features_app = CreateIota2FeatureExtractionApplication(feat_parameters)
        else:
            features_app = in_stack
        app_dep = [in_stack, in_stack_dep]
        features_labels = []
        return (features_app, app_dep), features_labels