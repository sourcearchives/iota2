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

import argparse
import os
import serviceError
import shutil
import serviceConfigFile as SCF
import logging
import serviceLogger as sLog
import oso_directory
import numpy as np
from subprocess import Popen, PIPE

def write_PBS(job_directory, log_directory, task_name, step_to_compute,
              nb_parameters, request, OTB, script_path, config_path):
    """
    write PBS file, according to ressource requested
    param : nb_parameters [int] could be use to optimize HPC request
    """
    log_err = os.path.join(log_directory, task_name + "_err.log")
    log_out = os.path.join(log_directory, task_name + "_out.log")
    ressources = ("#!/bin/bash\n"
                  "#PBS -N {0}\n"
                  "#PBS -l select={1}"
                  ":ncpus={2}"
                  ":mem={3}"
                  ":mpiprocs={4}\n"
                  "#PBS -l walltime={5}\n"
                  "#PBS -o {6}\n"
                  "#PBS -e {7}\n"
                  "export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS={8}\n\n").format(request.name, request.nb_node, request.nb_cpu,
                                                                                request.ram, request.nb_MPI_process, request.walltime,
                                                                                log_out, log_err, request.nb_cpu)

    modules = ("module load mpi4py/2.0.0-py2.7\n"
               "module load pygdal/2.1.0-py2.7\n"
               "module load python/2.7.12\n"
               "source {0}/config_otb.sh").format(OTB)
    
    exe = ("\n\nmpirun -np {0} python {1}/iota2.py -config {2} "
           "-starting_step {3} -ending_step {4}").format(request.nb_MPI_process, script_path,
                                                         config_path, step_to_compute,
                                                         step_to_compute)
    
    pbs = ressources + modules + exe
    
    pbs_path = os.path.join(job_directory, task_name + ".pbs")
    if os.path.exists(pbs_path):
        os.remove(pbs_path)
    with open(pbs_path, "w") as pbs_f:
        pbs_f.write(pbs)
    return pbs_path
    
def launchChain(cfg):
    """
    create output directory and then, launch iota2 to HPC
    """
    import iota2_builder as chain

    # Check configuration file
    #cfg.checkConfigParameters()
    # Starting of logging service
    sLog.serviceLogger(cfg, __name__)
    # Local instanciation of logging
    logger = logging.getLogger(__name__)
    logger.info("START of iota2 chain")
    
    cfg.checkConfigParameters()
    config_path = cfg.pathConf
    PathTEST = cfg.getParam('chain', 'outputPath')
    start_step = cfg.getParam("chain", "firstStep")
    end_step = cfg.getParam("chain", "lastStep")
    scripts = cfg.getParam("chain", "pyAppPath")
    job_dir = cfg.getParam("chain", "jobsPath")
    log_dir = cfg.getParam("chain", "logPath")
    OTB_super = cfg.getParam("chain", "OTB_HOME")

    chain_to_process = chain.iota2(cfg)
    steps = chain_to_process.steps
    nb_steps = len(steps)
    all_steps = chain_to_process.get_steps_number()
    start_step = all_steps[0]
    end_step = all_steps[-1]
    
    if end_step == -1:
        end_step = nb_steps

    #Lists start from index 0
    start_step-=1

    stepToCompute = np.arange(start_step, end_step)
    current_step = 1
    for step_num in np.arange(start_step, end_step):
        try :
            nbParameter = len(steps[step_num].parameters)
        except TypeError :
            nbParameter = 0
        ressources = steps[step_num].ressources

        pbs = write_PBS(job_directory=job_dir, log_directory=log_dir,
                        task_name=steps[step_num].TaskName, step_to_compute=step_num+1,
                        nb_parameters=nbParameter, request=ressources,
                        OTB=OTB_super, script_path=scripts, config_path=config_path)

        if current_step == 1:
            qsub = ("qsub {0}").format(pbs)
        else:
            qsub = ("qsub -W depend=afterok:{0} {1}").format(job_id, pbs)

        qsub = qsub.split(" ")
        process = Popen(qsub, shell=False, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        job_id = stdout.strip('\n')
        
        current_step+=1

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "This function allows you launch the chain according to a configuration file")
    parser.add_argument("-config",dest = "config",help ="path to configuration file",required=True)
    args = parser.parse_args()
    cfg = SCF.serviceConfigFile(args.config)
    try:
        launchChain(cfg)
    # Exception manage by the chain
    # We only print the error message
    except serviceError.osoError as e:
        print e
    # Exception not manage (bug)
    # print error message + all stack
    except Exception as e:
        print e
        raise
