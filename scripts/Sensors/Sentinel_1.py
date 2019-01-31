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
        # sensors attributes
        self.mask_pattern = "BorderMask.tif"
        #~ self.mask_rules = {"NODATA":1, "DATA":0}
        # define bands to get and their order
        # output's names
        self.footprint_name = "{}_{}_footprint.tif".format(self.__class__.name,
                                                           tile_name)
        # about gapFilling interpolations
        
        
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