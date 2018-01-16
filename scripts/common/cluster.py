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
from subprocess import Popen, PIPE, STDOUT

def get_HPC_disponibility(nb_cpu, ram, mpi_proc, chunk_percent):
    
    """
    usage : function use to predict ressources request by iota2

    IN :
    nb_cpu [int]
    ram [str]
    mpi_proc [int]
    chunk_percent [float]
    
    OUT
    [float] : number of chunk according to inputs parameters
    [string] : add this string to MPI command to run one process by chunk
    """
    def get_RAM(ram):
        """
        usage return ram in gb
        ram [param] [str]
        
        out [ram] [str] : ram in gb
        """
        
        ram = ram.lower().replace(" ", "")
        if "gb" in ram:
            ram = int(ram.split("gb")[0])
        elif "mb" in ram:
            ram = float(ram.split("mb")[0])/1024
        return str(ram)
    
    ram = get_RAM(ram)

    from subprocess import Popen, PIPE
    import re

    # HPC hardware by nodes cpu_HPC -> number of cpus ram_HPC -> RAM (gb) avail
    cpu_HPC = 24
    ram_HPC = 120
    
    #if only one process could be launch by nodes
    MPI_nodes = None
    if nb_cpu > int(cpu_HPC/2) or int(ram) > int(ram_HPC/2):
        mpi_proc = 1
        MPI_nodes = "--map-by ppr:1:node:pe={}".format(nb_cpu)

    cmd = 'qhostpbs | grep rh7 | grep t72h | grep -v "full" | grep -v "down" | grep -v "offl"'
    
    #RegEx to find available cpu 
    regEx_cpu = re.compile("(\d+[\s\d]?)/(\d+[\s\d]?)/(\d+[\s\d]?)/(\d+[\s\d]?)")
    
    #RegEx to find available cpu 
    regEx_ram = re.compile("([\s\d]?[\s\d]?\d+)+/(\d+\d+\d+)+")

    process = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    
    nb_chunk = 0
    stdout = stdout.split("\n")
    for node in stdout:
        if not node or node == "":
            continue

        cpu_busy = regEx_cpu.findall(node)[0][0].replace(" ","")
        ram_busy = regEx_ram.findall(node)[0][0].replace(" ","")
        
        cpu_avail = int(cpu_HPC) - int(cpu_busy)
        ram_avail = int(ram_HPC) - int(ram_busy)

        if cpu_avail > float(nb_cpu)*mpi_proc and ram_avail > float(ram)*mpi_proc:
            nb_chunk += min(int(float(cpu_avail)/float(nb_cpu)),
                            int(float(ram_avail)/float(ram)))

    return nb_chunk*chunk_percent, MPI_nodes


def write_PBS(job_directory, log_directory, task_name, step_to_compute,
              nb_parameters, request, OTB, script_path, config_path,
              config_ressources_req=None):
    """
    write PBS file, according to ressource requested
    param : nb_parameters [int] could be use to optimize HPC request
    """
    log_err = os.path.join(log_directory, task_name + "_err.log")
    log_out = os.path.join(log_directory, task_name + "_out.log")
    itk_threads = str(int(int(request.nb_cpu)/int(request.nb_MPI_process))+1)
    ressources = ("#!/bin/bash\n"
                  "#PBS -N {0}\n"
                  "#PBS -l select={1}"
                  ":ncpus={2}"
                  ":mem={3}"
                  ":mpiprocs={4}\n"
                  "#PBS -l walltime={5}\n"
                  "#PBS -o {6}\n"
                  "#PBS -e {7}\n"
                  "export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS={8}\n\n").format(request.name, request.nb_chunk, request.nb_cpu,
                                                                                request.ram, request.nb_MPI_process, request.walltime,
                                                                                log_out, log_err, itk_threads)

    modules = ("module load mpi4py/2.0.0-py2.7\n"
               "module load gcc/6.3.0\n"
               "module load python/2.7.12\n"
               "source {0}/config_otb.sh\n").format(OTB)

    ressources_HPC = ""
    if config_ressources_req:
        ressources_HPC = "-config_ressources " + config_ressources_req

    nprocs = int(request.nb_MPI_process)*int(request.nb_chunk)
    exe = ("\n\nmpirun -x ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS -np {0} "
           "python {1}/iota2.py -config {2} "
           "-starting_step {3} -ending_step {4} {5}").format(nprocs, script_path,
                                                             config_path, step_to_compute,
                                                             step_to_compute, ressources_HPC)
    
    pbs = ressources + modules + exe

    pbs_path = os.path.join(job_directory, task_name + ".pbs")
    if os.path.exists(pbs_path):
        os.remove(pbs_path)
    with open(pbs_path, "w") as pbs_f:
        pbs_f.write(pbs)
    return pbs_path, log_err

def check_errors(log_path):
    """
    IN
    log_path [string] : path to output log
    """
    import re
    import os

    err_flag = False
    if not os.path.exists(log_path):
        return True

    #RegEx to find errors patterns
    regEx_logErr = re.compile("parameter : '.*' : failed")
    
    with open(log_path, "r") as log_err:
        for line in log_err:
            error_find = regEx_logErr.findall(line.rstrip())
            if error_find:
                err_flag = True
    return err_flag


def launchChain(cfg, config_ressources=None):
    """
    create output directory and then, launch iota2 to HPC
    """
    import iota2_builder as chain

    # Check configuration file
    cfg.checkConfigParameters()
    # Starting of logging service
    sLog.serviceLogger(cfg, __name__)
    # Local instanciation of logging
    logger = logging.getLogger(__name__)
    logger.info("START of iota2 chain")
    
    config_path = cfg.pathConf
    PathTEST = cfg.getParam('chain', 'outputPath')
    start_step = cfg.getParam("chain", "firstStep")
    end_step = cfg.getParam("chain", "lastStep")
    scripts = cfg.getParam("chain", "pyAppPath")
    job_dir = cfg.getParam("chain", "jobsPath")
    log_dir = cfg.getParam("chain", "logPath")
    OTB_super = cfg.getParam("chain", "OTB_HOME")

    chain_to_process = chain.iota2(cfg, config_ressources)
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

        pbs, log_err = write_PBS(job_directory=job_dir, log_directory=log_dir,
                                 task_name=steps[step_num].TaskName, step_to_compute=step_num+1,
                                 nb_parameters=nbParameter, request=ressources,
                                 OTB=OTB_super, script_path=scripts, config_path=config_path,
                                 config_ressources_req=config_ressources)

        if current_step == 1:
            qsub = ("qsub -W block=true {0}").format(pbs)
        else:
            #qsub = ("qsub -W block=true,depend=afterok:{0} {1}").format(job_id, pbs)
            qsub = ("qsub -W block=true {0}").format(pbs)

        qsub = qsub.split(" ")
        process = Popen(qsub, shell=False, stdout=PIPE, stderr=STDOUT)
        process.wait()
        stdout, stderr = process.communicate()
        job_id = stdout.strip('\n')
        
        errors = check_errors(steps[step_num].logFile)
        if errors:
            return errors

        current_step+=1

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "This function allows you launch the chain according to a configuration file")
    parser.add_argument("-config",dest="config",help ="path to IOTA2 configuration file",
                        required=True)
    parser.add_argument("-config_ressources", dest="config_ressources",
                        help="path to IOTA2 ressources configuration file", required=False)
    args = parser.parse_args()
    cfg = SCF.serviceConfigFile(args.config)
    try:
        launchChain(cfg, args.config_ressources)
    # Exception manage by the chain
    # We only print the error message
    except serviceError.osoError as e:
        print e
    # Exception not manage (bug)
    # print error message + all stack
    except Exception as e:
        print e
        raise
