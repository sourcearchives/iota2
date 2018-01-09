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
import serviceConfigFile as SCF


class Ressources():
    def __init__(self, name, nb_cpu, nb_MPI_process, ram, nb_chunk, walltime):

        self.name = name
        self.nb_cpu = str(nb_cpu)
        self.nb_MPI_process = str(nb_MPI_process)
        self.ram = ram
        self.nb_chunk = str(nb_chunk)
        self.walltime = walltime

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
    cfg = SCF.serviceConfigFile(iota2_ressources_description, checkConfig=False)
    available_steps = cfg.getAvailableSections()
    
    iota2_HPC_requests = {}
    for step in available_steps:
        iota2_HPC_requests[step] = Ressources(name=cfg.getParam(step, 'name'),
                                              nb_cpu=cfg.getParam(step, 'nb_cpu'),
                                              nb_MPI_process=cfg.getParam(step, 'nb_MPI_process'),
                                              ram=cfg.getParam(step, 'ram'),
                                              nb_chunk=cfg.getParam(step, 'nb_chunk'),
                                              walltime=cfg.getParam(step, 'walltime'))
    return iota2_HPC_requests
