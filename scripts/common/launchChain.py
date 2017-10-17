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

import argparse, os
import fileUtils as fu
from config import Config
import serviceConfigFile as SCF
import codeStrings
import serviceError

def Launch(cfg):
    iota2_logPath = cfg.getParam('chain', 'logPath')
    iota2_scriptsPath = cfg.getParam('chain', 'pyAppPath')
    iota2_jobs = cfg.getParam('chain', 'jobsPath')
    configPath = cfg.pathConf
    iota2_errLog = iota2_logPath + "/IOTA2_err.log"
    iota2_outLog = iota2_logPath + "/IOTA2_out.log"
            
    if os.path.exists(iota2_errLog):
        os.remove(iota2_errLog)
    if os.path.exists(iota2_outLog):
        os.remove(iota2_outLog)
    """
    cmd = "qsub -V -N IOTA2 -o "+iota2_outLog+" -e "+iota2_errLog+"\
          -l select=1:ncpus=1:mem=4000mb -l walltime=80:00:00 \
           -- /usr/bin/bash -c \"python "+iota2_scriptsPath+"/launchChainSequential.py "+configPath+"\" "
    os.system(cmd)
    """
    mpi_m = "module load mpi4py/2.0.0-py2.7"
    gdal_m = "module load pygdal/2.1.0-py2.7"
    python_m = "module load python/2.7.12"
    OTB = cfg.getParam('chain', 'OTB_HOME') + "/config_otb.sh"

    iota_PBS = iota2_jobs + "/IOTA2.pbs"
    if os.path.exists(iota_PBS):
        os.remove(iota_PBS)
    
    ressources = ("#!/bin/bash\n"
                  "#PBS -N IOTA2\n"
                  "#PBS -l select=1"
                  ":ncpus=1"
                  ":mem=4000mb\n"
                  "#PBS -l walltime=01:00:00\n"
                  "#PBS -o {0}\n"
                  "#PBS -e {1}\n").format(iota2_outLog,
                                          iota2_errLog)

    modules = ("{0}\n{1}\n{2}\n"
               "source {3}\n").format(python_m, gdal_m, mpi_m, OTB)
                   
    PBS_script = ("python {0}/launchChainSequential.py "
                  "{1}").format(iota2_scriptsPath, configPath)

    PBS = ressources + modules + PBS_script

    with open(iota_PBS,"w") as f:
        f.write(PBS)
    cmd = "qsub -V " + iota_PBS
    os.system(cmd)
    
def gen_oso_sequential(cfg):

    MODE = cfg.getParam('chain', 'mode')
    CLASSIFMODE = cfg.getParam('argClassification', 'classifMode')

    if CLASSIFMODE == "fusion" and MODE == "one_region":
        raise Exception("you can't choose the 'one region' mode and use the fusion mode together")

    import launchChainSequential as lcs

    # Launch chain in sequential mode
    lcs.launchChainSequential(cfg)


def launchChain(Fileconfig, reallyLaunch=True):

    """
    IN :
        Fileconfig [string] : path to the configuration file which rule the classification
    this function is the one which launch all process 
    """

    cfg = SCF.serviceConfigFile(Fileconfig)
    cfg.checkConfigParameters()
    chainType = cfg.getParam('chain', 'executionMode')
    MODE = cfg.getParam('chain', 'mode')
    classifier = cfg.getParam('argTrain', 'classifier')
    classificationMode = cfg.getParam('argClassification', 'classifMode')

    if (MODE=="multi_regions" and classificationMode=="fusion" and classifier!="rf") and (MODE=="multi_regions" and classificationMode=="fusion" and classifier!="svm"):
        raise ValueError('If you chose the multi_regions mode, you must use rf or svm classifier')
        
    if chainType == "parallel":
        Launch(cfg)
    elif chainType == "sequential":
        gen_oso_sequential(cfg)
    #if 1==1:gen_oso_sequential(cfg)
    
    else:
        raise Exception("Execution mode "+chainType+" does not exist.")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "This function allows you launch the chain according to a configuration file")
    parser.add_argument("-launch.config",dest = "config",help ="path to configuration file",required=True)
    args = parser.parse_args()
    launchChain(args.config)
    """
    try:
        launchChain(args.config)
    # Exception manage by the chain
    # We only print the error message
    except serviceError.osoError as e:
        print e
    # Exception not manage (bug)
    # print error message + all stack
    except Exception as e:
        print e
        raise
    """
            
