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

def launchChain(cfg):
    """
    create output directory and then, launch iota2
    """
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
    start_step = cfg.getParam("chain", "startFromStep")
    end_step = cfg.getParam("chain", "endStep")
    nb_mpi_process = cfg.getParam("chain", "max_process")
    scripts = cfg.getParam("chain", "pyAppPath")

    if PathTEST != "/" and os.path.exists(PathTEST) and start_step == 1:
        choice = ""
        while (choice != "yes") and (choice != "no") and (choice != "y") and (choice != "n"):
            choice = raw_input("the path " + PathTEST + " already exist, do you want to remove it ? yes or no : ")
        if (choice == "yes") or (choice == "y"):
            shutil.rmtree(PathTEST)
        else:
            sys.exit(-1)

    oso_directory.GenerateDirectories(PathTEST)

    cmd = ("mpirun -np {0} python {1}/iota2.py -config {2} "
           "-starting_step {3} -ending_step {4}").format(nb_mpi_process, scripts,
                                                         config_path, start_step,
                                                         end_step)
    os.system(cmd)
            
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
    
            
