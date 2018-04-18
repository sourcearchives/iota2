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


# This is needed in order to be able to send python objects throug MPI send
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

def stop_workers(mpi_service):
    """
    stop workers
    :param mpi_service
    """
    for i in range(1, mpi_service.size):
        print("Worker process with rank {}/{} stopped".format(i,mpi_service.size-1))
        mpi_service.comm.send(None, dest=i, tag=1)


def launchTask(function, parameter, logger, mpi_services=None):
    """
    usage : 
    IN
    OUT
    """
    import sys
    logger.root.log(51,'************* WORKER REPORT *************')
    if mpi_services:
        logger.root.log(51, "worker : " + str(mpi_services.rank))
    
    logger.root.log(51, "-----------> TRACE <-----------")

    start_job = time.time()
    start_date = datetime.datetime.now()
    returned_data = None
    try:
        returned_data = function(parameter)
        logger.root.log(51, "parameter : '" + str(parameter) + "' : ended")
    except KeyboardInterrupt:
        raise
    except :
        traceback.print_exc()
        logger.root.log(51, "parameter : '" + str(parameter) + "' : failed")

        if mpi_services:
            stop_workers(mpi_services)
        
    end_job = time.time()
    end_date = datetime.datetime.now()

    logger.root.log(51, "---------> END TRACE <---------")
    logger.root.log(51, "Execution time [sec] : " + str(end_job - start_job))
    logger.root.log(51, "****************************************\n")

    worker_complete_log = logger.root.handlers[0].stream.getvalue()
    logger.root.handlers[0].stream.close()

    return worker_complete_log, start_date, end_date, returned_data


def mpi_schedule_job_array(job_array, mpi_service=MPIService(),logPath=None,
                           logger_lvl="INFO", enable_console=False):
    """
    A simple MPI scheduler to execute jobs in parallel.
    """
    
    if mpi_service.rank != 0:
        return None

    returned_data_list = []

    job = job_array.job
    param_array_origin = job_array.param_array
    
    if not param_array_origin:
        raise Exception("JobArray must contain a list of parameter as argument")
        sys.exit(1)
    try:
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
                    mpi_service.comm.send([job, task_param, logger_lvl, enable_console], dest=i, tag=0)
            while nb_completed_tasks < nb_tasks:
                [worker_rank, [start, end, worker_complete_log, returned_data]] = mpi_service.comm.recv(source=MPI.ANY_SOURCE, tag=0)
                returned_data_list.append(returned_data)
                #Write worker log
                with open(logPath,"a+") as log_f:
                    log_f.write(worker_complete_log)
                nb_completed_tasks += 1
                if len(param_array) > 0:
                    task_param = param_array.pop(0)
                    mpi_service.comm.send([job, task_param,logger_lvl,enable_console], dest=worker_rank, tag=0)
        else:
            #if not launch thanks to mpirun, launch each parameters one by one
            for param in param_array:
                worker_log = serviceLogger.Log_task(logger_lvl, enable_console)
                worker_complete_log, start_date, end_date, returned_data = launchTask(job,
                                                                                     param,
                                                                                     worker_log)
                with open(logPath,"a+") as log_f:
                    log_f.write(worker_complete_log)

                returned_data_list.append(returned_data)
    except KeyboardInterrupt:
        raise
    except:
        if mpi_service.rank == 0 and mpi_service.size > 1:
            print "Something went wrong, we should log errors."
            traceback.print_exc()
            stop_workers(mpi_service)
            sys.exit(1)

    return returned_data_list

def start_workers(mpi_service):
    mpi_service.comm.barrier()
    if mpi_service.rank != 0:
        # Sending started signal
        mpi_service.comm.send(mpi_service.rank,dest=0,tag=0)
        mpi_status = MPI.Status()
        while 1:
            # waiting sending works by master
            task = mpi_service.comm.recv(source=0, tag=MPI.ANY_TAG, status=mpi_status)
            if task is None:
                sys.exit(0)
            # unpack task
            
            [task_job, task_param, logger_lvl, enable_console] = task
            
            worker_log = serviceLogger.Log_task(logger_lvl, enable_console)
            
            
            worker_complete_log, start_date, end_date, returned_data = launchTask(task_job,
                                                                  task_param,
                                                                  worker_log,
                                                                  mpi_service)
            mpi_service.comm.send([mpi_service.rank, [start_date, end_date, worker_complete_log, returned_data]], dest=0, tag=0)
    else:
        nb_started_workers = 0
        while nb_started_workers < mpi_service.size-1:
            rank = mpi_service.comm.recv(source=MPI.ANY_SOURCE, tag=0)
            print("Worker process with rank {}/{} started".format(rank,mpi_service.size-1))
            nb_started_workers+=1

def print_step_summarize(iota2_chain):
    """
    usage : print iota2 steps that will be run
    """
    
    if MPIService().rank != 0:
        return None
    
    print("Full processing include the following steps (checked steps will be run): ")
    for group in iota2_chain.steps_group.keys():
        print("Group {}:".format(group))
        for key in iota2_chain.steps_group[group]:
            highlight = "[ ]"
            if key >= args.start and key<=args.end:
                highlight="[x]"
            print("\t {} Step {}: {}".format(highlight, key, iota2_chain.steps_group[group][key]))
    print("\n")


def remove_tmp_files(cfg, current_step, chain):
    """
    use to keep only /final directory
    """
    import shutil
    iota2_outputs_dir = cfg.getParam('chain', 'outputPath')

    keep_dir = ["final"]

    last_step = chain.get_steps_number()[-1]
    directories = chain.get_dir()
    dirs_to_rm = [d for d in directories if not os.path.split(d)[-1] in keep_dir]

    if current_step == last_step:
        for dir_to_rm in dirs_to_rm:
            if os.path.exists(dir_to_rm):
                shutil.rmtree(dir_to_rm)


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

    parser.add_argument("-config_ressources", dest="config_ressources",
                        help="path to IOTA2 ressources configuration file",
                        required=False)

    args = parser.parse_args()

    cfg = SCF.serviceConfigFile(args.configPath)
    cfg.checkConfigParameters()
    chain_to_process = chain.iota2(cfg, args.config_ressources)
    logger_lvl = cfg.getParam('chain', 'logFileLevel')
    enable_console = cfg.getParam('chain', 'enableConsole')

    try:
        rm_tmp = cfg.getParam('chain', 'remove_tmp_files')
    except:
        rm_tmp = False
            
    if args.start == args.end == 0:
        all_steps = chain_to_process.get_steps_number()

        args.start = all_steps[0]
        args.end = all_steps[-1]

    steps = chain_to_process.steps

    if args.end == -1:
        args.end = len(steps)

    print_step_summarize(chain_to_process)

    # Initialize MPI service
    mpi_service = MPIService()

    # Start worker processes
    start_workers(mpi_service)

    for step in np.arange(args.start, args.end+1):

        params = steps[step-1].parameters
        param_array = []
        if callable(params):
            param_array = params()
        else:                                                                                                                                                                               
            param_array = [param for param in params]

        for group in chain_to_process.steps_group.keys():
            if step in chain_to_process.steps_group[group].keys():
                print "Running step {}: {} ({} tasks)".format(step, chain_to_process.steps_group[group][step],
                                                              len(param_array))
                break

        if args.parameters:
            params = args.parameters

        mpi_schedule_job_array(JobArray(steps[step-1].jobs, params), mpi_service,
                               steps[step-1].logFile, logger_lvl)

        if rm_tmp:
            remove_tmp_files(cfg, current_step=step, chain=chain_to_process)

    stop_workers(mpi_service)

