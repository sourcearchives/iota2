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
        pass
        
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
        pass

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