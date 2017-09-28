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

import sys
import traceback
import datetime
import pickle
import dill
from mpi4py import MPI

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

def mpi_schedule_job_array(job_array, mpi_service):
    """
    A simple MPI scheduler to execute jobs in parallel.
    """
    param_array = job_array.param_array
    job = job_array.job
    try:
        if mpi_service.rank == 0:
            # master
            nb_completed_tasks = 0
            nb_tasks = len(param_array)
            for i in range(1, mpi_service.size):
                if len(param_array)>0:
                    task_param = param_array.pop(0)
                    mpi_service.comm.send([job, task_param], dest=i, tag=0)
            while nb_completed_tasks<nb_tasks:
                [slave_rank, [start, end]] = mpi_service.comm.recv(source=MPI.ANY_SOURCE, tag=0)
                nb_completed_tasks += 1
                if len(param_array)>0:
                    task_param = param_array.pop(0)
                    mpi_service.comm.send([job, task_param], dest=slave_rank, tag=0)
            print "All tasks completed"
            kill_slaves(mpi_service)
            mpi_service.comm.Barrier()
        else:
            # slave
            mpi_status = MPI.Status()
            while 1:
                # waiting sending works by master
                print 'Slave '+str(mpi_service.rank)+' is ready...'
                [task_job, task_param] = mpi_service.comm.recv(source=0, tag=MPI.ANY_TAG, status=mpi_status)
                if mpi_status.Get_tag():
                    print 'Closed rank '+str(mpi_service.rank)
                    break
                start_date = datetime.datetime.now()
                task_job(task_param)
                end_date = datetime.datetime.now()
                mpi_service.comm.send([mpi_service.rank, [start_date, end_date]], dest=0, tag=0)

    except:
        if mpi_service.rank == 0:
            print "Something went wrong, we should log errors."
            traceback.print_exc()
            kill_slaves(mpi_service)
            mpi_service.comm.Barrier()
            sys.exit(1)

if __name__ == "__main__":
    def my_complex_function(a, b, c):
        print a
        return b+c
    param_list = list(range(10))
    ja = JobArray(lambda x: my_complex_function(x, 2, 3),param_list)
    mpi_schedule_job_array(ja, MPIService())
