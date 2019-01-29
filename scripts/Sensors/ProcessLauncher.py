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

def preprocess(tile_name, config_path, working_directory, RAM):
    """
    """
    from Sensors_container import Sensors_container

    remoteSensor_container = Sensors_container(config_path, tile_name,
                                               working_dir=working_directory)
    remoteSensor_container.sensors_preprocess(available_ram=RAM)

def commonMasks(tile_name, config_path, working_directory, RAM):
    """
    """
    from Sensors_container import Sensors_container

    remoteSensor_container = Sensors_container(config_path, tile_name,
                                               working_dir=working_directory)
    commonMask, _ = remoteSensor_container.get_common_sensors_footprint(available_ram=RAM)
    commonMask.ExecuteAndWriteOutput()

def 