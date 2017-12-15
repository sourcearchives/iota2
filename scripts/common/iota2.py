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


import iota2_builder as chain
import fileUtils as fut
import argparse
fut.updatePyPath()

import sys
import traceback
import datetime
import pickle
import dill
import time
import numpy as np
from mpi4py import MPI
import oso_directory
import serviceLogger
import os


# This is needed in order to be able to send pyhton objects throug MPI send
MPI.pickle.dumps = dill.dumps
MPI.pickle.loads = dill.loads

class MPIService():
    """
    Class for storing the MPI context
    """
    def __init__(self):
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()

class JobArray():
    """
    Class for storing a function to be applied to an array of parameters.
    - job is a callable object like a lambda expression; it takes a single parameter
    - param_array is a list of the parameters for each call to job
    """
    def __init__(self, job, param_array):
        self.job = job
        self.param_array = param_array

def kill_slaves(mpi_service):
    """
    kill slaves
    :param mpi_service
    """
    for i in range(1, mpi_service.size):
        print "Kill signal to slave "+str(i), "debug"
        mpi_service.comm.send(None, dest=i, tag=1)


def launchTask(function, parameter, logger, mpi_services=None):
    """
    usage : 
    IN
    OUT
    """
    logger.root.log(51,'************* SLAVE REPORT *************')
    if mpi_services:
        logger.root.log(51, "slave : " + str(mpi_services.rank))
    
    logger.root.log(51, "-----------> TRACE <-----------")

    start_job = time.time()
    start_date = datetime.datetime.now()

    try:        
        function(parameter)
        logger.root.log(51, "parameter : '" + str(parameter) + "' : ended")
    except Exception as e:
        traceback.print_exc()
        logger.root.log(51, "parameter : '" + str(parameter) + "' : failed")
        sys.exit(-1)

    end_job = time.time()
    end_date = datetime.datetime.now()

    logger.root.log(51, "---------> END TRACE <---------")
    logger.root.log(51, "Execution time [sec] : " + str(end_job - start_job))
    logger.root.log(51, "****************************************\n")

    slave_complete_log = logger.root.handlers[0].stream.getvalue()
    logger.root.handlers[0].stream.close()

    return slave_complete_log, start_date, end_date


def mpi_schedule_job_array(job_array, mpi_service=MPIService(),logPath=None, logger_lvl="INFO"):
    """
    A simple MPI scheduler to execute jobs in parallel.
    """
    job = job_array.job
    param_array_origin = job_array.param_array
    
    if not param_array_origin:
        raise Exception("JobArray must contain a list of parameter as argument")
        sys.exit(1)
    try:
        if mpi_service.rank == 0:
            if os.path.exists(logPath):
                os.remove(logPath)
            if callable(param_array_origin):
                param_array = param_array_origin()
            else:
                #shallowCopy
                param_array = [param for param in param_array_origin]
            if mpi_service.size > 1:
                # master
                nb_completed_tasks = 0
                nb_tasks = len(param_array)
                for i in range(1, mpi_service.size):
                    if len(param_array) > 0:
                        task_param = param_array.pop(0)
                        mpi_service.comm.send([job, task_param], dest=i, tag=0)
                while nb_completed_tasks < nb_tasks:
                    [slave_rank, [start, end, slave_complete_log]] = mpi_service.comm.recv(source=MPI.ANY_SOURCE, tag=0)
                    #Write slave log
                    with open(logPath,"a+") as log_f:
                        log_f.write(slave_complete_log)
                    nb_completed_tasks += 1
                    if len(param_array) > 0:
                        task_param = param_array.pop(0)
                        mpi_service.comm.send([job, task_param], dest=slave_rank, tag=0)
                kill_slaves(mpi_service)
            else:
                #if not launch thanks to mpirun, launch each parameters one by one
                for param in param_array:
                    slave_log = serviceLogger.Log_task(logger_lvl)
                    slave_complete_log, start_date, end_date = launchTask(job,
                                                                          param,
                                                                          slave_log)
                    with open(logPath,"a+") as log_f:
                        log_f.write(slave_complete_log)
        else:
            # slave
            mpi_status = MPI.Status()
            while 1:
                # waiting sending works by master
                [task_job, task_param] = mpi_service.comm.recv(source=0, tag=MPI.ANY_TAG, status=mpi_status)
                slave_log = serviceLogger.Log_task(logger_lvl)
                slave_complete_log, start_date, end_date = launchTask(task_job,
                                                                      task_param,
                                                                      slave_log,
                                                                      mpi_service)
                mpi_service.comm.send([mpi_service.rank, [start_date, end_date, slave_complete_log]], dest=0, tag=0)
    except:
        if mpi_service.rank == 0 and mpi_service.size > 1:
            print "Something went wrong, we should log errors."
            traceback.print_exc()
            kill_slaves(mpi_service)
            sys.exit(1)


if __name__ == "__main__":

    import serviceConfigFile as SCF

    parser = argparse.ArgumentParser(description = "This function allow you to"
                                                   "launch iota2 processing chain"
                                                   "as MPI process or not")

    parser.add_argument("-config",dest = "configPath",help = "path to the configuration"
                                                             "file which rule le run",
                        required=True)
    parser.add_argument("-starting_step",dest = "start",help ="start chain from 'starting_step'",
                        default=0,
                        type=int,
                        required=False)
    parser.add_argument("-ending_step",dest = "end",help ="run chain until 'ending_step'"
                                                          "-1 mean 'to the end'",
                        default=0,
                        type=int,
                        required=False)
    parser.add_argument("-parameters",dest = "parameters",help ="Launch specific parameters",
                        nargs='+',
                        default=None,
                        required=False)
                        
    args = parser.parse_args()

    cfg = SCF.serviceConfigFile(args.configPath)
    chain_to_process = chain.iota2(cfg)
    logger_lvl = cfg.getParam('chain', 'logFileLevel')

    if args.start == args.end == 0:
        all_steps = chain_to_process.get_steps_number()
        args.start = all_steps[0]
        args.end = all_steps[-1]

    #lists starts from index 0
    args.start-=1

    if args.end == -1:
        args.end = len(steps)

    steps = chain_to_process.steps

    for step in np.arange(args.start, args.end):
        params = steps[step].parameters
        if args.parameters:
            params = args.parameters
        mpi_schedule_job_array(JobArray(steps[step].jobs, params), MPIService(),
                               steps[step].logFile, logger_lvl)



