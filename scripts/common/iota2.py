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

def mpi_schedule_job_array(job_array, mpi_service=MPIService()):#def mpi_schedule_job_array(job_array, mpi_service=MPIService()):
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
                    [slave_rank, [start, end]] = mpi_service.comm.recv(source=MPI.ANY_SOURCE, tag=0)
                    nb_completed_tasks += 1
                    if len(param_array) > 0:
                        task_param = param_array.pop(0)
                        mpi_service.comm.send([job, task_param], dest=slave_rank, tag=0)
                kill_slaves(mpi_service)
            else:
                #if not launch thanks to mpirun, launch each parameters one by one
                for param in param_array:
                    try :
                        job(param)
                    except Exception as e:
                        print (e)
                        traceback.print_exc()
                        sys.exit(1)
        else:
            # slave
            mpi_status = MPI.Status()
            while 1:
                # waiting sending works by master
                [task_job, task_param] = mpi_service.comm.recv(source=0, tag=MPI.ANY_TAG, status=mpi_status)
                if mpi_status.Get_tag() == 1:
                    print 'Closed rank ' + str(mpi_service.rank)
                    break
                start_job = time.time()
                start_date = datetime.datetime.now()
                try:
                    task_job(task_param)
                except Exception as e:
                    traceback.print_exc()
                    sys.exit(1)
                end_job = time.time()
                end_date = datetime.datetime.now()

                print "\n************* SLAVE REPORT *************"
                print "slave : " + str(mpi_service.rank)
                print "parameter : '" + str(task_param) + "' : ended"
                print "time [sec] : " + str(end_job - start_job)
                print "****************************************"
                mpi_service.comm.send([mpi_service.rank, [start_date, end_date]], dest=0, tag=0)
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
    args = parser.parse_args()

    cfg = SCF.serviceConfigFile(args.configPath)

    if args.start == args.end == 0:
        args.start = cfg.getParam('chain', 'firstStep')
        args.end = cfg.getParam('chain', 'lastStep')

    steps = chain.iota2(cfg).steps

    #lists starts from index 0
    args.start-=1

    if args.end == -1:
        args.end = len(steps)

    for step in np.arange(args.start, args.end):
        steps[step].ressources.set_env_THREADS()
        mpi_schedule_job_array(JobArray(steps[step].jobs, steps[step].parameters), MPIService())



