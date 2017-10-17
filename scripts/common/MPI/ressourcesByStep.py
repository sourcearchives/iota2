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
import serviceConfigFile as SCF


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

        #modules needed
        self.mpi_m = "module load mpi4py/2.0.0-py2.7"
        self.gdal_m = "module load pygdal/2.1.0-py2.7"
        self.python_m = "module load python/2.7.12"

    def write_PBS(self, cfg, log_err, log_out, mode, scriptPath, pickleObj, MPI_cmd):
        """
        write PBS if mode = "Job_Tasks" or mode == "Job_MPI_Tasks"
        """
        PBS_path = cfg.getParam('chain', 'jobsPath') + "/" + self.name + ".pbs"
        OTB = cfg.getParam('chain', 'OTB_HOME') + "/config_otb.sh"

        mpi_ressource = ""
        script = ("python {0}/launch_tasks.py -mode common -task {1}").format(scriptPath,
                                                                              pickleObj)
        if mode == "Job_MPI_Tasks":
            mpi_ressource = ":mpiprocs=" + self.nb_MPI_process
            script = (MPI_cmd + " python {1}/launch_tasks.py -mode MPI -task {2}").format(MPI_cmd,
                                                                               scriptPath,
                                                                               pickleObj)
        ressources = ("#!/bin/bash\n"
                      "#PBS -N {0}\n"
                      "#PBS -l select={1}"
                      ":ncpus={2}"
                      ":mem={3}"
                      "{4}\n"
                      "#PBS -l walltime={5}\n"
                      "#PBS -o {6}\n"
                      "#PBS -e {7}\n"
                      "export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS={8}\n").format(self.name, self.nb_node, self.nb_cpu,
                                                                           self.ram, mpi_ressource, self.walltime,
                                                                           self.log_out, self.log_err, self.nb_cpu)
        
        modules = ("{0}\n{1}\n{2}\n"
                   "source {3}\n").format(self.python_m, self.gdal_m, self.mpi_m, OTB)
        
        PBS_script = ("{0}\n{1}\n{2}").format(ressources, modules, script)
        
        if mode == "Job_Tasks" or mode == "Job_MPI_Tasks":
            if os.path.exists(PBS_path):
                os.remove(PBS_path)
            with open(PBS_path, "w") as f:
                f.write(PBS_script)
        return PBS_path


    def build_cmd(self, mode, scriptPath, pickleObj, config):
        """
        build commands
        """
        
        cmd = None
        
        MPI_cmd = ("mpirun -x ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS --report-bindings -np {0}"
                   " --map-by ppr:{1}:socket:"
                   "pe={2}").format(self.nb_MPI_process,
                                    str(self.nbProcessBySocket),
                                    str(self.nbThreadsByProcess))
        MPI_s2calc_cmd = ("mpirun -np {0}"
                   " --map-by ppr:{1}:socket:"
                   "pe={2}").format(self.nb_MPI_process,
                                    str(self.nbProcessBySocket),
                                    str(self.nbThreadsByProcess))
    
        pbsPath = self.write_PBS(config, self.log_err, self.log_out, mode,
                                 scriptPath, pickleObj, MPI_cmd)

        if mode == "Job_MPI_Tasks" or mode == "Job_Tasks":
            cmd = "qsub -W block=true " + pbsPath
        elif mode == "MPI_Tasks":
            cmd =("{0} python {1}/launch_tasks.py "
                  "-task {2}").format(MPI_s2calc_cmd, scriptPath, pickleObj)
        elif mode == "Tasks":
            cmd =("{0} python {1}/launch_tasks.py -mode common "
                  "-task {2}").format(MPI_s2calc_cmd, scriptPath, pickleObj)

        return cmd


get_common_mask = Ressources(name="CommonMasks",
                             nb_cpu=2,
                             nb_MPI_process=2,
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
