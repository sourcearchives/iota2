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
from Sensors import (Landsat5, Landsat8,
                     Sentinel_2, Sentinel_2_S2C,
                     Sentinel_2_L3A, Sentinel_1,
                     User_stack)

class Sensors_container(object):
    def __init__(self, config_path, tile_name, working_dir):
        """
        """
        from Common import ServiceConfigFile as SCF

        self.cfg = SCF.serviceConfigFile(config_path)
        self.tile_name = tile_name
        self.working_dir = working_dir

        self.enabled_sensors = self.get_enabled_sensors(self.cfg)

        #~ print getSensorTimeSeries(self.get_enabled_sensors_name(self.cfg)[0])

    def __str__(self):
        """
        return enabled sensors and the current tile
        """
        return "tile's name : {}, available sensors : {}".format(self.tile_name,
                                                                 ", ".join(self.get_enabled_sensors_name(self.cfg)))

    def __repr__(self):
        """
        return available dates by sensors
        """
        return self.__str__()

    def get_iota2_sensors_names(self):
        """
        """
        available_sensors_name = [Landsat5.name,
                                  Landsat8.name,
                                  Sentinel_1.name,
                                  Sentinel_2.name,
                                  Sentinel_2_S2C.name,
                                  Sentinel_2_L3A.name,
                                  User_stack.name]
        return available_sensors_name

    def get_enabled_sensors_name(self, cfg):
        """
        """
        l5 = self.cfg.getParam("chain", "L5Path")
        l8 = self.cfg.getParam("chain", "L8Path")
        s1 = self.cfg.getParam("chain", "S1Path")
        s2 = self.cfg.getParam("chain", "S2Path")
        s2_s2c = self.cfg.getParam("chain", "S2_S2C_Path")
        s2_l3a = self.cfg.getParam("chain", "S2_L3A_Path")
        user_stack = self.cfg.getParam("chain", "userFeatPath")

        enabled_sensors = []
        if not "none" in l5.lower():
            enabled_sensors.append(Landsat5.name)
        if not "none" in l8.lower():
            enabled_sensors.append(Landsat8.name)
        if not "none" in s1.lower():
            enabled_sensors.append(Sentinel_1.name)
        if not "none" in s2.lower():
            enabled_sensors.append(Sentinel_2.name)
        if not "none" in s2_s2c.lower():
            enabled_sensors.append(Sentinel_2_S2C.name)
        if not "none" in s2_l3a.lower():
            enabled_sensors.append(Sentinel_2_L3A.name)
        if not "none" in user_stack.lower():
            enabled_sensors.append(User_stack.name)
        return enabled_sensors

    def get_enabled_sensors(self, cfg):
        """
        """
        l5 = self.cfg.getParam("chain", "L5Path")
        l8 = self.cfg.getParam("chain", "L8Path")
        s1 = self.cfg.getParam("chain", "S1Path")
        s2 = self.cfg.getParam("chain", "S2Path")
        s2_s2c = self.cfg.getParam("chain", "S2_S2C_Path")
        s2_l3a = self.cfg.getParam("chain", "S2_L3A_Path")
        user_stack = self.cfg.getParam("chain", "userFeatPath")

        enabled_sensors = []
        if not "none" in l5.lower():
            enabled_sensors.append(Landsat5)
        if not "none" in l8.lower():
            enabled_sensors.append(Landsat8)
        if not "none" in s1.lower():
            enabled_sensors.append(Sentinel_1)
        if not "none" in s2.lower():
            enabled_sensors.append(Sentinel_2)
        if not "none" in s2_s2c.lower():
            enabled_sensors.append(Sentinel_2_S2C)
        if not "none" in s2_l3a.lower():
            # every sensors should be built as below
            enabled_sensors.append(Sentinel_2_L3A(self.cfg.pathConf, tile_name=self.tile_name))
        if not "none" in user_stack.lower():
            enabled_sensors.append(User_stack)
        return enabled_sensors

    def sensors_preprocess(self, available_ram=128):
        """
        """
        for sensor in self.enabled_sensors:
            self.sensor_preprocess(sensor, self.working_dir, available_ram)

    def sensor_preprocess(self, sensor, working_dir, available_ram):
        """
        prepare sensor data
        """
        sensor_prepro_app = sensor.preprocess(working_dir=working_dir, ram=available_ram)
        return sensor_prepro_app

    def sensors_dates(self):
        """
        return sorted available dates per sensor(callable after sensors_preprocess)
        
        TODO :
        add flag to check if sensors_preprocess allready called once ?
        """
        sensors_dates = []
        for sensor in self.enabled_sensors:
            dates_list = sensor.get_available_dates()
            sensors_dates.append((sensor.__class__.name, dates_list))
        return sensors_dates

    def get_sensors_footprint(self, available_ram=128):
        """
        """
        sensors_footprint = []
        for sensor in self.enabled_sensors:
            sensors_footprint.append((sensor.__class__.name, sensor.footprint(available_ram)))
        return sensors_footprint

    def get_sensors_time_series(self, available_ram=128):
        """
        return the time series as a otb's application ready to be executed
        """
        sensors_time_series = []
        for sensor in self.enabled_sensors:
            sensors_time_series.append((sensor.__class__.name, sensor.get_time_series(available_ram)))
        return sensors_time_series