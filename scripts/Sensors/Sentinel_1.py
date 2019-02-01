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

class Sentinel_1(Sensor):

    name = 'Sentinel1'

    def __init__(self, config_path, tile_name):
        """
        """
        import ConfigParser
        from Common import ServiceConfigFile as SCF
        Sensor.__init__(self)

        if not os.path.exists(config_path):
            return

        self.tile_name = tile_name
        self.cfg_IOTA2 = SCF.serviceConfigFile(config_path)
        cfg_sensors = (self.cfg_IOTA2.getParam("chain", "pyAppPath")).split(os.path.sep)
        cfg_sensors = (os.path.sep).join(cfg_sensors[0:-1] + ["config", "sensors.cfg"])
        cfg_sensors = SCF.serviceConfigFile(cfg_sensors, iota_config=False)
        
        config_parser = ConfigParser.ConfigParser()

        # running attributes
        self.s1_cfg = self.cfg_IOTA2.getParam("chain", "S1Path")
        config_parser.read(self.s1_cfg)
        s1_output_processing = config_parser.get('Paths', 'output')
        self.all_tiles = self.cfg_IOTA2.getParam("chain", "listTile")
        self.output_processing = os.path.join(s1_output_processing, tile_name[1:])
        self.features_dir = os.path.join(self.cfg_IOTA2.getParam("chain", "outputPath"),
                                         "features", tile_name)
        self.use_gapfilling = self.cfg_IOTA2.getParam("GlobChain", "useGapFilling")
        # sensors attributes
        self.mask_pattern = "BorderMask.tif"
        # output's names
        self.mask_orbit_pol_name = "{}_{}_MASK".format(self.__class__.name, tile_name)
        self.gapFilling_orbit_pol_name = "{}_{}_TSG".format(self.__class__.name, tile_name)
        self.sar_features_name = "{}_{}_TSF".format(self.__class__.name, tile_name)
        self.footprint_name = "{}_{}_footprint.tif".format(self.__class__.name,
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

    def preprocess(self, working_dir=None, ram=128, logger=logger):
        """
        """
        from SAR.S1Processor import S1PreProcess
        # TODO, propagate the ram parameter
        S1PreProcess(self.s1_cfg, self.tile_name, working_dir)

    def footprint(self, ram=128):
        """
        """
        from Common.OtbAppBank import CreateBandMathApplication
        from Common.FileUtils import FileSearch_AND
        s1_border_masks = FileSearch_AND(self.output_processing, True, self.mask_pattern)
        
        sum_mask = "+".join(["im{}b1".format(i + 1) for i in range(len(s1_border_masks))])
        expression = "{}=={}?0:1".format(sum_mask, len(s1_border_masks))
        raster_footprint = os.path.join(self.features_dir, "tmp", self.footprint_name)
        footprint_app = CreateBandMathApplication({"il": s1_border_masks,
                                                   "out": raster_footprint,
                                                   "exp": expression,
                                                   "ram": str(ram)})
        footprint_app_dep = []
        return footprint_app, footprint_app_dep

    def get_time_series(self, ram=128):
        """
        Due to the SAR data, time series must be split by polarisation and orbit
        (ascending / descending)
        """
        from Common.OtbAppBank import getSARstack
        from Common.FileUtils import getNbDateInTile
        (allFiltered,
         allMasks,
         interpDateFiles,
         inputDateFiles) = getSARstack(self.s1_cfg,
                                       self.tile_name,
                                       self.all_tiles.split(" "),
                                       os.path.join(self.cfg_IOTA2.getParam("chain", "outputPath"),
                                                    "features"),
                                       workingDirectory=None)
        # to be clearer
        s1_data = OrderedDict()
        s1_labels = OrderedDict()

        for filtered, masks, interp_dates, in_dates in zip(allFiltered, allMasks, interpDateFiles, inputDateFiles):
            sar_mode = os.path.basename(filtered.GetParameterValue("outputstack"))
            sar_mode = "_".join(os.path.splitext(sar_mode)[0].split("_")[0:-1])
            polarisation = sar_mode.split("_")[1]
            orbit = sar_mode.split("_")[2]

            s1_data[sar_mode] = filtered
            sar_dates = sorted(getNbDateInTile(in_dates, display=False, raw_dates=True),key=lambda x: int(x))
            labels = ["{}_{}_{}_{}".format(self.__class__.name, orbit, polarisation, date).lower() for date in sar_dates]
            s1_labels[sar_mode] = labels
        dependancies = []
        return (s1_data, dependancies), s1_labels

    def get_time_series_masks(self, ram=128, logger=logger):
        """
        Due to the SAR data, masks series must be split by polarisation and orbit
        (ascending / descending)
        """
        from Common.OtbAppBank import getSARstack
        from Common.OtbAppBank import CreateConcatenateImagesApplication
        (allFiltered,
         allMasks,
         interpDateFiles,
         inputDateFiles) = getSARstack(self.s1_cfg,
                                       self.tile_name,
                                       self.all_tiles.split(" "),
                                       os.path.join(self.cfg_IOTA2.getParam("chain", "outputPath"),
                                                    "features"),
                                       workingDirectory=None)
        # to be clearer
        s1_masks = OrderedDict()
        for filtered, masks, interp_dates, in_dates in zip(allFiltered, allMasks, interpDateFiles, inputDateFiles):
            sar_mode = os.path.basename(filtered.GetParameterValue("outputstack"))
            sar_mode = "_".join(os.path.splitext(sar_mode)[0].split("_")[0:-1])
            polarisation = sar_mode.split("_")[1]
            orbit = sar_mode.split("_")[2]
            mask_orbit_pol_name = "{}_{}_{}.tif".format(self.mask_orbit_pol_name,
                                                        orbit, polarisation)

            mask_orbit_pol = os.path.join(self.features_dir, "tmp", mask_orbit_pol_name)
            masks_app = CreateConcatenateImagesApplication({"il": masks,
                                                            "out": mask_orbit_pol,
                                                            "pixType": "uint8" if len(masks) > 255 else "uint16",
                                                            "ram": str(ram)})
            s1_masks[sar_mode] = masks_app

        dependancies = []
        return s1_masks, dependancies, len(dates_masks)

    def get_time_series_gapFilling(self, ram=128):
        """
        Due to the SAR data, time series must be split by polarisation and orbit
        (ascending / descending)
        """
        import ConfigParser

        from Common.FileUtils import getNbDateInTile
        from Common.OtbAppBank import getSARstack
        from Common.OtbAppBank import CreateConcatenateImagesApplication
        from Common.OtbAppBank import CreateImageTimeSeriesGapFillingApplication

        (allFiltered,
         allMasks,
         interpDateFiles,
         inputDateFiles) = getSARstack(self.s1_cfg,
                                       self.tile_name,
                                       self.all_tiles.split(" "),
                                       os.path.join(self.cfg_IOTA2.getParam("chain", "outputPath"),
                                                    "features"),
                                       workingDirectory=None)
        # to be clearer
        s1_data = OrderedDict()
        s1_labels = OrderedDict()

        config = ConfigParser.ConfigParser()
        config.read(self.s1_cfg)

        interpolation_method = "linear"
        if config.has_option("Processing", "gapFilling_interpolation"):
            interpolation_method = config.get("Processing", "gapFilling_interpolation")
        dependancies = []

        for filtered, masks, interp_dates, in_dates in zip(allFiltered, allMasks, interpDateFiles, inputDateFiles):
            sar_mode = os.path.basename(filtered.GetParameterValue("outputstack"))
            sar_mode = "_".join(os.path.splitext(sar_mode)[0].split("_")[0:-1])
            polarisation = sar_mode.split("_")[1]
            orbit = sar_mode.split("_")[2]

            masks_stack = CreateConcatenateImagesApplication({"il":masks})
            masks_stack.Execute()
            filtered.Execute()
            dependancies.append((filtered, masks_stack))
            gapFilling_orbit_pol_name = "{}_{}_{}.tif".format(self.gapFilling_orbit_pol_name,
                                                              orbit, polarisation)
            gapFilling_raster = os.path.join(self.features_dir, "tmp", gapFilling_orbit_pol_name)
            gap_app = CreateImageTimeSeriesGapFillingApplication({"in": filtered,
                                                                  "mask": masks_stack,
                                                                  "it": interpolation_method,
                                                                  "id": in_dates,
                                                                  "od": interp_dates,
                                                                  "comp": str(1),
                                                                  "out": gapFilling_raster})
            s1_data[sar_mode] = gap_app

            sar_dates = sorted(getNbDateInTile(interp_dates, display=False, raw_dates=True),key=lambda x: int(x))
            labels = ["{}_{}_{}_{}".format(self.__class__.name, orbit, polarisation, date).lower() for date in sar_dates]
            s1_labels[sar_mode] = labels
            
        return (s1_data, dependancies), s1_labels

    def get_features(self, ram=128, logger=logger):
        """
        """
        import ConfigParser
        from Common.FileUtils import getNbDateInTile, FileSearch_AND
        from Common.OtbAppBank import CreateConcatenateImagesApplication
        from Common.OtbAppBank import generateSARFeat_dates

        if self.use_gapfilling:
            (s1_data, dependancies), s1_labels = self.get_time_series_gapFilling(ram)
        else:
            (s1_data, dependancies), s1_labels = self.get_time_series(ram)
        config = ConfigParser.ConfigParser()
        config.read(self.s1_cfg)

        sar_features_expr = None
        if config.has_option("Features", "expression"):
            sar_features_expr_cfg = config.get("Features", "expression")
            if not "none" in sar_features_expr_cfg.lower():
                sar_features_expr = sar_features_expr_cfg.split(",")

        dependancies = [dependancies]
        s1_features = []
        sar_time_series = {"asc": {"vv":{"App":None,
                                         "availDates":None},
                                   "vh":{"App":None,
                                         "availDates":None}},
                           "des": {"vv":{"App":None,
                                         "availDates":None},
                                   "vh":{"App":None,
                                         "availDates":None}}}
        for sensor_mode, time_series_app in s1_data.items():
            _, polarisation, orbit = sensor_mode.split("_")
            sar_time_series[orbit.lower()][polarisation.lower()]["App"] = time_series_app
            time_series_app.Execute()
            s1_features.append(time_series_app)
            dependancies.append(time_series_app)
            if self.use_gapfilling:
                date_file = FileSearch_AND(self.features_dir, True, "{}_{}_dates_interpolation.txt".format(polarisation.lower(),
                                                                                                           orbit.upper()))[0]
            else:
                tar_dir = os.path.join(config.get("Paths", "output"), self.tile_name[1:])
                date_file = FileSearch_AND(tar_dir, True, "{}_{}_dates_input.txt".format(polarisation.lower(),
                                                                                         orbit.upper()))[0]
            sar_time_series[orbit.lower()][polarisation.lower()]["availDates"] = getNbDateInTile(date_file,
                                                                                                 display=False,
                                                                                                 raw_dates=True)
        features_labels = []
        for sensor_mode, features in s1_labels.items():
            features_labels += features
        if sar_features_expr:
            userSAR_features, userSAR_features_lab = generateSARFeat_dates(sar_features_expr, sar_time_series)
            userSAR_features.Execute()
            dependancies.append(userSAR_features)
            s1_features.append(userSAR_features)
            features_labels += userSAR_features_lab
        sar_features_raster = os.path.join(self.features_dir, "tmp", self.sar_features_name)
        sar_features = CreateConcatenateImagesApplication({"il": s1_features,
                                                           "out": sar_features_raster,
                                                           "ram": str(ram)})
        return (sar_features, dependancies), features_labels