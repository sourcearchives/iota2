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

import traceback
import datetime
import dill
import os
from mpi4py import MPI
import argparse
import time
import pickle
import datetime
import sys

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


def get_PBS_task_report(log_file):
    """
    usage : get if launched task succeed or failed by reading pbs job report

    OUT:
    exitCodeString [string] succeed or failed
    time [string] processing time in sec
    """
    import re

    exitCode = "-1"
    time = "-1"
    with open(log_file, "r") as f:
        for line in f:
            if "JOBEXITCODE" in re.sub('\W+', '', line):
                exitCode = re.sub('\W+', '', line)[-1]

            if "RES USED" in line.rstrip():
                walltime = line.rstrip().split("=")[-1].split(":")
                H = int(walltime[0])
                M = int(walltime[1])
                S = int(walltime[2])
                time = float(H * 3600.0 + M * 60.0 + S)

    exitCodeString = "JOB EXIT CODE not found"
    if exitCode == "0":
        exitCodeString = "Succeed"
    elif exitCode == "1" or exitCode == "2":
        exitCodeString = "Failed"

    return exitCodeString, time


def kill_slaves(mpi_service):
    """
    kill slaves
    :param mpi_service
    """
    for i in range(1, mpi_service.size):
        print "Kill signal to slave " + str(i), "debug"
        mpi_service.comm.send(None, dest=i, tag=1)




def launchBashCmd(bashCmd):
    """
    usage : function use to launch bashCmd
    """
    #using subprocess will be better.
    os.system(bashCmd)


def launch_common_task(task_function):
    exit_code = 0
    try:
        task_function()
    except Exception as e:
        print(e)
        exit_code = 1
    return exit_code


def print_main_log_report(step_name=None, job_id=None, exitCode=None,
                          Qtime=None, pTime=None, logPath=None, mode=None):
    """
    print and save trace
    """
    log_report = "\nSTEP : " + step_name + "\n"
    if mode == "Job_MPI_Tasks" or mode == "Job_Tasks":
        log_report += "\tJob id : " + job_id + "\n"
    log_report += "\tExit code : " + exitCode + "\n"
    if Qtime:
        log_report += "\tQueue time [sec] : " + str(Qtime) + "\n"
    if pTime:
        log_report += "\tProcessing time [sec] : " + str(pTime) + "\n"
    log_report += "\n------------------------------------------------------"
    print log_report

    with open(logPath, "a+") as f:
        f.write(log_report)

class Tasks():
    """
    Class tasks definition : this class launch MPI process
    """
    def __init__(self, tasks, ressources, iota2_config, MPI_service=None,
                 prev_job_id=None):
        """
        :param tasks [tuple] first element must be lambda function
                             second element is a list of variable parameter
        :param ressources [Ressources Object]
        :param prev_job_id  [string] previous job id, doesn't use but maybe in the futur
        """
        self.parameters = None
        if isinstance(tasks, tuple):
            self.jobs = tasks[0]
            self.parameters = tasks[1]
        else:
            self.jobs = tasks
        #self.MPI_service = MPI_service
        self.iota2_config = iota2_config
        self.TaskName = ressources.name

        #self.ressources = ressources
        self.nb_cpu = ressources.nb_cpu

        #self.log_err = os.path.join(self.logDirectory, self.TaskName + "_err.log")
        #self.log_out = os.path.join(self.logDirectory, self.TaskName + "_out.log")
        #self.log_chain_report = os.path.join(self.logDirectory, "IOTA2_main_report.log")
        #self.ressources.log_err = self.log_err
        #self.ressources.log_out = self.log_out

        os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = str(self.nb_cpu)
        os.environ["OMP_NUM_THREADS"] = str(self.nb_cpu)

        self.current_job_id = None
        self.previous_job_id = prev_job_id

        
        
        
        
