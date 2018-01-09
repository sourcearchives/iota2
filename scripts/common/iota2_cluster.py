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


def get_qsub_cmd(cfg, config_ressources=None):
    """
    build qsub cmd to launch iota2 on HPC
    """
    
    log_dir = cfg.getParam("chain", "logPath")
    OTB_super = cfg.getParam("chain", "OTB_HOME")
    scripts = cfg.getParam("chain", "pyAppPath")
    job_dir = cfg.getParam("chain", "jobsPath")
    config_path = cfg.pathConf
    
    iota2_main = os.path.join(job_dir, "iota2.pbs")
    chainName = "iota2"
    walltime = "00:10:00"
    log_err = os.path.join(log_dir, "iota2_err.log")
    log_out = os.path.join(log_dir, "iota2_out.log")

    if os.path.exists(iota2_main):
        os.remove(iota2_main)

    ressources = ("#!/bin/bash\n"
                  "#PBS-N {0}\n"
                  "#PBS-l select=1"
                  ":ncpus=1"
                  ":mem=4000mb\n"
                  "#PBS -l walltime={1}\n"
                  "#PBS -o {2}\n"
                  "#PBS -e {3}\n").format(chainName, walltime, log_out, log_err)

    modules = ("module load mpi4py/2.0.0-py2.7\n"
               "module load pygdal/2.1.0-py2.7\n"
               "module load python/2.7.12\n"
               "source {0}/config_otb.sh\n").format(OTB_super)
    
    exe = ("python {0}/cluster.py -config {1}").format(scripts, config_path)
    if config_ressources:
        exe = ("python {0}/cluster.py -config {1} -config_ressources {2}").format(scripts, config_path, config_ressources)
    pbs = ressources + modules + exe

    with open(iota2_main, "w") as iota2_f:
        iota2_f.write(pbs)

    qsub = ("qsub {0}").format(iota2_main)
    return qsub


def launchChain(cfg, config_ressources=None):
    """
    launch iota2 to HPC
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
    
    qsub_cmd = get_qsub_cmd(cfg, config_ressources)
    process = Popen(qsub_cmd, shell=True, stdout=PIPE, stderr=PIPE)
    

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="This function allows you launch the chain according to a configuration file")
    parser.add_argument("-config", dest="config",
                        help="path to IOTA2 configuration file", required=True)
    parser.add_argument("-config_ressources", dest="config_ressources",
                        help="path to IOTA2 HPC ressources configuration file",
                        required=False, default=None)
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

