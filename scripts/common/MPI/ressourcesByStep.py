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
    def __init__(self, name, nb_cpu, nb_MPI_process, ram, nb_node, walltime):

        self.name = name
        self.nb_cpu = str(nb_cpu)
        self.nb_MPI_process = str(nb_MPI_process)
        self.ram = ram
        self.nb_node = str(nb_node)
        self.walltime = walltime

    def set_env_THREADS(self):
        os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = str(self.nb_cpu)
        os.environ["OMP_NUM_THREADS"] = str(self.nb_cpu)

iota2_dir = Ressources(name="IOTA2_dir",
                             nb_cpu=1,
                             nb_MPI_process=2,
                             ram="4000mb",
                             nb_node=1,
                             walltime="00:10:00")

get_common_mask = Ressources(name="CommonMasks",
                             nb_cpu=2,
                             nb_MPI_process=2,
                             ram="10000mb",
                             nb_node=1,
                             walltime="02:00:00")

get_pixValidity = Ressources(name="NbView",
                             nb_cpu=10,
                             nb_MPI_process=3,
                             ram="50000mb",
                             nb_node=1,
                             walltime="03:00:00")

envelope = Ressources(name="Envelope",
                      nb_cpu=1,
                      nb_MPI_process=2,
                      ram="4000mb",
                      nb_node=1,
                      walltime="00:10:00")

regionShape = Ressources(name="regionShape",
                      nb_cpu=1,
                      nb_MPI_process=2,
                      ram="4000mb",
                      nb_node=1,
                      walltime="00:10:00")

splitRegions = Ressources(name="splitRegions",
                      nb_cpu=1,
                      nb_MPI_process=2,
                      ram="4000mb",
                      nb_node=1,
                      walltime="00:10:00")

extract_data_region_tiles = Ressources(name="extract_data_region_tiles",
                                       nb_cpu=24,
                                       nb_MPI_process=40,
                                       ram="40000mb",
                                       nb_node=2,
                                       walltime="20:00:00")

split_learning_val = Ressources(name="split_learning_val",
                                nb_cpu=10,
                                nb_MPI_process=10,
                                ram="10000mb",
                                nb_node=1,
                                walltime="01:00:00")

split_learning_val_sub = Ressources(name="split_learning_val_sub",
                                    nb_cpu=10,
                                    nb_MPI_process=10,
                                    ram="4000mb",
                                    nb_node=1,
                                    walltime="01:00:00")

vectorSampler = Ressources(name="vectorSampler",
                           nb_cpu=20,
                           nb_MPI_process=10,
                           ram="80000mb",
                           nb_node=2,
                           walltime="50:00:00")

mergeSample = Ressources(name="mergeSample",
                         nb_cpu=5,
                         nb_MPI_process=3,
                         ram="80000mb",
                         nb_node=1,
                         walltime="05:00:00")

stats_by_models = Ressources(name="stats_by_models",
                             nb_cpu=5,
                             nb_MPI_process=2,
                             ram="4000mb",
                             nb_node=1,
                             walltime="00:10:00")

training = Ressources(name="training",
                      nb_cpu=10,
                      nb_MPI_process=8,
                      ram="100gb",
                      nb_node=2,
                      walltime="20:00:00")

cmdClassifications = Ressources(name="cmdClassifications",
                                nb_cpu=5,
                                nb_MPI_process=2,
                                ram="4000mb",
                                nb_node=1,
                                walltime="05:00:00")

classifications = Ressources(name="classifications",
                             nb_cpu=20,
                             nb_MPI_process=5,
                             ram="80000mb",
                             nb_node=1,
                             walltime="20:00:00")

classifShaping = Ressources(name="classifShaping",
                            nb_cpu=5,
                            nb_MPI_process=2,
                            ram="10000mb",
                            nb_node=1,
                            walltime="01:00:00")

gen_confusionMatrix = Ressources(name="genCmdconfusionMatrix",
                             nb_cpu=1,
                             nb_MPI_process=2,
                             ram="4000mb",
                             nb_node=1,
                             walltime="01:00:00")

confusionMatrix = Ressources(name="confusionMatrix",
                             nb_cpu=5,
                             nb_MPI_process=10,
                             ram="4000mb",
                             nb_node=1,
                             walltime="01:00:00")

fusion = Ressources(name="fusion",
                    nb_cpu=1,
                    nb_MPI_process=2,
                    ram="4000mb",
                    nb_node=1,
                    walltime="01:00:00")

noData = Ressources(name="noData",
                    nb_cpu=1,
                    nb_MPI_process=2,
                    ram="4000mb",
                    nb_node=1,
                    walltime="01:00:00")

statsReport = Ressources(name="statsReport",
                         nb_cpu=5,
                         nb_MPI_process=2,
                         ram="4000mb",
                         nb_node=1,
                         walltime="01:00:00")

confusionMatrixFusion = Ressources(name="confusionMatrixFusion",
                         nb_cpu=1,
                         nb_MPI_process=2,
                         ram="4000mb",
                         nb_node=1,
                         walltime="01:00:00")

reportGen = Ressources(name="reportGeneration",
                         nb_cpu=1,
                         nb_MPI_process=2,
                         ram="4000mb",
                         nb_node=1,
                         walltime="01:00:00")
mergeOutStats = Ressources(name="mergeOutStats",
                         nb_cpu=1,
                         nb_MPI_process=2,
                         ram="4000mb",
                         nb_node=1,
                         walltime="01:00:00")
