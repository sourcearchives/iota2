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


def mpi_schedule_job_array(job_array, mpi_service=MPIService()):
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
                    print(e)
                end_job = time.time()
                end_date = datetime.datetime.now()

                print "\n************* SLAVE REPORT *************"
                print "slave : " + str(mpi_service.rank)
                print "parameter : '" + str(task_param) + "' : ended"
                print "time [sec] : " + str(end_job - start_job)
                print "****************************************"
                mpi_service.comm.send([mpi_service.rank, [start_date, end_date]], dest=0, tag=0)

    except:
        if mpi_service.rank == 0:
            print "Something went wrong, we should log errors."
            traceback.print_exc()
            kill_slaves(mpi_service)
            sys.exit(1)


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


class Python_Task():
    """
    Class tasks definition : this class launch python process
                             which need low ressources
    """
    def __init__(self, task, iota2_config, taskName):
        if not callable(task):
            raise Exception("task not callable")
        self.task = task
        self.TaskName = taskName
        self.iota2_config = iota2_config
        outputPath = self.iota2_config.getParam("chain", "outputPath")
        self.pickleDirectory = outputPath + "/TasksObj"
        if not os.path.exists(self.pickleDirectory):
            os.mkdir(self.pickleDirectory)

        self.pickleObj = os.path.join(self.pickleDirectory, self.TaskName + ".task")
        self.logDirectory = self.iota2_config.getParam("chain", "logPath")
        self.log_chain_report = os.path.join(self.logDirectory, "IOTA2_main_report.log")

        self.log_err = os.path.join(self.logDirectory, self.TaskName + "_err.log")
        self.log_out = os.path.join(self.logDirectory, self.TaskName + "_out.log")

    def run(self):
        """
        launch tasks
        """
        import subprocess
        import pickle

        pickle.dump(self.task, open(self.pickleObj, 'wb'))
        dir_path = os.path.dirname(os.path.realpath(__file__))
        cmd = "python " + dir_path + "/launch_tasks.py -mode python -task " + self.pickleObj
        start_task = time.time()
        mpi = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        mpi.wait()
        stdout, stderr = mpi.communicate()
        end_task = time.time()
        exitCode = "Failed ? " + str(stderr)
        if not stderr:
            exitCode = "Succeed"
        else:
            exitCode = "Failed ? please check : " + self.log_err

        step_name = self.TaskName

        with open(self.log_err, "w") as f:
            f.write(stderr)
        with open(self.log_out, "w") as f:
            f.write(stdout)

        print_main_log_report(step_name=self.TaskName, job_id=None,
                              exitCode=exitCode, Qtime=None, pTime=None,
                              logPath=self.log_chain_report, mode="Python")


class Tasks():
    """
    Class tasks definition : this class launch MPI process
    """
    def __init__(self, tasks, ressources, iota2_config,
                 prev_job_id=None):
        """
        :param tasks [tuple] first element must be lambda function
                             second element is a list of variable parameter
        :param ressources [Ressources Object]
        :param prev_job_id  [string] previous job id, doesn't use but maybe in the futur
        """

        self.iota2_config = iota2_config
        self.jobs = None
        self.parameters = None
        if isinstance(tasks, tuple) and self.iota2_config.getParam("chain", "executionMode") == "parallel":
            self.launch_mode = "Job_MPI_Tasks"
            self.parameters = tasks[1]
            self.jobsFunction = tasks[0]
        elif isinstance(tasks, tuple) and not self.iota2_config.getParam("chain", "executionMode") == "parallel":
            self.launch_mode = "MPI_Tasks"
            self.parameters = tasks[1]
            self.jobsFunction = tasks[0]
        elif not isinstance(tasks, tuple) and self.iota2_config.getParam("chain", "executionMode") == "parallel":
            self.launch_mode = "Job_Tasks"
            self.jobs = tasks
        elif not isinstance(tasks, tuple) and not self.iota2_config.getParam("chain", "executionMode") == "parallel":
            self.launch_mode = "Tasks"
            self.jobs = tasks

        exeMode = self.iota2_config.getParam("chain", "executionMode")
        outputPath = self.iota2_config.getParam("chain", "outputPath")
        self.logDirectory = self.iota2_config.getParam("chain", "logPath")

        self.TaskName = ressources.name

        self.ressources = ressources
        self.nb_cpu = ressources.nb_cpu

        self.log_err = os.path.join(self.logDirectory, self.TaskName + "_err.log")
        self.log_out = os.path.join(self.logDirectory, self.TaskName + "_out.log")
        self.log_chain_report = os.path.join(self.logDirectory, "IOTA2_main_report.log")
        self.ressources.log_err = self.log_err
        self.ressources.log_out = self.log_out

        self.pickleDirectory = outputPath + "/TasksObj"
        if not os.path.exists(self.pickleDirectory):
            os.mkdir(self.pickleDirectory)

        self.pickleObj = os.path.join(self.pickleDirectory,
                                      self.ressources.name + ".task")

        os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = str(self.nb_cpu)
        os.environ["OMP_NUM_THREADS"] = str(self.nb_cpu)

        self.current_job_id = None
        self.previous_job_id = prev_job_id

        if os.path.exists(self.pickleObj):
            os.remove(self.pickleObj)

    def prepareRun(self):
        """
        """
        if callable(self.parameters):
            self.parameters = self.parameters()
        if self.launch_mode == "Job_MPI_Tasks" or self.launch_mode == "MPI_Tasks":
            self.jobs = JobArray(self.jobsFunction, self.parameters)
        #serialize object
        pickle.dump(self.jobs, open(self.pickleObj, 'wb'))

    def run(self):
        """
        launch tasks
        """
        import subprocess

        self.prepareRun()

        dir_path = os.path.dirname(os.path.realpath(__file__))
        cmd = self.ressources.build_cmd(mode=self.launch_mode, scriptPath=dir_path,
                                        pickleObj=self.pickleObj, config=self.iota2_config)
        if os.path.exists(self.log_err):
            os.remove(self.log_err)
        if os.path.exists(self.log_out):
            os.remove(self.log_out)
        #print cmd
        start_task = time.time()
        tasksExe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = tasksExe.communicate()
        tasksExe.wait()

        end_task = time.time()
        totalTime = float(end_task - start_task)
        self.current_job_id = "0"
        if self.launch_mode == "Job_MPI_Tasks" or self.launch_mode == "Job_Tasks":
            #waiting for log copy
            time.sleep(2)
            exitCode, pTime = get_PBS_task_report(self.log_out)
            self.current_job_id = stdout.rstrip()
        else:
            pTime = totalTime
            exitCode = "Succeed"
            if stderr:
                exitCode = "Failed ? please check : " + str(self.log_err)
            #write log, if not in parallel mode
            with open(self.log_err, "w") as f:
                f.write(stderr)
            with open(self.log_out, "w") as f:
                f.write(stdout)

        Qtime = "{0:.2f}".format(totalTime - pTime)
        print_main_log_report(step_name=self.TaskName, job_id=self.current_job_id,
                              exitCode=exitCode, Qtime=str(Qtime), pTime=str(pTime),
                              logPath=self.log_chain_report, mode=self.launch_mode)

    def get_current_Job_id(self):
        return self.current_job_id

    def set_previous_Job_id(self, ID):
        self.previous_job_id = ID

if __name__ == "__main__":

    import pickle
    import sys
    import os

    parser = argparse.ArgumentParser(description="This script launch tasks")
    parser.add_argument("-mode", help="launch MPI tasks or common tasks",
                        dest="mode", required=False, default="MPI",
                        choices=["MPI", "common", "python"])
    parser.add_argument("-task", help="task to launch",
                        dest="task", required=True)
    args = parser.parse_args()

    parentDir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                             os.pardir))
    sys.path.append(parentDir)
    import serviceConfigFile
    with open(args.task, 'rb') as f:
        pickleObj = pickle.load(f)
    if args.mode == "MPI":
        mpi_schedule_job_array(pickleObj, mpi_service=MPIService())
    elif args.mode == "common" or args.mode == "python":
        launch_common_task(pickleObj)
