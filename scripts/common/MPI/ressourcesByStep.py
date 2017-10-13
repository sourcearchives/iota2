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

#TODO add function to compute number of selected node ->select=??
#depend from mpiprocs, procs and number of available number of socket threads

import os

class Ressources():
    def __init__(self, name, nb_cpu, nb_MPI_process, ram, nb_node, walltime):
        
        self.name = name
        self.nb_cpu = str(nb_cpu)
        self.nb_MPI_process = str(nb_MPI_process)
        self.ram = ram
        self.nb_node = str(nb_node)
        self.walltime = walltime
        self.log_err = None
        self.log_out = None

        self.nbProcessBySocket = 12#Depends of machine architecture
        self.nbThreadsByProcess = int(self.nb_cpu)/int(self.nb_MPI_process)

        os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = str(nb_cpu)
        os.environ["OMP_NUM_THREADS"] = str(nb_cpu)

    def build_cmd(self, mode, scriptPath, pickleObj):
        """
        build commands
        """
        cmd = None
        MPI_PBS_ressources = ("-N {0} -l select={1}"
                              ":ncpus={2}:mpiprocs={3}"
                              ":mem={4} -l walltime={5}"
                              " -o {6} -e {7}").format(self.name, self.nb_node,
                                                       self.nb_cpu, self.nb_MPI_process,
                                                       self.ram, self.walltime,
                                                       self.log_out, self.log_err)
        PBS_ressources = ("-N {0} -l select={1}"
                          ":ncpus={2}"
                          ":mem={3} -l walltime={4}"
                          " -o {5} -e {6}").format(self.name, self.nb_node,
                                                       self.nb_cpu, self.ram,
                                                       self.walltime, self.log_out,
                                                       self.log_err)
        MPI_cmd = ("mpirun -x ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS --report-bindings -np {0}"
                   " --map-by ppr:{1}:socket:"
                   "pe={2}").format(self.nb_MPI_process,
                                    str(self.nbProcessBySocket),
                                    str(self.nbThreadsByProcess))

        if mode == "Job_MPI_Tasks":
            cmd =("qsub -W block=true {0} -V -- /usr/bin/bash"
                  " -c \"{1} python {2}/launch_tasks.py "
                  "-task {3}\"").format(MPI_PBS_ressources, MPI_cmd, scriptPath, pickleObj)
        elif mode == "MPI_Tasks":
            cmd =("{0} python {1}/launch_tasks.py "
                  "-task {2}\"").format(MPI_cmd, scriptPath, pickleObj)
        elif mode == "Job_Tasks":
            cmd =("qsub -W block=true {0} -V -- /usr/bin/bash"
                  " -c \" python {1}/launch_tasks.py -mode common "
                  "-task {2}\"").format(PBS_ressources, scriptPath, pickleObj)
        elif mode == "Tasks":
            cmd =("{0} python {1}/launch_tasks.py -mode common "
                  "-task {3}\"").format(MPI_cmd, scriptPath, pickleObj)
        elif mode == "Python":
            pass

        return cmd


get_common_mask = Ressources(name="CommonMasks",
                             nb_cpu=10,
                             nb_MPI_process=5,
                             ram="10000mb",
                             nb_node=1,
                             walltime="00:10:00")

envelope = Ressources(name="Envelope",
                      nb_cpu=1,
                      nb_MPI_process=-1,
                      ram="4000mb",
                      nb_node=1,
                      walltime="00:10:00")
                      
regionShape = Ressources(name="regionShape",
                      nb_cpu=1,
                      nb_MPI_process=-1,
                      ram="4000mb",
                      nb_node=1,
                      walltime="00:10:00")
                      
splitRegions = Ressources(name="splitRegions",
                      nb_cpu=1,
                      nb_MPI_process=-1,
                      ram="4000mb",
                      nb_node=1,
                      walltime="00:10:00")
                                            
extract_data_region_tiles = Ressources(name="extract_data_region_tiles",
                                       nb_cpu=10,
                                       nb_MPI_process=10,
                                       ram="4000mb",
                                       nb_node=1,
                                       walltime="00:10:00")
                                            
split_learning_val = Ressources(name="split_learning_val",
                                nb_cpu=10,
                                nb_MPI_process=10,
                                ram="4000mb",
                                nb_node=1,
                                walltime="00:10:00")
                                            
split_learning_val_sub = Ressources(name="split_learning_val_sub",
                                    nb_cpu=10,
                                    nb_MPI_process=10,
                                    ram="4000mb",
                                    nb_node=1,
                                    walltime="00:10:00")
                                            
vectorSampler = Ressources(name="vectorSampler",
                           nb_cpu=10,
                           nb_MPI_process=10,
                           ram="4000mb",
                           nb_node=1,
                           walltime="00:10:00")
                                            
mergeSample = Ressources(name="mergeSample",
                         nb_cpu=5,
                         nb_MPI_process=-1,
                         ram="4000mb",
                         nb_node=1,
                         walltime="00:10:00")
                                            
stats_by_models = Ressources(name="stats_by_models",
                             nb_cpu=5,
                             nb_MPI_process=2,
                             ram="4000mb",
                             nb_node=1,
                             walltime="00:10:00")
                                            
training = Ressources(name="training",
                      nb_cpu=1,
                      nb_MPI_process=5,
                      ram="4000mb",
                      nb_node=1,
                      walltime="00:10:00")
                                            
cmdClassifications = Ressources(name="cmdClassifications",
                                nb_cpu=5,
                                nb_MPI_process=-1,
                                ram="4000mb",
                                nb_node=1,
                                walltime="00:10:00")
                                            
classifications = Ressources(name="classifications",
                             nb_cpu=2,
                             nb_MPI_process=2,
                             ram="4000mb",
                             nb_node=1,
                             walltime="00:10:00")
                                            
classifShaping = Ressources(name="classifShaping",
                            nb_cpu=5,
                            nb_MPI_process=-1,
                            ram="10000mb",
                            nb_node=1,
                            walltime="00:10:00")
                                            
gen_confusionMatrix = Ressources(name="genCmdconfusionMatrix",
                             nb_cpu=1,
                             nb_MPI_process=-1,
                             ram="4000mb",
                             nb_node=1,
                             walltime="00:10:00")

confusionMatrix = Ressources(name="confusionMatrix",
                             nb_cpu=5,
                             nb_MPI_process=10,
                             ram="4000mb",
                             nb_node=1,
                             walltime="00:10:00")
                                            
fusion = Ressources(name="fusion",
                    nb_cpu=1,
                    nb_MPI_process=-1,
                    ram="4000mb",
                    nb_node=1,
                    walltime="00:10:00")
                                            
noData = Ressources(name="noData",
                    nb_cpu=1,
                    nb_MPI_process=-1,
                    ram="4000mb",
                    nb_node=1,
                    walltime="00:10:00")
                                            
statsReport = Ressources(name="statsReport",
                         nb_cpu=5,
                         nb_MPI_process=2,
                         ram="4000mb",
                         nb_node=1,
                         walltime="00:10:00")
