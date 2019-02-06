#!/usr/bin/env python
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
import shutil
import logging
from subprocess import Popen, PIPE
import numpy as np
from Common import ServiceLogger as sLog
from Common import ServiceError as sErr
from Common import ServiceConfigFile as SCF


def get_qsub_cmd(cfg, config_ressources=None, parallel_mode="MPI"):
    """
    build qsub cmd to launch iota2 on HPC
    """

    log_dir = os.path.join(cfg.getParam("chain", "outputPath"), "logs")
    scripts = os.path.join(os.environ.get('IOTA2DIR'), "scripts")
    job_dir = cfg.getParam("chain", "jobsPath")
    if job_dir is None:
        raise Exception("the parameter 'chain.jobsPath' is needed to launch IOTA2 on clusters")

    iota2_module_path = os.environ.get('MODULE_PATH')
    iota2_module_name = os.environ.get('MODULE_NAME')
    try:
        OTB_super = cfg.getParam("chain", "OTB_HOME")
    except:
        OTB_super = None
    config_path = cfg.pathConf
    iota2_main = os.path.join(job_dir, "iota2.pbs")

    config_ressources_path = os.path.join(scripts, "MPI", "iota2_HPC_ressources_request.cfg")

    if config_ressources:
        config_ressources_path = config_ressources

    cfg_resources = SCF.serviceConfigFile(config_ressources_path, iota_config=False)
    chainName = cfg_resources.getParam("iota2_chain", "name")
    walltime = cfg_resources.getParam("iota2_chain", "walltime")
    cpu = cfg_resources.getParam("iota2_chain", "nb_cpu")
    ram = cfg_resources.getParam("iota2_chain", "ram")

    log_err = os.path.join(log_dir, "iota2_err.log")
    log_out = os.path.join(log_dir, "iota2_out.log")

    if os.path.exists(iota2_main):
        os.remove(iota2_main)

    ressources = ("#!/bin/bash\n"
                  "#PBS -N {}\n"
                  "#PBS -l select=1"
                  ":ncpus={}"
                  ":mem={}\n"
                  "#PBS -l walltime={}\n"
                  "#PBS -o {}\n"
                  "#PBS -e {}\n").format(chainName, cpu, ram, walltime, log_out, log_err)

    if OTB_super:
        modules = ("module load gcc/6.3.0\n"
                   "module load mpi4py/2.0.0-py2.7\n"
                   "source {}/config_otb.sh\n").format(OTB_super)
    elif OTB_super == None and iota2_module_path:
        modules = ("module use {}\n"
                   "module load {}\n").format(iota2_module_path, iota2_module_name)
    elif OTB_super == None and iota2_module_path == None:
        modules = ("module load {}\n"
                   "export GDAL_CACHEMAX=128\n").format(iota2_module_name)

    exe = ("python {0}/Cluster.py -config {1} -mode {2}").format(scripts,
                                                                 config_path,
                                                                 parallel_mode)
    if config_ressources:
        exe = ("python {0}/Cluster.py -config {1} -config_ressources {2} -mode {3}").format(scripts,
                                                                                            config_path,
                                                                                            config_ressources,
                                                                                            parallel_mode)
    pbs = ressources + modules + exe

    with open(iota2_main, "w") as iota2_f:
        iota2_f.write(pbs)

    qsub = ("qsub {0}").format(iota2_main)
    return qsub


def launchChain(cfg, config_ressources=None, parallel_mode="MPI"):
    """
    launch iota2 to HPC
    """
    import Iota2Builder as chain

    if not "IOTA2DIR" in os.environ:
        raise Exception ("environment variable 'IOTA2DIR' not found, please load a IOTA2's module")
    if not "MODULE_NAME" in os.environ:
        raise Exception ("environment variable 'MODULE_NAME' not found, please load a IOTA2's module")
    if not "MODULE_PATH" in os.environ:
        raise Exception ("environment variable 'MODULE_PATH' not found, please load a IOTA2's module")

    # Check configuration file
    cfg.checkConfigParameters()
    # Starting of logging service
    sLog.serviceLogger(cfg, __name__)
    # Local instanciation of logging
    logger = logging.getLogger(__name__)
    logger.info("START of iota2 chain")
    qsub_cmd = get_qsub_cmd(cfg, config_ressources, parallel_mode)
    process = Popen(qsub_cmd, shell=True, stdout=PIPE, stderr=PIPE)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="This function allows you launch the chain according to a configuration file")
    parser.add_argument("-config", dest="config",
                        help="path to IOTA2 configuration file", required=True)
    parser.add_argument("-config_ressources", dest="config_ressources",
                        help="path to IOTA2 HPC ressources configuration file",
                        required=False, default=None)
    parser.add_argument("-mode", dest="parallel_mode",
                        help="parallel jobs strategy",
                        required=False,
                        default="MPI",
                        choices=["MPI", "JobArray"])
    args = parser.parse_args()
    cfg = SCF.serviceConfigFile(args.config)

    try:
        launchChain(cfg, args.config_ressources, args.parallel_mode)
    # Exception manage by the chain
    # We only print the error message
    except sErr.osoError as e:
        print e
    # Exception not manage (bug)
    # print error message + all stack
    except Exception as e:
        print e
        raise

