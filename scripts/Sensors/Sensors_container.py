# !/usr/bin/python
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

"""
This class manage sensor's data by tile, providing services needed in whole IOTA²
library
"""
from Sensors import Landsat5, Landsat8, Sentinel_2, Sentinel_2_S2C

class Sensors_container(object):
    def __init__(self, config_path, tile_name):
        """
        
        """
        from Common import ServiceConfigFile as SCF

        self.cfg = SCF.serviceConfigFile(config_path)
        self.tile_name = tile_name

        print self.get_iota2_sensors_names(self.cfg)

    def __str__(self):
        """
        return enable sensors and the current tile
        """
        #~ get_available_sensors(self)
        return self.tile_name

    def __repr__():
        """
        return available dates by sensors
        """
    def get_available_sensors(self):
        pass

    def get_iota2_sensors_names(self, cfg):
        """
        """
        l5 = self.cfg.getParam("chain", "L5Path")
        l8 = self.cfg.getParam("chain", "L8Path")
        s1 = self.cfg.getParam("chain", "S1Path")
        s2 = self.cfg.getParam("chain", "S2Path")
        s2_s2c = self.cfg.getParam("chain", "S2_S2C_Path")
        s2_l3a = self.cfg.getParam("chain", "S2_L3A_Path")
        user_stack = self.cfg.getParam("chain", "userFeatPath")
        
        
        