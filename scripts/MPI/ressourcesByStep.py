#!/usr/bin/python
#-*- coding: utf-8 -*-

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

import os
from Common import ServiceConfigFile as SCF


class Ressources():
    def __init__(self, name, nb_cpu, ram, walltime,
                 process_min, process_max):

        self.name = name
        self.nb_cpu = str(nb_cpu)
        self.ram = ram
        self.walltime = walltime
        self.process_min = process_min
        self.process_max = process_max

    def set_env_THREADS(self):
        os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = str(self.nb_cpu)
        os.environ["OMP_NUM_THREADS"] = str(self.nb_cpu)


def iota2_ressources(iota2_ressources_description="iota2_HPC_ressources_request.cfg"):
    """
    usage : 
    
    IN :
    iota2_ressources_description [string] : path to a configuration file which
                                            describe step's HPC request. 
    OUT :
    iota2_HPC_requests [dic of Ressources Object] : dictionnary containing all
                                                    ressources request
    """
    iota2_ressources_description = os.path.join(os.path.dirname(os.path.realpath(__file__)), iota2_ressources_description)
    cfg = SCF.serviceConfigFile(iota2_ressources_description, iota_config=False)
    available_steps = cfg.getAvailableSections()
    
    iota2_HPC_requests = {}
    for step in available_steps:
        try:
            process_max = cfg.getParam(step, 'process_max')
        except:
            process_max = -1
        try:
            process_min = cfg.getParam(step, 'process_min')
        except:
            process_min = 1
        iota2_HPC_requests[step] = Ressources(name=cfg.getParam(step, 'name'),
                                              nb_cpu=cfg.getParam(step, 'nb_cpu'),
                                              ram=cfg.getParam(step, 'ram'),
                                              walltime=cfg.getParam(step, 'walltime'),
                                              process_min=process_min,
                                              process_max=process_max)
    return iota2_HPC_requests

